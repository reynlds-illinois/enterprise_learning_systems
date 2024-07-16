-- you can change your list of SIS Term IDs
-- I also disallowed StudentViewEnrollment type
--
SELECT etd.sis_source_id as banner_term, ed."type" as role, count(distinct p.sis_user_id) as users, count(ed.id) as enrollments
FROM canvas.enrollments ed
  JOIN canvas.courses cd on cd.id = ed.course_id
  JOIN canvas.enrollment_terms etd on etd.id = cd.enrollment_term_id
  JOIN canvas.accounts ad on ad.id = cd.account_id
  join canvas.users u on u.id = ed.user_id 
  join canvas.pseudonyms p on p.user_id = u.id
WHERE etd.sis_source_id in ('120198', 
                            '120200', '120201', '120205', '120208', 
                            '120210', '120211', '120215', '120218', 
                            '120220', '120221', '120225', '120228', 
                            '120230', '120231', '120235', '120238',
                            '120238', '120240', '120241')
  AND ed.workflow_state in ('active', 'invited')
  AND ed.type != 'StudentViewEnrollment'
GROUP BY etd.sis_source_id, ed."type"
order by etd.sis_source_id asc
