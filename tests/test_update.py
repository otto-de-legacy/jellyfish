# -*- coding: utf-8 -*-
import json
import unittest
from unittest import mock

import redislite
import requests
import requests_mock
from mock import MagicMock

from app import config
from app import update
from tests.helper import testdata_helper

unittest.util._MAX_LENGTH = 1000


@requests_mock.Mocker()
class TestView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        config.rdb = redislite.Redis('redis.db')
        cls.marathon = {"protocol": "http",
                        "host": "some-marathon.com",
                        "apps": "/v2/apps",
                        "username": "username",
                        "password": "password",
                        "blacklist": [".*marathon-healthcheck"],
                        "root_app_lable": "ROOT_APP",
                        "status_path_lable": "STATUS_PATH",
                        "base_domain": "some-domain.com"}
        cls.app = {"id": "/group/vertical/name",
                   "env": {"STATUS_PATH": "/service/internal/status"},
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
                   "deployments": [],
                   "labels": {}}
        cls.app_server_service = {"id": "/group/vertical/name",
                                  "url": "http://some-domain.com/service/internal/status"}
        cls.marathon_apps = {"apps": [cls.app,
                                      {"id": "/develop/mesos/marathon-healthcheck",
                                       "instances": 2,
                                       "cpus": 0.01,
                                       "mem": 4}]}
        cls.marathon_apps_json = json.dumps(cls.marathon_apps)

    def setUp(self):
        config.rdb.flushall()
        config.rdb.flushdb()

    def test_get_apps_200(self, mock):
        mock.register_uri('GET', "http://username:password@some-marathon.com/v2/apps", text=self.marathon_apps_json)
        self.assertEquals(self.marathon_apps["apps"], update.get_apps(self.marathon))
        self.assertCountEqual(json.dumps(self.marathon_apps['apps']),
                              config.rdb.get(self.marathon['host'] + '-cache').decode())
        self.assertEquals(None, config.rdb.get(self.marathon['host'] + '-errors'))

    def test_get_apps_401(self, mock):
        mock.register_uri('GET', "http://username:password@some-marathon.com/v2/apps", text="some html",
                          status_code=401)
        self.assertEquals([], update.get_apps(self.marathon))
        self.assertEqual(None, config.rdb.get(self.marathon['host'] + '-cache'))
        self.assertEquals(b'could not read marathon: some-marathon.com [ JSONDecodeError ]',
                          config.rdb.get(self.marathon['host'] + '-errors'))

    def test_get_apps_not_available(self, mock):
        tmp = requests.get
        requests.get = MagicMock(side_effect=requests.exceptions.Timeout)
        self.assertEquals([], update.get_apps(self.marathon))
        self.assertEqual(0, len(mock.request_history))
        self.assertEqual(None, config.rdb.get('some-marathon.com-cache'))
        self.assertEqual(None, config.rdb.get(self.marathon['host'] + '-cache'))
        requests.get = tmp

    def test_get_apps_use_cache(self, mock):
        mock.register_uri('GET', "http://username:password@some-marathon.com/v2/apps", text=self.marathon_apps_json)
        self.assertEquals(self.marathon_apps["apps"], update.get_apps(self.marathon))
        self.assertCountEqual(json.dumps(self.marathon_apps['apps']),
                              config.rdb.get(self.marathon['host'] + '-cache').decode())
        self.assertEquals(None, config.rdb.get(self.marathon['host'] + '-errors'))

        mock.register_uri('GET', "http://username:password@some-marathon.com/v2/apps", text="some html",
                          status_code=401)
        self.assertEquals(self.marathon_apps["apps"], update.get_apps(self.marathon))
        self.assertCountEqual(json.dumps(self.marathon_apps['apps']),
                              config.rdb.get(self.marathon['host'] + '-cache').decode())
        self.assertEquals(b'could not read marathon: some-marathon.com [ JSONDecodeError ]',
                          config.rdb.get(self.marathon['host'] + '-errors'))

        mock.register_uri('GET', "http://username:password@some-marathon.com/v2/apps", text=self.marathon_apps_json)
        self.assertEquals(self.marathon_apps["apps"], update.get_apps(self.marathon))
        self.assertCountEqual(json.dumps(self.marathon_apps['apps']),
                              config.rdb.get(self.marathon['host'] + '-cache').decode())
        self.assertEquals(None, config.rdb.get(self.marathon['host'] + '-errors'))

    def test_get_status_url(self, _):
        self.assertEquals("http://name.vertical.group.domain.de/status_path",
                          update.get_status_url("name", "group", "vertical", "", "domain.de", "/status_path", None, {}))
        self.assertEquals("http://vertical.group.domain.de/status_path",
                          update.get_status_url("vertical", "group", "vertical", "", "domain.de", "/status_path", True,
                                                {}))
        self.assertEquals("http://vertical.group.domain.de/status_path",
                          update.get_status_url("name", "group", "vertical", "", "domain.de", "/status_path", True, {}))
        self.assertEquals("http://name.subgroup.vertical.group.domain.de/status_path",
                          update.get_status_url("name", "group", "vertical", "subgroup", "domain.de", "/status_path",
                                                None, {}))
        self.assertEquals("http://vertical.group.domain.de/status_path",
                          update.get_status_url("name", "group", "vertical", "subgroup", "domain.de", "/status_path",
                                                True, {}))
        self.assertEquals("http://vertical.group.domain.de/status_path",
                          update.get_status_url("name", "group", "vertical", "subgroup", "domain.de", "/status_path",
                                                True,
                                                {"status_path": {"dog": "wololololololo"}}))
        self.assertEquals("http://group.alternate_status_path/status_path",
                          update.get_status_url("name", "group", "vertical", "subgroup", "domain.de", "/status_path",
                                                True,
                                                {"status_path": {
                                                    "name": "http://{environment}.alternate_status_path/status_path"}}))

    def test_itemize_app_id(self, _):
        group, vertical, subgroup, name, color = update.itemize_app_id("/group/vertical/name")
        self.assertEquals("group", group)
        self.assertEquals("vertical", vertical)
        self.assertEquals("", subgroup)
        self.assertEquals("name", name)
        self.assertEquals("GRN", color)

        group, vertical, subgroup, name, color = update.itemize_app_id("/group/vertical/name/blu")
        self.assertEquals("group", group)
        self.assertEquals("vertical", vertical)
        self.assertEquals("", subgroup)
        self.assertEquals("name", name)
        self.assertEquals("BLU", color)

        group, vertical, subgroup, name, color = update.itemize_app_id("/group/vertical/subgroup/name")
        self.assertEquals("group", group)
        self.assertEquals("vertical", vertical)
        self.assertEquals("subgroup", "subgroup")
        self.assertEquals("name", name)
        self.assertEquals("GRN", color)

        group, vertical, subgroup, name, color = update.itemize_app_id("/group/vertical/subgroup/name/blu")
        self.assertEquals("group", group)
        self.assertEquals("vertical", vertical)
        self.assertEquals("subgroup", "subgroup")
        self.assertEquals("name", name)
        self.assertEquals("BLU", color)

    def test_get_in_list(self, _):
        l = ["a", "b", "c"]
        self.assertEquals("a", update.get_in_list(0, l))
        self.assertEquals("b", update.get_in_list(1, l))
        self.assertEquals("c", update.get_in_list(2, l, "default"))
        self.assertEquals("default", update.get_in_list(3, l, "default"))
        self.assertEquals(None, update.get_in_list(3, l))

    def test_get_in_dict(self, _):
        d = {"a": {"b": "value"}}
        self.assertEquals(d["a"], update.get_in_dict(["a"], d))
        self.assertEquals("value", update.get_in_dict(["a", "b"], d, "default"))
        self.assertEquals("default", update.get_in_dict(["c"], d, "default"))
        self.assertEquals(None, update.get_in_dict(["a", "b", "c"], d))
        self.assertEquals("default", update.get_in_dict(["a", "b", "c"], d, "default"))
        self.assertEquals(None, update.get_in_dict(["c"], d))
        self.assertEquals(None, update.get_in_dict(["c"], None))
        self.assertEquals("default", update.get_in_dict(["c"], None, "default"))
        self.assertEquals(None, update.get_in_dict(["c"], {}))
        self.assertEquals("default", update.get_in_dict(["c"], {}, "default"))
        self.assertEquals(None, update.get_in_dict(["c", None], d))
        self.assertEquals("default", update.get_in_dict(["c", None], d, "default"))

    def test_get_job_info(self, _):
        self.assertDictEqual({"status": 0, "message": "ok", "started": None, "stopped": None, "running": False},
                             update.get_job_info(
                                 job={
                                     "status": "OK",
                                     "message": "ok"
                                 }))

        self.assertDictEqual({"status": 2, "message": "warning", "started": None, "stopped": None, "running": True},
                             update.get_job_info(
                                 job={
                                     "status": "WARNING",
                                     "message": "warning",
                                     "running": "some-id"
                                 }))

        self.assertDictEqual({"status": 2, "message": "warning", "started": "today", "stopped": None, "running": False},
                             update.get_job_info(
                                 job={
                                     "status": "WARNING",
                                     "message": "warning",
                                     "started": "today"
                                 }))

        self.assertDictEqual({"status": 2, "message": "warning", "started": "today", "stopped": None, "running": False},
                             update.get_job_info(
                                 job={
                                     "status": "WARNING",
                                     "message": "warning",
                                     "started": "today",
                                     "running": None
                                 }))

        self.assertDictEqual(
            {"status": 2, "message": "warning", "started": "yesterday", "stopped": "today", "running": True},
            update.get_job_info(
                job={
                    "status": "WARNING",
                    "message": "warning",
                    "started": "yesterday",
                    "stopped": "today",
                    "running": "some-id"
                }))

    def test_get_task_info_with_out_color(self, request_mock, *_):
        status = testdata_helper.get_status()
        request_mock.register_uri('GET', "http://name.vertical.group.some-domain.com/service/internal/status",
                                  text=json.dumps(status),
                                  headers={'x-color': 'GRN'})
        expected = testdata_helper.get_task()
        self.assertDictEqual(expected, update.get_task_info(self.app, self.marathon))
        self.assertEquals(1, len(request_mock.request_history))
        self.assertEquals("http://name.vertical.group.some-domain.com/service/internal/status",
                          request_mock.request_history[0].url)

    def test_get_task_info_visit_staged(self, request_mock, *_):
        status = testdata_helper.get_status()
        staged_status = testdata_helper.get_status(status="ERROR")
        request_mock.register_uri('GET', "http://name.vertical.group.some-domain.com/service/internal/status",
                                  text=json.dumps(status),
                                  headers={'x-color': 'BLU'})
        request_mock.register_uri('GET', "http://staged.name.vertical.group.some-domain.com/service/internal/status",
                                  text=json.dumps(staged_status),
                                  headers={'x-color': 'BLU'})

        expected_inactive = testdata_helper.get_task(id="/group/vertical/name/GRN",
                                                     app_status=3, status=3, severity=30, active_color="BLU",
                                                     color="GRN",
                                                     status_url='http://staged.name.vertical.group.some-domain.com/service/internal/status',
                                                     marathon_link='http://some-marathon.com/ui/#/apps/%2Fgroup%2Fvertical%2Fname%2FGRN')
        expected_active = testdata_helper.get_task(id="/group/vertical/name/BLU",
                                                   active_color="BLU", color="BLU",
                                                   status_url='http://name.vertical.group.some-domain.com/service/internal/status',
                                                   marathon_link='http://some-marathon.com/ui/#/apps/%2Fgroup%2Fvertical%2Fname%2FBLU')

        app_inactive = self.app.copy()
        app_inactive["id"] = "/group/vertical/name/GRN"
        app_active = self.app.copy()
        app_active["id"] = "/group/vertical/name/BLU"

        self.assertDictEqual(expected_inactive, update.get_task_info(app_inactive, self.marathon))
        self.assertDictEqual(expected_active, update.get_task_info(app_active, self.marathon))
        self.assertEquals(3, len(request_mock.request_history))
        self.assertEquals("http://name.vertical.group.some-domain.com/service/internal/status",
                          request_mock.request_history[0].url)
        self.assertEquals("http://staged.name.vertical.group.some-domain.com/service/internal/status",
                          request_mock.request_history[1].url)
        self.assertEquals("http://name.vertical.group.some-domain.com/service/internal/status",
                          request_mock.request_history[2].url)

    @mock.patch('app.update.get_application_status', return_value=[testdata_helper.get_status(), "GRN", 200])
    def test_get_task_info(self, *_):
        expected = testdata_helper.get_task()
        self.assertDictEqual(expected, update.get_task_info(self.app, self.marathon))

    @mock.patch('app.update.get_application_status', return_value=[testdata_helper.get_status(), "GRN", 200])
    def test_get_task_info_job_does_not_change(self, *_):
        expected = testdata_helper.get_task()
        self.assertDictEqual(expected, update.get_task_info(self.app, self.marathon))

    @mock.patch('app.update.get_application_status', return_value=[{}, None, 404])
    def test_get_task_info_status_page_not_available(self, *_):
        expected = testdata_helper.get_task(status=1, app_status=1, severity=1,
                                            status_page_status_code=404,
                                            version="UNKNOWN",
                                            active_color=None, jobs={})
        self.assertDictEqual(expected, update.get_task_info(self.app, self.marathon))

    @mock.patch('app.update.get_application_status', return_value=[{}, None, 503])
    def test_get_task_info_status_page_503(self, *_):
        expected = testdata_helper.get_task(status=3, app_status=1, severity=30,
                                            status_page_status_code=503,
                                            version="UNKNOWN",
                                            active_color=None, jobs={})

        self.assertDictEqual(expected, update.get_task_info(self.app, self.marathon))

    @mock.patch('app.update.get_application_status', return_value=[{}, None, 503])
    def test_get_task_info_status_page_503_in_live(self, *_):
        expected = testdata_helper.get_task(id='/live/vertical/name',
                                            group='live',
                                            status_url='http://name.vertical.live.some-domain.com/service/internal/status',
                                            marathon_link='http://some-marathon.com/ui/#/apps/%2Flive%2Fvertical%2Fname',
                                            status=3, app_status=1, severity=3000,
                                            status_page_status_code=503,
                                            version="UNKNOWN",
                                            active_color=None, jobs={})
        live_app = self.app.copy()
        live_app["id"] = "/live/vertical/name"
        self.assertDictEqual(expected, update.get_task_info(live_app, self.marathon))

    def test_get_task_info_no_status_page(self, *_):
        expected = testdata_helper.get_task(status=1, app_status=1, severity=1,
                                            status_url='',
                                            status_page_status_code=None,
                                            version="UNKNOWN",
                                            active_color=None, jobs={})
        app = self.app.copy()
        app.pop("env")
        self.assertDictEqual(expected, update.get_task_info(app, self.marathon))

    def test_get_task_info_suspended(self, _):
        expected = testdata_helper.get_task(status=1, app_status=1, severity=1,
                                            status_page_status_code=None,
                                            version="UNKNOWN",
                                            active_color=None, jobs={},
                                            instances=0)
        app = self.app.copy()
        app["instances"] = 0
        self.assertDictEqual(expected, update.get_task_info(app, self.marathon))

    def test_get_application_status_200(self, request_mock):
        status = testdata_helper.get_status()
        request_mock.register_uri('GET', "http://some-status-url/status", text=json.dumps(status),
                                  headers={'x-color': 'GRN'})

        app_status, active_color, status_code = update.get_application_status("http://some-status-url/status", {})
        self.assertEquals(status, app_status)
        self.assertEquals("GRN", active_color)
        self.assertEquals(200, status_code)

    def test_get_application_status_with_cookies(self, request_mock):
        request_mock.register_uri('GET', "http://some-status-url/status", status_code=200)

        app_status, active_color, status_code = update.get_application_status("http://some-status-url/status",
                                                                              {'cookies': {"cake": "strawberry"}})
        self.assertEquals({}, app_status)
        self.assertEquals(None, active_color)
        self.assertEquals(200, status_code)
        cookies = request_mock.request_history[0]._request._cookies._cookies['']['/']
        self.assertEquals(1, len(cookies))
        self.assertEquals({"cake": "strawberry"}, {cookies['cake'].name: cookies['cake'].value})

    def test_get_application_status_with_headers(self, request_mock):
        request_mock.register_uri('GET', "http://some-status-url/status", status_code=200)

        app_status, active_color, status_code = update.get_application_status("http://some-status-url/status",
                                                                              {'headers': {"Accept": "strawberry"}})
        self.assertEquals({}, app_status)
        self.assertEquals(None, active_color)
        self.assertEquals(200, status_code)
        self.assertEquals("strawberry", request_mock.request_history[0]._request.headers['Accept'])

    def test_get_application_status_400(self, request_mock):
        request_mock.register_uri('GET', "http://some-status-url/status", status_code=400)

        app_status, active_color, status_code = update.get_application_status("http://some-status-url/status", {})
        self.assertEquals({}, app_status)
        self.assertEquals(None, active_color)
        self.assertEquals(400, status_code)

    def test_get_application_status_not_available(self, request_mock):
        tmp = requests.get
        requests.get = MagicMock(side_effect=requests.exceptions.Timeout)

        app_status, active_color, status_code = update.get_application_status("http://some-status-url/status", {})
        self.assertEquals({}, app_status)
        self.assertEquals(0, len(request_mock.request_history))
        self.assertEquals(None, active_color)
        self.assertEquals(None, status_code)
        requests.get = tmp

    def test_overall_status(self, _):
        self.assertEquals(0, update.overall_status(testdata_helper.get_task()))
        self.assertEquals(3, update.overall_status(testdata_helper.get_task(instances=1, healthy=0)))
        self.assertEquals(3, update.overall_status(testdata_helper.get_task(app_status=3)))

        task = testdata_helper.get_task()
        task["app_status"] = None
        self.assertEquals(1, update.overall_status(task))

    @mock.patch('app.update.get_apps',
                return_value=[{'id': '/develop/mesos/some-marathon-healthcheck'}, {'id': '/develop/dog/cat'},
                              {'id': '/develop/banana/pyjama'}])
    @mock.patch('app.update.get_task_info',
                return_value={'info': 'data'})
    def test_update_marathon(self, *_):
        # set previous
        config.rdb.set('1234', ','.join(['/develop/dog/cat', '/develop/car/plane']))
        config.rdb.set('/develop/car/plane', 'delete me')
        config.rdb.sadd('all-services', '/develop/dog/cat', '/develop/car/plane')

        update.update_marathon(thread_id='1234', cfg=self.marathon, interval=1, greedy=True)

        self.assertEqual('/develop/dog/cat,/develop/banana/pyjama', config.rdb.get('1234').decode())
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/develop/dog/cat').decode()))
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/develop/banana/pyjama').decode()))
        self.assertEqual(None, config.rdb.get('/develop/car/plane'))
        self.assertEqual({b'/develop/dog/cat', b'/develop/banana/pyjama'}, config.rdb.smembers('all-services'))

    @mock.patch('app.update.get_apps',
                return_value=[{'id': '/develop/mesos/some-marathon-healthcheck'},
                              {'id': '/develop/dog/cat'},
                              {'id': '/develop/banana/pyjama'}])
    @mock.patch('app.update.get_task_info',
                return_value={'info': 'data'})
    def test_update_marathon_no_previous_tasks(self, *_):
        # no previous
        config.rdb.set('/develop/car/plane', 'delete me')
        config.rdb.sadd('all-services', '/develop/dog/cat', '/develop/car/plane')

        update.update_marathon(thread_id='1234', cfg=self.marathon, interval=1, greedy=True)

        self.assertEqual('/develop/dog/cat,/develop/banana/pyjama', config.rdb.get('1234').decode())
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/develop/dog/cat').decode()))
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/develop/banana/pyjama').decode()))
        self.assertEqual(b'delete me', config.rdb.get('/develop/car/plane'))
        self.assertEqual({b'/develop/car/plane', b'/develop/dog/cat', b'/develop/banana/pyjama'},
                         config.rdb.smembers('all-services'))

    @mock.patch('app.update.get_service_info', return_value={'info': 'data'})
    def test_update_service(self, *_):
        service_list = [{'url': 'Some url with dog-ci', 'id': '/dog-ci/vertical/service'},
                        {'url': 'Some url with cat', 'id': '/cat/vertical/service'}]

        update.update_service('1234', service_list, 0, greedy=True)
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/dog-ci/vertical/service').decode()))
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/cat/vertical/service').decode()))
        self.assertEqual({b'/dog-ci/vertical/service', b'/cat/vertical/service'}, config.rdb.smembers('all-services'))

    @mock.patch('app.update.get_application_status', return_value=[testdata_helper.get_status(), "GRN", 200])
    def test_get_service_info(self, *_):
        expected = testdata_helper.get_task(marathon=None, status_url="http://some-domain.com/service/internal/status")
        del expected["marathon"]
        self.assertDictEqual(expected, update.get_service_info(self.app_server_service))

    def test_calculate_severity(self, _):
        self.assertEquals(1, update.calculate_severity({'status': 1, 'group': 'develop'}))
        self.assertEquals(30, update.calculate_severity({'status': 3, 'group': 'develop'}))
        self.assertEquals(100, update.calculate_severity({'status': 1, 'group': 'live'}))
        self.assertEquals(3000, update.calculate_severity({'status': 3, 'group': 'live'}))
