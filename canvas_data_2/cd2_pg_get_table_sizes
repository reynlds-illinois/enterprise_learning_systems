select schemaname, relname as table_name,
       pg_size_pretty(pg_relation_size(quote_ident(schemaname) ||'.'|| quote_ident(relname))) as table_size 
from (select schemaname, relname 
      from pg_stat_user_tables order by relname) t
