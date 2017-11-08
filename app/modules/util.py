from flask import logging
import json
import requests

logger = logging.getLogger(__name__)


def get_application_status(status_url, cfg):
    status_code = None
    try:
        request_result = requests.get(status_url,
                                      headers=cfg['headers'] if 'headers' in cfg else {},
                                      cookies=cfg['cookies'] if 'cookies' in cfg else {},
                                      verify=False,
                                      timeout=5)
        active_color = request_result.headers.get('x-color', None)
        status_code = request_result.status_code
        status_page_data = json.loads(request_result.text)
    except (ValueError, requests.exceptions.Timeout,
            requests.exceptions.ConnectionError) as error:
        logger.warning(' '.join(["could not read status page:", status_url, "[", error.__class__.__name__, "]"]))
        return {}, None, status_code
    return status_page_data, active_color, status_code


def itemize_app_id(app_id):
    color_codes = ['BLU', 'GRN']
    split = app_id.split("/")
    group = split[1]
    vertical = split[2]

    if len(split) == 4 or len(split) == 5 and str.upper(split[-1]) in color_codes:
        subgroup = ""
        name = split[3]
    else:
        subgroup = split[3]
        name = split[4]

    if str.upper(split[-1]) in color_codes:
        color = str.upper(split[-1])
    else:
        color = 'GRN'
    return group, vertical, subgroup, name, color


def calculate_severity(task):
    return task["status"] * (10 if task["status"] == 3 else 1) * (100 if task['group'] == 'live' else 1)


def get_job_info(job):
    current_status = status_level(job["status"])
    return {"status": current_status,
            "message": job.get("message", ""),
            "running": bool("running" in job and job["running"]),
            "started": job.get("started", None),
            "stopped": job.get("stopped", None)}


def status_level(status):
    level = 1
    if status == "OK":
        level = 0
    if status == "UNKNOWN":
        level = 1
    if status == "WARNING":
        level = 2
    if status == "ERROR":
        level = 3
    return level
