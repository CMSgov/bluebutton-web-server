/*
 Query for view:  vw_impl_global_state_per_app

 NOTE: Use this query when creating or updating this view
*/

CREATE 
OR REPLACE VIEW vw_impl_global_state_per_app AS 
SELECT 
  t1.vpc, 
  t1.year, 
  t1.week_number, 
  t1.start_date, 
  t1.end_date, 
  t1.report_date, 
  t1.max_group_timestamp, 
  t1.max_real_bene_cnt, 
  t1.max_synth_bene_cnt, 
  t1.max_crosswalk_real_bene_count,
  t1.max_crosswalk_synthetic_bene_count,
  t1.max_crosswalk_table_count,
  t1.max_crosswalk_archived_table_count,
  t1.max_grant_real_bene_count,
  t1.max_grant_synthetic_bene_count,
  t1.max_grant_table_count,
  t1.max_grant_archived_table_count,
  t1.max_grant_real_bene_deduped_count,
  t1.max_grant_synthetic_bene_deduped_count,
  t1.max_grantarchived_real_bene_deduped_count,
  t1.max_grantarchived_synthetic_bene_deduped_count,
  t1.max_grant_and_archived_real_bene_deduped_count,
  t1.max_grant_and_archived_synthetic_bene_deduped_count,
  t1.max_token_real_bene_deduped_count,
  t1.max_token_synthetic_bene_deduped_count,
  t1.max_token_table_count,
  t1.max_token_archived_table_count,
  t1.max_global_apps_active_cnt, 
  t1.max_global_apps_inactive_cnt, 
  t1.max_global_apps_require_demographic_scopes_cnt, 
  t2.name app_name, 
  t2.id app_id, 
  t2.created app_created, 
  t2.updated app_updated, 
  t2.active app_active, 
  t2.first_active app_first_active, 
  t2.last_active app_last_active, 
  t2.require_demographic_scopes app_require_demographic_scopes, 
  t2.user_organization app_user_organization,
  t2.user_id app_user_id,
  t2.user_username app_user_username,
  t2.user_date_joined app_user_date_joined,
  t2.user_last_login app_user_last_login,
  t2.real_bene_cnt app_real_bene_cnt, 
  t2.synth_bene_cnt app_synth_bene_cnt,
  t2.grant_real_bene_count app_grant_real_bene_count,
  t2.grant_synthetic_bene_count app_grant_synthetic_bene_count,
  t2.grant_table_count app_grant_table_count,
  t2.grant_archived_table_count app_grant_archived_table_count,
  t2.grantarchived_real_bene_deduped_count app_grantarchived_real_bene_deduped_count,
  t2.grantarchived_synthetic_bene_deduped_count app_grantarchived_synthetic_bene_deduped_count,
  t2.grant_and_archived_real_bene_deduped_count app_grant_and_archived_real_bene_deduped_count,
  t2.grant_and_archived_synthetic_bene_deduped_count app_grant_and_archived_synthetic_bene_deduped_count,
  t2.token_real_bene_count app_token_real_bene_count,
  t2.token_synthetic_bene_count app_token_synthetic_bene_count,
  t2.token_table_count app_token_table_count,
  t2.token_archived_table_count app_token_archived_table_count
FROM 
  (
    (
      SELECT 
        vpc, 
        year,
        week_number, 
        (
          "min"(e_date) - INTERVAL '1' DAY
        ) start_date, 
        (
          "max"(e_date) - INTERVAL '1' DAY
        ) end_date, 
        "max"(e_date) report_date, 
        "max"(group_timestamp) max_group_timestamp, 
        "max"(real_bene_cnt) max_real_bene_cnt, 
        "max"(synth_bene_cnt) max_synth_bene_cnt, 
        "max"(crosswalk_real_bene_count) max_crosswalk_real_bene_count,
        "max"(crosswalk_synthetic_bene_count) max_crosswalk_synthetic_bene_count,
        "max"(crosswalk_table_count) max_crosswalk_table_count,
        "max"(crosswalk_archived_table_count) max_crosswalk_archived_table_count,
        "max"(grant_real_bene_count) max_grant_real_bene_count,
        "max"(grant_synthetic_bene_count) max_grant_synthetic_bene_count,
        "max"(grant_table_count) max_grant_table_count,
        "max"(grant_archived_table_count) max_grant_archived_table_count,
        "max"(grant_real_bene_deduped_count) max_grant_real_bene_deduped_count,
        "max"(grant_synthetic_bene_deduped_count) max_grant_synthetic_bene_deduped_count,
        "max"(grantarchived_real_bene_deduped_count) max_grantarchived_real_bene_deduped_count,
        "max"(grantarchived_synthetic_bene_deduped_count) max_grantarchived_synthetic_bene_deduped_count,
        "max"(grant_and_archived_real_bene_deduped_count) max_grant_and_archived_real_bene_deduped_count,
        "max"(grant_and_archived_synthetic_bene_deduped_count) max_grant_and_archived_synthetic_bene_deduped_count,
        "max"(token_real_bene_deduped_count) max_token_real_bene_deduped_count,
        "max"(token_synthetic_bene_deduped_count) max_token_synthetic_bene_deduped_count,
        "max"(token_table_count) max_token_table_count,
        "max"(token_archived_table_count) max_token_archived_table_count,
        "max"(global_apps_active_cnt) max_global_apps_active_cnt, 
        "max"(global_apps_inactive_cnt) max_global_apps_inactive_cnt, 
        "max"(
          global_apps_require_demographic_scopes_cnt
        ) max_global_apps_require_demographic_scopes_cnt 
      FROM 
        (
          SELECT DISTINCT 
            vpc, 
            CAST(
              "from_iso8601_timestamp"(time_of_event) AS date
            ) e_date, 
            EXTRACT(
              YEAR 
              FROM 
                (
                  CAST(
                    "from_iso8601_timestamp"(time_of_event) AS date
                  ) - INTERVAL '1' DAY
                )
            ) year, 
            EXTRACT(
              WEEK 
              FROM 
                (
                  CAST(
                    "from_iso8601_timestamp"(time_of_event) AS date
                  ) - INTERVAL '1' DAY
                )
            ) week_number, 
            group_timestamp, 
            real_bene_cnt, 
            synth_bene_cnt, 
            crosswalk_real_bene_count,
            crosswalk_synthetic_bene_count,
            crosswalk_table_count,
            crosswalk_archived_table_count,
            grant_real_bene_count,
            grant_synthetic_bene_count,
            grant_table_count,
            grant_archived_table_count,
            grant_real_bene_deduped_count,
            grant_synthetic_bene_deduped_count,
            grantarchived_real_bene_deduped_count,
            grantarchived_synthetic_bene_deduped_count,
            grant_and_archived_real_bene_deduped_count,
            grant_and_archived_synthetic_bene_deduped_count,
            token_real_bene_deduped_count,
            token_synthetic_bene_deduped_count,
            token_table_count,
            token_archived_table_count,
            global_apps_active_cnt, 
            global_apps_inactive_cnt, 
            global_apps_require_demographic_scopes_cnt 
          FROM 
            bb2.events_impl_perf_mon 
          WHERE 
            (type = 'global_state_metrics' and vpc = 'impl')
        ) 
      GROUP BY 
        vpc, 
        year,
        week_number
    ) t1 
    INNER JOIN (
      SELECT DISTINCT 
        group_timestamp, 
        vpc, 
        name, 
        id, 
        created, 
        updated,
        active, 
        first_active, 
        last_active, 
        require_demographic_scopes, 
        user_organization,
        user_id,
        user_username,
        user_date_joined,
        user_last_login,
        real_bene_cnt, 
        synth_bene_cnt,
        grant_real_bene_count,
        grant_synthetic_bene_count,
        grant_table_count,
        grant_archived_table_count,
        grantarchived_real_bene_deduped_count,
        grantarchived_synthetic_bene_deduped_count,
        grant_and_archived_real_bene_deduped_count,
        grant_and_archived_synthetic_bene_deduped_count,
        token_real_bene_count,
        token_synthetic_bene_count,
        token_table_count,
        token_archived_table_count
      FROM 
        bb2.events_impl_perf_mon 
      WHERE 
        (
          type = 'global_state_metrics_per_app' and vpc = 'impl'
        )
    ) t2 ON (
     (
      (
        (
          (
            (
              (
                t1.max_group_timestamp = t2.group_timestamp
              ) 
              AND (t1.vpc = t2.vpc)
            ) 
            AND (t2.name <> 'TestApp')
          ) 
          AND (
            t2.name <> 'BlueButton Client (Test - Internal Use Only)'
          )
        ) 
        AND (t2.name <> 'MyMedicare PROD')
      ) 
      AND (t2.name <> 'new-relic')
    )
    AND (t2.name <> 'MIL-Inaugural Test')
   )    
  )
