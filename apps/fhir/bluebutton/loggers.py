import json
import logging


"""
  Logger and logging function for waffle flags, switches
"""
waffle_event_logger = logging.getLogger('audit.waffle.event')


def log_v2_blocked(user=None, path=None, app=None, err=None, **kwargs):
    log_dict = {"type": "v2_blocked",
                "user": str(user) if user else None,
                "path": path if user else None,
                "app_id": app.id if app else None,
                "app_name": str(app.name) if app else None,
                "dev_id": str(app.user.id) if app else None,
                "dev_name": str(app.user.username) if app else None,
                "response_code": err.status_code,
                "message": str(err) if err else None}
    log_dict.update(kwargs)
    waffle_event_logger.info(json.dumps(log_dict))
