"""REST API to determine Coach and GM of the Year for a fantasy league."""
import threading
import ff_espn_api  # pylint: disable=import-error
import flask  # pylint: disable=import-error
import fantasy_coty
from fantasy_coty.api import processor
from fantasy_coty.model import modify_db, query_db


@fantasy_coty.app.route("/api/v1/start/", methods=["GET", "POST"])
def start_processing():
    """Start processing a season."""
    context = {}

    if flask.request.method == "POST":
        # get the data from the POST request
        league_info = flask.request.get_json()
        league_id = league_info["league_id"]
        year = league_info["year"]

        query = "SELECT * FROM seasons WHERE leagueid = ? AND year = ?"
        db_row = query_db(query, [league_id, year], one=True)

        if not db_row:
            # this season has never been processed, start it up
            # TODO: check if they own the league first
            processor.jobs_mtx.acquire()
            processor.running_jobs[league_id] = (0, -1, False)
            processor.jobs_mtx.release()

            # add this season to the database and mark it as in progress
            query = "INSERT INTO seasons(leagueid, year, processed) VALUES (?, ?, ?);"
            args = [league_id, year, False]
            modify_db(query, args)

            # re-query the database to get the newly inserted row
            query = "SELECT * FROM seasons WHERE leagueid = ? AND year = ?"
            db_row = query_db(query, [league_id, year], one=True)

            thread = threading.Thread(
                target=processor.start_thread,
                args=[league_id, year, db_row["seasonid"], flask.current_app._get_current_object()],
            )
            thread.start()

        if not db_row["processed"]:
            # it's currently being processed, return its current processing location
            context["location"] = f"/api/v1/{league_id}/{year}/progress/"
            return flask.jsonify(**context), 202
        else:
            # it's done already! serve them up the endpoint where the awards data is stored
            context["location"] = f"/api/v1{league_id}/{year}/results/"
            return flask.jsonify(**context), 200

    # otherwise, redirect to search page
    return flask.redirect(flask.url_for("TODO"))


@fantasy_coty.app.route("/api/v1/<int:league_id>/<int:year>/results/", methods=["GET"])
def get_awards(league_id, year):
    """Return Coach and GM of the year for a given league.

    Example:
    {
        "coty": "Conor Rafferty",
        "coty_team": "Scituate Sailors",
        "coty_suboptimal": 199.8,
        "gmoty": "Conor D. Rafferty",
        "gmoty_team": "Scituate Sailors 2.0",
        "gmoty_optimal": 2156.42,
        "league_id": 1371476,
        "year": 2019
        "url": "/api/v1/1371476/2019/awards/"
    }
    """
    # TODO: actually add to SQL tables
    context = {}
    query = "SELECT * FROM seasons WHERE leagueid = ? AND year = ? AND processed = true"
    season_db_row = query_db(query, [league_id, year], one=True)

    if not season_db_row:
        context["message"] = "Not Found"
        context["status_code"] = "404"
        return flask.jsonify(**context), 404

    seasonid = season_db_row["seasonid"]
    coty_query = (
        "SELECT teamname, owner, optimal, actual, optimal - actual AS difference FROM "
        + "teams WHERE seasonid = ? ORDER BY difference ASC"
    )
    coty_db_row = query_db(coty_query, [seasonid])[0]

    gmoty_query = (
        "SELECT teamname, owner, optimal, actual FROM teams WHERE seasonid = ?"
        + " ORDER BY optimal DESC"
    )
    gmoty_db_row = query_db(gmoty_query, [seasonid])[0]

    context["coty"] = coty_db_row["owner"]
    context["coty_team"] = coty_db_row["teamname"]
    context["coty_suboptimal"] = coty_db_row["optimal"] - coty_db_row["actual"]

    context["gmoty"] = gmoty_db_row["owner"]
    context["gmoty_team"] = gmoty_db_row["teamname"]
    context["gmoty_optimal"] = gmoty_db_row["optimal"]

    context["league_id"] = league_id
    context["year"] = year
    context["url"] = f"/api/v1/{league_id}/{year}/awards/"

    return flask.jsonify(**context), 200


@fantasy_coty.app.route("/api/v1/<int:league_id>/<int:year>/progress/", methods=["GET"])
def get_progress(league_id, year):
    """Get a progress update from a running job."""
    context = {}

    # TODO: this should rely on a database as well

    seen = False
    processor.jobs_mtx.acquire()
    if league_id in processor.running_jobs:
        status = processor.running_jobs[league_id]
        seen = True
    processor.jobs_mtx.release()

    if not seen:
        context["message"] = "Not Found"
        context["status_code"] = "404"
        return flask.jsonify(**context), 404

    weeks_done, weeks_total, finished = status

    context["weeks_done"] = weeks_done
    context["weeks_total"] = weeks_total

    # we're finished, give them the endpoint with the results
    if finished:
        context["location"] = f"/api/v1{league_id}/{year}/results/"

    return flask.jsonify(**context), 200
