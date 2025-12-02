-- DROP FUNCTION IF EXISTS retrieve_team_context(IN season_year INT, IN team TEXT);
CREATE OR REPLACE FUNCTION retrieve_team_context(IN season_year INT, IN team TEXT)
RETURNS TABLE (
    ath_id INT,
    ath_name TEXT,
    ath_gender TEXT,
    ath_team TEXT,
    ath_year TEXT,
    event_type TEXT,
    event_time TEXT,
    event_wind TEXT,
    event_date DATE
)
LANGUAGE PLPGSQL
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.athlete_id as ath_id,
        a.full_name::TEXT as ath_name,
        a.gender::TEXT as ath_gender,
        a.school::TEXT as ath_team,
        p.student_year::TEXT as ath_year,
        p.event_class::TEXT as event_type, 
        p.time::TEXT as event_time,
        p.wind::TEXT as event_wind,
        p.meet_date::DATE as event_date
    FROM athletes as a
    JOIN performances as p ON p.athlete_id = a.athlete_id
    WHERE (
        p.meet_date > MAKE_DATE(season_year, 1, 1)
        AND p.meet_date < MAKE_DATE(season_year, 5, 1)
        AND a.school = team);
END;
$$;

-- DROP FUNCTION IF EXISTS retrieve_opponent_context_agg(IN season_year INT, IN exclude_team TEXT);
CREATE OR REPLACE FUNCTION retrieve_opponent_context_agg(IN season_year INT, IN exclude_team TEXT)
RETURNS TABLE (
    ath_id INT,
    ath_name TEXT,
    ath_gender TEXT,
    ath_team TEXT,
    ath_year TEXT,
    event_type TEXT,
    event_time TEXT,
    event_wind TEXT,
    event_date DATE
)
LANGUAGE PLPGSQL
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.athlete_id as ath_id,
        a.full_name::TEXT as ath_name,
        a.gender::TEXT as ath_gender,
        a.school::TEXT as ath_team,
        p.student_year::TEXT as ath_year,
        p.event_class::TEXT as event_type, 
        p.time::TEXT as event_time,
        p.wind::TEXT as event_wind,
        p.meet_date::DATE as event_date
    FROM athletes as a
    JOIN performances as p ON p.athlete_id = a.athlete_id
    WHERE ( -- correlated subquery!!!! 
        p.meet_date > MAKE_DATE(season_year, 1, 1)
        AND p.meet_date < MAKE_DATE(season_year, 5, 1)
        AND a.school != exclude_team
        AND (
            CASE
                -- mm:ss.ss
                WHEN p.time LIKE '%:%' THEN
                    split_part(p.time, ':', 1)::NUMERIC * 60 
                    + split_part(p.time, ':', 2)::NUMERIC

                -- ss.ss
                ELSE
                    p.time::NUMERIC
			END
        ) = (
            SELECT MIN(
                CASE
                    WHEN p2.time LIKE '%:%' THEN
                        split_part(p2.time, ':', 1)::NUMERIC * 60
                        + split_part(p2.time, ':', 2)::NUMERIC

                    ELSE
                        p2.time::NUMERIC
				END
            )
            FROM athletes as a2
            JOIN performances as p2 ON p2.athlete_id = a2.athlete_id
            WHERE (
                p2.meet_date > MAKE_DATE(season_year, 1, 1)
                AND p2.meet_date < MAKE_DATE(season_year, 5, 1)
                AND a2.school != exclude_team
                AND a2.school = a.school
                AND a2.gender = a.gender
                AND p2.event_class = p.event_class
            )
        )
    );
END;
$$;  

-- DROP FUNCTION IF EXISTS retrieve_conference_context(IN season_year INT);
CREATE OR REPLACE FUNCTION retrieve_conference_context(IN season_year INT)
RETURNS TABLE (
    ath_id INT,
    ath_name TEXT,
    ath_gender TEXT,
    ath_team TEXT,
    event_type TEXT,
    event_date DATE
)
LANGUAGE PLPGSQL
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.athlete_id as ath_id, 
        a.full_name::TEXT as ath_name,
        a.gender::TEXT as ath_gender,
        a.school::TEXT as ath_team,
        p.event_class::TEXT as event_type,
        p.meet_date::DATE as event_date
    FROM athletes as a
    JOIN performances as p ON p.athlete_id = a.athlete_id
    WHERE (
        p.meet_date > MAKE_DATE(season_year, 5, 1)
        AND p.meet_date < MAKE_DATE(season_year, 5, 10));
END;
$$;

-- DROP FUNCTION IF EXISTS retrieve_event_performance(IN season INT, IN team TEXT, IN event_class TEXT);
CREATE OR REPLACE FUNCTION retrieve_event_performance(IN season_year INT, IN team TEXT, IN event_class TEXT)
RETURNS TABLE(
    ath_id INT,
    ath_name TEXT,
    event_time TEXT
)
LANGUAGE PLPGSQL
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.athlete_id as ath_id,
        a.full_name::TEXT as ath_name,
        p.event_time::TEXT as event_time
    FROM athletes as a
    JOIN performances as p ON p.athlete_id = a.athlete_id
    WHERE (
        p.meet_date > MAKE_DATE(season_year, 1, 1)
        AND p.meet_date < MAKE_DATE(season_year, 5, 1)
        AND a.school = team
        AND p.event_class = event_class
    )
    ORDER BY p.event_time ASC;
END;
$$;

-- DROP FUNCTION IF EXISTS get_teams_years();
CREATE OR REPLACE FUNCTION get_teams_years()
RETURNS TABLE(
    season_year INT,
    school TEXT
)
LANGUAGE PLPGSQL
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        EXTRACT(YEAR FROM p.meet_date)::INT as meet_year,
        a.school::TEXT as school
    FROM athletes as a
    JOIN performances as p ON p.athlete_id = a.athlete_id
    GROUP BY (meet_year, a.school)
    ORDER BY meet_year ASC;
END;
$$;

-- DROP FUNCTION IF EXISTS get_events();
CREATE OR REPLACE FUNCTION get_events()
RETURNS TABLE (event_type TEXT)
LANGUAGE PLPGSQL
AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT(event_class)::TEXT
    FROM performances;
END;
$$;