/* Query for view:  vw_global_state */


select *,
       total_crosswalk_real_bene - total_grants_all_real_bene as diff_total_crosswalk_vs_grant_real_bene,
       total_crosswalk_synth_bene - total_grants_all_synth_bene as diff_total_crosswalk_vs_grant_synth_bene
  from (
  select vpc,
       week_number,
       start_date,
       end_date,
       report_date, /* NOTE: This date contains top level from nightly 2am (Monday) */
       max_group_timestamp,
       max_real_bene_cnt as total_crosswalk_real_bene,
       max_synth_bene_cnt as total_crosswalk_synth_bene,
       max_global_apps_active_cnt as total_apps_in_system,
       max_global_apps_inactive_cnt as total_inactive_apps_in_system,
       max_global_apps_require_demographic_scopes_cnt as total_apps_require_demo_scopes_cnt,
       /* Counts for active apps */
       count(case when app_active=True then 1 end) as total_apps_active,
       count(case when app_real_bene_cnt > 25 and app_active=True then 1 end) as total_apps_active_bene_cnt_gt25,
       count(case when app_real_bene_cnt <= 25 and app_active=True then 1 end) as total_apps_active_bene_cnt_le25,
       count(case when app_created is not null and app_active=True then 1 end) as total_apps_active_registered,
       count(case when app_first_active is not null and app_active=True then 1 end) as total_apps_active_first_api,
       count(case when app_require_demographic_scopes=True and app_active=True then 1 end) as total_apps_active_require_demographic,
       sum(case when app_active=True then app_real_bene_cnt end) as total_grants_active_real_bene,
       sum(case when app_active=True then app_synth_bene_cnt end) as total_grants_active_synth_bene,
       /* Counts for ALL (active and in-active) apps */
       count(*) as total_apps_all,
       count(case when app_real_bene_cnt > 25 then 1 end) as total_apps_all_real_bene_gt25,
       count(case when app_real_bene_cnt <= 25 then 1 end) as total_apps_all_real_bene_le25,
       count(case when app_created is not null then 1 end) as total_apps_all_registered,
       count(case when app_first_active is not null then 1 end) as total_apps_all_first_api,
       count(case when app_require_demographic_scopes=True then 1 end) as total_apps_all_require_demographic,
       sum(app_real_bene_cnt) as total_grants_all_real_bene,
       sum(app_synth_bene_cnt) as total_grants_all_synth_bene
  from vw_global_state_per_app
  group by vpc,
           week_number,
           start_date,
           end_date,
           report_date,
           max_group_timestamp,
           max_real_bene_cnt,
           max_synth_bene_cnt,
           max_global_apps_active_cnt,
           max_global_apps_inactive_cnt,
           max_global_apps_require_demographic_scopes_cnt
  order by vpc, week_number)
