-- =============================================================================
-- Phase 3 Business Queries
-- Answers executive-level questions about Bears performance (2016-2025)
-- =============================================================================

-- =============================================================================
-- BQ-01: Season Performance Trend
--        Core season-over-season scoreboard for Power BI dashboard
-- =============================================================================

SELECT
    Season,
    Wins,
    Losses,
    Ties,
    ROUND(CAST(Wins AS REAL) / Games_Played * 100, 1)   AS Win_Pct,
    Points_For,
    Points_Against,
    Point_Differential,
    ROUND(CAST(Points_For AS REAL) / Games_Played, 1)   AS Pts_For_PG,
    ROUND(CAST(Points_Against AS REAL) / Games_Played, 1) AS Pts_Against_PG,
    Total_Offense_Yards,
    ROUND(CAST(Total_Offense_Yards AS REAL) / Games_Played, 1) AS Yards_PG,
    Turnover_Differential,
    CASE WHEN Wins >= 9 THEN 'Playoff Contender'
         WHEN Wins >= 6 THEN 'Middle of Pack'
         ELSE 'Rebuilding'
    END AS Season_Tier
FROM fact_team_stats
ORDER BY Season;

-- =============================================================================
-- BQ-02: Playoff Contention History
--        Seasons where Bears finished 9+ wins (typical wild card threshold)
-- =============================================================================

SELECT
    Season,
    Wins,
    Losses,
    Ties,
    ROUND(CAST(Wins AS REAL) / Games_Played * 100, 1) AS Win_Pct,
    Points_For,
    Points_Against
FROM fact_team_stats
WHERE Wins >= 9
ORDER BY Wins DESC;

-- =============================================================================
-- BQ-03: Bears vs. NFL League Average by Season
--        Benchmarks Bears offense and defense against all 32 teams
-- =============================================================================

WITH league_avg AS (
    SELECT
        Season,
        ROUND(AVG(Points_For), 1)           AS Avg_League_Pts_For,
        ROUND(AVG(Points_Against), 1)        AS Avg_League_Pts_Against,
        ROUND(AVG(Total_Offense_Yards), 0)   AS Avg_League_Yards,
        ROUND(AVG(Passing_Yards), 0)         AS Avg_League_Pass_Yds,
        ROUND(AVG(Rushing_Yards), 0)         AS Avg_League_Rush_Yds,
        ROUND(AVG(CAST(Wins AS REAL) / (Wins + Losses + CASE WHEN Ties > 0 THEN Ties ELSE 0 END) * 100), 1) AS Avg_League_Win_Pct
    FROM fact_nfl_league_stats
    GROUP BY Season
)
SELECT
    t.Season,
    t.Points_For                    AS CHI_Pts_For,
    l.Avg_League_Pts_For            AS NFL_Avg_Pts_For,
    t.Points_For - l.Avg_League_Pts_For AS Pts_For_vs_Avg,
    t.Points_Against                AS CHI_Pts_Against,
    l.Avg_League_Pts_Against        AS NFL_Avg_Pts_Against,
    t.Total_Offense_Yards           AS CHI_Total_Yards,
    l.Avg_League_Yards              AS NFL_Avg_Yards,
    t.Total_Offense_Yards - l.Avg_League_Yards AS Yards_vs_Avg,
    n.Offensive_Rank,
    n.Defensive_Rank
FROM fact_team_stats t
JOIN league_avg l ON l.Season = t.Season
JOIN fact_nfl_league_stats n ON n.Season = t.Season AND n.Team = 'CHI'
ORDER BY t.Season;

-- =============================================================================
-- BQ-04: Top 10 Individual Player Seasons — Total Yards
--        Best single-season yardage performances by a Bears player
-- =============================================================================

SELECT
    Season,
    Player_Name,
    Position,
    Games_Played,
    Total_Yards,
    Total_TDs,
    Passing_Yards,
    Rushing_Yards,
    Receiving_Yards,
    ROUND(CAST(Total_Yards AS REAL) / Games_Played, 1) AS Yards_Per_Game
FROM fact_player_stats
WHERE Total_Yards > 0
ORDER BY Total_Yards DESC
LIMIT 10;

-- =============================================================================
-- BQ-05: Top QB Seasons
--        Best passing seasons in the window
-- =============================================================================

SELECT
    Season,
    Player_Name,
    Games_Played,
    Passing_Yards,
    Passing_TDs,
    Interceptions_Thrown,
    ROUND(CAST(Passing_Yards AS REAL) / Games_Played, 1)    AS Pass_Yds_Per_Game,
    ROUND(CAST(Passing_TDs AS REAL) / NULLIF(Interceptions_Thrown, 0), 2) AS TD_INT_Ratio
FROM fact_player_stats
WHERE Position = 'QB' AND Passing_Yards > 500
ORDER BY Passing_Yards DESC
LIMIT 10;

-- =============================================================================
-- BQ-06: Top RB Seasons
--        Best rushing seasons in the window
-- =============================================================================

SELECT
    Season,
    Player_Name,
    Games_Played,
    Rushing_Yards,
    Rushing_TDs,
    Receptions,
    Receiving_Yards,
    ROUND(CAST(Rushing_Yards AS REAL) / Games_Played, 1) AS Rush_Yds_Per_Game
FROM fact_player_stats
WHERE Position = 'RB' AND Rushing_Yards > 200
ORDER BY Rushing_Yards DESC
LIMIT 10;

-- =============================================================================
-- BQ-07: Top WR/TE Receiving Seasons
-- =============================================================================

SELECT
    Season,
    Player_Name,
    Position,
    Games_Played,
    Targets,
    Receptions,
    Receiving_Yards,
    Receiving_TDs,
    ROUND(CAST(Receptions AS REAL) / NULLIF(Targets, 0) * 100, 1) AS Catch_Pct,
    ROUND(CAST(Receiving_Yards AS REAL) / NULLIF(Receptions, 0), 1) AS Yards_Per_Rec
FROM fact_player_stats
WHERE Position IN ('WR', 'TE') AND Receiving_Yards > 200
ORDER BY Receiving_Yards DESC
LIMIT 10;

-- =============================================================================
-- BQ-08: Turnover Differential Impact on Win Total
--        Correlation between turnovers, takeaways, and season wins
-- =============================================================================

SELECT
    Season,
    Wins,
    Turnovers,
    Takeaways,
    Turnover_Differential,
    ROUND(CAST(Wins AS REAL) / Games_Played * 100, 1) AS Win_Pct,
    CASE
        WHEN Turnover_Differential > 0  THEN 'Positive (+)'
        WHEN Turnover_Differential = 0  THEN 'Even'
        ELSE 'Negative (-)'
    END AS TO_Diff_Category
FROM fact_team_stats
ORDER BY Turnover_Differential DESC;

-- Summary: average wins by turnover differential category
SELECT
    CASE
        WHEN Turnover_Differential > 0  THEN 'Positive (+)'
        WHEN Turnover_Differential = 0  THEN 'Even'
        ELSE 'Negative (-)'
    END AS TO_Diff_Category,
    COUNT(*)            AS Seasons,
    ROUND(AVG(Wins), 1) AS Avg_Wins,
    SUM(Wins)           AS Total_Wins
FROM fact_team_stats
GROUP BY TO_Diff_Category
ORDER BY Avg_Wins DESC;

-- =============================================================================
-- BQ-09: Salary Efficiency — Cost Per Win by Season
--        How much did each Bears win cost in guaranteed contract money?
-- =============================================================================

WITH season_payroll AS (
    SELECT
        Season,
        SUM(Guaranteed_Money)   AS Total_Guaranteed,
        SUM(Contract_Value)     AS Total_Contract_Value,
        COUNT(Player_Name)      AS Players_Under_Contract
    FROM fact_salary_data
    GROUP BY Season
)
SELECT
    t.Season,
    t.Wins,
    t.Losses,
    sp.Players_Under_Contract,
    ROUND(sp.Total_Contract_Value / 1000000, 1)         AS Total_Contract_Value_M,
    ROUND(sp.Total_Guaranteed / 1000000, 1)             AS Total_Guaranteed_M,
    ROUND(sp.Total_Contract_Value / NULLIF(t.Wins, 0) / 1000000, 2) AS Contract_Cost_Per_Win_M,
    ROUND(sp.Total_Guaranteed / NULLIF(t.Wins, 0) / 1000000, 2)     AS Guaranteed_Per_Win_M
FROM fact_team_stats t
JOIN season_payroll sp ON sp.Season = t.Season
ORDER BY t.Season;

-- =============================================================================
-- BQ-10: Salary Efficiency — Top Paid Players vs. Production
--        Identifies high/low value contracts (guaranteed money vs. total yards)
-- =============================================================================

SELECT
    s.Season,
    s.Player_Name,
    s.Position,
    ROUND(s.Guaranteed_Money / 1000000, 2)              AS Guaranteed_M,
    ROUND(s.Contract_Value / 1000000, 2)                AS Contract_Value_M,
    p.Games_Played,
    p.Total_Yards,
    p.Total_TDs,
    CASE
        WHEN p.Total_Yards > 0
        THEN ROUND(s.Guaranteed_Money / p.Total_Yards, 0)
        ELSE NULL
    END AS Guaranteed_Per_Yard,
    CASE
        WHEN p.Total_Yards > 1000 AND s.Guaranteed_Money / p.Total_Yards < 5000
            THEN 'High Value'
        WHEN p.Total_Yards > 500 AND s.Guaranteed_Money / p.Total_Yards < 15000
            THEN 'Fair Value'
        WHEN p.Total_Yards IS NULL OR p.Total_Yards = 0
            THEN 'Non-Skill Position'
        ELSE 'Overpaid'
    END AS Value_Rating
FROM fact_salary_data s
LEFT JOIN fact_player_stats p
    ON p.Season = s.Season AND p.Player_Name = s.Player_Name
WHERE s.Guaranteed_Money > 1000000
ORDER BY s.Guaranteed_Money DESC
LIMIT 30;

-- =============================================================================
-- BQ-11: Offensive Rank vs. Win Total by Season
--        Does a better offense translate to more wins for the Bears?
-- =============================================================================

SELECT
    n.Season,
    t.Wins,
    t.Losses,
    n.Offensive_Rank,
    n.Defensive_Rank,
    t.Points_For,
    t.Points_Against,
    t.Total_Offense_Yards
FROM fact_team_stats t
JOIN fact_nfl_league_stats n ON n.Season = t.Season AND n.Team = 'CHI'
ORDER BY n.Offensive_Rank ASC;

-- =============================================================================
-- BQ-12: Best and Worst Seasons — Composite Ranking
--        Ranks all 10 seasons across multiple dimensions
-- =============================================================================

SELECT
    Season,
    Wins,
    Losses,
    ROUND(CAST(Points_For AS REAL) / Games_Played, 1)       AS Pts_For_PG,
    ROUND(CAST(Total_Offense_Yards AS REAL) / Games_Played, 1) AS Yards_PG,
    Turnover_Differential,
    RANK() OVER (ORDER BY Wins DESC, Point_Differential DESC) AS Overall_Rank
FROM fact_team_stats
ORDER BY Overall_Rank;

-- =============================================================================
-- BQ-13: Streak Analysis — Consecutive Wins and Losses
--        Longest winning and losing streaks in the dataset
-- =============================================================================

WITH game_sequence AS (
    SELECT
        Season,
        Week,
        Game_Date,
        Result,
        ROW_NUMBER() OVER (ORDER BY Season, Week) AS game_num
    FROM fact_game_logs
    WHERE Result IN ('W', 'L')
),
streak_groups AS (
    SELECT
        Season, Week, Game_Date, Result, game_num,
        game_num - ROW_NUMBER() OVER (PARTITION BY Result ORDER BY game_num) AS streak_id
    FROM game_sequence
),
streaks AS (
    SELECT
        Result,
        MIN(Game_Date) AS streak_start,
        MAX(Game_Date) AS streak_end,
        COUNT(*)        AS streak_length
    FROM streak_groups
    GROUP BY Result, streak_id
)
SELECT
    Result,
    streak_start,
    streak_end,
    streak_length
FROM streaks
ORDER BY streak_length DESC
LIMIT 10;

-- =============================================================================
-- BQ-14: Division Rivals Head-to-Head Record
--        Bears record against NFC North rivals (GB, MIN, DET)
-- =============================================================================

SELECT
    Opponent,
    COUNT(*)                                                    AS Total_Games,
    SUM(CASE WHEN Result = 'W' THEN 1 ELSE 0 END)              AS Wins,
    SUM(CASE WHEN Result = 'L' THEN 1 ELSE 0 END)              AS Losses,
    SUM(CASE WHEN Result = 'T' THEN 1 ELSE 0 END)              AS Ties,
    ROUND(SUM(CASE WHEN Result = 'W' THEN 1.0 ELSE 0 END) / COUNT(*), 3) AS Win_Pct,
    ROUND(AVG(Points_For), 1)                                   AS Avg_Pts_For,
    ROUND(AVG(Points_Against), 1)                               AS Avg_Pts_Against
FROM fact_game_logs
WHERE Opponent IN ('GB', 'MIN', 'DET')
GROUP BY Opponent
ORDER BY Win_Pct DESC;

-- Division rivalry by season (for trend analysis)
SELECT
    Season,
    Opponent,
    Result,
    Points_For,
    Points_Against,
    Home_Away
FROM fact_game_logs
WHERE Opponent IN ('GB', 'MIN', 'DET')
ORDER BY Season, Opponent;

-- =============================================================================
-- BQ-15: Player Career Summary (Bears tenure)
--        Total production across all seasons with the team
-- =============================================================================

SELECT
    p.Player_Name,
    p.Position,
    dp.Position_Group,
    MIN(p.Season)                   AS First_Season,
    MAX(p.Season)                   AS Last_Season,
    COUNT(DISTINCT p.Season)        AS Seasons_Played,
    SUM(p.Games_Played)             AS Total_Games,
    SUM(p.Total_Yards)              AS Career_Yards,
    SUM(p.Total_TDs)                AS Career_TDs,
    SUM(p.Passing_Yards)            AS Career_Pass_Yds,
    SUM(p.Rushing_Yards)            AS Career_Rush_Yds,
    SUM(p.Receiving_Yards)          AS Career_Rec_Yds
FROM fact_player_stats p
LEFT JOIN dim_positions dp ON dp.Position = p.Position
GROUP BY p.Player_Name, p.Position, dp.Position_Group
HAVING SUM(p.Total_Yards) > 0
ORDER BY Career_Yards DESC
LIMIT 25;
