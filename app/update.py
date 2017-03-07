# -*- coding: utf-8 -*-
import json
import pickle
import re
from pprint import pprint
from threading import Timer
from urllib.parse import quote_plus

import requests
from delorean import Delorean
from flask import logging

from app import config

logger = logging.getLogger(__name__)


def update_marathon(thread_id, cfg, interval, greedy=False):
    app_list = get_apps(cfg)
    previous_tasks = (config.rdb.get(thread_id) or b'').decode().split(',')
    blacklist = '(?:%s)' % '|'.join(cfg['blacklist']) if 'blacklist' in cfg else '1234'
    tasks = list()
    for app in app_list:
        try:
            _, _, _, app_name, _ = itemize_app_id(app["id"])
            if not re.match(blacklist, app["id"]):
                config.rdb.sadd("all-services", app["id"])
                config.rdb.set(app["id"], json.dumps(get_task_info(app, cfg)))
                tasks.append(app["id"])
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
        Timer(interval=interval, function=update_marathon,
              args=(thread_id, cfg, interval)).start()


def update_service(thread_id, service_list, interval, greedy=False):
    for service in service_list:
        config.rdb.sadd("all-services", service["id"])
        config.rdb.set(service["id"], json.dumps(get_service_info(service)))
    config.rdb.set("single_services", pickle.dumps(Delorean.now()))
    if not greedy:
        logger.debug("Finish update for services")
        Timer(interval=interval, function=update_service,
              args=(thread_id, service_list, interval)).start()


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
    task["group"], task["vertical"], task["subgroup"], task["name"], task["color"] = itemize_app_id(app["id"])
    task["full-name"] = "-".join([task["vertical"], task["name"]])

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
    status_path = get_in_dict(["env", cfg.get("status_path_lable")], app, "") or \
                  get_in_dict(["labels", cfg.get("status_path_lable")], app, "")
    task["status_url"] = get_status_url(task["name"], task["group"], task["vertical"], task["subgroup"],
                                        cfg['base_domain'], status_path,
                                        root_app, cfg)

    if status_path and task["marathon"]["instances"] > 0:
        status_page_data, active_color, status_page_code = get_application_status(task["status_url"], cfg)
        if task["color"] and active_color and task["color"] != active_color:
            task["status_url"] = task["status_url"].replace('http://', 'http://staged.')
            status_page_data, _, status_page_code = get_application_status(task["status_url"], cfg)
        task["version"] = get_in_dict(["application", "version"], status_page_data, "UNKNOWN")
        task["status_page_status_code"] = status_page_code
        task["active_color"] = active_color
        task["app_status"] = status_level(get_in_dict(["application", "status"], status_page_data, "UNKNOWN"))
        task["jobs"] = dict()
        for job, job_info in get_in_dict(["application", "statusDetails"], status_page_data, {}).items():
            task["jobs"][job] = get_job_info(job_info)
    else:
        task["version"] = "UNKNOWN"
        task["active_color"] = None
        task["status_page_status_code"] = None
        task["app_status"] = status_level("UNKNOWN")
        task["jobs"] = dict()

    graphite_cpu_url = get_in_dict(['graphite', 'cpu'], cfg, "")
    graphite_mem_url = get_in_dict(['graphite', 'mem'], cfg, "")
    if task["marathon"]["instances"] > 0 and graphite_cpu_url and graphite_mem_url:
        resources = get_peak_resource_usage(graphite_cpu_url, graphite_mem_url, task["name"], task["vertical"],
                                            task["group"],
                                            task["color"] if 'blu' in task["id"] or 'grn' in task["id"] else None)
        task["marathon"]["max_cpu"] = resources["max_cpu"]
        task["marathon"]["max_mem"] = resources["max_mem"]
    else:
        task["marathon"]["max_cpu"] = 0
        task["marathon"]["max_mem"] = 0

    task["status"] = overall_status(task)
    task["severity"] = calculate_severity(task)
    return task


def get_service_info(service):
    task = dict()
    task["id"] = service["id"]
    task["status_url"] = service["url"]
    task["group"], task["vertical"], task["subgroup"], task["name"], task["color"] = itemize_app_id(service["id"])
    task["full-name"] = "-".join([task["vertical"], task["name"]])

    status_page_data, active_color, status_page_code = get_application_status(service["url"], service)
    task["version"] = get_in_dict(["application", "version"], status_page_data, "UNKNOWN")
    task["status_page_status_code"] = status_page_code
    task["active_color"] = active_color
    task["app_status"] = status_level(get_in_dict(["application", "status"], status_page_data, "UNKNOWN"))
    task["jobs"] = dict()
    for job, job_info in get_in_dict(["application", "statusDetails"], status_page_data, {}).items():
        task["jobs"][job] = get_job_info(job_info)

    task["status"] = task["app_status"]
    task["severity"] = calculate_severity(task)
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


def get_in_list(index, list, default=None):
    if len(list) > index:
        return list[index]
    else:
        return default


def get_in_dict(key_list, my_dict, default=None):
    tmp = my_dict
    for key in key_list:
        if not isinstance(tmp, dict):
            return default
        tmp = tmp.get(key, default)
    return tmp


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


def overall_status(task):
    if task["marathon"]["healthy"] < task["marathon"]["instances"] or \
                    task["status_page_status_code"] and task["status_page_status_code"] > 500:
        return status_level("ERROR")
    else:
        return 1 if "app_status" not in task or task["app_status"] is None else task["app_status"]


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


def get_peak_resource_usage(base_url_cpu, base_url_mem, service, vertical, env, color):
    if color:
        color = "-" + color.lower()
    else:
        color = ""
    graphite_url_mem = base_url_mem.format(
        env, vertical, service, color)
    graphite_url_cpu = base_url_cpu.format(
        env, vertical, service, color)

    try:
        mem_result = requests.get(graphite_url_mem, headers={"Accept": "application/json"}, verify=False, timeout=30)
        mem = round(get_max(json.loads(mem_result.text)[0]['datapoints']) / 1024 / 1024, 2)
    except (ValueError, IndexError, requests.exceptions.Timeout,
            requests.exceptions.ConnectionError) as error:
        logger.warning(
            ' '.join(
                ["could not read MEM usage from graphite for :", service + ", " + vertical + ", " + env + " " + "[",
                 error.__class__.__name__, "]", graphite_url_mem]))
        mem = 0

    try:
        cpu_result = requests.get(graphite_url_cpu, headers={"Accept": "application/json"}, verify=False, timeout=30)
        cpu = round(get_max(json.loads(cpu_result.text)[0]['datapoints']), 2)
    except (ValueError, IndexError, requests.exceptions.Timeout,
            requests.exceptions.ConnectionError) as error:
        logger.warning(
            ' '.join(
                ["could not read CPU usage from graphite for :", service + ", " + vertical + ", " + env + " " + "[",
                 error.__class__.__name__, "]", graphite_url_cpu]))
        cpu = 0

    return {'max_cpu': cpu, 'max_mem': mem}


def get_max(series):
    return max([p[0] if p[0] else 0 for p in series])
