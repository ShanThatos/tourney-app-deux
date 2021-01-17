tourney_index
SELECT JSON_AGG(TO_JSON(tourneys) ORDER BY date ASC) AS tourneys, 
	TRIM(TO_CHAR(date, 'Month')) AS month, 
	DATE_PART('month', date) AS monthnum, 
	DATE_PART('year', date) AS year
	FROM tourneys
	GROUP BY month, monthnum, year
	ORDER BY year, monthnum;