/* Query for view:  vw_global_state_per_app */

select t1.vpc,
       t1.week_number,
       t1.start_date,
       t1.end_date,
       t1.report_date,
       t1.max_group_timestamp,
       t1.max_real_bene_cnt,
       t1.max_synth_bene_cnt,
       t1.max_global_apps_active_cnt,
       t1.max_global_apps_inactive_cnt,
       t1.max_global_apps_require_demographic_scopes_cnt,
       t2.name as app_name,
       t2.created as app_created,
       t2.active as app_active,
       t2.first_active as app_first_active,
       t2.last_active as app_last_active,
       t2.require_demographic_scopes as app_require_demographic_scopes,
       t2.real_bene_cnt as app_real_bene_cnt,
       t2.synth_bene_cnt as app_synth_bene_cnt,
       t2.user_organization as app_user_organization
  from (select vpc,
               week_number,
               min(e_date) - interval '1' day as start_date,
               max(e_date) - interval '1' day as end_date,
               max(e_date) as report_date,
               max(group_timestamp) as max_group_timestamp,
               max(real_bene_cnt) as max_real_bene_cnt,
               max(synth_bene_cnt) as max_synth_bene_cnt,
               max(global_apps_active_cnt) as max_global_apps_active_cnt,
               max(global_apps_inactive_cnt) as max_global_apps_inactive_cnt,
               max(global_apps_require_demographic_scopes_cnt) as max_global_apps_require_demographic_scopes_cnt
          from (select vpc,
                       CAST(from_iso8601_timestamp(time_of_event) as DATE) as e_date,
                       extract(week from (CAST(from_iso8601_timestamp(time_of_event) as DATE) - interval '1' day)) as week_number,
                       group_timestamp,
                       real_bene_cnt,
                       synth_bene_cnt,
                       global_apps_active_cnt,
                       global_apps_inactive_cnt,
                       global_apps_require_demographic_scopes_cnt
                 from  bb2.events_global_state)
         group by vpc, week_number) as t1
JOIN bb2.events_global_state_apps as t2 on t1.max_group_timestamp = t2.group_timestamp
                                           and t1.vpc = t2.vpc
                                           /* Exclude known internal test and non-3rd party apps below */
                                           and t2.name != 'TestApp' 
                                           and t2.name != 'BlueButton Client (Test - Internal Use Only)' 
                                           and t2.name != 'MyMedicare PROD'
                                           and t2.name != 'new-relic'
