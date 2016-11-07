# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock

import redislite
from app import config
from app import start

unittest.util._MAX_LENGTH = 1000


class TestView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        config.rdb = redislite.Redis('redis.db')

    def setUp(self):
        config.rdb.flushall()
        config.rdb.flushdb()

    def test_start_tasks(self):
        mock = Mock(return_value=None)
        start.start_thread_timer = mock

        config = {
            "environments": [
                {
                    "name": "dog-ci",
                    "alias": "dog"
                },
                {
                    "name": "cat",
                    "alias": "Perser"
                }
            ],
            "marathons": [
                {
                    "protocol": "http",
                    "host": "localhost:12345",
                    "apps": "/v2/apps",
                    "username": "username",
                    "password": "password"
                }
            ],
            "services": [
                {
                    "id": "/{environment}/vertical/service",
                    "url": "Some url with {environment}"
                }
            ]
        }

        start.start_tasks(config, True)
        self.assertEqual(2, len(mock.call_args_list))
        self.assertEqual({'apps': '/v2/apps', 'password': 'password', 'host': 'localhost:12345', 'username': 'username', 'protocol': 'http'}, mock.call_args_list[0][0][2])
        self.assertEqual([{'url': 'Some url with dog-ci', 'id': '/dog-ci/vertical/service'}, {'url': 'Some url with cat', 'id': '/cat/vertical/service'}], mock.call_args_list[1][0][2])
