select count(*)
from canvas.courses c 
    join canvas.enrollment_terms et on et.id = c.enrollment_term_id 
where et.sis_source_id = '120231'    -- <- change your SIS term ID here
    and c.workflow_state != 'deleted'
