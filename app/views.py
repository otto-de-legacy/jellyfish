import json
import logging
from delorean import Delorean, parse
from dotmap import DotMap
from flask import request, url_for, jsonify, Blueprint, redirect

from app import config
from app import view_util
from app.util import get_in_dict

logger = logging.getLogger('views')

blueprint = Blueprint('views', __name__)


def get_all_apps():
    apps = config.rdb.smembers("all-services") or []
    app_list = list()
    for app in apps:
        raw_app = config.rdb.get(app)
        if raw_app:
            app_list.append(json.loads(raw_app.decode()))
    return app_list


def get_error_messages(app_list):
    errors = dict()
    errors['all'] = set()
    for app in app_list:
        if "marathon" in app:
            raw_error_message = config.rdb.get(app['marathon']['origin'] + '-errors')
            if raw_error_message:
                if not app['vertical'] in errors:
                    errors[app['vertical']] = set()
                errors['all'].add(raw_error_message.decode())
                errors[app['vertical']].add(raw_error_message.decode())
    return errors


def filter(name, include, exclude):
    return name in include or (not include and name not in exclude)


def get_filter_lists(l):
    return [n for n in l if n[0] != '!'], [n[1:] for n in l if n[0] == '!']


def filter_state(app_list, name_filter, group_filter, type_filter, active_color_only_filter, status_filter,
                 include_jobs, include_age, env_filter):
    if name_filter:
        include_names, exclude_names = get_filter_lists(name_filter)
    if group_filter:
        include_groups, exclude_groups = get_filter_lists(group_filter)
    if type_filter:
        include_types, exclude_types = get_filter_lists(type_filter)
    if env_filter:
        include_envs, exclude_envs = get_filter_lists(env_filter)
    filtered_list = list()
    for app in app_list:
        if not name_filter or filter(app['name'].split('::')[1], include=include_names, exclude=exclude_names):
            if not env_filter or filter(app['group'], include=include_envs, exclude=exclude_envs):
                if not group_filter or filter(app['vertical'], include=include_groups, exclude=exclude_groups):
                    if not type_filter or filter(get_in_dict(["marathon", "labels", "type"], app, ""),
                                                 include=include_types,
                                                 exclude=exclude_types):
                        if not active_color_only_filter or not app["active_color"] \
                                or app["color"] == app["active_color"]:
                            if app["status"] >= status_filter:
                                if include_jobs:
                                    filtered_jobs = dict()
                                    for job_name, job_info in app["jobs"].items():
                                        if job_info['status'] >= status_filter:
                                            if job_info['status'] >= 1 and include_age and job_info.get('stopped',
                                                                                                        False):
                                                job_info["age"] = get_humanize_age(job_info)
                                            filtered_jobs[job_name] = job_info
                                    app["jobs"] = filtered_jobs
                                else:
                                    app["jobs"] = dict()
                                filtered_list.append(app)
    return filtered_list


def get_humanize_age(job):
    if job:
        now = Delorean.now()
        return (now - (now - parse(job['stopped'], dayfirst=False, yearfirst=True))).humanize()
    return ""


def transform_to_display_data(apps):
    display_data = DotMap()
    for app in apps:
        display_data["all"][app["full-name"]][app["group"]][app["color"]] = app
        display_data[app["vertical"]][app["name"]][app["group"]][app["color"]] = app
    return display_data.toDict()


def list_services_by_severity(transformed_data):
    sorted_services = dict()
    for vertical, services in transformed_data.items():
        sorted_services[vertical] = sorted(services.keys())
    for vertical, services in sorted_services.items():
        sorted_services[vertical] = sorted(services,
                                           key=lambda service_name:
                                           sum_severity_per_service(transformed_data[vertical][service_name]),
                                           reverse=True)
    return sorted_services


def sum_severity_per_service(service):
    service_severity = 0
    for group_name, group in service.items():
        for color_name, color in group.items():
            service_severity += color['severity']
    return service_severity


def get_app_resource_allocation(tasks):
    app_resources = DotMap()
    vertical_resources = DotMap()

    for task in tasks:
        if "marathon" in task:
            for field in ['cpu', 'mem']:
                sum = task["marathon"]["instances"] * task["marathon"][field]
                add_to(app_resources, task["vertical"], task["name"], task["full-name"], field, sum)
                add_to(vertical_resources, task["vertical"], None, None, field, sum)

    for task in tasks:
        if "marathon" not in task:
            for field in ['cpu', 'mem']:
                add_to(app_resources, task["vertical"], task["name"], task["full-name"], field, 0)
                add_to(vertical_resources, task["vertical"], None, None, field, 0)

    return vertical_resources.toDict(), app_resources.toDict()


def add_to(dotmap, vertical, name, full_name, field, value):
    if name:
        if not dotmap[vertical][name][field]:
            dotmap[vertical][name][field] = 0
        if not dotmap["all"][full_name][field]:
            dotmap["all"][full_name][field] = 0
        dotmap[vertical][name][field] += value
        dotmap["all"][full_name][field] += value
    else:
        if not dotmap[vertical][field]:
            dotmap[vertical][field] = 0
        if not dotmap["all"][field]:
            dotmap["all"][field] = 0
        dotmap[vertical][field] += value
        dotmap["all"][field] += value


def get_tabs(app_list):
    tabs = set()
    tabs.add("all")
    for app in app_list:
        tabs.add(app["vertical"])
    return list(tabs)


def filter_environments(environments, env_filter):
    if env_filter:
        include_envs, exclude_envs = get_filter_lists(env_filter)
        filtered_environments = list()
        for env in environments:
            if filter(env['name'].lower(),
                      include=[e.lower() for e in include_envs],
                      exclude=[e.lower() for e in exclude_envs]):
                filtered_environments.append(env)
        return filtered_environments
    else:
        return environments


@blueprint.route('/')
@blueprint.route('/index')
def index():
    return redirect(url_for('views.monitor'))


@blueprint.route('/monitor', methods=['GET'])
def monitor(cinema_mode=False):
    group_filter, name_filter, status_filter, type_filter, env_filter = get_filter_values()
    active_color_filter = request.args.get('active_color_only', 'false') == 'true'
    status_filter = int(request.args.get('level', 0))
    include_jobs = request.args.get('jobs', 'true') == 'true'
    include_age = request.args.get('status_age', "true") == 'true'
    auto_refresh = request.args.get('refresh', False)

    app_list = get_all_apps()
    filtered_apps = filter_state(app_list=app_list,
                                 name_filter=name_filter,
                                 group_filter=group_filter,
                                 type_filter=type_filter,
                                 active_color_only_filter=active_color_filter,
                                 status_filter=status_filter,
                                 include_jobs=include_jobs,
                                 include_age=include_age,
                                 env_filter=env_filter)
    vertical_resource_allocation, app_resource_allocation = get_app_resource_allocation(app_list)
    transformed_data = transform_to_display_data(filtered_apps)

    return view_util.render("jellyfish.html",
                            "Jellyfish",
                            state=transformed_data,
                            services_by_severity=list_services_by_severity(transformed_data),
                            vertical_ressources=vertical_resource_allocation,
                            app_ressources=app_resource_allocation,
                            tabs=get_tabs(app_list),
                            errors=get_error_messages(app_list),
                            environments=filter_environments(config.config["environments"],
                                                             env_filter),
                            cinema_mode=cinema_mode,
                            auto_refresh=auto_refresh)


def get_filter_values():
    name_filter = request.args.get('filter', False)
    group_filter = request.args.get('group', False)
    type_filter = request.args.get('type', False)
    env_filter = request.args.get('env', False)
    status_filter = int(request.args.get('level', 0))
    if name_filter:
        name_filter = name_filter.split(",")
    if group_filter:
        group_filter = group_filter.split(",")
    if env_filter:
        env_filter = env_filter.split(",")
    if type_filter:
        type_filter = type_filter.split(",")
    return group_filter, name_filter, status_filter, type_filter, env_filter


@blueprint.route('/monitor/cinema', methods=['GET'])
def toggles_cinema():
    return monitor(cinema_mode=True)


@blueprint.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


def error_page(error):
    return view_util.render("error.html",
                            "Error",
                            error=error)
