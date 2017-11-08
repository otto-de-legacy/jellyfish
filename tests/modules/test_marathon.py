# -*- coding: utf-8 -*-
import json
import unittest
from unittest import mock

import redislite
import requests
import requests_mock
from mock import MagicMock

from app.modules import marathon
from app import config
from tests.helper import testdata_helper


@requests_mock.Mocker()
class TestMarathon(unittest.TestCase):
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
        self.assertEquals(self.marathon_apps["apps"], marathon.get_apps(self.marathon))
        self.assertCountEqual(json.dumps(self.marathon_apps['apps']),
                              config.rdb.get(self.marathon['host'] + '-cache').decode())
        self.assertEquals(None, config.rdb.get(self.marathon['host'] + '-errors'))

    def test_get_apps_401(self, mock):
        mock.register_uri('GET', "http://username:password@some-marathon.com/v2/apps", text="some html",
                          status_code=401)
        self.assertEquals([], marathon.get_apps(self.marathon))
        self.assertEqual(None, config.rdb.get(self.marathon['host'] + '-cache'))
        self.assertEquals(b'could not read marathon: some-marathon.com [ JSONDecodeError ]',
                          config.rdb.get(self.marathon['host'] + '-errors'))

    def test_get_apps_not_available(self, mock):
        tmp = requests.get
        requests.get = MagicMock(side_effect=requests.exceptions.Timeout)
        self.assertEquals([], marathon.get_apps(self.marathon))
        self.assertEqual(0, len(mock.request_history))
        self.assertEqual(None, config.rdb.get('some-marathon.com-cache'))
        self.assertEqual(None, config.rdb.get(self.marathon['host'] + '-cache'))
        requests.get = tmp

    def test_get_apps_use_cache(self, mock):
        mock.register_uri('GET', "http://username:password@some-marathon.com/v2/apps", text=self.marathon_apps_json)
        self.assertEquals(self.marathon_apps["apps"], marathon.get_apps(self.marathon))
        self.assertCountEqual(json.dumps(self.marathon_apps['apps']),
                              config.rdb.get(self.marathon['host'] + '-cache').decode())
        self.assertEquals(None, config.rdb.get(self.marathon['host'] + '-errors'))

        mock.register_uri('GET', "http://username:password@some-marathon.com/v2/apps", text="some html",
                          status_code=401)
        self.assertEquals(self.marathon_apps["apps"], marathon.get_apps(self.marathon))
        self.assertCountEqual(json.dumps(self.marathon_apps['apps']),
                              config.rdb.get(self.marathon['host'] + '-cache').decode())
        self.assertEquals(b'could not read marathon: some-marathon.com [ JSONDecodeError ]',
                          config.rdb.get(self.marathon['host'] + '-errors'))

        mock.register_uri('GET', "http://username:password@some-marathon.com/v2/apps", text=self.marathon_apps_json)
        self.assertEquals(self.marathon_apps["apps"], marathon.get_apps(self.marathon))
        self.assertCountEqual(json.dumps(self.marathon_apps['apps']),
                              config.rdb.get(self.marathon['host'] + '-cache').decode())
        self.assertEquals(None, config.rdb.get(self.marathon['host'] + '-errors'))

    def test_get_status_url(self, _):
        self.assertEquals("http://name.vertical.group.domain.de/status_path",
                          marathon.get_status_url("name", "group", "vertical", "", "domain.de", "/status_path", None,
                                                  {}))
        self.assertEquals("http://vertical.group.domain.de/status_path",
                          marathon.get_status_url("vertical", "group", "vertical", "", "domain.de", "/status_path",
                                                  True,
                                                  {}))
        self.assertEquals("http://vertical.group.domain.de/status_path",
                          marathon.get_status_url("name", "group", "vertical", "", "domain.de", "/status_path", True,
                                                  {}))
        self.assertEquals("http://name.subgroup.vertical.group.domain.de/status_path",
                          marathon.get_status_url("name", "group", "vertical", "subgroup", "domain.de", "/status_path",
                                                  None, {}))
        self.assertEquals("http://vertical.group.domain.de/status_path",
                          marathon.get_status_url("name", "group", "vertical", "subgroup", "domain.de", "/status_path",
                                                  True, {}))
        self.assertEquals("http://vertical.group.domain.de/status_path",
                          marathon.get_status_url("name", "group", "vertical", "subgroup", "domain.de", "/status_path",
                                                  True,
                                                  {"status_path": {"dog": "wololololololo"}}))
        self.assertEquals("http://group.alternate_status_path/status_path",
                          marathon.get_status_url("name", "group", "vertical", "subgroup", "domain.de", "/status_path",
                                                  True,
                                                  {"status_path": {
                                                      "name": "http://{environment}.alternate_status_path/status_path"}}))

    def test_get_task_info_with_out_color(self, request_mock, *_):
        status = testdata_helper.get_status()
        request_mock.register_uri('GET', "http://name.vertical.group.some-domain.com/service/internal/status",
                                  text=json.dumps(status),
                                  headers={'x-color': 'GRN'})
        expected = testdata_helper.get_task()
        self.assertDictEqual(expected, marathon.get_task_info(self.app, self.marathon))
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

        self.assertDictEqual(expected_inactive, marathon.get_task_info(app_inactive, self.marathon))
        self.assertDictEqual(expected_active, marathon.get_task_info(app_active, self.marathon))
        self.assertEquals(3, len(request_mock.request_history))
        self.assertEquals("http://name.vertical.group.some-domain.com/service/internal/status",
                          request_mock.request_history[0].url)
        self.assertEquals("http://staged.name.vertical.group.some-domain.com/service/internal/status",
                          request_mock.request_history[1].url)
        self.assertEquals("http://name.vertical.group.some-domain.com/service/internal/status",
                          request_mock.request_history[2].url)

    @mock.patch('app.modules.util.get_application_status', return_value=[testdata_helper.get_status(), "GRN", 200])
    def test_get_task_info(self, *_):
        expected = testdata_helper.get_task()
        self.assertDictEqual(expected, marathon.get_task_info(self.app, self.marathon))

    @mock.patch('app.modules.util.get_application_status', return_value=[testdata_helper.get_status(), "GRN", 200])
    def test_get_task_info_job_does_not_change(self, *_):
        expected = testdata_helper.get_task()
        self.assertDictEqual(expected, marathon.get_task_info(self.app, self.marathon))

    @mock.patch('app.modules.util.get_application_status', return_value=[{}, None, 404])
    def test_get_task_info_status_page_not_available(self, *_):
        expected = testdata_helper.get_task(status=1, app_status=1, severity=1,
                                            status_page_status_code=404,
                                            version="UNKNOWN",
                                            active_color=None, jobs={})
        self.assertDictEqual(expected, marathon.get_task_info(self.app, self.marathon))

    @mock.patch('app.modules.util.get_application_status', return_value=[{}, None, 503])
    def test_get_task_info_status_page_503(self, *_):
        expected = testdata_helper.get_task(status=3, app_status=1, severity=30,
                                            status_page_status_code=503,
                                            version="UNKNOWN",
                                            active_color=None, jobs={})

        self.assertDictEqual(expected, marathon.get_task_info(self.app, self.marathon))

    @mock.patch('app.modules.util.get_application_status', return_value=[{}, None, 503])
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
        self.assertDictEqual(expected, marathon.get_task_info(live_app, self.marathon))

    def test_get_task_info_no_status_page(self, *_):
        expected = testdata_helper.get_task(status=1, app_status=1, severity=1,
                                            status_url='',
                                            status_page_status_code=None,
                                            version="UNKNOWN",
                                            active_color=None, jobs={})
        app = self.app.copy()
        app.pop("env")
        self.assertDictEqual(expected, marathon.get_task_info(app, self.marathon))

    def test_get_task_info_suspended(self, _):
        expected = testdata_helper.get_task(status=1, app_status=1, severity=1,
                                            status_page_status_code=None,
                                            version="UNKNOWN",
                                            active_color=None, jobs={},
                                            instances=0)
        app = self.app.copy()
        app["instances"] = 0
        self.assertDictEqual(expected, marathon.get_task_info(app, self.marathon))

    def test_overall_status(self, _):
        self.assertEquals(0, marathon.overall_status(testdata_helper.get_task()))
        self.assertEquals(3, marathon.overall_status(testdata_helper.get_task(instances=1, healthy=0)))
        self.assertEquals(3, marathon.overall_status(testdata_helper.get_task(app_status=3)))

        task = testdata_helper.get_task()
        task["app_status"] = None
        self.assertEquals(1, marathon.overall_status(task))

    @mock.patch('app.modules.marathon.get_apps',
                return_value=[{'id': '/develop/mesos/some-marathon-healthcheck'}, {'id': '/develop/dog/cat'},
                              {'id': '/develop/banana/pyjama'}])
    @mock.patch('app.modules.marathon.get_task_info',
                return_value={'info': 'data'})
    def test_update_marathon(self, *_):
        # set previous
        config.rdb.set('1234', ','.join(['/develop/dog/cat', '/develop/car/plane']))
        config.rdb.set('/develop/car/plane', 'delete me')
        config.rdb.sadd('all-services', '/develop/dog/cat', '/develop/car/plane')

        marathon.update_marathon(thread_id='1234', cfg=self.marathon, interval=1, greedy=True)

        self.assertEqual('/develop/dog/cat,/develop/banana/pyjama', config.rdb.get('1234').decode())
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/develop/dog/cat').decode()))
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/develop/banana/pyjama').decode()))
        self.assertEqual(None, config.rdb.get('/develop/car/plane'))
        self.assertEqual({b'/develop/dog/cat', b'/develop/banana/pyjama'}, config.rdb.smembers('all-services'))

    @mock.patch('app.modules.marathon.get_apps',
                return_value=[{'id': '/develop/mesos/some-marathon-healthcheck'},
                              {'id': '/develop/dog/cat'},
                              {'id': '/develop/banana/pyjama'}])
    @mock.patch('app.modules.marathon.get_task_info',
                return_value={'info': 'data'})
    def test_update_marathon_no_previous_tasks(self, *_):
        # no previous
        config.rdb.set('/develop/car/plane', 'delete me')
        config.rdb.sadd('all-services', '/develop/dog/cat', '/develop/car/plane')

        marathon.update_marathon(thread_id='1234', cfg=self.marathon, interval=1, greedy=True)

        self.assertEqual('/develop/dog/cat,/develop/banana/pyjama', config.rdb.get('1234').decode())
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/develop/dog/cat').decode()))
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/develop/banana/pyjama').decode()))
        self.assertEqual(b'delete me', config.rdb.get('/develop/car/plane'))
        self.assertEqual({b'/develop/car/plane', b'/develop/dog/cat', b'/develop/banana/pyjama'},
                         config.rdb.smembers('all-services'))
