-- =============================================================================
-- Phase 3 Reusable Views
-- Run once after 02_import.py; views persist in bearlytics.db
-- Power BI and ad-hoc queries should SELECT from these views
-- =============================================================================

-- =============================================================================
-- vw_season_summary
-- One row per season: wins, scoring, yards, turnover diff, tier label
-- Primary Power BI data source for season-trend visuals
-- =============================================================================

DROP VIEW IF EXISTS vw_season_summary;
CREATE VIEW vw_season_summary AS
SELECT
    t.Season,
    t.Wins,
    t.Losses,
    t.Ties,
    t.Games_Played,
    ROUND(CAST(t.Wins AS REAL) / t.Games_Played * 100, 1)          AS Win_Pct,
    t.Points_For,
    t.Points_Against,
    t.Point_Differential,
    ROUND(CAST(t.Points_For AS REAL)     / t.Games_Played, 1)      AS Pts_For_PG,
    ROUND(CAST(t.Points_Against AS REAL) / t.Games_Played, 1)      AS Pts_Against_PG,
    t.Passing_Yards,
    t.Rushing_Yards,
    t.Total_Offense_Yards,
    ROUND(CAST(t.Total_Offense_Yards AS REAL) / t.Games_Played, 1) AS Yards_PG,
    ROUND(CAST(t.Passing_Yards AS REAL) / t.Total_Offense_Yards * 100, 1) AS Pass_Pct,
    ROUND(CAST(t.Rushing_Yards AS REAL) / t.Total_Offense_Yards * 100, 1) AS Rush_Pct,
    t.Passing_TDs,
    t.Rushing_TDs,
    t.Total_TDs,
    t.Turnovers,
    t.Takeaways,
    t.Turnover_Differential,
    n.Offensive_Rank,
    n.Defensive_Rank,
    CASE
        WHEN t.Wins >= 9 THEN 'Playoff Contender'
        WHEN t.Wins >= 6 THEN 'Middle of Pack'
        ELSE 'Rebuilding'
    END AS Season_Tier
FROM fact_team_stats t
JOIN fact_nfl_league_stats n ON n.Season = t.Season AND n.Team = 'CHI';

-- =============================================================================
-- vw_game_log_detail
-- Game-by-game results enriched with running record and result label
-- =============================================================================

DROP VIEW IF EXISTS vw_game_log_detail;
CREATE VIEW vw_game_log_detail AS
SELECT
    g.Season,
    g.Week,
    g.Game_Date,
    g.Opponent,
    dt.Team_Name                                    AS Opponent_Full_Name,
    dt.Conference                                   AS Opponent_Conference,
    dt.Division                                     AS Opponent_Division,
    g.Home_Away,
    g.Result,
    g.Points_For,
    g.Points_Against,
    g.Point_Differential,
    g.Wins_After_Game,
    g.Losses_After_Game,
    g.Ties_After_Game,
    g.Wins_After_Game || '-' || g.Losses_After_Game ||
        CASE WHEN g.Ties_After_Game > 0 THEN '-' || g.Ties_After_Game ELSE '' END AS Record_After_Game
FROM fact_game_logs g
LEFT JOIN dim_teams dt ON dt.Team = g.Opponent;

-- =============================================================================
-- vw_player_season_stats
-- Player stats enriched with position group from dim_positions
-- =============================================================================

DROP VIEW IF EXISTS vw_player_season_stats;
CREATE VIEW vw_player_season_stats AS
SELECT
    ps.Season,
    ps.Player_Name,
    ps.Position,
    dp.Position_Group,
    ps.Team,
    ps.Games_Played,
    ps.Passing_Yards,
    ps.Passing_TDs,
    ps.Interceptions_Thrown,
    ps.Rushing_Yards,
    ps.Rushing_TDs,
    ps.Targets,
    ps.Receptions,
    ps.Receiving_Yards,
    ps.Receiving_TDs,
    ps.Total_Yards,
    ps.Total_TDs,
    ROUND(CAST(ps.Total_Yards  AS REAL) / NULLIF(ps.Games_Played, 0), 1) AS Yards_Per_Game,
    ROUND(CAST(ps.Passing_Yards AS REAL) / NULLIF(ps.Games_Played, 0), 1) AS Pass_Yds_Per_Game,
    ROUND(CAST(ps.Rushing_Yards AS REAL) / NULLIF(ps.Games_Played, 0), 1) AS Rush_Yds_Per_Game,
    ROUND(CAST(ps.Receiving_Yards AS REAL) / NULLIF(ps.Games_Played, 0), 1) AS Rec_Yds_Per_Game,
    ROUND(CAST(ps.Receptions AS REAL) / NULLIF(ps.Targets, 0) * 100, 1) AS Catch_Pct
FROM fact_player_stats ps
LEFT JOIN dim_positions dp ON dp.Position = ps.Position;

-- =============================================================================
-- vw_player_career_stats
-- Rolled-up career totals for every player who suited up for the Bears
-- =============================================================================

DROP VIEW IF EXISTS vw_player_career_stats;
CREATE VIEW vw_player_career_stats AS
SELECT
    ps.Player_Name,
    ps.Position,
    dp.Position_Group,
    MIN(ps.Season)                          AS First_Season,
    MAX(ps.Season)                          AS Last_Season,
    COUNT(DISTINCT ps.Season)               AS Seasons,
    SUM(ps.Games_Played)                    AS Career_Games,
    SUM(ps.Passing_Yards)                   AS Career_Pass_Yds,
    SUM(ps.Passing_TDs)                     AS Career_Pass_TDs,
    SUM(ps.Interceptions_Thrown)            AS Career_INTs,
    SUM(ps.Rushing_Yards)                   AS Career_Rush_Yds,
    SUM(ps.Rushing_TDs)                     AS Career_Rush_TDs,
    SUM(ps.Targets)                         AS Career_Targets,
    SUM(ps.Receptions)                      AS Career_Receptions,
    SUM(ps.Receiving_Yards)                 AS Career_Rec_Yds,
    SUM(ps.Receiving_TDs)                   AS Career_Rec_TDs,
    SUM(ps.Total_Yards)                     AS Career_Total_Yards,
    SUM(ps.Total_TDs)                       AS Career_Total_TDs
FROM fact_player_stats ps
LEFT JOIN dim_positions dp ON dp.Position = ps.Position
GROUP BY ps.Player_Name, ps.Position, dp.Position_Group;

-- =============================================================================
-- vw_salary_efficiency
-- Combines salary data with player production for cost-per-output analysis
-- =============================================================================

DROP VIEW IF EXISTS vw_salary_efficiency;
CREATE VIEW vw_salary_efficiency AS
SELECT
    s.Season,
    s.Player_Name,
    s.Position,
    dp.Position_Group,
    ROUND(s.Guaranteed_Money / 1000000, 3)      AS Guaranteed_M,
    ROUND(s.Contract_Value / 1000000, 3)        AS Contract_Value_M,
    s.Contract_Length_Years,
    p.Games_Played,
    p.Total_Yards,
    p.Total_TDs,
    p.Passing_Yards,
    p.Rushing_Yards,
    p.Receiving_Yards,
    CASE
        WHEN p.Total_Yards > 0
        THEN ROUND(s.Guaranteed_Money / p.Total_Yards, 0)
        ELSE NULL
    END AS Guaranteed_Per_Yard,
    CASE
        WHEN p.Total_TDs > 0
        THEN ROUND(s.Contract_Value / p.Total_TDs / 1000000, 3)
        ELSE NULL
    END AS Contract_Value_Per_TD_M,
    CASE
        WHEN p.Total_Yards > 1000 AND s.Guaranteed_Money / p.Total_Yards < 5000
            THEN 'High Value'
        WHEN p.Total_Yards > 500 AND s.Guaranteed_Money / p.Total_Yards < 15000
            THEN 'Fair Value'
        WHEN p.Total_Yards IS NULL OR p.Total_Yards = 0
            THEN 'Non-Skill / Injured'
        ELSE 'Overpaid'
    END AS Value_Rating
FROM fact_salary_data s
LEFT JOIN fact_player_stats p
    ON p.Season = s.Season AND p.Player_Name = s.Player_Name
LEFT JOIN dim_positions dp ON dp.Position = s.Position;

-- =============================================================================
-- vw_bears_vs_league
-- Bears season stats side-by-side with NFL averages for context
-- =============================================================================

DROP VIEW IF EXISTS vw_bears_vs_league;
CREATE VIEW vw_bears_vs_league AS
WITH league_avg AS (
    SELECT
        Season,
        ROUND(AVG(Points_For), 1)           AS Avg_League_Pts_For,
        ROUND(AVG(Points_Against), 1)        AS Avg_League_Pts_Against,
        ROUND(AVG(Total_Offense_Yards), 0)   AS Avg_League_Yards,
        ROUND(AVG(Passing_Yards), 0)         AS Avg_League_Pass_Yds,
        ROUND(AVG(Rushing_Yards), 0)         AS Avg_League_Rush_Yds
    FROM fact_nfl_league_stats
    GROUP BY Season
)
SELECT
    t.Season,
    t.Wins,
    t.Losses,
    t.Points_For                            AS CHI_Pts_For,
    l.Avg_League_Pts_For                    AS NFL_Avg_Pts_For,
    ROUND(t.Points_For - l.Avg_League_Pts_For, 1) AS Pts_For_vs_Avg,
    t.Points_Against                        AS CHI_Pts_Against,
    l.Avg_League_Pts_Against                AS NFL_Avg_Pts_Against,
    ROUND(t.Points_Against - l.Avg_League_Pts_Against, 1) AS Pts_Against_vs_Avg,
    t.Total_Offense_Yards                   AS CHI_Total_Yards,
    l.Avg_League_Yards                      AS NFL_Avg_Yards,
    ROUND(t.Total_Offense_Yards - l.Avg_League_Yards, 0) AS Yards_vs_Avg,
    t.Passing_Yards                         AS CHI_Pass_Yds,
    l.Avg_League_Pass_Yds                   AS NFL_Avg_Pass_Yds,
    t.Rushing_Yards                         AS CHI_Rush_Yds,
    l.Avg_League_Rush_Yds                   AS NFL_Avg_Rush_Yds,
    n.Offensive_Rank,
    n.Defensive_Rank
FROM fact_team_stats t
JOIN league_avg l ON l.Season = t.Season
JOIN fact_nfl_league_stats n ON n.Season = t.Season AND n.Team = 'CHI';

-- =============================================================================
-- vw_home_away_by_season
-- Home / Away splits per season for trend analysis in Power BI
-- =============================================================================

DROP VIEW IF EXISTS vw_home_away_by_season;
CREATE VIEW vw_home_away_by_season AS
SELECT
    Season,
    Home_Away,
    COUNT(*)                                                    AS Games,
    SUM(CASE WHEN Result = 'W' THEN 1 ELSE 0 END)              AS Wins,
    SUM(CASE WHEN Result = 'L' THEN 1 ELSE 0 END)              AS Losses,
    SUM(CASE WHEN Result = 'T' THEN 1 ELSE 0 END)              AS Ties,
    ROUND(SUM(CASE WHEN Result = 'W' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) AS Win_Pct,
    ROUND(AVG(Points_For), 1)                                   AS Avg_Pts_For,
    ROUND(AVG(Points_Against), 1)                               AS Avg_Pts_Against,
    ROUND(AVG(Point_Differential), 1)                           AS Avg_Diff,
    MAX(Points_For)                                             AS Max_Pts_For,
    MIN(Points_For)                                             AS Min_Pts_For
FROM fact_game_logs
GROUP BY Season, Home_Away;

-- =============================================================================
-- Quick verification: list all views
-- =============================================================================

SELECT name AS view_name
FROM sqlite_master
WHERE type = 'view'
ORDER BY name;
