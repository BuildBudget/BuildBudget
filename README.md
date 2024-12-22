# BuildBudget

## Commands

Connect to prod DB

```bash
heroku pg:psql postgresql-contoured-46009 --app actions-insider
```

Pull prod DB to local DB

```bash
heroku pg:pull postgresql-contoured-46009 postgres://edu@localhost:5432/actions_insider --app actions-insider
```

Run tests

```bash
./scripts/test_and_report.sh
```

## Environment Variables

Here's a list of environment variables that need to be set in order to run the application.

 - DEBUG: Set to `True` to enable debug mode.


```mermaid
classDiagram
direction BT
class actions_data_billing {
   integer total_minutes_used
   integer total_paid_minutes_used
   integer included_minutes
   jsonb minutes_used_breakdown
   bigint id
}
class actions_data_job {
   varchar(100) name
   varchar(50) status
   varchar(50) conclusion
   timestamp with time zone created_at
   timestamp with time zone updated_at
   varchar(200) check_run_url
   timestamp with time zone completed_at
   varchar(200) html_url
   jsonb labels
   varchar(100) node_id
   integer runner_group_id
   varchar(100) runner_group_name
   integer runner_id
   varchar(100) runner_name
   timestamp with time zone started_at
   jsonb steps
   varchar(200) url
   bigint workflow_run_id
   integer id
}
class actions_data_membership {
   varchar(50) state
   varchar(50) role
   integer organization_id
   bigint user_id
   bigint id
}
class actions_data_ownerentity {
   varchar(100) login
   varchar(200) avatar_url
   varchar(100) api_token
   varchar(50) entity_type
   integer id
}
class actions_data_pullrequest {
   integer number
   varchar(200) url
   timestamp with time zone created_at
   timestamp with time zone updated_at
   integer id
}
class actions_data_repository {
   varchar(100) name
   integer owner_id
   integer id
}
class actions_data_step {
   varchar(100) name
   varchar(50) status
   varchar(50) conclusion
   timestamp with time zone created_at
   timestamp with time zone updated_at
   integer job_id
   bigint id
}
class actions_data_workflow {
   varchar(100) node_id
   varchar(100) name
   varchar(100) path
   varchar(50) state
   varchar(200) url
   varchar(200) html_url
   timestamp with time zone created_at
   timestamp with time zone updated_at
   integer repository_id
   integer id
}
class actions_data_workflowrun {
   varchar(50) status
   varchar(50) conclusion
   timestamp with time zone created_at
   timestamp with time zone updated_at
   integer repository_id
   integer workflow_id
   integer actor_id
   varchar(200) artifacts_url
   varchar(200) cancel_url
   integer check_suite_id
   varchar(100) check_suite_node_id
   varchar(200) check_suite_url
   varchar(100) display_title
   varchar(50) event
   varchar(100) head_branch
   varchar(100) head_commit
   integer head_repository_id
   varchar(100) head_sha
   varchar(200) html_url
   varchar(200) jobs_url
   varchar(200) logs_url
   varchar(100) name
   varchar(100) node_id
   varchar(100) path
   varchar(200) previous_attempt_url
   varchar(200) rerun_url
   integer run_attempt
   integer run_number
   timestamp with time zone run_started_at
   integer triggering_actor_id
   varchar(200) url
   varchar(200) workflow_url
   integer run_id
   bigint id
}
class actions_data_workflowrun_pull_requests {
   bigint workflowrun_id
   integer pullrequest_id
   bigint id
}
class actions_data_workflowrun_referenced_workflows {
   bigint workflowrun_id
   integer workflow_id
   bigint id
}
class auth_group {
   varchar(150) name
   integer id
}
class auth_group_permissions {
   integer group_id
   integer permission_id
   bigint id
}
class auth_permission {
   varchar(255) name
   integer content_type_id
   varchar(100) codename
   integer id
}
class auth_user {
   varchar(128) password
   timestamp with time zone last_login
   boolean is_superuser
   varchar(150) username
   varchar(150) first_name
   varchar(150) last_name
   varchar(254) email
   boolean is_staff
   boolean is_active
   timestamp with time zone date_joined
   integer id
}
class auth_user_groups {
   integer user_id
   integer group_id
   bigint id
}
class auth_user_user_permissions {
   integer user_id
   integer permission_id
   bigint id
}
class django_admin_log {
   timestamp with time zone action_time
   text object_id
   varchar(200) object_repr
   smallint action_flag
   text change_message
   integer content_type_id
   integer user_id
   integer id
}
class django_content_type {
   varchar(100) app_label
   varchar(100) model
   integer id
}
class django_migrations {
   varchar(255) app
   varchar(255) name
   timestamp with time zone applied
   bigint id
}
class django_session {
   text session_data
   timestamp with time zone expire_date
   varchar(40) session_key
}
class pg_stat_statements {
   oid userid
   oid dbid
   boolean toplevel
   bigint queryid
   text query
   bigint plans
   double precision total_plan_time
   double precision min_plan_time
   double precision max_plan_time
   double precision mean_plan_time
   double precision stddev_plan_time
   bigint calls
   double precision total_exec_time
   double precision min_exec_time
   double precision max_exec_time
   double precision mean_exec_time
   double precision stddev_exec_time
   bigint rows
   bigint shared_blks_hit
   bigint shared_blks_read
   bigint shared_blks_dirtied
   bigint shared_blks_written
   bigint local_blks_hit
   bigint local_blks_read
   bigint local_blks_dirtied
   bigint local_blks_written
   bigint temp_blks_read
   bigint temp_blks_written
   double precision blk_read_time
   double precision blk_write_time
   double precision temp_blk_read_time
   double precision temp_blk_write_time
   bigint wal_records
   bigint wal_fpi
   numeric wal_bytes
   bigint jit_functions
   double precision jit_generation_time
   bigint jit_inlining_count
   double precision jit_inlining_time
   bigint jit_optimization_count
   double precision jit_optimization_time
   bigint jit_emission_count
   double precision jit_emission_time
}
class pg_stat_statements_info {
   bigint dealloc
   timestamp with time zone stats_reset
}
class social_auth_association {
   varchar(255) server_url
   varchar(255) handle
   varchar(255) secret
   integer issued
   integer lifetime
   varchar(64) assoc_type
   bigint id
}
class social_auth_code {
   varchar(254) email
   varchar(32) code
   boolean verified
   timestamp with time zone timestamp
   bigint id
}
class social_auth_nonce {
   varchar(255) server_url
   integer timestamp
   varchar(65) salt
   bigint id
}
class social_auth_partial {
   varchar(32) token
   smallint next_step
   varchar(32) backend
   timestamp with time zone timestamp
   jsonb data
   bigint id
}
class social_auth_usersocialauth {
   varchar(32) provider
   varchar(255) uid
   integer user_id
   timestamp with time zone created
   timestamp with time zone modified
   jsonb extra_data
   bigint id
}

actions_data_job  -->  actions_data_workflowrun

actions_data_membership  -->  actions_data_ownerentity
actions_data_membership  -->  social_auth_usersocialauth
actions_data_repository  -->  actions_data_ownerentity
actions_data_step  -->  actions_data_job
actions_data_workflow  -->  actions_data_repository
actions_data_workflowrun  -->  actions_data_ownerentity
actions_data_workflowrun  -->  actions_data_ownerentity
actions_data_workflowrun  -->  actions_data_repository
actions_data_workflowrun  -->  actions_data_repository
actions_data_workflowrun  -->  actions_data_workflow
actions_data_workflowrun_pull_requests  -->  actions_data_pullrequest
actions_data_workflowrun_pull_requests  -->  actions_data_workflowrun
actions_data_workflowrun_referenced_workflows  -->  actions_data_workflow
actions_data_workflowrun_referenced_workflows  -->  actions_data_workflowrun
auth_group_permissions  -->  auth_group
auth_group_permissions  -->  auth_permission
auth_permission  -->  django_content_type
auth_user_groups  -->  auth_group
auth_user_groups  -->  auth_user
auth_user_user_permissions  -->  auth_permission
auth_user_user_permissions  -->  auth_user
django_admin_log  -->  auth_user
django_admin_log  -->  django_content_type
social_auth_usersocialauth  -->  auth_user

```
