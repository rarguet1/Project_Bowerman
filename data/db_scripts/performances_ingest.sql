-- DROP FUNCTION IF EXISTS ingest_performances(IN payload JSONB);
CREATE OR REPLACE FUNCTION ingest_performances(IN payload JSONB)
RETURNS BIGINT
LANGUAGE PLPGSQL
AS $$
DECLARE
    record			JSONB;
    athlete_row		RECORD;
    ath_id		 	INT;
    inserted	 	BIGINT := 0;
BEGIN
    FOR record IN
        SELECT value
        FROM jsonb_array_elements(payload)
    LOOP
        -- into athletes
        INSERT INTO athletes (
            full_name, 
            school, 
            gender
        )
        VALUES (
            record->>'full_name',
            record->>'school',
            record->>'gender'
        )
        ON CONFLICT (full_name, school)
		DO NOTHING
		RETURNING athlete_id INTO ath_id;

		IF ath_id IS NULL THEN 
		SELECT athlete_id INTO ath_id 
		FROM athletes
		WHERE full_name = record->>'full_name' AND school = record->>'school';
		END IF;

        -- into performances
        INSERT INTO performances (
            athlete_id,
            event_class,
            time,
            wind,
            conference_rank,
            meet_date
        )
        VALUES (
            ath_id,
            record->>'event_class',
            record->>'time',
            record->>'wind',
            record->>'conference_rank',
            (record->>'meet_date')::DATE
        );

        inserted := inserted + 1;
    END LOOP;

    RETURN inserted;
END;
$$;
