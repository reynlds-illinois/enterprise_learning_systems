select distinct p.sis_user_id as NetID,
                c.sis_source_id as CourseID, 
                COALESCE(s.override_score, s.final_score) as CourseScore
from canvas.enrollments e 
  join canvas.users u on e.user_id = u.id
  join canvas.courses c on e.course_id = c.id 
  join canvas.scores s on e.id = s.enrollment_id 
  join canvas.pseudonyms p on p.user_id = u.id
  join canvas.enrollment_terms et on et.id = c.enrollment_term_id 
where et.sis_source_id = '120245'                        -- < termID
  and e."type" = 'StudentEnrollment'
--and c.sis_source_id = 'COURSE_ID_HERE'                 -- < course ID (optional)
  and e.workflow_state in ('active', 'completed')        -- < enrollment workflow_state
  and c.workflow_state in ('completed', 'available')     -- < course workflow_state
  and s.course_score = true
  and COALESCE(s.override_score, s.final_score) <= 70    -- < course score percentage threshold
order by CourseScore desc
