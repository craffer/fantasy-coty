"""Fantasy COTY development configuration."""
import os

# Root of this application, useful if it doesn't occupy an entire domain
APPLICATION_ROOT = "/"

# Database file is var/fantasy.sqlite3
DATABASE_FILENAME = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "var", "fantasy.sqlite3"
)
