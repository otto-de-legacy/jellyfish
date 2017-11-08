import json
from threading import Timer
from flask import logging

import boto3

from app import config

logger = logging.getLogger(__name__)


def update_aws(thread_id, service, interval, greedy=False):
    application_environment_mapping = get_beanstalk_environments(service)
    for application, environment in application_environment_mapping.items():
        health = get_beanstalk_health(environment)
        app_id = service["id"] + '/' + application
        config.rdb.set(app_id, json.dumps(health))
        config.rdb.sadd("all-services", app_id)
    if not greedy:
        logger.debug("Finish update for aws")
        Timer(interval=interval,
              function=update_aws,
              args=(thread_id, service, interval)).start()


def get_beanstalk_client(access_key, secret_key):
    return boto3.client(
        'elasticbeanstalk',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key)


def get_beanstalk_environments(service):
    return {}


def get_beanstalk_health(service):
    return {}
