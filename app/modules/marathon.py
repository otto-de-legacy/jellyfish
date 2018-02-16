import json
import pickle
import re
from threading import Timer
from urllib.parse import quote_plus
from flask import logging

import requests
from delorean import Delorean

from app import config
from app.util import get_in_dict
from app.modules import util

logger = logging.getLogger(__name__)


def update_marathon(thread_id, cfg, interval, greedy=False):
    app_list = get_apps(cfg)
    previous_tasks = (config.rdb.get(thread_id) or b'').decode().split(',')
    blacklist = '(?:%s)' % '|'.join(cfg['blacklist']) if 'blacklist' in cfg else '1234'
    tasks = list()
    for app in app_list:
        try:
            _, _, _, app_name, _ = util.itemize_app_id(app["id"])
            if not re.match(blacklist, app["id"]):
                app_id = "marathon::" + app["id"]
                config.rdb.sadd("all-services", app_id)
                config.rdb.set(app_id, json.dumps(get_task_info(app, cfg)))
                tasks.append(app_id)
        except Exception as error:
            logger.error(
                ' '.join([cfg['host'] + ":" + (app["id"] if app else "unkown"), "[",
                          error.__class__.__name__, "]"]), exc_info=True)

    for app_id in list(set(previous_tasks) - set(tasks)):
        config.rdb.delete(app_id)
        config.rdb.srem("all-services", app_id)
    config.rdb.set(thread_id, ",".join(tasks))

    config.rdb.set(cfg['host'], pickle.dumps(Delorean.now()))
    if not greedy:
        logger.debug("Finish update for " + cfg['host'])
        Timer(interval=interval,
              function=update_marathon,
              args=(thread_id, cfg, interval)).start()


def get_apps(marathon):
    marathon_url = ''.join([marathon['protocol'],
                            "://",
                            quote_plus(marathon['username']),
                            ':',
                            quote_plus(marathon['password']),
                            '@',
                            marathon['host'],
                            marathon['apps']])
    try:
        request_result = requests.get(marathon_url,
                                      headers={"Accept": "application/json"},
                                      verify=False,
                                      timeout=5)
        data = json.loads(request_result.text)
        config.rdb.set(marathon['host'] + '-cache', json.dumps(data["apps"]))
        config.rdb.delete(marathon['host'] + '-errors')
    except (ValueError, requests.exceptions.Timeout,
            requests.exceptions.ConnectionError) as error:

        error_message = ' '.join(["could not read marathon:", marathon['host'], "[", error.__class__.__name__, "]"])

        logger.warning(error_message)
        config.rdb.set(marathon['host'] + '-errors', error_message)
        raw_cache = config.rdb.get(marathon['host'] + '-cache')
        if raw_cache:
            return json.loads(raw_cache.decode())
        return []
    return data["apps"]


def get_task_info(app, cfg):
    task = dict()
    task["id"] = app["id"]
    task["group"], task["vertical"], task["subgroup"], name, task["color"] = util.itemize_app_id(app["id"])

    task["name"] = "marathon::" + name
    full_name = "-".join([task["vertical"], name])
    task["full-name"] = "marathon::" + full_name

    task["marathon"] = dict()
    task["marathon"]["origin"] = cfg["host"]
    task["marathon"]["instances"] = app["instances"]
    task["marathon"]["cpu"] = app["cpus"]
    task["marathon"]["mem"] = app["mem"]
    task["marathon"]["staged"] = app["tasksStaged"]
    task["marathon"]["running"] = app["tasksRunning"]
    task["marathon"]["healthy"] = app["tasksHealthy"]
    task["marathon"]["unhealthy"] = app["tasksUnhealthy"]
    task["marathon"]["marathon_link"] = cfg['protocol'] + "://" + cfg['host'] + "/ui/#/apps/" + \
                                        quote_plus(task["id"])
    task["marathon"]["labels"] = app["labels"]

    root_app = get_in_dict(["env", cfg.get("root_app_lable")], app, "") or \
               get_in_dict(["labels", cfg.get("root_app_lable")], app, "")
    root_app = root_app == 'true' or root_app == 'True'
    status_path = get_in_dict(["env", cfg.get("status_path_lable")], app, "") or \
                  get_in_dict(["labels", cfg.get("status_path_lable")], app, "")
    task["status_url"] = get_status_url(name, task["group"], task["vertical"], task["subgroup"],
                                        cfg['base_domain'], status_path,
                                        root_app, cfg)

    if status_path and task["marathon"]["instances"] > 0:
        status_page_data, active_color, status_page_code = util.get_application_status(task["status_url"], cfg)
        if task["color"] and active_color and task["color"] != active_color:
            task["status_url"] = task["status_url"].replace('http://', 'http://staged.')
            status_page_data, _, status_page_code = util.get_application_status(task["status_url"], cfg)
        task["version"] = get_in_dict(["application", "version"], status_page_data, "UNKNOWN")
        task["status_page_status_code"] = status_page_code
        task["active_color"] = active_color
        task["app_status"] = util.status_level(get_in_dict(["application", "status"], status_page_data, "UNKNOWN"))
        task["jobs"] = dict()
        for job, job_info in get_in_dict(["application", "statusDetails"], status_page_data, {}).items():
            task["jobs"][job] = util.get_job_info(job_info)
    else:
        task["version"] = "UNKNOWN"
        task["active_color"] = None
        task["status_page_status_code"] = None
        task["app_status"] = util.status_level("UNKNOWN")
        task["jobs"] = dict()

    task["status"] = overall_status(task)
    task["severity"] = util.calculate_severity(task)
    return task


def get_status_url(name, group, vertical, subgroup, base_domain, status_path, root_app, cfg):
    if 'status_path' in cfg and name in cfg['status_path']:
        return cfg['status_path'][name].replace('{environment}', group)
    if root_app:
        name = vertical
    if status_path:
        status_url_prefix = name + "." + subgroup if subgroup else name
        status_url_prefix = status_url_prefix + "." + vertical if not root_app else name
        return ''.join(['http://', status_url_prefix, '.', group, '.', base_domain, status_path])
    else:
        return ''


def overall_status(task):
    if task["marathon"]["healthy"] < task["marathon"]["instances"] or \
            task["status_page_status_code"] and task["status_page_status_code"] > 500:
        return util.status_level("ERROR")
    else:
        return 1 if "app_status" not in task or task["app_status"] is None else task["app_status"]
