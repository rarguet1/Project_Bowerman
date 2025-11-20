-- DROP FUNCTION IF EXISTS retrieve_all(IN season_year INT, IN team TEXT);
CREATE OR REPLACE FUNCTION retrieve_all(IN season_year INT, IN team TEXT)
RETURNS TABLE (
    ath_name TEXT,
    ath_gender TEXT,
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
        a.full_name::TEXT as ath_name, 
        a.gender::TEXT as ath_gender, 
        p.event_class::TEXT as event_type, 
        p.time::TEXT as event_time,
        p.wind::TEXT as event_wind,
        p.meet_date::DATE as event_date
    FROM athletes as a
    JOIN performances as p ON p.athlete_id = a.athlete_id
    WHERE EXTRACT(YEAR FROM p.meet_date) = season_year and a.school = team;
END;
$$;

-- THIS FUNCTION IS INCOMPLETE AND NEED TO BE EDITED!!!
-- DROP FUNCTION IF EXISTS retrieve_before_conference(IN season_year INT);
CREATE OR REPLACE FUNCTION retrieve_before_conference(IN season_year INT, team TEXT)
RETURNS TABLE (
	ath_name TEXT,
	ath_gender CHAR,
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
		a.full_name, 
		p.event_class, 
		p.time, 
		p.meet_date
	FROM athletes as a
	JOIN performances as p ON p.athlete_id = a.athlete_id
	WHERE (
		EXTRACT(YEAR FROM p.meet_date) = season 
		AND p.meet_date < MAKE_DATE(season, 5, 1));
END;
$$;
