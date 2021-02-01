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