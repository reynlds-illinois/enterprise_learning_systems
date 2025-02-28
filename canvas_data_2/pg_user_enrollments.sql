select e.id as enrollment_id, 
       e.created_at, 
       p.sis_user_id as net_id, 
       c.sis_source_id as course_id, 
       cs.sis_source_id as section_id, 
       et.sis_source_id as banner_term, 
       r.name as course_role,
       'https://MYURL.INSTRUCTURE.COM/' || c.id as course_link   -- generate direct link to the Canvas course
from canvas.enrollments e
  join canvas.pseudonyms p on p.user_id = e.user_id 
  join canvas.courses c on c.id = e.course_id
  join canvas.roles r on r.id = e.role_id
  join canvas.enrollment_terms et on et.id = c.enrollment_term_id 
  join canvas.course_sections cs on cs.id = e.course_section_id 
where p.sis_user_id = 'USERNAME'
  --and et.name = '2025_SPRING'    -- limit to enrollment term
