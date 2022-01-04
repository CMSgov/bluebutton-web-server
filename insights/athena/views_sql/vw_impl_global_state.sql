/*
Query for view:  vw_impl_global_state

NOTE: Use this query when creating or updating this view
*/
CREATE 
OR REPLACE VIEW vw_impl_global_state AS 
SELECT 
  *, 
  (
    total_crosswalk_real_bene - app_grants_all_real_bene
  ) diff_total_crosswalk_vs_grant_and_archived_real_bene, 
  (
    total_crosswalk_synthetic_bene - app_grants_all_synthetic_bene
  ) diff_total_crosswalk_vs_grant_and_archived_synthetic_bene 
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
      /*
      NOTE: Metrics in this section prefixed by "total_" come from the 
            type = "global_state_metrics", 
            where counts are performed at time of logging.
      */
      max_crosswalk_real_bene_count total_crosswalk_real_bene, 
      max_crosswalk_synthetic_bene_count total_crosswalk_synthetic_bene, 
      max_crosswalk_table_count total_crosswalk_table_count,
      max_crosswalk_archived_table_count total_crosswalk_archived_table_count,
      max_grant_real_bene_count total_grant_real_bene_count,
      max_grant_synthetic_bene_count total_grant_synthetic_bene_count,
      max_grant_table_count total_grant_table_count,
      max_grant_archived_table_count total_grant_archived_table_count,
      max_grant_real_bene_deduped_count total_grant_real_bene_deduped_count,
      max_grant_synthetic_bene_deduped_count total_grant_synthetic_bene_deduped_count,
      max_grantarchived_real_bene_deduped_count total_grantarchived_real_bene_deduped_count,
      max_grantarchived_synthetic_bene_deduped_count total_grantarchived_synthetic_bene_deduped_count,
      max_grant_and_archived_real_bene_deduped_count total_grant_and_archived_real_bene_deduped_count,
      max_grant_and_archived_synthetic_bene_deduped_count total_grant_and_archived_synthetic_bene_deduped_count,
      max_token_real_bene_deduped_count total_token_real_bene_deduped_count,
      max_token_synthetic_bene_deduped_count total_token_synthetic_bene_deduped_count,
      max_token_table_count total_token_table_count,
      max_token_archived_table_count total_token_archived_table_count,
      max_global_apps_active_cnt total_apps_in_system, 
      max_global_apps_inactive_cnt total_inactive_apps_in_system, 
      max_global_apps_require_demographic_scopes_cnt total_apps_require_demo_scopes_cnt, 
      /*
      NOTE: Metrics in this section prefixed by "app_" come from the 
            type = "global_state_metrics_per_app",
            where the counts/sums are performed in SQL below.
      */
      "count"(
        (
          CASE WHEN (app_active = true) THEN 1 END
        )
      ) app_total_active, 
      "count"(
        (
          CASE WHEN (
            (app_real_bene_cnt > 25) 
            AND (app_active = true)
          ) THEN 1 END
        )
      ) app_active_bene_cnt_gt25, 
      "count"(
        (
          CASE WHEN (
            (app_real_bene_cnt <= 25) 
            AND (app_active = true)
          ) THEN 1 END
        )
      ) app_active_bene_cnt_le25, 
      "count"(
        (
          CASE WHEN (
            (app_created IS NOT NULL) 
            AND (app_active = true)
          ) THEN 1 END
        )
      ) app_active_registered, 
      "count"(
        (
          CASE WHEN (
            (app_first_active IS NOT NULL) 
            AND (app_active = true)
          ) THEN 1 END
        )
      ) app_active_first_api, 
      "count"(
        (
          CASE WHEN (
            (
              app_require_demographic_scopes = true
            ) 
            AND (app_active = true)
          ) THEN 1 END
        )
      ) app_active_require_demographic, 
      "sum"(
        (
          CASE WHEN (app_active = true) THEN app_real_bene_cnt END
        )
      ) app_grants_active_real_bene, 
      "sum"(
        (
          CASE WHEN (app_active = true) THEN app_synth_bene_cnt END
        )
      ) app_grants_active_synthetic_bene, 
      "count"(*) app_all, 
      "count"(
        (
          CASE WHEN (app_real_bene_cnt > 25) THEN 1 END
        )
      ) app_all_real_bene_gt25, 
      "count"(
        (
          CASE WHEN (app_real_bene_cnt <= 25) THEN 1 END
        )
      ) app_all_real_bene_le25, 
      "count"(
        (
          CASE WHEN (app_created IS NOT NULL) THEN 1 END
        )
      ) app_all_registered, 
      "count"(
        (
          CASE WHEN (app_first_active IS NOT NULL) THEN 1 END
        )
      ) app_all_first_api, 
      "count"(
        (
          CASE WHEN (
            app_require_demographic_scopes = true
          ) THEN 1 END
        )
      ) app_all_require_demographic, 
      "sum"(app_grant_and_archived_real_bene_deduped_count) app_grants_all_real_bene, 
      "sum"(app_grant_and_archived_synthetic_bene_deduped_count) app_grants_all_synthetic_bene 
    FROM 
      vw_impl_global_state_per_app 
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
      max_crosswalk_real_bene_count,
      max_crosswalk_synthetic_bene_count,
      max_crosswalk_table_count,
      max_crosswalk_archived_table_count,
      max_grant_real_bene_count,
      max_grant_synthetic_bene_count,
      max_grant_table_count,
      max_grant_archived_table_count,
      max_grant_real_bene_deduped_count,
      max_grant_synthetic_bene_deduped_count,
      max_grantarchived_real_bene_deduped_count,
      max_grantarchived_synthetic_bene_deduped_count,
      max_grant_and_archived_real_bene_deduped_count,
      max_grant_and_archived_synthetic_bene_deduped_count,
      max_token_real_bene_deduped_count,
      max_token_synthetic_bene_deduped_count,
      max_token_table_count,
      max_token_archived_table_count,
      max_global_apps_active_cnt,
      max_global_apps_inactive_cnt,
      max_global_apps_require_demographic_scopes_cnt,
      max_global_apps_active_cnt, 
      max_global_apps_inactive_cnt, 
      max_global_apps_require_demographic_scopes_cnt 
    ORDER BY 
      vpc ASC,
      start_date ASC
  )
