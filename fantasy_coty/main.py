"""Fetch data using ESPN's API to determine Coach and GM of the Year for a fantasy league.

Conor Rafferty <craffer@umich.edu>
"""
import argparse
import itertools
from collections import defaultdict
import ff_espn_api  # pylint: disable=import-error


def init_league() -> ff_espn_api.League:
    """Initialize a League object from the command line arguments."""
    parser = argparse.ArgumentParser(description='Determine the fantasy Coach and GM of the Year.')
    parser.add_argument('league_id', type=int, help='ESPN FF league ID, from the URL')
    parser.add_argument('year', type=int, help='year to analyze')
    parser.add_argument('--username', '-u', type=str, help='ESPN username, if league is private',
                        default=None)
    parser.add_argument('--password', '-p', type=str, help='ESPN password, if league is private',
                        default=None)
    args = parser.parse_args()
    return ff_espn_api.League(league_id=args.league_id, year=args.year, username=args.username,
                              password=args.password)


def get_lineup_settings(matchup: ff_espn_api.Matchup) -> defaultdict(int):
    """Return the number of allowed starters for each position type."""
    home_lineup = matchup.home_lineup
    pos_counts = defaultdict(int)
    for player in home_lineup:
        if player.slot_position != 'BE':
            pos_counts[player.slot_position] += 1
    return pos_counts


def add_to_list(pos_list, settings, player) -> bool:
    """Conditionally replace the lowest scoring player in a list with this player."""
    if player.points < 0:
        return False
    if len(pos_list) < settings[player.position]:
        pos_list.append(player.points)
        return True
    # otherwise, if we beat the lowest scorer, replace it
    elif player.points > min(pos_list):
        # TODO: run flex algorithm on player we're replacing here
        pos_list[pos_list.index(min(pos_list))] = player.points
        return True
    # didn't add it to the pos_list
    return False


def calc_optimal_score(matchup: ff_espn_api.Matchup, settings: defaultdict(int), home: bool
                       ) -> float:
    """Calculate the optimal line-up score for a team in a Matchup.

    Note: this assumes standard lineup settings. We hope to fix this in the future.
    """
    # TODO: dynamically generate flex options
    flex = 'RB/WR/TE'
    # TODO: this should probably contain Players instead of scores for further analysis
    optimal = defaultdict(list)

    lineup = matchup.home_lineup if home else matchup.away_lineup
    for player in lineup:
        # add it to the optimal list for its position if it beats something in that list
        if not add_to_list(optimal[player.position], settings, player) and player.position in flex \
                and flex in settings:
            # if it didn't hit for its position and is a possible flex, test its flex potential
            add_to_list(optimal[flex], settings, player)

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
        if verbose:
            print(f"Processing week {i}...")
        box_scores = league.box_scores(i)
        for matchup in box_scores:
            home_optimal = calc_optimal_score(matchup, lineup_settings, True)
            home_scores = {}
            # actual score, from the players who started
            home_scores['starters'] = matchup.home_score
            # score of the entire team, including bench
            home_scores['whole_team'] = sum([player.points for player in matchup.home_lineup])
            # suboptimality = optimal lineup score - actual score
            home_scores['suboptimality'] = home_optimal - home_scores['starters']
            res[matchup.home_team].append(home_scores)

            away_optimal = calc_optimal_score(matchup, lineup_settings, False)
            away_scores = {}
            # actual score, from the players who started
            away_scores['starters'] = matchup.away_score
            # score of the entire team, including bench
            away_scores['whole_team'] = sum([player.points for player in matchup.away_lineup])
            # actual score - optimal lineup score
            # suboptimality = optimal lineup score - actual score
            away_scores['suboptimality'] = away_optimal - away_scores['starters']
            res[matchup.away_team].append(away_scores)

    return res


def get_sorted_suboptimals(results: defaultdict(list), verbose: bool = True
                           ) -> list((ff_espn_api.Team, float)):
    """Return a sorted list of how each team performed relative to the optimal lineup."""
    season_suboptimality = {}
    for team, scores in results.items():
        season_suboptimality[team] = sum(week['suboptimality'] for week in scores)
    sorted_res = sorted(season_suboptimality.items(), key=lambda kv: (kv[1], kv[0]))

    if verbose:
        print("\nTotal suboptimality over the course of a season:")
        for i, (team, total) in enumerate(sorted_res):
            print(f"{i + 1}. {team.team_name} points left on the bench: {total:.2f}")

    return sorted_res


def get_sorted_team_scores(results: defaultdict(list), verbose: bool = True
                           ) -> list((ff_espn_api.Team, float)):
    """Return a sorted list of how each team (including bench players) performed."""
    total_team_score = {}
    for team, scores in results.items():
        total_team_score[team] = sum(week['whole_team'] for week in scores)
    sorted_res = sorted(total_team_score.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)

    if verbose:
        print("\nTotal team scores over the course of a season:")
        for i, (team, total) in enumerate(sorted_res):
            print(f"{i + 1}. {team.team_name} total score: {total:.2f}")

    return sorted_res


def print_awards(league: ff_espn_api.League, sorted_suboptimals: list((ff_espn_api.Team, float)),
                 sorted_team_scores: list((ff_espn_api.Team, float))) -> None:
    """Print the team with the best lineups relative to optimal, and the most total team points."""
    print("\nAWARDS")
    print("------")
    print(f"Coach of the year: {sorted_suboptimals[0][0].team_name}'s coach, whose starters" +
          f" scored just {sorted_suboptimals[0][1]:.2f} less than optimal lineups.")
    print(f"GM of the year: {sorted_team_scores[0][0].team_name}'s GM, whose team as a whole" +
          f" scored {sorted_team_scores[0][1]:.2f} points in the {league.year} regular season.")


def main():
    """Fetch data and run our algorithm to determine Coach and GM of the Year."""
    league = init_league()

    results = process_season(league)

    sorted_suboptimals = get_sorted_suboptimals(results)
    sorted_team_scores = get_sorted_team_scores(results)

    print_awards(league, sorted_suboptimals, sorted_team_scores)


if __name__ == "__main__":
    main()
