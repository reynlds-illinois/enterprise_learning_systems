select e."type" , count(e."type")
from canvas.enrollments e 
  join canvas.courses c on e.course_id = c.id 
  join canvas.users u on e.user_id = u.id 
  join canvas.pseudonyms p on p.user_id = u.id 
  join canvas.enrollment_terms et on c.enrollment_term_id = et.id
  join canvas.course_sections cs on cs.course_id = c.id
where et.sis_source_id = '120238'
  and e.workflow_state in ('active', 'invited')
  and e."type" != 'StudentViewEnrollment'
group by e."type" 
