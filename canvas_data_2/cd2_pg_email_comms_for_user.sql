-- query to show any email address (comm paths) associated with a
-- username in Canvas
--
select p.sis_user_id, cc."path", cc."position", cc.workflow_state
from canvas.communication_channels cc 
  join canvas.pseudonyms p on p.id = cc.pseudonym_id
where p.sis_user_id like 'ischoolhd-account%'            -- <- change this
order by p.sis_user_id asc