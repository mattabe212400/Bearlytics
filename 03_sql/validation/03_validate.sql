-- =============================================================================
-- Phase 3 Validation Queries
-- Run after 02_import.py to confirm database integrity
-- =============================================================================

-- =============================================================================
-- SECTION 1: Row Counts
-- Expected: dim_teams=32, dim_players=510, dim_positions=18,
--           date_dimension=3653, fact_team_stats=10,
--           fact_game_logs=165, fact_player_stats=196,
--           fact_salary_data=1155, fact_nfl_league_stats=320
-- =============================================================================

SELECT 'dim_teams'            AS table_name, COUNT(*) AS row_count FROM dim_teams
UNION ALL
SELECT 'dim_players',                         COUNT(*) FROM dim_players
UNION ALL
SELECT 'dim_positions',                       COUNT(*) FROM dim_positions
UNION ALL
SELECT 'date_dimension',                      COUNT(*) FROM date_dimension
UNION ALL
SELECT 'fact_team_stats',                     COUNT(*) FROM fact_team_stats
UNION ALL
SELECT 'fact_game_logs',                      COUNT(*) FROM fact_game_logs
UNION ALL
SELECT 'fact_player_stats',                   COUNT(*) FROM fact_player_stats
UNION ALL
SELECT 'fact_salary_data',                    COUNT(*) FROM fact_salary_data
UNION ALL
SELECT 'fact_nfl_league_stats',               COUNT(*) FROM fact_nfl_league_stats;

-- =============================================================================
-- SECTION 2: Season Range Validation
-- All fact tables should cover exactly seasons 2016-2025 (10 seasons)
-- =============================================================================

SELECT 'fact_team_stats'      AS table_name,
       MIN(Season) AS min_season, MAX(Season) AS max_season,
       COUNT(DISTINCT Season) AS distinct_seasons
FROM fact_team_stats
UNION ALL
SELECT 'fact_game_logs',
       MIN(Season), MAX(Season), COUNT(DISTINCT Season)
FROM fact_game_logs
UNION ALL
SELECT 'fact_player_stats',
       MIN(Season), MAX(Season), COUNT(DISTINCT Season)
FROM fact_player_stats
UNION ALL
SELECT 'fact_salary_data',
       MIN(Season), MAX(Season), COUNT(DISTINCT Season)
FROM fact_salary_data
UNION ALL
SELECT 'fact_nfl_league_stats',
       MIN(Season), MAX(Season), COUNT(DISTINCT Season)
FROM fact_nfl_league_stats;

-- =============================================================================
-- SECTION 3: NULL Checks on Critical Columns
-- Any result > 0 indicates a data problem
-- =============================================================================

SELECT 'fact_team_stats.Season'       AS check_name, COUNT(*) AS null_count FROM fact_team_stats   WHERE Season IS NULL
UNION ALL
SELECT 'fact_team_stats.Wins',                        COUNT(*) FROM fact_team_stats   WHERE Wins IS NULL
UNION ALL
SELECT 'fact_team_stats.Points_For',                  COUNT(*) FROM fact_team_stats   WHERE Points_For IS NULL
UNION ALL
SELECT 'fact_game_logs.Season',                       COUNT(*) FROM fact_game_logs    WHERE Season IS NULL
UNION ALL
SELECT 'fact_game_logs.Week',                         COUNT(*) FROM fact_game_logs    WHERE Week IS NULL
UNION ALL
SELECT 'fact_game_logs.Result',                       COUNT(*) FROM fact_game_logs    WHERE Result IS NULL
UNION ALL
SELECT 'fact_player_stats.Player_Name',               COUNT(*) FROM fact_player_stats WHERE Player_Name IS NULL
UNION ALL
SELECT 'fact_salary_data.Player_Name',                COUNT(*) FROM fact_salary_data  WHERE Player_Name IS NULL
UNION ALL
SELECT 'fact_salary_data.Contract_Value',             COUNT(*) FROM fact_salary_data  WHERE Contract_Value IS NULL
UNION ALL
SELECT 'fact_nfl_league_stats.Team',                  COUNT(*) FROM fact_nfl_league_stats WHERE Team IS NULL
UNION ALL
SELECT 'dim_teams.Team',                              COUNT(*) FROM dim_teams         WHERE Team IS NULL
UNION ALL
SELECT 'dim_players.Player_Name',                     COUNT(*) FROM dim_players       WHERE Player_Name IS NULL;

-- =============================================================================
-- SECTION 4: Duplicate Key Checks
-- Any result > 0 means duplicate primary keys exist
-- =============================================================================

-- fact_game_logs: (Season, Week) must be unique
SELECT 'fact_game_logs duplicates' AS check_name, COUNT(*) AS dup_count
FROM (
    SELECT Season, Week, COUNT(*) AS n
    FROM fact_game_logs
    GROUP BY Season, Week
    HAVING n > 1
);

-- fact_player_stats: (Season, Player_Name) must be unique
SELECT 'fact_player_stats duplicates' AS check_name, COUNT(*) AS dup_count
FROM (
    SELECT Season, Player_Name, COUNT(*) AS n
    FROM fact_player_stats
    GROUP BY Season, Player_Name
    HAVING n > 1
);

-- fact_nfl_league_stats: (Season, Team) must be unique
SELECT 'fact_nfl_league_stats duplicates' AS check_name, COUNT(*) AS dup_count
FROM (
    SELECT Season, Team, COUNT(*) AS n
    FROM fact_nfl_league_stats
    GROUP BY Season, Team
    HAVING n > 1
);

-- =============================================================================
-- SECTION 5: Referential Integrity Checks
-- Any result > 0 means a fact-table team code has no matching dim_teams record
-- =============================================================================

-- Opponents in game logs that don't exist in dim_teams
SELECT 'game_log opponents not in dim_teams' AS check_name, COUNT(DISTINCT Opponent) AS orphan_count
FROM fact_game_logs
WHERE Opponent NOT IN (SELECT Team FROM dim_teams);

-- Teams in nfl_league_stats not in dim_teams
SELECT 'nfl_league_stats teams not in dim_teams' AS check_name, COUNT(DISTINCT Team) AS orphan_count
FROM fact_nfl_league_stats
WHERE Team NOT IN (SELECT Team FROM dim_teams);

-- =============================================================================
-- SECTION 6: Business Logic Sanity Checks
-- =============================================================================

-- Bears should always be Team = 'CHI' in player/salary tables
SELECT 'non-CHI rows in fact_player_stats' AS check_name, COUNT(*) AS row_count
FROM fact_player_stats
WHERE Team != 'CHI';

SELECT 'non-CHI rows in fact_salary_data' AS check_name, COUNT(*) AS row_count
FROM fact_salary_data
WHERE Team != 'CHI';

-- Games per season (regular season should be 16 through 2020, 17 from 2021)
SELECT Season, COUNT(*) AS games_played
FROM fact_game_logs
GROUP BY Season
ORDER BY Season;

-- Win + Loss + Ties should equal Games_Played in team stats
SELECT Season, Wins, Losses, Ties,
       Games_Played,
       (Wins + Losses + Ties)          AS wlt_sum,
       (Wins + Losses + Ties) - Games_Played AS discrepancy
FROM fact_team_stats
ORDER BY Season;

-- Points_For in team stats should roughly match sum of game logs
SELECT
    t.Season,
    t.Points_For                                    AS team_stats_pts,
    SUM(g.Points_For)                               AS game_log_sum,
    t.Points_For - SUM(g.Points_For)                AS delta
FROM fact_team_stats t
JOIN fact_game_logs g ON g.Season = t.Season
GROUP BY t.Season
ORDER BY t.Season;

-- NFL league stats: each season should have exactly 32 teams
SELECT Season, COUNT(DISTINCT Team) AS team_count
FROM fact_nfl_league_stats
GROUP BY Season
ORDER BY Season;

-- =============================================================================
-- SECTION 7: Data Profile Summary
-- =============================================================================

-- Distribution of Results in game logs
SELECT Result, COUNT(*) AS games, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_game_logs), 1) AS pct
FROM fact_game_logs
GROUP BY Result
ORDER BY games DESC;

-- Position distribution in player stats
SELECT Position, COUNT(*) AS player_seasons
FROM fact_player_stats
GROUP BY Position
ORDER BY player_seasons DESC;

-- Salary data: avg contract value by position (all seasons)
SELECT Position,
       COUNT(*)                                 AS contracts,
       ROUND(AVG(Contract_Value) / 1000000, 2)  AS avg_contract_M,
       ROUND(AVG(Guaranteed_Money) / 1000000, 2) AS avg_guaranteed_M
FROM fact_salary_data
GROUP BY Position
ORDER BY avg_contract_M DESC
LIMIT 15;
