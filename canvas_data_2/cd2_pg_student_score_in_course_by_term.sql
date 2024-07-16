-- this query against CD2 will show the "final_score" per student enrollment per course at the point in time when it is run
-- it is recommended that this be run once a day to collect the final_score points for analysis and reporting at a later time
-- you can change your SIS Term ID as necessary
--
select distinct s.final_score, p.sis_user_id, e.last_activity_at, e.workflow_state as workflow_state_user, 
  c.sis_source_id, c.workflow_state as workflow_state_course
from canvas.scores s 
  join canvas.enrollments e on e.id = s.enrollment_id 
  join canvas.courses c on c.id = e.course_id 
  join canvas.enrollment_terms et on et.id = c.enrollment_term_id 
  join canvas.users u on u.id = e.user_id 
  join canvas.pseudonyms p on p.user_id = u.id 
  join canvas.roles r on r.id = e.role_id 
where et.sis_source_id = '120241'
  and s.course_score is true 
  and e.workflow_state != 'deleted'
  and p.sis_user_id is not null
  --and s.final_score is not null
group by s.final_score, p.sis_user_id, e.last_activity_at, e.workflow_state, c.sis_source_id, c.workflow_state
order by p.sis_user_id, c.sis_source_id
