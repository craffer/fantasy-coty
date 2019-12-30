"""Functions to perform optimal lineup calculations."""
import threading
import queue
from collections import defaultdict
import ff_espn_api
from fantasy_coty.model import modify_db, query_db

# map from league_id to (weeks processed, weeks total, finished)
running_jobs = {}
jobs_mtx = threading.Lock()


def start_thread(league_id, year, season_id, app):
    """Process a fantasy season in a thread."""
    with app.app_context():
        league = ff_espn_api.League(league_id=league_id, year=year)
        results = process_season(league)

        db_add_totals(results, season_id)


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


def db_add_totals(results: defaultdict(list), seasonid: int, verbose: bool = True):
    """Add team results to the database."""
    totals = {}
    for team, scores in results.items():
        actual_total = 0
        optimal_total = 0
        for actual, optimal in scores:
            actual_total += actual
            optimal_total += optimal
        totals[team] = actual_total, optimal_total

    # add each team and its calculated season totals to the database
    for team, (actual, optimal) in totals.items():
        query = (
            "INSERT INTO teams(seasonid, teamname, owner, actual, optimal) VALUES (?, ?, ?, ?, ?);"
        )
        args = [seasonid, team.team_name, team.owner, actual, optimal]
        modify_db(query, args)

    # now that that's done, update our season record in the database
    query = "UPDATE seasons SET processed = ? WHERE seasonid = ?"
    modify_db(query, [True, seasonid])
