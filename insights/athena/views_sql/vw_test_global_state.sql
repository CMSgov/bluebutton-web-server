/*
 Query for view:  vw_test_global_state
 
 NOTE: This view depends on the intermediate reporting table
 bb2.test_global_state_per_app being updated
 first via the 
 bb2.vw_test_global_state_per_app view.
 
 It will get the min_report_date from this existing table.
 
 
 NOTE: Use this query when creating or updating this view
 */
CREATE
OR REPLACE VIEW vw_test_global_state AS
/* Set the report_date_range to be selected.

 This is used to select time_of_event records that are
 >= min_report_date AND < max_report_date
 
 This is used for inserting only new records in to 
 bb2.test_global_state table.
 
 For recovery purposes (such as recreating the table),
 the date ranges can be hard coded via uncommenting/commenting
 the related SQL. Then Restore back to the 
 original version after recovery!
 */
WITH report_date_range AS (
  /* Select gets the min_report_date to select new records from 
   the bb2.events_test_perf_mon table. 
   
   Use this to HARD CODE the MIN report date for recovery purposes.
   For example, you can use a past date like '2000-01-01'. 
   */
  /*
   SELECT date_trunc('week', CAST('2022-08-01' AS date)) min_report_date,
  */
  /*
   This is normally the maximum/last report_date from the 
   bb2.test_global_state table via the select below: */
  SELECT
    (
      SELECT
        date_trunc('week', MAX(report_date))
      FROM
        bb2.test_global_state
    ) AS min_report_date,

    /* Use the following to select the MAX report date.
     
     This can be hard coded for recovery purposes as below:   */
    /*
     date_trunc('week', CAST('2022-08-29' AS date)) max_report_date 
    */
    /* This is normally set using the built-in "current_date" */
    date_trunc('week', current_date) max_report_date
),
report_partitions_range AS (
  SELECT
    CONCAT(
      CAST(YEAR(min_report_date) AS VARCHAR),
      '-',
      LPAD(CAST(MONTH(min_report_date) AS VARCHAR), 2, '0'),
      '-',
      LPAD(CAST(DAY(min_report_date) AS VARCHAR), 2, '0')
    ) AS min_partition_date
  FROM
    (
      select
        min_report_date
      FROM
        report_date_range
    )
),
/* Temp table for V1 FHIR events */
v1_fhir_events AS (
  select
    time_of_event,
    path,
    fhir_id,
    req_qparam_lastupdated
  from
    "bb2"."events_test_perf_mon"
  WHERE
    (
      type = 'request_response_middleware'
      and vpc = 'test'
      and request_method = 'GET'
      and path LIKE '/v1/fhir%'
      and response_code = 200
      and app_name != 'new-relic'
      and cast("from_iso8601_timestamp"(time_of_event) AS date) >= (
        select
          min_report_date
        FROM
          report_date_range
      )
      and cast("from_iso8601_timestamp"(time_of_event) AS date) < (
        select
          max_report_date
        FROM
          report_date_range
      )
      /*
       AND concat(dt, '-', partition_1, '-', partition_2) >= (
       SELECT
       min_partition_date
       FROM
       report_partitions_range
       )
       */
    )
),
/* Temp table for V2 FHIR events */
v2_fhir_events AS (
  select
    time_of_event,
    path,
    fhir_id,
    req_qparam_lastupdated
  from
    "bb2"."events_test_perf_mon"
  WHERE
    (
      type = 'request_response_middleware'
      and vpc = 'test'
      and request_method = 'GET'
      and path LIKE '/v2/fhir%'
      and response_code = 200
      and app_name != 'new-relic'
      and cast("from_iso8601_timestamp"(time_of_event) AS date) >= (
        select
          min_report_date
        FROM
          report_date_range
      )
      and cast("from_iso8601_timestamp"(time_of_event) AS date) < (
        select
          max_report_date
        FROM
          report_date_range
      )
      /*
       AND concat(dt, '-', partition_1, '-', partition_2) >= (
       SELECT
       min_partition_date
       FROM
       report_partitions_range
       )
       */
    )
),
/* Temp table for AUTH events */
auth_events AS (
  select
    time_of_event,
    auth_require_demographic_scopes,
    auth_crosswalk_action,
    auth_share_demographic_scopes,
    auth_status,
    share_demographic_scopes,
    allow,
    json_extract(user, '$.crosswalk.fhir_id') as fhir_id
  from
    "bb2"."events_test_perf_mon"
  WHERE
    (
      type = 'Authorization'
      and vpc = 'test'
      and auth_app_name != 'new-relic'
      and cast("from_iso8601_timestamp"(time_of_event) AS date) >= (
        select
          min_report_date
        FROM
          report_date_range
      )
      and cast("from_iso8601_timestamp"(time_of_event) AS date) < (
        select
          max_report_date
        FROM
          report_date_range
      )
      /*
       AND concat(dt, '-', partition_1, '-', partition_2) >= (
       SELECT
       min_partition_date
       FROM
       report_partitions_range
       )
       */
    )
)
/* Main select */
SELECT
  *,
  (
    total_crosswalk_real_bene - app_all_grant_real_bene
  ) diff_total_crosswalk_vs_grant_and_archived_real_bene,
  (
    total_crosswalk_synthetic_bene - app_all_grant_synthetic_bene
  ) diff_total_crosswalk_vs_grant_and_archived_synthetic_bene,
  /* V1 FHIR resource stats top level */
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) >= 0
      )
  ) as fhir_v1_call_real_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) < 0
      )
  ) as fhir_v1_call_synthetic_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/ExplanationOfBenefit%'
        and try_cast(fhir_id as BIGINT) >= 0
      )
  ) as fhir_v1_eob_call_real_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/ExplanationOfBenefit%'
        and try_cast(fhir_id as BIGINT) < 0
      )
  ) as fhir_v1_eob_call_synthetic_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/Coverage%'
        and try_cast(fhir_id as BIGINT) >= 0
      )
  ) as fhir_v1_coverage_call_real_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/Coverage%'
        and try_cast(fhir_id as BIGINT) < 0
      )
  ) as fhir_v1_coverage_call_synthetic_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/Patient%'
        and try_cast(fhir_id as BIGINT) >= 0
      )
  ) as fhir_v1_patient_call_real_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/Patient%'
        and try_cast(fhir_id as BIGINT) < 0
      )
  ) as fhir_v1_patient_call_synthetic_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/metadata%'
      )
  ) as fhir_v1_metadata_call_count,
  /* V1 since (lastUpdated) stats top level */
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/ExplanationOfBenefit%'
        and try_cast(fhir_id as BIGINT) >= 0
        and req_qparam_lastupdated != ''
      )
  ) as fhir_v1_eob_since_call_real_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/ExplanationOfBenefit%'
        and try_cast(fhir_id as BIGINT) < 0
        and req_qparam_lastupdated != ''
      )
  ) as fhir_v1_eob_since_call_synthetic_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/Coverage%'
        and try_cast(fhir_id as BIGINT) >= 0
        and req_qparam_lastupdated != ''
      )
  ) as fhir_v1_coverage_since_call_real_count,
  (
    select
      count(*)
    from
      v1_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v1/fhir/Coverage%'
        and try_cast(fhir_id as BIGINT) < 0
        and req_qparam_lastupdated != ''
      )
  ) as fhir_v1_coverage_since_call_synthetic_count,
  /* V2 FHIR resource stats top level */
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) >= 0
      )
  ) as fhir_v2_call_real_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) < 0
      )
  ) as fhir_v2_call_synthetic_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/ExplanationOfBenefit%'
        and try_cast(fhir_id as BIGINT) >= 0
      )
  ) as fhir_v2_eob_call_real_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/ExplanationOfBenefit%'
        and try_cast(fhir_id as BIGINT) < 0
      )
  ) as fhir_v2_eob_call_synthetic_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/Coverage%'
        and try_cast(fhir_id as BIGINT) >= 0
      )
  ) as fhir_v2_coverage_call_real_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/Coverage%'
        and try_cast(fhir_id as BIGINT) < 0
      )
  ) as fhir_v2_coverage_call_synthetic_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/Patient%'
        and try_cast(fhir_id as BIGINT) >= 0
      )
  ) as fhir_v2_patient_call_real_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/Patient%'
        and try_cast(fhir_id as BIGINT) < 0
      )
  ) as fhir_v2_patient_call_synthetic_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/metadata%'
      )
  ) as fhir_v2_metadata_call_count,
  /* V2 since (lastUpdated) stats top level */
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/ExplanationOfBenefit%'
        and try_cast(fhir_id as BIGINT) >= 0
        and req_qparam_lastupdated != ''
      )
  ) as fhir_v2_eob_since_call_real_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/ExplanationOfBenefit%'
        and try_cast(fhir_id as BIGINT) < 0
        and req_qparam_lastupdated != ''
      )
  ) as fhir_v2_eob_since_call_synthetic_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/Coverage%'
        and try_cast(fhir_id as BIGINT) >= 0
        and req_qparam_lastupdated != ''
      )
  ) as fhir_v2_coverage_since_call_real_count,
  (
    select
      count(*)
    from
      v2_fhir_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and path LIKE '/v2/fhir/Coverage%'
        and try_cast(fhir_id as BIGINT) < 0
        and req_qparam_lastupdated != ''
      )
  ) as fhir_v2_coverage_since_call_synthetic_count,
  /* AUTH and demographic scopes stats top level */
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) >= 0
        and auth_status = 'OK'
        and allow = True
      )
  ) as auth_ok_real_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) < 0
        and auth_status = 'OK'
        and allow = True
      )
  ) as auth_ok_synthetic_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) >= 0
        and auth_status = 'FAIL'
      )
  ) as auth_fail_or_deny_real_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) < 0
        and auth_status = 'FAIL'
      )
  ) as auth_fail_or_deny_synthetic_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) >= 0
        and auth_status = 'OK'
        and allow = True
        and auth_require_demographic_scopes = 'True'
        and share_demographic_scopes = 'True'
      )
  ) as auth_demoscope_required_choice_sharing_real_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) < 0
        and auth_status = 'OK'
        and allow = True
        and auth_require_demographic_scopes = 'True'
        and share_demographic_scopes = 'True'
      )
  ) as auth_demoscope_required_choice_sharing_synthetic_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) >= 0
        and auth_status = 'OK'
        and allow = True
        and auth_require_demographic_scopes = 'True'
        and share_demographic_scopes = 'False'
      )
  ) as auth_demoscope_required_choice_not_sharing_real_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) < 0
        and auth_status = 'OK'
        and allow = True
        and auth_require_demographic_scopes = 'True'
        and share_demographic_scopes = 'False'
      )
  ) as auth_demoscope_required_choice_not_sharing_synthetic_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) >= 0
        and allow = False
        and auth_require_demographic_scopes = 'True'
      )
  ) as auth_demoscope_required_choice_deny_real_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) < 0
        and allow = False
        and auth_require_demographic_scopes = 'True'
      )
  ) as auth_demoscope_required_choice_deny_synthetic_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) >= 0
        and auth_status = 'OK'
        and allow = True
        and auth_require_demographic_scopes = 'False'
      )
  ) as auth_demoscope_not_required_not_sharing_real_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) < 0
        and auth_status = 'OK'
        and allow = True
        and auth_require_demographic_scopes = 'False'
      )
  ) as auth_demoscope_not_required_not_sharing_synthetic_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) >= 0
        and allow = False
        and auth_require_demographic_scopes = 'False'
      )
  ) as auth_demoscope_not_required_deny_real_bene_count,
  (
    select
      count(*)
    from
      auth_events
    WHERE
      (
        cast("from_iso8601_timestamp"(time_of_event) AS date) >= start_date
        and cast("from_iso8601_timestamp"(time_of_event) AS date) <= end_date
        and try_cast(fhir_id as BIGINT) < 0
        and allow = False
        and auth_require_demographic_scopes = 'False'
      )
  ) as auth_demoscope_not_required_deny_synthetic_bene_count
FROM
  (
    SELECT
      vpc,
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
      max_global_developer_count total_developer_count,
      max_global_developer_distinct_organization_name_count total_developer_distinct_organization_name_count,
      max_global_developer_with_first_api_call_count total_developer_with_first_api_call_count,
      max_global_developer_with_registered_app_count total_developer_with_registered_app_count,
      /*
       NOTE: Metrics in this section prefixed by "app_" come from the 
       type = "global_state_metrics_per_app",
       per the vw_test_global_state_per_app view
       where the counts/sums are performed in SQL below.
       */
      "count"(
        (
          CASE
            WHEN (app_active = true) THEN 1
          END
        )
      ) app_total_active,
      "count"(
        (
          CASE
            WHEN (
              (app_real_bene_cnt > 25)
              AND (app_active = true)
            ) THEN 1
          END
        )
      ) app_active_bene_cnt_gt25,
      "count"(
        (
          CASE
            WHEN (
              (app_real_bene_cnt <= 25)
              AND (app_active = true)
            ) THEN 1
          END
        )
      ) app_active_bene_cnt_le25,
      "count"(
        (
          CASE
            WHEN (
              (app_created IS NOT NULL)
              AND (app_active = true)
            ) THEN 1
          END
        )
      ) app_active_registered,
      "count"(
        (
          CASE
            WHEN (
              (app_first_active IS NOT NULL)
              AND (app_active = true)
            ) THEN 1
          END
        )
      ) app_active_first_api,
      "count"(
        (
          CASE
            WHEN (
              (
                app_require_demographic_scopes = true
              )
              AND (app_active = true)
            ) THEN 1
          END
        )
      ) app_active_require_demographic,
      "sum"(
        (
          CASE
            WHEN (app_active = true) THEN app_real_bene_cnt
          END
        )
      ) app_grant_active_real_bene,
      "sum"(
        (
          CASE
            WHEN (app_active = true) THEN app_synth_bene_cnt
          END
        )
      ) app_grant_active_synthetic_bene,
      "count"(*) app_all,
      "count"(
        (
          CASE
            WHEN (app_real_bene_cnt > 25) THEN 1
          END
        )
      ) app_all_real_bene_gt25,
      "count"(
        (
          CASE
            WHEN (app_real_bene_cnt <= 25) THEN 1
          END
        )
      ) app_all_real_bene_le25,
      "count"(
        (
          CASE
            WHEN (app_created IS NOT NULL) THEN 1
          END
        )
      ) app_all_registered,
      "count"(
        (
          CASE
            WHEN (app_first_active IS NOT NULL) THEN 1
          END
        )
      ) app_all_first_api,
      "count"(
        (
          CASE
            WHEN (
              app_require_demographic_scopes = true
            ) THEN 1
          END
        )
      ) app_all_require_demographic,
      "sum"(app_grant_and_archived_real_bene_deduped_count) app_all_grant_real_bene,
      "sum"(
        app_grant_and_archived_synthetic_bene_deduped_count
      ) app_all_grant_synthetic_bene,
      "sum"(
        app_fhir_v1_call_real_count
      ) app_all_fhir_v1_call_real_count,
      "sum"(
        app_fhir_v1_call_synthetic_count
      ) app_all_fhir_v1_call_synthetic_count,
      "sum"(
        app_fhir_v1_eob_call_real_count
      ) app_all_fhir_v1_eob_call_real_count,
      "sum"(
        app_fhir_v1_eob_call_synthetic_count
      ) app_all_fhir_v1_eob_call_synthetic_count,
      "sum"(
        app_fhir_v1_coverage_call_real_count
      ) app_all_fhir_v1_coverage_call_real_count,
      "sum"(
        app_fhir_v1_coverage_call_synthetic_count
      ) app_all_fhir_v1_coverage_call_synthetic_count,
      "sum"(
        app_fhir_v1_patient_call_real_count
      ) app_all_fhir_v1_patient_call_real_count,
      "sum"(
        app_fhir_v1_patient_call_synthetic_count
      ) app_all_fhir_v1_patient_call_synthetic_count,
      "sum"(
        app_fhir_v1_metadata_call_count
      ) app_all_fhir_v1_metadata_call_count,
      "sum"(
        app_fhir_v1_eob_since_call_real_count
      ) app_all_fhir_v1_eob_since_call_real_count,
      "sum"(
        app_fhir_v1_eob_since_call_synthetic_count
      ) app_all_fhir_v1_eob_since_call_synthetic_count,
      "sum"(
        app_fhir_v1_coverage_since_call_real_count
      ) app_all_fhir_v1_coverage_since_call_real_count,
      "sum"(
        app_fhir_v1_coverage_since_call_synthetic_count
      ) app_all_fhir_v1_coverage_since_call_synthetic_count,
      "sum"(
        app_fhir_v2_call_real_count
      ) app_all_fhir_v2_call_real_count,
      "sum"(
        app_fhir_v2_call_synthetic_count
      ) app_all_fhir_v2_call_synthetic_count,
      "sum"(
        app_fhir_v2_eob_call_real_count
      ) app_all_fhir_v2_eob_call_real_count,
      "sum"(
        app_fhir_v2_eob_call_synthetic_count
      ) app_all_fhir_v2_eob_call_synthetic_count,
      "sum"(
        app_fhir_v2_coverage_call_real_count
      ) app_all_fhir_v2_coverage_call_real_count,
      "sum"(
        app_fhir_v2_coverage_call_synthetic_count
      ) app_all_fhir_v2_coverage_call_synthetic_count,
      "sum"(
        app_fhir_v2_patient_call_real_count
      ) app_all_fhir_v2_patient_call_real_count,
      "sum"(
        app_fhir_v2_patient_call_synthetic_count
      ) app_all_fhir_v2_patient_call_synthetic_count,
      "sum"(
        app_fhir_v2_metadata_call_count
      ) app_all_fhir_v2_metadata_call_count,
      "sum"(
        app_fhir_v2_eob_since_call_real_count
      ) app_all_fhir_v2_eob_since_call_real_count,
      "sum"(
        app_fhir_v2_eob_since_call_synthetic_count
      ) app_all_fhir_v2_eob_since_call_synthetic_count,
      "sum"(
        app_fhir_v2_coverage_since_call_real_count
      ) app_all_fhir_v2_coverage_since_call_real_count,
      "sum"(
        app_fhir_v2_coverage_since_call_synthetic_count
      ) app_all_fhir_v2_coverage_since_call_synthetic_count,
      "sum"(
        app_auth_ok_real_bene_count
      ) app_all_auth_ok_real_bene_count,
      "sum"(
        app_auth_ok_synthetic_bene_count
      ) app_all_auth_ok_synthetic_bene_count,
      "sum"(
        app_auth_fail_or_deny_real_bene_count
      ) app_all_auth_fail_or_deny_real_bene_count,
      "sum"(
        app_auth_fail_or_deny_synthetic_bene_count
      ) app_all_auth_fail_or_deny_synthetic_bene_count,
      "sum"(
        app_auth_demoscope_required_choice_sharing_real_bene_count
      ) app_all_auth_demoscope_required_choice_sharing_real_bene_count,
      "sum"(
        app_auth_demoscope_required_choice_sharing_synthetic_bene_count
      ) app_all_auth_demoscope_required_choice_sharing_synthetic_bene_count,
      "sum"(
        app_auth_demoscope_required_choice_not_sharing_real_bene_count
      ) app_all_auth_demoscope_required_choice_not_sharing_real_bene_count,
      "sum"(
        app_auth_demoscope_required_choice_not_sharing_synthetic_bene_count
      ) app_all_auth_demoscope_required_choice_not_sharing_synthetic_bene_count,
      "sum"(
        app_auth_demoscope_required_choice_deny_real_bene_count
      ) app_all_auth_demoscope_required_choice_deny_real_bene_count,
      "sum"(
        app_auth_demoscope_required_choice_deny_synthetic_bene_count
      ) app_all_auth_demoscope_required_choice_deny_synthetic_bene_count,
      "sum"(
        app_auth_demoscope_not_required_not_sharing_real_bene_count
      ) app_all_auth_demoscope_not_required_not_sharing_real_bene_count,
      "sum"(
        app_auth_demoscope_not_required_not_sharing_synthetic_bene_count
      ) app_all_auth_demoscope_not_required_not_sharing_synthetic_bene_count,
      "sum"(
        app_auth_demoscope_not_required_deny_real_bene_count
      ) app_all_auth_demoscope_not_required_deny_real_bene_count,
      "sum"(
        app_auth_demoscope_not_required_deny_synthetic_bene_count
      ) app_all_auth_demoscope_not_required_deny_synthetic_bene_count
    FROM
      test_global_state_per_app
    WHERE
      cast(report_date AS date) >= (
        select
          min_report_date
        FROM
          report_date_range
      )
      AND cast(report_date AS date) <= (
        select
          max_report_date
        FROM
          report_date_range
      )
    GROUP BY
      vpc,
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
      max_global_developer_count,
      max_global_developer_distinct_organization_name_count,
      max_global_developer_with_first_api_call_count,
      max_global_developer_with_registered_app_count
    ORDER BY
      start_date ASC
  )
ORDER BY
  start_date ASC