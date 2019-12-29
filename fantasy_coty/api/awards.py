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
            processor.running_jobs[league_id] = None
            processor.jobs_mtx.release()

            thread = threading.Thread(target=processor.start_thread, args=[league_id, year])
            thread.start()

            # add this season to the database and mark it as in progress
            query = "INSERT INTO seasons(leagueid, year, processed) VALUES (?, ?, ?);"
            args = [league_id, year, False]
            modify_db(query, args)
            # re-query the database to get the newly inserted row
            db_row = query_db(query, [league_id, year], one=True)

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


@fantasy_coty.app.route("/api/v1/<int:league_id>/<int:year>/start/", methods=["GET"])
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
    pass


@fantasy_coty.app.route("/api/v1/<int:league_id>/<int:year>/progress/", methods=["GET"])
def get_progress(league_id, year):
    """Get a progress update from a running job."""
    context = {}
    processor.jobs_mtx.acquire()
    weeks_done, weeks_total = processor.running_jobs[league_id]
    processor.jobs_mtx.release()

    context["weeks_done"] = weeks_done
    context["weeks_total"] = weeks_total

    return flask.jsonify(**context), 200
