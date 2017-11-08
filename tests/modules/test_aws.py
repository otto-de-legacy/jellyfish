# -*- coding: utf-8 -*-
import json
import unittest
from unittest import mock

import redislite
import requests_mock

from app.modules import aws
from app import config

unittest.util._MAX_LENGTH = 1000


class TestView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        config.rdb = redislite.Redis('redis.db')

    def setUp(self):
        config.rdb.flushall()
        config.rdb.flushdb()

    @mock.patch('app.modules.aws.get_beanstalk_environments',
                return_value={'mammal-dog': 'mammal-dog-develop',
                              'mammal-cat': 'mammal-cat-develop'})
    @mock.patch('app.modules.aws.get_beanstalk_health', return_value={'info': 'data'})
    def test_update_aws(self, *_):
        service = {'id': '/dog-ci/vertical', 'access_key': 'AAAA', 'secret_key': '1234'}

        aws.update_aws('1234', service, 0, greedy=True)
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/dog-ci/vertical/mammal-dog').decode()))
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/dog-ci/vertical/mammal-cat').decode()))
        self.assertEqual({b'/dog-ci/vertical/mammal-dog', b'/dog-ci/vertical/mammal-cat'},
                         config.rdb.smembers('all-services'))

    @mock.patch('app.modules.aws.get_beanstalk_health', return_value={'info': 'data'})
    def test_get_beanstalk_environments(self, *_):
        pass
