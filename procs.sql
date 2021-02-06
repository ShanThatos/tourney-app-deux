tourney_index
SELECT JSON_AGG(TO_JSON(tourneys) ORDER BY date ASC) AS tourneys, 
	TRIM(TO_CHAR(date, 'Month')) AS month, 
	DATE_PART('month', date)::int AS monthnum, 
	DATE_PART('year', date)::int AS year
	FROM tourneys
	GROUP BY month, monthnum, year
	ORDER BY year, monthnum;
tourney_index_coach_info
SELECT JSON_OBJECT_AGG(tourney_id, TO_JSON(tourneycoach)) AS data FROM tourneycoach WHERE coach_id = %s;
virtual_adv_reg
SELECT JSON_OBJECT_AGG(tourney_id, t.json_object_agg) AS data FROM 
	(SELECT tourney_id, JSON_OBJECT_AGG(student_id, t.json_object_agg) FROM 
		(SELECT tourney_id, student_id, JSON_OBJECT_AGG(test, taking_test)
			FROM tourneystudent ts, students s
			WHERE taking_test AND ts.student_id = s.id AND s.coach_id = %s
			GROUP BY tourney_id, student_id) t
		GROUP BY tourney_id) t;
virtual_adv_reg_check
SELECT * FROM tourneystudent WHERE (tourney_id, student_id, test) IN %s AND taking_test;
virtual_tourney_reg
SELECT JSON_OBJECT_AGG(student_id, t.json_object_agg) AS data FROM 
	(SELECT student_id, JSON_OBJECT_AGG(test, taking_test)
		FROM tourneystudent ts, students s
		WHERE taking_test AND ts.student_id = s.id AND s.coach_id = %s AND ts.tourney_id = %s
		GROUP BY student_id) t;
virtual_tourney_scores
SELECT JSON_OBJECT_AGG(student_id, t.json_object_agg) AS data FROM 
	(SELECT student_id, JSON_OBJECT_AGG(test, TO_JSON(ts))
		FROM tourneystudent ts, students s
		WHERE taking_test AND ts.student_id = s.id AND s.coach_id = %s AND ts.tourney_id = %s
		GROUP BY student_id) t;
tourney_attending
SELECT *, 
	(SELECT JSONB_OBJECT_AGG(t.sl, t.k)
		FROM (SELECT t.sl, 
			(JSONB_OBJECT_AGG(t.test, count) || JSONB_BUILD_OBJECT('T', SUM(count))) AS k
			FROM (SELECT t.sl, t.test, COUNT(*)
				FROM (SELECT *, (CASE WHEN s.grade <= 5 THEN 'E' ELSE 'M' END) AS sl
						FROM tourneystudent ts, students s
						WHERE ts.student_id = s.id
							AND ts.tourney_id = tc.tourney_id
							AND s.coach_id = c.id
							AND ts.taking_test) t
				GROUP BY t.sl, t.test) t
			GROUP BY t.sl) t) AS data
	FROM tourneycoach tc, coaches c
	WHERE tc.coach_id = c.id AND tc.tourney_id = %s
	ORDER BY school_name, name;
results_individual_grade_test
SELECT *, (s.first_name || ' ' || s.last_name) AS name,
	(CASE WHEN s.school_id IS NOT NULL THEN
		(SELECT sh.name FROM schools sh WHERE s.school_id = sh.id)
		ELSE (SELECT c.school_name FROM coaches c WHERE s.coach_id = c.id)
	END) AS school_name, 
	(CASE WHEN EXISTS(
			SELECT * FROM tourneystudent ts2, students s2
				WHERE ts2.student_id = s2.id
					AND ts2.tourney_id = ts.tourney_id
					AND s2.grade = s.grade
					AND ts2.test = ts.test
					AND ts2.score = ts.score
					AND s2.id <> s.id
		) THEN ts.score::TEXT || ts.tie
		ELSE ts.score::TEXT END) AS score_display
	FROM tourneystudent ts, students s
	WHERE ts.student_id = s.id
		AND ts.tourney_id = %s
		AND s.grade = %s
		AND ts.test = %s
	ORDER BY score DESC, tie ASC;