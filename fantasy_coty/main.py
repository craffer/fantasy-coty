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
    parser.add_argument('league_id', type=int, help='ESPN FF league ID, from the URL.')
    parser.add_argument('year', type=int, help='Year to analyze.')
    args = parser.parse_args()
    return ff_espn_api.League(league_id=args.league_id, year=args.year)


def calc_optimal_score(matchup: ff_espn_api.Matchup, home: bool) -> float:
    """Calculate the optimal line-up score for a team in a Matchup.

    Note: this assumes standard lineup settings. We hope to fix this in the future.
    """
    flex = 'RB/WR/TE'
    # TODO: this should probably contain Players instead of scores for further analysis
    optimal = {
        'QB': [0],
        'RB': [0, 0],
        'WR': [0, 0],
        'TE': [0],
        flex: [0],
        'D/ST': [0],
        'K': [0]
    }

    lineup = matchup.home_lineup if home else matchup.away_lineup
    for player in lineup:
        pos_list = optimal[player.position]
        if player.position in flex:
            if player.points > min(pos_list):
                # overwrite the lowest score in this position list
                pos_list[pos_list.index(min(pos_list))] = player.points
            else:
                # check if they're the optimal flex
                optimal[flex][0] = max(optimal[flex][0], player.points)
        else:
            pos_list[0] = max(pos_list[0], player.points)

    # sum all the scores across each list in our optimal dictionary
    return sum([sum(i) for i in itertools.zip_longest(*optimal.values(), fillvalue=0)])


def process_season(league: ff_espn_api.League) -> defaultdict(list):
    """Calculate optimal scores and total team scores across a fantasy season."""
    res = defaultdict(list)

    num_weeks = league.settings.reg_season_count

    for i in range(1, num_weeks + 1):
        print(f"Processing week {i}...")
        box_scores = league.box_scores(i)
        for matchup in box_scores:
            home_optimal = calc_optimal_score(matchup, True)
            home_scores = {}
            # actual score, from the players who started
            home_scores['starters'] = matchup.home_score
            # score of the entire team, including bench
            home_scores['whole_team'] = sum([player.points for player in matchup.home_lineup])
            # suboptimality = optimal lineup score - actual score
            home_scores['suboptimality'] = home_optimal - home_scores['starters']
            res[matchup.home_team].append(home_scores)

            away_optimal = calc_optimal_score(matchup, False)
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


def get_sorted_suboptimals(results: defaultdict(list)) -> list((ff_espn_api.Team, float)):
    """Return a sorted list of how each team performed relative to the optimal lineup."""
    season_suboptimality = {}
    for team, scores in results.items():
        season_suboptimality[team] = sum(week['suboptimality'] for week in scores)
    return sorted(season_suboptimality.items(), key=lambda kv: (kv[1], kv[0]))


def get_sorted_team_scores(results: defaultdict(list)) -> list((ff_espn_api.Team, float)):
    """Return a sorted list of how each team (including bench players) performed."""
    total_team_score = {}
    for team, scores in results.items():
        total_team_score[team] = sum(week['whole_team'] for week in scores)
    return sorted(total_team_score.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)


def main():
    """Fetch data and run our algorithm to determine Coach and GM of the Year."""
    league = init_league()

    results = process_season(league)

    sorted_suboptimals = get_sorted_suboptimals(results)
    sorted_team_scores = get_sorted_team_scores(results)

    print("\nTotal suboptimality over the course of a season:")
    for i, (team, total) in enumerate(sorted_suboptimals):
        print(f"{i + 1}. {team.team_name} points left on the bench: {total:.2f}")

    print("\nTotal team scores over the course of a season:")
    for i, (team, total) in enumerate(sorted_team_scores):
        print(f"{i + 1}. {team.team_name} total score: {total:.2f}")

    print("\nAWARDS")
    print("------")
    print(f"Coach of the year: {sorted_suboptimals[0][0].team_name}'s coach, whose starters" +
          f" scored just {sorted_suboptimals[0][1]:.2f} less than optimal lineups.")
    print(f"GM of the year: {sorted_team_scores[0][0].team_name}'s GM, whose team as a whole" +
          f" scored {sorted_team_scores[0][1]:.2f} points in the {league.year} regular season.")


if __name__ == "__main__":
    main()
