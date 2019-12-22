# Fantasy Coach and GM of the Year

This project aims to analyze performance of a fantasy football team's starters each week relative to the performance of the entire team (bench included). This allows us to see who has the best team overall (including their bench players), and who made the most with what they had by putting up the best performances relative to their team as a whole.

## Installation

To use the program in its current form, clone this repo and (preferably after creating a Python virtual environment) install the dependencies using the command below.

```bash
pip3 install -r requirements.txt
```

## Usage

After following the installation instructions above, clone the repo using the command below. If your ESPN league is set to private (not viewable to public), you need to provide your EPSN credentials as the username and password parameters. Here, `league_id` is the 7-digit integer from your ESPN fantasy URL.

```bash
python3 fantasy_coty/main.py league_id year -u USERNAME -p PASSWORD
```

## How It Works

Currently, the program operates as follows:

1. Calculate the optimal lineup for a team each week in the regular season
2. Calculate the points scored by an entire team, including bench players, for each week in the regular season
3. Award Coach of the Year to the manager whose had the least difference between the optimal lineups and their actual lineups over the course of a season, meaning they made the most of the roster they had
4. Award GM of the Year to the manager who had the highest total points (including bench players) across a season, meaning they put together the team with the best players

## Roadmap

Our immediate goal is to add testing so that code coverage reaches 100%. In the future, we plan to make GM of the year more accurate by accounting for injured and suspended players, and plan to include more stats such as Owner of the Year (decided by creating some metric that combines Coaching and GM stats). The eventual goal is to transform this command line program into an API with a public-facing website.
