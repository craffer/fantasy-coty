"""Fantasy COTY model (database) API."""
import sqlite3
import flask  # pylint: disable=import-error
import fantasy_coty


def dict_factory(cursor, row):
    """Convert database row objects to a dictionary.

    This is useful for building dictionaries which are
    then used to render a template.  Note that
    this would be inefficient for large queries.
    """
    output = {}
    for idx, col in enumerate(cursor.description):
        output[col[0]] = row[idx]
    return output


def get_db():
    """Open a new database connection."""
    if not hasattr(flask.g, "sqlite_db"):
        flask.g.sqlite_db = sqlite3.connect(fantasy_coty.app.config["DATABASE_FILENAME"])
        flask.g.sqlite_db.row_factory = dict_factory

        # Foreign keys have to be enabled per-connection.  This is an sqlite3
        # backwards compatibility thing.
        flask.g.sqlite_db.execute("PRAGMA foreign_keys = ON")

    return flask.g.sqlite_db


def query_db(query, args=(), one=False):
    """Query database, from sqlite3 documentation."""
    cur = get_db().execute(query, args)
    result = cur.fetchall()
    cur.close()
    return (result[0] if result else None) if one else result


def modify_db(query, args=()):
    """Modify database."""
    database = get_db()
    cur = database.execute(query, args)
    database.commit()
    cur.close()


@fantasy_coty.app.teardown_appcontext
def close_db(error):
    # pylint: disable=unused-argument
    """Close the database at the end of a request."""
    if hasattr(flask.g, "sqlite_db"):
        flask.g.sqlite_db.commit()
        flask.g.sqlite_db.close()
