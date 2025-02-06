-- Course role enrollment counts
select count(distinct p.sis_user_id) as unique_users, 
             e."type" as course_role,
             count(e."type") as role_enrollments
from canvas.enrollments e 
  join canvas.courses c on e.course_id = c.id 
  join canvas.enrollment_terms et on c.enrollment_term_id = et.id
  join canvas.pseudonyms p on p.user_id = e.user_id 
where et.sis_source_id = '120251'
  and e.workflow_state in ('active', 'invited')
  and e."type" != 'StudentViewEnrollment'
group by e."type"
--
-- Courses under UNIT/DEPT for term
select (select a3.sis_source_id from canvas.accounts a3 where a3.id = a.parent_account_id) as parent_acct, 
  a.sis_source_id as account, c.sis_source_id as course_id
from canvas.courses c
  join canvas.accounts a on a.id = c.account_id 
  join canvas.enrollment_terms et on et.id = c.enrollment_term_id 
where et.sis_source_id = '120251'
  and c.sis_source_id is not NULL
  and (a.parent_account_id in (select a2.id
                               from canvas.accounts a2 
                               where a2.parent_account_id = 1
                                 and a2.deleted_at is null))
order by c.sis_source_id asc
--
-- Course totals under UNIT/DEPT for term
select (select a3.sis_source_id from canvas.accounts a3 where a3.id = a.parent_account_id group by a3.sis_source_id) as parent_acct, 
  a.sis_source_id as account, count(c.sis_source_id)
from canvas.courses c
  join canvas.accounts a on a.id = c.account_id 
  join canvas.enrollment_terms et on et.id = c.enrollment_term_id 
where et.sis_source_id = '120251'
  and c.sis_source_id is not NULL
  and (a.parent_account_id in (select a2.id
                               from canvas.accounts a2 
                               where a2.parent_account_id = 1
                                 and a2.deleted_at is null))
group by a.parent_account_id, a.sis_source_id
order by count desc
