import json
import pickle
from threading import Timer
from delorean import Delorean
from flask import logging

from app import config

from app.util import get_in_dict
from app.modules import util

logger = logging.getLogger(__name__)


def update_standalone(thread_id, service_list, interval, greedy=False):
    for service in service_list:
        service_id = "standalone::" + service["id"]
        config.rdb.sadd("all-services", service_id)
        config.rdb.set(service_id, json.dumps(get_service_info(service)))
    config.rdb.set("standalone_services", pickle.dumps(Delorean.now()))
    if not greedy:
        logger.debug("Finish update for services")
        Timer(interval=interval,
              function=update_standalone,
              args=(thread_id, service_list, interval)).start()


def get_service_info(service):
    task = dict()
    task["id"] = service["id"]
    task["status_url"] = service["url"]
    task["group"], task["vertical"], task["subgroup"], name, task["color"] = util.itemize_app_id(service["id"])

    task["name"] = "standalone::" + name
    full_name = "-".join([task["vertical"], name])
    task["full-name"] = "standalone::" + full_name

    status_page_data, active_color, status_page_code = util.get_application_status(service["url"], service)
    task["version"] = get_in_dict(["application", "version"], status_page_data, "UNKNOWN")
    task["status_page_status_code"] = status_page_code
    task["active_color"] = active_color
    task["app_status"] = util.status_level(get_in_dict(["application", "status"], status_page_data, "UNKNOWN"))
    task["jobs"] = dict()
    for job, job_info in get_in_dict(["application", "statusDetails"], status_page_data, {}).items():
        task["jobs"][job] = util.get_job_info(job_info)

    task["status"] = task["app_status"]
    task["severity"] = util.calculate_severity(task)
    return task
