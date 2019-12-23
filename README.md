# Fantasy Coach and GM of the Year

This project aims to analyze performance of a fantasy football team's starters each week relative to the performance of the entire team (bench included). This allows us to see who has the best team overall (including their bench players), and who made the most with what they had by putting up the best performances relative to their team as a whole.

## Installation

To use the program in its current form, clone this repo and (preferably after creating a Python virtual environment) install the dependencies using the command below.

```console
$ make init
```

## Usage

After following the installation instructions above, clone the repo using the command below. If your ESPN league is set to private (not viewable to public), you need to provide your EPSN credentials as the username and password parameters. Here, `league_id` is the 7-digit integer from your ESPN fantasy URL.

```console
$ python3 fantasy_coty/main.py league_id year -u USERNAME -p PASSWORD
```

## How It Works

Currently, the program operates as follows:

1. Calculate the highest score possible for a team each week in the regular season
   - This "optimal score" represents the points scored by the best legal (per the league's settings) combination of the players on a team in a given week
2. Award Coach of the Year to the manager whose team had the least difference between the optimal scores and their actual scores over the course of a season, meaning they made the most of the roster they had
3. Award GM of the Year to the manager whose team had the highest optimal score total over the course of the season, meaning they put together the best roster

## Roadmap

Our immediate goal is to add testing so that code coverage reaches 100%. In the future, we plan to make GM of the year more accurate by accounting for injured and suspended players, and plan to include more stats such as Owner of the Year (decided by creating some metric that combines Coaching and GM stats). The eventual goal is to transform this command line program into an API with a public-facing website.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
