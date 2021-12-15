/*
Query for view:  vw_test_global_state

NOTE: Use this query when creating or updating this view
*/
CREATE 
OR REPLACE VIEW vw_test_global_state AS 
SELECT 
  *, 
  (
    total_crosswalk_real_bene - total_grants_all_real_bene
  ) diff_total_crosswalk_vs_grant_real_bene, 
  (
    total_crosswalk_synth_bene - total_grants_all_synth_bene
  ) diff_total_crosswalk_vs_grant_synth_bene 
FROM 
  (
    SELECT 
      vpc, 
      year,
      week_number, 
      start_date, 
      end_date, 
      report_date, 
      max_group_timestamp, 
      max_real_bene_cnt total_crosswalk_real_bene, 
      max_synth_bene_cnt total_crosswalk_synth_bene, 
      max_global_apps_active_cnt total_apps_in_system, 
      max_global_apps_inactive_cnt total_inactive_apps_in_system, 
      max_global_apps_require_demographic_scopes_cnt total_apps_require_demo_scopes_cnt, 
      "count"(
        (
          CASE WHEN (app_active = true) THEN 1 END
        )
      ) total_apps_active, 
      "count"(
        (
          CASE WHEN (
            (app_real_bene_cnt > 25) 
            AND (app_active = true)
          ) THEN 1 END
        )
      ) total_apps_active_bene_cnt_gt25, 
      "count"(
        (
          CASE WHEN (
            (app_real_bene_cnt <= 25) 
            AND (app_active = true)
          ) THEN 1 END
        )
      ) total_apps_active_bene_cnt_le25, 
      "count"(
        (
          CASE WHEN (
            (app_created IS NOT NULL) 
            AND (app_active = true)
          ) THEN 1 END
        )
      ) total_apps_active_registered, 
      "count"(
        (
          CASE WHEN (
            (app_first_active IS NOT NULL) 
            AND (app_active = true)
          ) THEN 1 END
        )
      ) total_apps_active_first_api, 
      "count"(
        (
          CASE WHEN (
            (
              app_require_demographic_scopes = true
            ) 
            AND (app_active = true)
          ) THEN 1 END
        )
      ) total_apps_active_require_demographic, 
      "sum"(
        (
          CASE WHEN (app_active = true) THEN app_real_bene_cnt END
        )
      ) total_grants_active_real_bene, 
      "sum"(
        (
          CASE WHEN (app_active = true) THEN app_synth_bene_cnt END
        )
      ) total_grants_active_synth_bene, 
      "count"(*) total_apps_all, 
      "count"(
        (
          CASE WHEN (app_real_bene_cnt > 25) THEN 1 END
        )
      ) total_apps_all_real_bene_gt25, 
      "count"(
        (
          CASE WHEN (app_real_bene_cnt <= 25) THEN 1 END
        )
      ) total_apps_all_real_bene_le25, 
      "count"(
        (
          CASE WHEN (app_created IS NOT NULL) THEN 1 END
        )
      ) total_apps_all_registered, 
      "count"(
        (
          CASE WHEN (app_first_active IS NOT NULL) THEN 1 END
        )
      ) total_apps_all_first_api, 
      "count"(
        (
          CASE WHEN (
            app_require_demographic_scopes = true
          ) THEN 1 END
        )
      ) total_apps_all_require_demographic, 
      "sum"(app_real_bene_cnt) total_grants_all_real_bene, 
      "sum"(app_synth_bene_cnt) total_grants_all_synth_bene 
    FROM 
      vw_test_global_state_per_app 
    GROUP BY 
      vpc, 
      year,
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
    ORDER BY 
      vpc ASC, 
      year ASC, 
      week_number ASC
  )
