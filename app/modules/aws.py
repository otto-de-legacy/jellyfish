import json
from threading import Timer
from flask import logging

import boto3

from app import config
from app.modules import util
from app.util import get_in_dict

logger = logging.getLogger(__name__)


def update_aws(thread_id, service, interval, greedy=False):
    beanstalk_client = get_beanstalk_client(service['region_name'], service['access_key'], service['secret_key'])
    application_environment_mapping = get_beanstalk_environments(beanstalk_client)
    for application, environment in application_environment_mapping.items():
        app_id = service["id"] + '/' + application

        health = get_beanstalk_health(service, beanstalk_client, app_id, environment)

        config.rdb.set(app_id, json.dumps(health))
        config.rdb.sadd("all-services", app_id)
    if not greedy:
        logger.debug("Finish update for aws")
        Timer(interval=interval,
              function=update_aws,
              args=(thread_id, service, interval)).start()


def get_beanstalk_client(region_name, access_key, secret_key):
    return boto3.client(
        'elasticbeanstalk',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region_name)


def get_beanstalk_environments(beanstalk_client):
    data = dict()
    response = beanstalk_client.describe_environments()
    for env in response['Environments']:
        application_name = env['ApplicationName']
        environment_name = env['EnvironmentName']
        data[application_name] = environment_name
    return data


def get_beanstalk_health(service, beanstalk_client, app_id, environment_name):
    response = beanstalk_client.describe_environment_health(
        EnvironmentName=environment_name,
        AttributeNames=[
            'Status', 'Color', 'Causes', 'ApplicationMetrics', 'InstancesHealth', 'All', 'HealthStatus', 'RefreshedAt'
        ]
    )

    group, vertical, _, _, _ = util.itemize_app_id(app_id)
    name = environment_name.split('-')[1]

    task = dict()
    task["id"] = app_id
    task[
        "status_url"] = "https://" + name + "." + group + "." + vertical + "." + service[
        'domain_suffix'] + "/" + vertical + "-" + name + "/internal/status"
    task["group"] = group
    task["vertical"] = vertical
    task["subgroup"] = ""
    task["name"] = name
    task["color"] = "GRN"
    task["full-name"] = task["vertical"] + "-" + task["name"]
    task["active_color"] = "GRN"

    instances = 0
    for status in response['InstancesHealth']:
        instances += response['InstancesHealth'][status]

    unhealthy = 0
    for status in ['Degraded', 'Severe', 'Warning', 'Unknown']:
        unhealthy += response['InstancesHealth'][status]

    task["marathon"] = dict()
    task["marathon"]["origin"] = "aws"
    task["marathon"]["instances"] = instances
    task["marathon"]["cpu"] = 0
    task["marathon"]["mem"] = 0
    task["marathon"]["staged"] = response['InstancesHealth']['Pending']
    task["marathon"]["running"] = response['InstancesHealth']['Ok']
    task["marathon"]["healthy"] = response['InstancesHealth']['Ok']
    task["marathon"]["unhealthy"] = unhealthy
    task["marathon"]["marathon_link"] = ""
    task["marathon"]["labels"] = {}

    task = get_service_info(task)

    task["status"] = overall_status(task)
    task["severity"] = util.calculate_severity(task)
    return task


def get_service_info(task):
    status_page_data, active_color, status_page_code = util.get_application_status(task["status_url"], {})
    task["version"] = get_in_dict(["application", "version"], status_page_data, "UNKNOWN")
    task["status_page_status_code"] = status_page_code
    task["app_status"] = util.status_level(get_in_dict(["application", "status"], status_page_data, "UNKNOWN"))
    task["jobs"] = dict()
    for job, job_info in get_in_dict(["application", "statusDetails"], status_page_data, {}).items():
        task["jobs"][job] = util.get_job_info(job_info)

    task["status"] = overall_status(task)
    task["severity"] = util.calculate_severity(task)
    return task


def overall_status(task):
    if task["marathon"]["healthy"] < task["marathon"]["instances"] or \
                    task["status_page_status_code"] and task["status_page_status_code"] > 500:
        return util.status_level("ERROR")
    else:
        return 1 if "app_status" not in task or task["app_status"] is None else task["app_status"]
