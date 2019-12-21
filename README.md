# Fantasy Coach and GM of the Year

This project aims to analyze performance of a fantasy football team's starters each week relative to the performance of the entire team (bench included). This allows us to see who has the best team overall (including their bench players), and who made the most with what they had by putting up the best performances relative to their team as a whole.

## How It Works

Currently, the program operates as follows:

1. Calculate the optimal lineup for a team each week in the regular season
2. Calculate the points scored by an entire team, including bench players, for each week in the regular season
3. Award Coach of the Year to the manager whose had the least difference between the optimal lineups and their actual lineups over the course of a season, meaning they made the most of the roster they had
4. Award GM of the Year to the manager who had the highest total points (including bench players) across a season, meaning they put together the team with the best players

### Future Planning

In the future, we hope to make GM of the year more accurate by accounting for injured players, and hope to include more stats such as Owner of the Year. In the immediate future, our next goal is to allow for leagues with non-standard roster settings to use this program.
