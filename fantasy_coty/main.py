"""Initally test the ESPN FF API, using ff_espn_api."""
from collections import defaultdict
import ff_espn_api  # pylint: disable=import-error

# set it up for Delt W17, 2019 season
LEAGUE_ID = 1371476
SEASON_ID = 2019


def main():
    """Determine who had the least difference between maximum possible points and actual points."""
    league = ff_espn_api.League(league_id=LEAGUE_ID, year=SEASON_ID)
    num_weeks = league.settings.reg_season_count

    results = defaultdict(list)

    for i in range(1, num_weeks + 1):
        print(f"Processing week {i}...")
        box_scores = league.box_scores(i)
        for matchup in box_scores:
            home_scores = {}
            home_scores['starters'] = matchup.home_score
            home_scores['whole_team'] = sum([player.points for player in matchup.home_lineup])
            home_scores['difference'] = home_scores['starters'] - home_scores['whole_team']
            results[matchup.home_team].append(home_scores)

            away_scores = {}
            away_scores['starters'] = matchup.home_score
            away_scores['whole_team'] = sum([player.points for player in matchup.home_lineup])
            away_scores['difference'] = away_scores['starters'] - away_scores['whole_team']
            results[matchup.home_team].append(away_scores)

    total_differential = {}
    for team, scores in results.items():
        total_differential[team] = sum(week['difference'] for week in scores)

    sorted_differentials = sorted(total_differential.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)

    total_team_score = {}
    for team, scores in results.items():
        total_team_score[team] = sum(week['whole_team'] for week in scores)

    sorted_team_scores = sorted(total_team_score.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)

    print("\nTotal differentials over the course of a season:")
    for i, (team, total) in enumerate(sorted_differentials):
        print(f"{i + 1}. {team.team_name} differential: {total:.2f}")

    print("\nTotal team scores over the course of a season:")
    for i, (team, total) in enumerate(sorted_team_scores):
        print(f"{i + 1}. {team.team_name} total score: {total:.2f}")

    print("\nAWARDS")
    print("------")
    print(f"Coach of the year: {sorted_differentials[0][0].team_name}'s coach, whose starters" +
          f" scored just {abs(sorted_differentials[0][1]):.2f} less than the team as a whole.")
    print(f"GM of the year: {sorted_team_scores[0][0].team_name}'s GM, whose team as a whole" +
          f" scored {sorted_team_scores[0][1]:.2f} points in the {SEASON_ID} regular season.")


if __name__ == "__main__":
    main()
