-- =============================================================================
-- bearlytics.db  |  Phase 3 Schema
-- Chicago Bears Analytics Database (2016-2025)
-- =============================================================================

PRAGMA foreign_keys = ON;

-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

DROP TABLE IF EXISTS dim_teams;
CREATE TABLE dim_teams (
    Team_ID         INTEGER PRIMARY KEY,
    Team            TEXT    NOT NULL,           -- 3-letter abbrev (CHI, GB, ...)
    Team_Name       TEXT,
    Conference      TEXT,
    Division        TEXT,
    City            TEXT,
    Nickname        TEXT
);

DROP TABLE IF EXISTS dim_players;
CREATE TABLE dim_players (
    Player_ID       INTEGER PRIMARY KEY,
    Player_Name     TEXT    NOT NULL,
    Position        TEXT,
    First_Season    INTEGER,
    Last_Season     INTEGER
);

DROP TABLE IF EXISTS dim_positions;
CREATE TABLE dim_positions (
    Position_ID     INTEGER PRIMARY KEY,
    Position        TEXT    NOT NULL,
    Position_Group  TEXT                        -- Offense / Defense / Special Teams
);

DROP TABLE IF EXISTS date_dimension;
CREATE TABLE date_dimension (
    Date        TEXT    PRIMARY KEY,            -- YYYY-MM-DD
    Year        INTEGER,
    Season      INTEGER,
    Quarter     INTEGER,
    Month       INTEGER,
    Month_Name  TEXT,
    Week        INTEGER,
    Day         INTEGER,
    Day_Name    TEXT,
    Is_Weekend  TEXT                            -- True / False
);

-- =============================================================================
-- FACT TABLES
-- =============================================================================

-- Bears season-level totals (one row per season)
DROP TABLE IF EXISTS fact_team_stats;
CREATE TABLE fact_team_stats (
    Season                  INTEGER PRIMARY KEY,
    Wins                    INTEGER,
    Losses                  INTEGER,
    Ties                    INTEGER,
    Points_For              INTEGER,
    Points_Against          INTEGER,
    Point_Differential      INTEGER,
    Games_Played            INTEGER,
    Passing_Yards           INTEGER,
    Rushing_Yards           INTEGER,
    Total_Offense_Yards     INTEGER,
    Passing_TDs             INTEGER,
    Rushing_TDs             INTEGER,
    Total_TDs               INTEGER,
    Turnovers               INTEGER,
    Takeaways               INTEGER,
    Turnover_Differential   INTEGER
);

-- Bears individual game results
DROP TABLE IF EXISTS fact_game_logs;
CREATE TABLE fact_game_logs (
    Season              INTEGER NOT NULL,
    Week                INTEGER NOT NULL,
    Game_Date           TEXT,
    Opponent            TEXT,
    Home_Away           TEXT,                  -- Home / Away
    Result              TEXT,                  -- W / L / T
    Points_For          INTEGER,
    Points_Against      INTEGER,
    Point_Differential  INTEGER,
    Wins_After_Game     INTEGER,
    Losses_After_Game   INTEGER,
    Ties_After_Game     INTEGER,
    PRIMARY KEY (Season, Week)
);

-- Bears player individual season stats
DROP TABLE IF EXISTS fact_player_stats;
CREATE TABLE fact_player_stats (
    Season              INTEGER NOT NULL,
    Player_Name         TEXT    NOT NULL,
    Position            TEXT,
    Team                TEXT,
    Passing_Yards       INTEGER,
    Passing_TDs         INTEGER,
    Interceptions_Thrown INTEGER,
    Rushing_Yards       INTEGER,
    Rushing_TDs         INTEGER,
    Targets             INTEGER,
    Receptions          INTEGER,
    Receiving_Yards     INTEGER,
    Receiving_TDs       INTEGER,
    Games_Played        INTEGER,
    Total_Yards         INTEGER,
    Total_TDs           INTEGER,
    PRIMARY KEY (Season, Player_Name)
);

-- Bears player salary/contract data
DROP TABLE IF EXISTS fact_salary_data;
CREATE TABLE fact_salary_data (
    Season                  INTEGER NOT NULL,
    Player_Name             TEXT    NOT NULL,
    Position                TEXT,
    Team                    TEXT,
    Guaranteed_Money        REAL,
    Contract_Value          REAL,
    Contract_Length_Years   INTEGER,
    PRIMARY KEY (Season, Player_Name)
);

-- NFL league-wide stats for all 32 teams (enables Bears vs. league comparisons)
DROP TABLE IF EXISTS fact_nfl_league_stats;
CREATE TABLE fact_nfl_league_stats (
    Season                  INTEGER NOT NULL,
    Team                    TEXT    NOT NULL,
    Wins                    INTEGER,
    Losses                  INTEGER,
    Ties                    INTEGER,
    Win_Percentage          REAL,
    Points_For              INTEGER,
    Points_Against          INTEGER,
    Point_Differential      INTEGER,
    Passing_Yards           INTEGER,
    Rushing_Yards           INTEGER,
    Total_Offense_Yards     INTEGER,
    Passing_TDs             INTEGER,
    Rushing_TDs             INTEGER,
    Turnovers               INTEGER,
    Takeaways               INTEGER,
    Turnover_Differential   INTEGER,
    Offensive_Rank          INTEGER,
    Defensive_Rank          INTEGER,
    PRIMARY KEY (Season, Team)
);
