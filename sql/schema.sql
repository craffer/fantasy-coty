CREATE TABLE seasons(
    seasonid INTEGER PRIMARY KEY,
    leagueid INTEGER NOT NULL,
    year INTEGER NOT NULL,
    processed BOOLEAN NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE teams(
    teamid INTEGER PRIMARY KEY,
    seasonid INTEGER NOT NULL,
    teamname VARCHAR(31) NOT NULL,
    owner VARCHAR(64) NOT NULL,
    actual REAL NOT NULL,
    optimal REAL NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(seasonid) REFERENCES seasons(seasonid)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
