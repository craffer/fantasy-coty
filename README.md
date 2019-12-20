# Fantasy Coach and GM of the Year

This project aims to analyze performance of a fantasy football team's starters each week relative to the performance of the entire team (bench included). This allows us to see who has the best team overall (including their bench players), and who made the most with what they had by putting up the best performances relative to their team as a whole.

## How It Works

Currently, the program operates as follows:

1. Calculate the difference between the score of players the team started - the score of the entire team (including bench players) for each week in the regular season
2. Award Coach of the Year to the manager whose had the least difference between those scores across a season, meaning they made the most of the roster they had
3. Award GM of the Year to the manager who had the highest total points (including bench players) across a season, meaning they put together the team with the best players

### Future Planning

Currently, the program doesn't account for things like injured players boosting up manager's hopes for COTY, and doesn't account for positional differences among starters and bench players. In the future, if we can use the API to determine which specific players started and which were benched, we can get a more accurate picture by quantifying "wrong decisions" made by coaches by starting one player over another.
