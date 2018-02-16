def get_task(id="/group/vertical/name",
             group="group",
             vertical="vertical",
             name="name",
             source="no_source",
             status_url="http://name.vertical.group.some-domain.com/service/internal/status",
             version="0.1.0",
             status=0, app_status=0,
             instances=1, healthy=1, unhealthy=0,
             color="GRN", active_color="GRN",
             origin='some-marathon.com',
             status_page_status_code=200,
             jobs=None, marathon=None,
             marathon_link='http://some-marathon.com/ui/#/apps/%2Fgroup%2Fvertical%2Fname',
             severity=0,
             type=None):
    return {
        "id": id,
        "group": group,
        "vertical": vertical,
        "name": source + "::" + name,
        "full-name": source + "::" + vertical + "-" + name,
        "color": color,
        "subgroup": '',
        "active_color": active_color,
        "status": status,
        "severity": severity,
        "app_status": app_status,
        "status_url": status_url,
        "status_page_status_code": status_page_status_code,
        "version": version,
        "jobs": jobs if jobs is not None else {"thread-1": {"message": "05-07-2016 20:34 [28 seconds ago]",
                                                            "status": 0,
                                                            "started": None,
                                                            "stopped": None,
                                                            "running": True},
                                               "thread-2": {"message": '05-07-2016 20:34 [33 seconds ago]',
                                                            "status": 2,
                                                            "started": "2016-08-12T09:16:38.83+02:00",
                                                            "stopped": "2016-08-15T09:16:38.82+02:00",
                                                            "running": False}},
        "marathon": marathon if marathon is not None else {"origin": origin,
                                                           "instances": instances,
                                                           "healthy": healthy,
                                                           "unhealthy": unhealthy,
                                                           "running": 1,
                                                           "staged": 0,
                                                           "cpu": 1,
                                                           "mem": 1024,
                                                           "marathon_link": marathon_link,
                                                           "labels": {} if not type else {"type": type}}}


def get_marathon_app():
    return {"id": "/group/vertical/name",
            "env": {"OTTO_STATUS_PATH": "/service/internal/status"},
            "instances": 1,
            "cpus": 1,
            "mem": 1024,
            "version": "2016-05-26T07:15:05.585Z",
            "versionInfo": {"lastScalingAt": "2016-05-26T07:15:05.585Z",
                            "lastConfigChangeAt": "2016-05-26T07:15:05.585Z"},
            "tasksStaged": 0,
            "tasksRunning": 1,
            "tasksHealthy": 1,
            "tasksUnhealthy": 0,
            "deployments": []}


def get_marathon_app_list():
    return {"apps": [get_marathon_app(),
                     {"id": "/develop/mesos/otto-marathon-healthcheck",
                      "instances": 2,
                      "cpus": 0.01,
                      "mem": 4}]}


def get_status(status="OK"):
    return {
        "application": {
            "environment": "live",
            "status": status,
            "version": "0.1.0",
            "group": "tools",
            "name": "some-servide",
            "commit": "508e363c1711d769d1106394b111d09d6f5d9d61",
            "vcs_link": "some-link",
            "statusDetails": {
                "thread-1": {
                    "status": "OK",
                    "message": "05-07-2016 20:34 [28 seconds ago]",
                    "running": "some-id"
                },
                "thread-2": {
                    "status": "WARNING",
                    "message": "05-07-2016 20:34 [33 seconds ago]",
                    "started": "2016-08-12T09:16:38.83+02:00",
                    "stopped": "2016-08-15T09:16:38.82+02:00"
                }
            },
            "description": "some-description"
        },
        "serviceSpecs": {},
        "system": {
            "systemstarttime": "05-07-2016 14:39",
            "systemtime": "05-07-2016 20:35",
            "hostname": "some-agent",
            "port": 31010,
            "uptime": "5 hours ago"
        },
        "team": {
            "contact_technical": "unknown",
            "contact_business": "unknown",
            "team": "unknown"
        }
    }


def describe_environments():
    return {'Environments': [
        {'ApplicationName': 'mammal-cat',
         'EnvironmentName': 'mammal-cat-develop',
         'Health': 'Green',
         'HealthStatus': 'Ok',
         'Status': 'Ready',
         'VersionLabel': 'someVersion1234'},
        {'ApplicationName': 'mammal-dog',
         'EnvironmentName': 'mammal-dog-develop',
         'Health': 'Grey',
         'HealthStatus': 'Unknown',
         'VersionLabel': 'someVersion5678'},

    ],
        'ResponseMetadata': {}}


def describe_environment_health():
    return {'ApplicationMetrics': {'RequestCount': 0},
            'Causes': [],
            'Color': 'Green',
            'EnvironmentName': 'mammal-dog',
            'HealthStatus': 'Ok',
            'InstancesHealth': {'Degraded': 0,
                                'Info': 0,
                                'NoData': 0,
                                'Ok': 1,
                                'Pending': 0,
                                'Severe': 1,
                                'Unknown': 0,
                                'Warning': 0},
            'RefreshedAt': 'someTime',
            'ResponseMetadata': {},
            'Status': 'Ready'}
