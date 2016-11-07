import json
import pickle
import socket

from app import config
from app import view_util
from delorean import Delorean
from flask import Response, render_template, request, jsonify, Blueprint

blueprint = Blueprint('status', __name__)


@blueprint.route("/internal/health")
def status_health():
    js = json.dumps({"status": "ok"})
    resp = Response(js, status=200, mimetype='text/plain')
    return resp


@blueprint.route("/internal/status")
def status_page():
    status = generate_status()
    if view_util.request_wants_json():
        return Response(json.dumps(status), status=200, mimetype=view_util.request_wants_json())
    return render_template("status_page.html",
                           status=status)


@blueprint.route("/internal/status.json")
def status_page_json():
    status = generate_status()
    return Response(json.dumps(status), status=200, mimetype='application/json')


@blueprint.route("/internal/info.json")
def info_json():
    return Response(json.dumps(blueprint.info), status=200, mimetype='application/json')


def generate_status():
    now = Delorean.now()
    up_time = (now - (now - blueprint.start_time)).humanize()

    return {
        "application": {
            "name": blueprint.info['name'],
            "description": blueprint.info['description'],
            "group": blueprint.info['group'],
            "environment": blueprint.environment,
            "version": blueprint.info['version'],
            "commit": blueprint.info['commit'],
            "vcs_link": blueprint.info['vcs_link'] + blueprint.info['commit'],
            "status": "OK",
            "statusDetails": get_job_status()
        },
        "system": {
            "hostname": socket.gethostname(),
            "port": blueprint.port,
            "systemtime": now.format_datetime(format=get_timestamp_format()),
            "systemstarttime": blueprint.start_time.format_datetime(format=get_timestamp_format()),
            "uptime": up_time
        },
        "team": {
            "team": blueprint.info['team'],
            "contact_technical": blueprint.info['contact_technical'],
            "contact_business": blueprint.info['contact_business']
        },
        "serviceSpecs": {

        }
    }


@blueprint.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp


def get_timestamp_format():
    return 'dd-MM-YYYY HH:mm'


def get_job_status():
    jobs = dict()
    now = Delorean.now()
    for name in blueprint.redis.lrange('thread-list', 0, -1):
        name = name.decode()
        raw_time_object = blueprint.redis.get(name)
        if raw_time_object:
            last_update = pickle.loads(raw_time_object)

            time_passed_since_last_update = (now - last_update)
            if time_passed_since_last_update.seconds > config.THREAD_UPDATE_INTERVAL * 3:
                status = "WARNING"
            else:
                status = "OK"
            update_age = (now - time_passed_since_last_update).humanize()
            message = last_update.format_datetime(format=get_timestamp_format()) + " [" + update_age + "]"
        else:
            message = "Never"
            status = "ERROR"

        jobs[name] = {"message": message, "status": status}
    return jobs
