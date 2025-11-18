-- DROP FUNCTION IF EXISTS retrieve_all(IN season INT);
CREATE OR REPLACE FUNCTION retrieve_all(IN season INT)
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
		a.gender, 
		p.event_class, 
		p.time, 
		p.meet_date
	FROM athletes as a
	JOIN performances as p ON p.athlete_id = a.athlete_id
	WHERE EXTRACT(YEAR FROM p.meet_date) = season;
END;
$$;

-- DROP FUNCTION IF EXISTS retrieve_before_conference(IN season INT);
CREATE OR REPLACE FUNCTION retrieve_before_conference(IN season INT)
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
	RETURNS QUERY
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
