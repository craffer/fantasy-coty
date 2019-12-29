"""Functions to perform optimal lineup calculations."""
import threading
import queue
from collections import defaultdict
import ff_espn_api

# map from league_id to (weeks processed, weeks total, finished)
running_jobs = {}
jobs_mtx = threading.Lock()


def start_thread(league_id, year):
    """Process a fantasy season in a thread."""
    league = ff_espn_api.League(league_id=league_id, year=year)
    results = process_season(league)

    sorted_suboptimals = get_suboptimality(results)
    sorted_totals = get_optimal_points_for(results)

    finished_context = get_awards_dict(league, sorted_suboptimals, sorted_totals)


def get_lineup_settings(matchup: ff_espn_api.Matchup) -> defaultdict(int):
    """Return the number of allowed starters for each position type."""
    home_lineup = matchup.home_lineup
    pos_counts = defaultdict(int)
    for player in home_lineup:
        if player.slot_position != "BE":
            pos_counts[player.slot_position] += 1
    return pos_counts


def add_to_optimal(
    optimal: defaultdict(ff_espn_api.BoxPlayer),
    settings: defaultdict(int),
    player: ff_espn_api.BoxPlayer,
):
    """Conditionally replace the lowest scoring player at this position with this player."""
    pos_list = optimal[player.position]
    # if a player scores negative points, they'll never be optimal
    if player.points < 0:
        return optimal

    # if the optimal lineup hasn't reached the max players for this position yet, it must be
    # optimal (so far) to include this player
    if len(pos_list) < settings[player.position]:
        pos_list.append(player)
        return optimal

    # otherwise, if we beat the lowest scorer, replace it
    lowest_scorer = min(pos_list, key=lambda x: x.points)
    q = queue.Queue()

    if player.points > lowest_scorer.points:
        min_index = pos_list.index(lowest_scorer)
        q.put(lowest_scorer)
        pos_list[min_index] = player
    else:
        q.put(player)

    # if we're evciting a player or deciding not to place our current player, we need to check
    # if its optimal for any of the spots that its eligible for, and the same for the player we
    # evict there
    while not q.empty():
        curr = q.get()
        for pos in curr.eligibleSlots:
            if pos in settings and pos not in ["BE", "IR"]:
                pos_list = optimal[pos]
                # same replacement logic as above, just in the FLEX (or other eligible) position
                if len(pos_list) < settings[pos]:
                    pos_list.append(curr)
                    return optimal
                lowest_scorer = min(pos_list, key=lambda x: x.points)
                if curr.points > lowest_scorer.points:
                    min_index = pos_list.index(lowest_scorer)
                    q.put(lowest_scorer)
                    pos_list[min_index] = curr

    return optimal


def calc_optimal_score(
    matchup: ff_espn_api.Matchup, settings: defaultdict(int), home: bool
) -> float:
    """Calculate the optimal line-up score for a team in a Matchup."""
    # dictionary from position to list of optimal Players
    optimal = defaultdict(list)

    lineup = matchup.home_lineup if home else matchup.away_lineup
    for player in lineup:
        # add it to the optimal list for its position if it beats something in that list
        add_to_optimal(optimal, settings, player)

    # sum all the scores across each list in our optimal dictionary
    opt_score = 0.0
    for lst in optimal.values():
        for player in lst:
            opt_score += player.points

    return opt_score


def process_season(league: ff_espn_api.League, verbose: bool = True) -> defaultdict(list):
    """Calculate optimal scores and total team scores across a fantasy season."""
    res = defaultdict(list)

    num_weeks = league.settings.reg_season_count
    # calculate the number of starters for each position from the first matchup
    lineup_settings = get_lineup_settings(league.box_scores(1)[0])

    for i in range(1, num_weeks + 1):
        jobs_mtx.acquire()
        running_jobs[league.league_id] = (i, num_weeks, False)
        jobs_mtx.release()

        if verbose:
            print(f"Processing week {i}...")

        box_scores = league.box_scores(i)
        for matchup in box_scores:
            # append a tuple of (actual score, optimal score) for both teams in the matchup
            res[matchup.home_team].append(
                (matchup.home_score, calc_optimal_score(matchup, lineup_settings, True))
            )
            res[matchup.away_team].append(
                (matchup.away_score, calc_optimal_score(matchup, lineup_settings, False))
            )

    jobs_mtx.acquire()
    running_jobs[league.league_id] = (num_weeks, num_weeks, True)
    jobs_mtx.release()

    # return a map from team -> list of above tuples, one for each week in the regular season
    return res


def get_suboptimality(
    results: defaultdict(list), verbose: bool = True
) -> list((ff_espn_api.Team, float)):
    """Return a sorted list of how each team performed relative to the optimal lineup."""
    season_suboptimality = {}
    for team, scores in results.items():
        season_suboptimality[team] = sum(optimal - actual for actual, optimal in scores)
    sorted_res = sorted(season_suboptimality.items(), key=lambda kv: (kv[1], kv[0]))

    if verbose:
        print("\nTotal suboptimality over the course of a season:")
        for i, (team, total) in enumerate(sorted_res):
            print(f"{i + 1}. {team.team_name} points left on the bench: {total:.2f}")

    return sorted_res


def get_optimal_points_for(
    results: defaultdict(list), verbose: bool = True
) -> list((ff_espn_api.Team, float)):
    """Return a sorted list of how each team (including bench players) performed."""
    optimal_season_total = {}
    for team, scores in results.items():
        optimal_season_total[team] = sum(optimal for actual, optimal in scores)
    sorted_res = sorted(optimal_season_total.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)

    if verbose:
        print("\nOptimal points for over the course of a season:")
        for i, (team, total) in enumerate(sorted_res):
            print(f"{i + 1}. {team.team_name} optimal total score: {total:.2f}")

    return sorted_res


def get_awards_dict(
    league: ff_espn_api.League,
    sorted_suboptimals: list((ff_espn_api.Team, float)),
    sorted_totals: list((ff_espn_api.Team, float)),
) -> None:
    """Print the team with the best lineups relative to optimal, and the most total team points."""
    coty_team, coty_sub = sorted_suboptimals[0]
    gmoty_team, gmoty_points = sorted_totals[0]

    context = {}

    context["coty"] = coty_team.owner
    context["coty_team"] = coty_team.team_name
    context["coty_suboptimal"] = round(coty_sub, 2)

    context["gmoty"] = gmoty_team.owner
    context["gmoty_team"] = gmoty_team.team_name
    context["gmoty_optimal"] = round(gmoty_points, 2)

    context["league_id"] = league.league_id
    context["year"] = league.year

    context["url"] = f"/api/v1/{league.league_id}/{league.year}/awards/"

    return context
