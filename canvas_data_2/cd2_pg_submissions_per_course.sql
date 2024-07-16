-- you can update your SIS course (source) ID
--
select c.sis_source_id, a.title, p.sis_user_id, a.points_possible, s.submitted_at, s.grade, s.graded_at 
from canvas.submissions s 
  join canvas.assignments a on a.id = s.assignment_id 
  join canvas.courses c on c.id = s.course_id 
  join canvas.users u on u.id = s.user_id 
  join canvas.pseudonyms p on p.user_id = u.id 
  join canvas.enrollment_terms et on et.id = c.enrollment_term_id 
where c.sis_source_id like '%_229717'
order by a.title, p.sis_user_id
