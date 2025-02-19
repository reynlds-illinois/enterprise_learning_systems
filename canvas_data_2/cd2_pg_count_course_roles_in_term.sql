-- you can change the SIS term ID as needed
-- I disallowed StudentViewEnrollment and any enrollment states that are NOT "active" or "invited"
--
SELECT ed.type, count(ed.type) AS TOTAL
FROM canvas.enrollments ed
  JOIN canvas.courses cd on cd.id = ed.course_id
  JOIN canvas.enrollment_terms etd on etd.id = cd.enrollment_term_id
  JOIN canvas.accounts ad on ad.id = cd.account_id
WHERE etd.sis_source_id = '120221'
  AND (ed.workflow_state = 'active' OR ed.workflow_state = 'invited')
  AND ed.type != 'StudentViewEnrollment'
GROUP BY ed.type
