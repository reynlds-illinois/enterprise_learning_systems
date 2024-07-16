-- you can change your SIS Term ID
--
select c.sis_source_id, c.id as c_course_id, p.sis_user_id, a.id as c_assignment_id, a.title, a.due_at, s.submitted_at, AGE(s.submitted_at, a.due_at)
from canvas.submissions s 
  join canvas.courses c on c.id = s.course_id 
  join canvas.assignments a on a.id = s.assignment_id 
  join canvas.pseudonyms p on p.user_id = s.user_id 
  join canvas.enrollment_terms et on et.id = c.enrollment_term_id 
where et.sis_source_id = '120235'
  and date(s.submitted_at) > date(a.due_at)
order by p.sis_user_id, a.due_at desc
