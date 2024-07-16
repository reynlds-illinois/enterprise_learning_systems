select a.content_type, count(a.content_type)
from canvas.attachments a 
where a.file_state != 'deleted'
group by a.content_type 
order by count(a.content_type) desc
