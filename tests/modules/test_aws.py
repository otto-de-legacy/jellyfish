# -*- coding: utf-8 -*-
import json
import unittest
from unittest import mock
from unittest.mock import MagicMock

import redislite
from app.modules import aws
from app import config
from tests.helper import testdata_helper


class TestAws(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        config.rdb = redislite.Redis('redis.db')

    def setUp(self):
        config.rdb.flushall()
        config.rdb.flushdb()

    @mock.patch('app.modules.aws.get_beanstalk_client', return_value={})
    @mock.patch('app.modules.aws.get_beanstalk_environments',
                return_value={'mammal-dog': 'mammal-dog-develop',
                              'mammal-cat': 'mammal-cat-develop'})
    @mock.patch('app.modules.aws.get_beanstalk_health', return_value={'info': 'data'})
    def test_update_aws(self, *_):
        service = {'id': '/dog-ci/vertical', 'access_key': 'AAAA', 'secret_key': '1234', 'region_name': 'some-region'}

        aws.update_aws('1234', service, 0, greedy=True)
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/dog-ci/vertical/mammal-dog').decode()))
        self.assertEqual({'info': 'data'}, json.loads(config.rdb.get('/dog-ci/vertical/mammal-cat').decode()))
        self.assertEqual({b'/dog-ci/vertical/mammal-dog', b'/dog-ci/vertical/mammal-cat'},
                         config.rdb.smembers('all-services'))

    def test_get_beanstalk_environments(self, *_):
        beanstalk_client = MagicMock()
        beanstalk_client.describe_environments = MagicMock(return_value=testdata_helper.describe_environments())
        self.assertEqual({'mammal-dog': 'mammal-dog-develop',
                          'mammal-cat': 'mammal-cat-develop'}, aws.get_beanstalk_environments(beanstalk_client))

    @mock.patch('app.modules.util.get_application_status', return_value=[{}, None, 200])
    def test_get_beanstalk_health(self, *_):
        beanstalk_client = MagicMock()
        service = {'id': '/dog-ci/vertical', 'domain_suffix': 'somewhere.com'}
        beanstalk_client.describe_environment_health = MagicMock(
            return_value=testdata_helper.describe_environment_health())

        expected = testdata_helper.get_task(status_url='https://name.group.vertical.somewhere.com/vertical-name/internal/status',
                                            version='UNKNOWN',
                                            app_status=1,
                                            status=3,
                                            jobs={},
                                            marathon={'cpu': 0,
                                                      'instances': 2,
                                                      'labels': {},
                                                      'marathon_link': '',
                                                      'mem': 0,
                                                      'origin': 'aws',
                                                      'running': 1,
                                                      'healthy': 1,
                                                      'staged': 0,
                                                      'unhealthy': 1},
                                            severity=30)
        self.assertEqual(expected, aws.get_beanstalk_health(service,
                                                            beanstalk_client,
                                                            '/group/vertical/name',
                                                            'vertical-name-develop'))
