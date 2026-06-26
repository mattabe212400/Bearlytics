-- =============================================================================
-- Phase 3 Exploratory Queries
-- Initial data discovery before formal business analysis
-- =============================================================================

-- =============================================================================
-- 1. Season Record Overview
--    Bears W-L-T record and win percentage for every season
-- =============================================================================

SELECT
    Season,
    Wins,
    Losses,
    Ties,
    Games_Played,
    ROUND(CAST(Wins AS REAL) / Games_Played, 3)     AS Win_Pct,
    Points_For,
    Points_Against,
    Point_Differential
FROM fact_team_stats
ORDER BY Season;

-- =============================================================================
-- 2. Scoring Efficiency by Season
--    Points per game (offense and defense)
-- =============================================================================

SELECT
    Season,
    Games_Played,
    ROUND(CAST(Points_For AS REAL)     / Games_Played, 1) AS Pts_For_Per_Game,
    ROUND(CAST(Points_Against AS REAL) / Games_Played, 1) AS Pts_Against_Per_Game,
    ROUND(CAST(Point_Differential AS REAL) / Games_Played, 1) AS Diff_Per_Game
FROM fact_team_stats
ORDER BY Pts_For_Per_Game DESC;

-- =============================================================================
-- 3. Offensive Balance: Passing vs. Rushing Split by Season
-- =============================================================================

SELECT
    Season,
    Passing_Yards,
    Rushing_Yards,
    Total_Offense_Yards,
    ROUND(CAST(Passing_Yards AS REAL) / Total_Offense_Yards * 100, 1) AS Pass_Pct,
    ROUND(CAST(Rushing_Yards AS REAL) / Total_Offense_Yards * 100, 1) AS Rush_Pct,
    ROUND(CAST(Total_Offense_Yards AS REAL) / Games_Played, 1)         AS Yards_Per_Game
FROM fact_team_stats
ORDER BY Season;

-- =============================================================================
-- 4. Turnover Differential by Season
--    Relationship between turnovers and wins
-- =============================================================================

SELECT
    Season,
    Wins,
    Turnovers,
    Takeaways,
    Turnover_Differential,
    ROUND(CAST(Wins AS REAL) / Games_Played, 3) AS Win_Pct
FROM fact_team_stats
ORDER BY Turnover_Differential DESC;

-- =============================================================================
-- 5. Home vs. Away Performance (all seasons combined)
-- =============================================================================

SELECT
    Home_Away,
    COUNT(*)                                                    AS Games,
    SUM(CASE WHEN Result = 'W' THEN 1 ELSE 0 END)              AS Wins,
    SUM(CASE WHEN Result = 'L' THEN 1 ELSE 0 END)              AS Losses,
    SUM(CASE WHEN Result = 'T' THEN 1 ELSE 0 END)              AS Ties,
    ROUND(AVG(Points_For), 1)                                   AS Avg_Points_For,
    ROUND(AVG(Points_Against), 1)                               AS Avg_Points_Against,
    ROUND(AVG(Point_Differential), 1)                           AS Avg_Diff,
    ROUND(SUM(CASE WHEN Result = 'W' THEN 1.0 ELSE 0 END) / COUNT(*), 3) AS Win_Pct
FROM fact_game_logs
GROUP BY Home_Away;

-- =============================================================================
-- 6. Home vs. Away Breakdown by Season
-- =============================================================================

SELECT
    Season,
    Home_Away,
    COUNT(*)                                                    AS Games,
    SUM(CASE WHEN Result = 'W' THEN 1 ELSE 0 END)              AS Wins,
    SUM(CASE WHEN Result = 'L' THEN 1 ELSE 0 END)              AS Losses,
    ROUND(AVG(Points_For), 1)                                   AS Avg_Pts_For,
    ROUND(AVG(Points_Against), 1)                               AS Avg_Pts_Against
FROM fact_game_logs
GROUP BY Season, Home_Away
ORDER BY Season, Home_Away;

-- =============================================================================
-- 7. Monthly / Weekly Scoring Distribution
--    Average points scored by week of the season
-- =============================================================================

SELECT
    Week,
    COUNT(*)                        AS Games_Played,
    ROUND(AVG(Points_For), 1)       AS Avg_Pts_For,
    ROUND(AVG(Points_Against), 1)   AS Avg_Pts_Against,
    MIN(Points_For)                 AS Min_Pts_For,
    MAX(Points_For)                 AS Max_Pts_For
FROM fact_game_logs
GROUP BY Week
ORDER BY Week;

-- =============================================================================
-- 8. Best and Worst Individual Games
-- =============================================================================

-- Top 10 wins by margin
SELECT Season, Week, Game_Date, Opponent, Home_Away, Points_For, Points_Against, Point_Differential
FROM fact_game_logs
WHERE Result = 'W'
ORDER BY Point_Differential DESC
LIMIT 10;

-- Top 10 losses by margin
SELECT Season, Week, Game_Date, Opponent, Home_Away, Points_For, Points_Against, Point_Differential
FROM fact_game_logs
WHERE Result = 'L'
ORDER BY Point_Differential ASC
LIMIT 10;

-- =============================================================================
-- 9. Most Frequently Faced Opponents
-- =============================================================================

SELECT
    Opponent,
    COUNT(*)                                                    AS Games,
    SUM(CASE WHEN Result = 'W' THEN 1 ELSE 0 END)              AS Wins,
    SUM(CASE WHEN Result = 'L' THEN 1 ELSE 0 END)              AS Losses,
    ROUND(AVG(Points_For), 1)                                   AS Avg_Pts_For,
    ROUND(AVG(Points_Against), 1)                               AS Avg_Pts_Against,
    ROUND(SUM(CASE WHEN Result = 'W' THEN 1.0 ELSE 0 END) / COUNT(*), 3) AS Win_Pct
FROM fact_game_logs
GROUP BY Opponent
ORDER BY Games DESC, Win_Pct DESC;

-- =============================================================================
-- 10. Player Count and Unique Positions by Season
-- =============================================================================

SELECT
    Season,
    COUNT(DISTINCT Player_Name)     AS Unique_Players,
    COUNT(DISTINCT Position)        AS Unique_Positions,
    SUM(Total_TDs)                  AS Total_Team_TDs,
    SUM(Total_Yards)                AS Total_Team_Yards
FROM fact_player_stats
GROUP BY Season
ORDER BY Season;

-- =============================================================================
-- 11. Position Group Depth (how many players per position each season)
-- =============================================================================

SELECT
    p.Position_Group,
    ps.Position,
    COUNT(DISTINCT ps.Player_Name)  AS Players,
    COUNT(DISTINCT ps.Season)       AS Seasons_Active
FROM fact_player_stats ps
LEFT JOIN dim_positions p ON p.Position = ps.Position
GROUP BY p.Position_Group, ps.Position
ORDER BY p.Position_Group, Players DESC;

-- =============================================================================
-- 12. Salary Cap Snapshot — Total Payroll by Season
-- =============================================================================

SELECT
    Season,
    COUNT(DISTINCT Player_Name)                             AS Players_On_Books,
    ROUND(SUM(Contract_Value) / 1000000, 1)                 AS Total_Contract_Value_M,
    ROUND(SUM(Guaranteed_Money) / 1000000, 1)               AS Total_Guaranteed_M,
    ROUND(AVG(Contract_Value) / 1000000, 2)                 AS Avg_Contract_Value_M,
    ROUND(AVG(Guaranteed_Money) / 1000000, 2)               AS Avg_Guaranteed_M
FROM fact_salary_data
GROUP BY Season
ORDER BY Season;

-- =============================================================================
-- 13. Date Dimension Sanity — Coverage Check
-- =============================================================================

SELECT
    Season,
    COUNT(*) AS Days_In_Season,
    MIN(Date) AS First_Day,
    MAX(Date) AS Last_Day
FROM date_dimension
GROUP BY Season
ORDER BY Season;
