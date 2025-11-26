-- DROP FUNCTION IF EXISTS retrieve_team_context(IN season_year INT);
CREATE OR REPLACE FUNCTION retrieve_team_context(IN season_year INT)
RETURNS TABLE (
    ath_id INT,
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
        a.gender::TEXT as ath_gender,
        a.school::TEXT as ath_team,
        p.year::TEXT as ath_year,
        p.event_class::TEXT as event_type, 
        p.time::TEXT as event_time,
        p.wind::TEXT as event_wind,
        p.meet_date::DATE as event_date
    FROM athletes as a
    JOIN performances as p ON p.athlete_id = a.athlete_id
    WHERE EXTRACT(YEAR FROM p.meet_date) = season_year;
END;
$$;

-- DROP FUNCTION IF EXISTS retrieve_conference_context(IN season_year INT);
CREATE OR REPLACE FUNCTION retrieve_conference_context(IN season_year INT)
RETURNS TABLE (
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
        a.full_name::TEXT as ath_name,
        a.gender::TEXT as ath_gender,
        a.school::TEXT as ath_team,
        p.event_class::TEXT as event_type,
        p.meet_date::DATE as event_date
    FROM athletes as a
    JOIN performances as p ON p.athlete_id = a.athlete_id
    WHERE (
        EXTRACT(YEAR FROM p.meet_date) = season_year 
        AND p.meet_date > MAKE_DATE(season_year, 5, 1)
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
    WHERE EXTRACT(YEAR FROM p.meet_date) = season_year AND a.school = team AND p.event_class = event_class
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