-- you can change the SIS ID of your term if needed
-- I chose to only count "active" and "invited" enrollments
-- I specifically disallowed "StudentViewEnrollment" and the "Test Student" name
--
SELECT date(ed.created_at) as EnrollDate, count(date(ed.created_at)) as Enrollments
--SELECT distinct date(ed.created_at) as EnrollDate, pd.sis_user_id, cd.sis_source_id
FROM canvas.enrollments ed
  JOIN canvas.courses cd on cd.id = ed.course_id
  JOIN canvas.enrollment_terms etd on etd.id = cd.enrollment_term_id
  JOIN canvas.accounts ad on ad.id = cd.account_id
  JOIN canvas.users ud on ud.id = ed.user_id
  JOIN canvas.pseudonyms pd on pd.user_id = ud.id
WHERE etd.sis_source_id = '120225'
  AND (ed.workflow_state = 'active' OR ed.workflow_state = 'invited')
  AND ed.type != 'StudentViewEnrollment'
  AND ud.name NOT LIKE 'Test Student'
GROUP BY date(ed.created_at)
ORDER BY date(ed.created_at) desc
