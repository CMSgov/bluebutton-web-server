resource "datadog_downtime_schedule" "test_overnight_weekends" {
  count = local.env == "test" ? 1 : 0

  scope            = "*"
  display_timezone = "UTC"
  message          = "${local.app} test shuts down overnight and on weekends."

  monitor_identifier {
    monitor_tags = [
      "application:${local.app}",
      "environment:${local.env}",
      "managed-by:tofu"
    ]
  }

  mute_first_recovery_notification = false

  notify_end_types = [
    "expired",
    "canceled"
  ]

  notify_end_states = [
    "alert",
    "warn",
    "no data"
  ]

  recurring_schedule {
    timezone = "UTC"

    recurrence {
      start    = "2026-07-23T02:00:00"
      duration = "12h"
      rrule    = "FREQ=DAILY;INTERVAL=1;BYHOUR=2;BYMINUTE=0"
    }

    recurrence {
      start    = "2026-07-25T02:00:00"
      duration = "2d"
      rrule    = "FREQ=WEEKLY;INTERVAL=1;BYHOUR=2;BYMINUTE=0;BYDAY=SA"
    }
  }
}
