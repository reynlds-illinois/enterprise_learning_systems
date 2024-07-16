-- update your student username and SIS course (source) ID below
--
select qs.submission_id, p.sis_user_id, c.sis_source_id, qs.started_at, qs.finished_at,
  (qs.finished_at - qs.started_at) as time_taken, 
   qs.score, qs.quiz_points_possible, q.title 
from canvas.quiz_submissions qs 
  join canvas.quizzes q on q.id = qs.quiz_id 
  join canvas.courses c on c.id = q.context_id 
  join canvas.users u on u.id = qs.user_id 
  join canvas.pseudonyms p on p.user_id = u.id 
where p.sis_user_id = 'USERNAME'
  and c.sis_source_id = 'SIS_COURSE_ID'
