# -*- coding: utf-8 -*-
import logging
import pickle
import uuid
from threading import Timer

import redislite
from app import config, status, styleguide, update, views
from delorean import Delorean
from eliza.config import ConfigLoader
from flask import Flask

logger = logging.getLogger(__name__)


def create_app(port, environment, working_dir, greedy_mode):
    flask = Flask(__name__)
    flask.config.from_pyfile('config.py')

    config_loader = ConfigLoader(verify=False)
    config.info = config_loader.load_application_info("./")
    config.config = config_loader.load_config("resources/", environment, fill_with_defaults=True)
    config.rdb = redislite.Redis(working_dir + 'redis.db')
    config.rdb.flushall()
    config.rdb.flushdb()

    start_tasks(config.config, greedy_mode)

    register_status_page(flask, config.rdb, config.info, environment, port)

    flask.register_blueprint(views.blueprint)
    flask.register_blueprint(styleguide.blueprint)

    return flask


def register_status_page(flask, rdb, info, environment, port):
    status.blueprint.redis = rdb
    status.blueprint.navigation_bar = config.navigation_bar
    status.blueprint.info = info
    status.blueprint.environment = environment
    status.blueprint.port = port
    status.blueprint.start_time = Delorean.now()
    status.blueprint.start_time = Delorean.now()
    flask.register_blueprint(status.blueprint)


def generate_id():
    return str(uuid.uuid4())


def start_tasks(config_file, greedy_mode):
    if 'marathons' in config_file:
        for marathon_cfg in config_file['marathons']:
            start_thread_timer(marathon_cfg['host'], update.update_marathon, marathon_cfg, greedy_mode)
    if 'services' in config_file:
        service_list = list()
        for service in config_file['services']:
            for env in config_file['environments']:
                service_list.append({'id': service['id'].replace('{environment}', env['name']),
                                     'url': service['url'].replace('{environment}', env['name'])})
        start_thread_timer("single_services", update.update_service, service_list, greedy_mode)


def start_thread_timer(thread_name, function, cfg, greedy_mode):
    thread_id = generate_id()
    config.rdb.lpush('thread-list', thread_name)
    config.rdb.set(thread_id + config.THREAD_SUFFIX, pickle.dumps(Delorean.now()))
    Timer(interval=1, function=function,
          args=(thread_id, cfg, config.THREAD_UPDATE_INTERVAL, greedy_mode)).start()
