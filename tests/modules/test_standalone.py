# -*- coding: utf-8 -*-
import json
import unittest
from unittest import mock

import redislite
import requests_mock
from app.modules import standalone
from app.modules import util
from app import config
from tests.helper import testdata_helper


@requests_mock.Mocker()
class TestStandalone(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        config.rdb = redislite.Redis('redis.db')
        cls.app_server_service = {"id": "/group/vertical/name",
                                  "url": "http://some-domain.com/service/internal/status"}

    def setUp(self):
        config.rdb.flushall()
        config.rdb.flushdb()

    @mock.patch('app.modules.standalone.get_service_info', return_value={'info': 'data'})
    def test_update_service(self, *_):
        service_list = [{'url': 'Some url with dog-ci', 'id': '/dog-ci/vertical/service'},
                        {'url': 'Some url with cat', 'id': '/cat/vertical/service'}]

        standalone.update_standalone('1234', service_list, 0, greedy=True)
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('standalone::/dog-ci/vertical/service').decode()))
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('standalone::/cat/vertical/service').decode()))
        self.assertEqual({b'standalone::/dog-ci/vertical/service', b'standalone::/cat/vertical/service'}, config.rdb.smembers('all-services'))

    @mock.patch('app.modules.util.get_application_status', return_value=[testdata_helper.get_status(), "GRN", 200])
    def test_get_service_info(self, *_):
        expected = testdata_helper.get_task(marathon=None, source="standalone", status_url="http://some-domain.com/service/internal/status")
        del expected["marathon"]
        self.assertDictEqual(expected, standalone.get_service_info(self.app_server_service))

    def test_calculate_severity(self, _):
        self.assertEquals(1, util.calculate_severity({'status': 1, 'group': 'develop'}))
        self.assertEquals(30, util.calculate_severity({'status': 3, 'group': 'develop'}))
        self.assertEquals(100, util.calculate_severity({'status': 1, 'group': 'live'}))
        self.assertEquals(3000, util.calculate_severity({'status': 3, 'group': 'live'}))
