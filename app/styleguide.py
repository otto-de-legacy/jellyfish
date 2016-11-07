from app.view_util import render
from flask import Blueprint

blueprint = Blueprint('styleguide', __name__)


@blueprint.route('/internal/style', methods=['GET'])
def style_guide():
    test_data = {
        "1) Green and Blue are OK (Marathon)": {"GRN": {
            "status": 0,
            "app_status": 0,
            "name": "1-grn",
            "version": "0.1.1464339",
            "status_age": "",
            "jobs": {"Job OK": {"status": 0}},
            "marathon": {
                "marathon_link": "/",
                "instances": 1,
                "healthy": 1,
                "staged": 0,
                "unhealthy": 0,
                "cpu": 1,
                "mem": 1024,
                "max_cpu": 0.5,
                "max_mem": 512
            }
        }, "BLU": {
            "status": 0,
            "app_status": 0,
            "name": "1-blu",
            "version": "0.1.1464339",
            "status_age": "",
            "jobs": {"Job OK": {"status": 0}},
            "marathon": {
                "marathon_link": "/",
                "instances": 1,
                "healthy": 1,
                "staged": 0,
                "unhealthy": 0,
                "cpu": 1,
                "mem": 1024,
                "max_cpu": 0.5,
                "max_mem": 512
            }
        }},
        "1b) Non Marathon Application": {"GRN": {
            "status": 0,
            "app_status": 0,
            "name": "1-grn",
            "version": "0.1.1464339",
            "status_age": "",
            "jobs": {"Job OK": {"status": 0}}
        }},
        "2) Running jobs will indicated as glowing": {"GRN": {
            "status": 0,
            "app_status": 0,
            "name": "2",
            "version": "0.1.1464339",
            "status_age": "",
            "jobs": {"Job OK": {"status": 0, "running": True},
                     "Job UNKNOWN": {"status": 1, "running": True},
                     "Job WARNING": {"status": 2, "running": True},
                     "Job ERROR": {"status": 3, "running": True}},
            "marathon": {
                "marathon_link": "/",
                "instances": 1,
                "healthy": 1,
                "staged": 0,
                "unhealthy": 0,
                "cpu": 1,
                "mem": 1024,
                "max_cpu": 0.5,
                "max_mem": 512
            }
        }},
        "3) App status is unknown (could not read status page) but marathon tasks are healthy": {"GRN": {
            "status": 1,
            "app_status": 1,
            "name": "3",
            "version": "UNKNOWN",
            "status_age": "",
            "jobs": {},
            "marathon": {
                "marathon_link": "/",
                "instances": 1,
                "healthy": 1,
                "staged": 0,
                "unhealthy": 0,
                "cpu": 1,
                "mem": 1024,
                "max_cpu": 0.5,
                "max_mem": 512
            }
        }},
        "4) App is suspended (0 of 0 instances)": {"GRN": {
            "status": 1,
            "app_status": 1,
            "name": "4",
            "version": "UNKNOWN",
            "status_age": "",
            "jobs": {},
            "marathon": {
                "marathon_link": "/",
                "instances": 0,
                "healthy": 0,
                "staged": 0,
                "unhealthy": 0,
                "cpu": 1,
                "mem": 1024,
                "max_cpu": 0.5,
                "max_mem": 512
            }
        }},
        "5) App status is warning": {"GRN": {
            "status": 2,
            "app_status": 2,
            "name": "5",
            "version": "0.1.1464339",
            "status_age": "",
            "jobs": {"Job OK": {"status": 0},
                     "Job UNKNOWN": {"status": 1},
                     "Job WARNING": {"status": 2},
                     "Job ERROR": {"status": 3}},
            "marathon": {
                "marathon_link": "/",
                "instances": 1,
                "healthy": 1,
                "staged": 0,
                "unhealthy": 0,
                "cpu": 1,
                "mem": 1024,
                "max_cpu": 0.5,
                "max_mem": 512
            }
        }},
        "6) App status is error": {"GRN": {
            "status": 3,
            "app_status": 3,
            "name": "6",
            "version": "0.1.1464339",
            "status_age": "",
            "jobs": {"Job OK": {"status": 0},
                     "Job UNKNOWN": {"status": 1},
                     "Job WARNING": {"status": 2},
                     "Job ERROR": {"status": 3}},
            "marathon": {
                "marathon_link": "/",
                "instances": 2,
                "healthy": 2,
                "staged": 0,
                "unhealthy": 0,
                "cpu": 1,
                "mem": 1024,
                "max_cpu": 0.5,
                "max_mem": 512
            }
        }},
        "7) App status of one instance is critical": {"GRN": {
            "status": 3,
            "app_status": 0,
            "name": "7",
            "version": "0.1.1464339",
            "status_age": "",
            "marathon_link": "/",
            "jobs": {"Job OK": {"status": 0},
                     "Job UNKNOWN": {"status": 1},
                     "Job WARNING": {"status": 2},
                     "Job ERROR": {"status": 3}},
            "marathon": {
                "marathon_link": "/",
                "instances": 2,
                "healthy": 1,
                "staged": 0,
                "unhealthy": 1,
                "cpu": 1,
                "mem": 1024,
                "max_cpu": 0.5,
                "max_mem": 512
            }
        }},
        "8) App is down": {"GRN": {
            "status": 3,
            "app_status": 1,
            "name": "8",
            "version": "UNKNOWN",
            "status_age": "",
            "marathon_link": "/",
            "jobs": {},
            "marathon": {
                "marathon_link": "/",
                "instances": 1,
                "healthy": 0,
                "staged": 0,
                "unhealthy": 0,
                "cpu": 1,
                "mem": 1024,
                "max_cpu": 0.5,
                "max_mem": 512
            }
        }},
        "9) App is healthy but status page is not accessible (status code > 500. possible issue with cname/varnish)": {"GRN": {
            "status": 3,
            "app_status": 1,
            "name": "9",
            "status_page_status_code": 503,
            "version": "UNKNOWN",
            "status_age": "",
            "jobs": {},
            "marathon": {
                "marathon_link": "/",
                "instances": 1,
                "healthy": 1,
                "staged": 0,
                "unhealthy": 0,
                "cpu": 1,
                "mem": 1024,
                "max_cpu": 0.5,
                "max_mem": 512
            }
        }},
    }
    return render("styleguide.html",
                  "Styleguide",
                  testdata=test_data)
