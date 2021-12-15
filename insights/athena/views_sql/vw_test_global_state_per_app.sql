/*
 Query for view:  vw_test_global_state_per_app

 NOTE: Use this query when creating or updating this view
*/

CREATE 
OR REPLACE VIEW vw_test_global_state_per_app AS 
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
  t1.max_global_apps_active_cnt, 
  t1.max_global_apps_inactive_cnt, 
  t1.max_global_apps_require_demographic_scopes_cnt, 
  t2.name app_name, 
  t2.created app_created, 
  t2.active app_active, 
  t2.first_active app_first_active, 
  t2.last_active app_last_active, 
  t2.require_demographic_scopes app_require_demographic_scopes, 
  t2.real_bene_cnt app_real_bene_cnt, 
  t2.synth_bene_cnt app_synth_bene_cnt, 
  t2.user_organization app_user_organization 
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
            global_apps_active_cnt, 
            global_apps_inactive_cnt, 
            global_apps_require_demographic_scopes_cnt 
          FROM 
            bb2.events_test_perf_mon 
          WHERE 
            (type = 'global_state_metrics' and vpc = 'test')
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
        created, 
        active, 
        first_active, 
        last_active, 
        require_demographic_scopes, 
        real_bene_cnt, 
        synth_bene_cnt, 
        user_organization 
      FROM 
        bb2.events_test_perf_mon 
      WHERE 
        (
          type = 'global_state_metrics_per_app' and vpc = 'test'
        )
    ) t2 ON (
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
  )
