import json
import unittest

import redislite
from dotmap import DotMap

from app import config
from app import views
from tests.helper import testdata_helper

unittest.util._MAX_LENGTH = 1000


class TestView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config.rdb = redislite.Redis('redis.db')
        cls.test_apps = [testdata_helper.get_task(name='dog', vertical='mammal'),
                         testdata_helper.get_task(name='cat', vertical='mammal'),
                         testdata_helper.get_task(name='salmon', vertical='fish')]
        cls.maxDiff = None

    def setUp(self):
        config.rdb.flushall()
        config.rdb.flushdb()

    def test_get_state(self):
        config.rdb.flushall()
        config.rdb.set('/mammal/cat', json.dumps({'info': 'mammal'}))
        config.rdb.set('/fish/salmon', json.dumps({'info': 'fish'}))
        config.rdb.sadd('all-services', '/mammal/cat', '/fish/salmon')

        self.assertCountEqual([DotMap(info='mammal'), DotMap(info='fish')], views.get_all_apps())

    def test_get_state_with_non_existent_app(self):
        config.rdb.set('/mammal/cat', json.dumps({'info': 'mammal'}))
        config.rdb.set('/fish/salmon', json.dumps({'info': 'fish'}))
        config.rdb.sadd('all-services', '/mammal/cat', '/fish/salmon', 'banana/pyjama')

        self.assertCountEqual([DotMap(info='mammal'), DotMap(info='fish')], views.get_all_apps())

    def test_filter(self):
        self.assertEqual(True, views.filter(name="dog", include=[], exclude=[]))
        self.assertEqual(True, views.filter(name="dog", include=["dog", "cat"], exclude=[]))
        self.assertEqual(False, views.filter(name="dog", include=["cat"], exclude=[]))
        self.assertEqual(False, views.filter(name="dog", include=["cat"], exclude=["dog"]))
        self.assertEqual(False, views.filter(name="dog", include=[], exclude=["dog"]))
        # include always wins
        self.assertEqual(True, views.filter(name="dog", include=["dog"], exclude=["dog"]))

    def test_filter_state(self):
        self.assertEqual(self.test_apps,
                         views.filter_state(app_list=self.test_apps, name_filter=None, group_filter=None,
                                            type_filter=None,
                                            active_color_only_filter=False,
                                            status_filter=0, include_jobs=True, include_age=False))

    def test_filter_state_name_filter(self):
        expected = [testdata_helper.get_task(name='dog', vertical='mammal')]
        self.assertEqual(expected, views.filter_state(app_list=self.test_apps, name_filter=['dog'], group_filter=None,
                                                      type_filter=None,
                                                      active_color_only_filter=False,
                                                      status_filter=0, include_jobs=True, include_age=False))

    def test_filter_state_not_name_filter(self):
        expected = [testdata_helper.get_task(name='dog', vertical='mammal'),
                    testdata_helper.get_task(name='salmon', vertical='fish')]
        self.assertEqual(expected,
                         views.filter_state(app_list=self.test_apps, name_filter=['!cat'], group_filter=None,
                                            type_filter=None,
                                            active_color_only_filter=False,
                                            status_filter=0, include_jobs=True, include_age=False))

    def test_filter_state_group_filter(self):
        expected = [testdata_helper.get_task(name='dog', vertical='mammal'),
                    testdata_helper.get_task(name='cat', vertical='mammal')]
        self.assertEqual(expected,
                         views.filter_state(app_list=self.test_apps, name_filter=None, group_filter=['mammal'],
                                            type_filter=None,
                                            active_color_only_filter=False,
                                            status_filter=0, include_jobs=True, include_age=False))

    def test_filter_state_labels_filter(self):
        test_apps = [testdata_helper.get_task(name='dog', vertical='mammal', type="pipeline"),
                     testdata_helper.get_task(name='cat', vertical='mammal', type="tool")]
        expected = [testdata_helper.get_task(name='dog', vertical='mammal', type="pipeline")]
        self.assertEqual(expected, views.filter_state(app_list=test_apps, name_filter=None, group_filter=None,
                                                      type_filter=['pipeline'],
                                                      active_color_only_filter=False,
                                                      status_filter=0, include_jobs=True, include_age=False))

    def test_filter_state_group_and_name_filter(self):
        expected = [testdata_helper.get_task(name='dog', vertical='mammal')]
        self.assertEqual(expected,
                         views.filter_state(app_list=self.test_apps, name_filter=['!cat'], group_filter=['mammal'],
                                            type_filter=None,
                                            active_color_only_filter=False,
                                            status_filter=0, include_jobs=True, include_age=False))

    def test_filter_state_level_filter(self):
        test_apps = [testdata_helper.get_task(status=1, name='dog', vertical='mammal'),
                     testdata_helper.get_task(status=2, name='cat', vertical='mammal'),
                     testdata_helper.get_task(status=3, name='salmon', vertical='fish')]
        expected = [test_apps[1],
                    test_apps[2]]
        self.assertEqual(expected,
                         views.filter_state(app_list=test_apps, name_filter=None, group_filter=None, type_filter=None,
                                            active_color_only_filter=False,
                                            status_filter=2, include_jobs=True, include_age=False))

    def test_filter_state_no_jobs(self):
        test_apps = [testdata_helper.get_task(name='dog', vertical='mammal'),
                     testdata_helper.get_task(name='cat', vertical='mammal')]

        app1 = testdata_helper.get_task(name='dog', vertical='mammal')
        app1["jobs"] = dict()
        app2 = testdata_helper.get_task(name='cat', vertical='mammal')
        app2["jobs"] = dict()

        expected = [app1,
                    app2]
        self.assertCountEqual(expected, views.filter_state(app_list=test_apps, name_filter=None, group_filter=None,
                                                           type_filter=None,
                                                           active_color_only_filter=False,
                                                           status_filter=0, include_jobs=False, include_age=False))

    def test_filter_state_active_color(self):
        test_apps = [testdata_helper.get_task(name='dog', vertical='mammal', color="GRN", active_color="BLU"),
                     testdata_helper.get_task(name='cat', vertical='mammal', color="BLU", active_color="BLU")]
        expected = [testdata_helper.get_task(name='cat', vertical='mammal', color="BLU", active_color="BLU")]
        self.assertCountEqual(expected, views.filter_state(app_list=test_apps, name_filter=None, group_filter=None,
                                                           type_filter=None,
                                                           active_color_only_filter=True,
                                                           status_filter=0, include_jobs=True, include_age=False))

    def test_transform_to_display_data(self):
        test_apps = [testdata_helper.get_task(status=1, name='dog', vertical='mammal'),
                     testdata_helper.get_task(status=3, name='salmon', vertical='fish')]
        expected = {
            'all': {'mammal-dog': {'group': {'GRN': testdata_helper.get_task(status=1, name='dog', vertical='mammal')}},
                    'fish-salmon': {
                        'group': {'GRN': testdata_helper.get_task(status=3, name='salmon', vertical='fish')}}},
            'mammal': {'dog': {'group': {'GRN': testdata_helper.get_task(status=1, name='dog', vertical='mammal')}}},
            'fish': {'salmon': {'group': {'GRN': testdata_helper.get_task(status=3, name='salmon', vertical='fish')}}}}
        self.assertDictEqual(expected, views.transform_to_display_data(test_apps))

    def test_get_tabs(self):
        test_apps = [testdata_helper.get_task(status=1, name='dog', vertical='mammal'),
                     testdata_helper.get_task(status=2, name='cat', vertical='mammal'),
                     testdata_helper.get_task(status=3, name='salmon', vertical='fish')]
        self.assertCountEqual(["all", "mammal", "fish"], views.get_tabs(test_apps))

    def test_get_resource_allocation(self):
        test_apps = [
            testdata_helper.get_task(status=1, name='dog', vertical='mammal', instances=2, max_cpu=0.5, max_mem=100),
            testdata_helper.get_task(status=2, name='cat', vertical='mammal', max_cpu=5, max_mem=110),
            testdata_helper.get_task(status=3, name='salmon', vertical='fish', instances=2, healthy=1, max_cpu=2,
                                     max_mem=120)]

        expected_vertical = {'all': {'cpu': 5, 'mem': 5120, 'max_cpu': 7.5, 'max_mem': 330},
                             'mammal': {'cpu': 3, 'mem': 3072, 'max_cpu': 5.5, 'max_mem': 210},
                             'fish': {'cpu': 2, 'mem': 2048, 'max_cpu': 2, 'max_mem': 120}}
        expected_apps = {'all': {'mammal-dog': {'cpu': 2,
                                                'max_cpu': 0.5,
                                                'max_mem': 100,
                                                'mem': 2048,
                                                'percentage_cpu': 25.0,
                                                'percentage_mem': 4.8828125},
                                 'mammal-cat': {'cpu': 1,
                                                'max_cpu': 5,
                                                'max_mem': 110,
                                                'mem': 1024,
                                                'percentage_cpu': 500.0,
                                                'percentage_mem': 10.7421875},
                                 'fish-salmon': {'cpu': 2,
                                                 'max_cpu': 2,
                                                 'max_mem': 120,
                                                 'mem': 2048,
                                                 'percentage_cpu': 100.0,
                                                 'percentage_mem': 5.859375}},
                         'mammal': {'dog': {'cpu': 2,
                                            'max_cpu': 0.5,
                                            'max_mem': 100,
                                            'mem': 2048,
                                            'percentage_cpu': 25.0,
                                            'percentage_mem': 4.8828125},
                                    'cat': {'cpu': 1,
                                            'max_cpu': 5,
                                            'max_mem': 110,
                                            'mem': 1024,
                                            'percentage_cpu': 500.0,
                                            'percentage_mem': 10.7421875}},
                         'fish': {'salmon': {'cpu': 2,
                                             'max_cpu': 2,
                                             'max_mem': 120,
                                             'mem': 2048,
                                             'percentage_cpu': 100.0,
                                             'percentage_mem': 5.859375}}}

        vertical, apps = views.get_app_resource_allocation(test_apps)
        self.assertDictEqual(expected_vertical, vertical)
        self.assertDictEqual(expected_apps, apps)

    def test_get_resource_allocation_with_non_marathon_services(self):
        test_apps = [testdata_helper.get_task(status=1, name='dog', vertical='mammal'),
                     testdata_helper.get_task(status=2, name='cat', vertical='mammal'),
                     testdata_helper.get_task(status=3, name='salmon', vertical='fish')]
        del test_apps[1]['marathon']

        expected_vertical = {'all': {'cpu': 2, 'mem': 2048, 'max_cpu': 2.0, 'max_mem': 2048.0},
                             'mammal': {'cpu': 1, 'mem': 1024, 'max_cpu': 1.0, 'max_mem': 1024.0},
                             'fish': {'cpu': 1, 'mem': 1024, 'max_cpu': 1.0, 'max_mem': 1024.0}}
        expected_apps = {'all': {'mammal-cat': {'cpu': 0, 'max_cpu': 0, 'max_mem': 0, 'mem': 0},
                                 'mammal-dog': {'cpu': 1,
                                                'max_cpu': 1,
                                                'max_mem': 1024,
                                                'mem': 1024,
                                                'percentage_cpu': 100.0,
                                                'percentage_mem': 100.0},
                                 'fish-salmon': {'cpu': 1,
                                                 'max_cpu': 1,
                                                 'max_mem': 1024,
                                                 'mem': 1024,
                                                 'percentage_cpu': 100.0,
                                                 'percentage_mem': 100.0}},
                         'fish': {'salmon': {'cpu': 1,
                                             'max_cpu': 1,
                                             'max_mem': 1024,
                                             'mem': 1024,
                                             'percentage_cpu': 100.0,
                                             'percentage_mem': 100.0}},
                         'mammal': {'cat': {'cpu': 0, 'max_cpu': 0, 'max_mem': 0, 'mem': 0},
                                    'dog': {'cpu': 1,
                                            'max_cpu': 1,
                                            'max_mem': 1024,
                                            'mem': 1024,
                                            'percentage_cpu': 100.0,
                                            'percentage_mem': 100.0}}}

        vertical, apps = views.get_app_resource_allocation(test_apps)
        self.assertDictEqual(expected_vertical, vertical)
        self.assertDictEqual(expected_apps, apps)

    def test_get_error_messages(self):
        expected = {'all': {'error dog', 'error cat', 'error salmon'},
                    'mammal': {'error dog', 'error cat'},
                    'fish': {'error salmon'}}

        test_apps = [
            testdata_helper.get_task(status=1, name='dog', vertical='mammal', origin="dog"),
            testdata_helper.get_task(status=2, name='cat', vertical='mammal', origin="cat"),
            testdata_helper.get_task(status=3, name='salmon', vertical='fish', origin="salmon")]

        config.rdb.set("dog-errors", "error dog")
        config.rdb.set("cat-errors", "error cat")
        config.rdb.set("salmon-errors", "error salmon")

        self.assertEqual(expected, views.get_error_messages(test_apps))

    def test_filter_environments(self):
        envs = [{'name': 'dev-ci', 'alias': 'ci'}, {'name': 'PRODUCTIVE', 'alias': 'prod'},
                {'name': 'dog', 'alias': 'cat'}, {'name': 'BANANA', 'alias': 'pyjama'}]
        expected = [{'name': 'dev-ci', 'alias': 'ci'}, {'name': 'PRODUCTIVE', 'alias': 'prod'}]
        self.assertEqual(expected, views.filter_environments(envs, ['ci', 'prod']))
        self.assertEqual(envs, views.filter_environments(envs, False))

    def test_filter_environments_not_filter(self):
        envs = [{'name': 'dev-ci', 'alias': 'ci'}, {'name': 'PRODUCTIVE', 'alias': 'prod'},
                {'name': 'dog', 'alias': 'cat'}, {'name': 'BANANA', 'alias': 'pyjama'}]
        expected = [{'name': 'PRODUCTIVE', 'alias': 'prod'},
                    {'name': 'dog', 'alias': 'cat'}, {'name': 'BANANA', 'alias': 'pyjama'}]
        self.assertEqual(expected, views.filter_environments(envs, ['!ci']))
        self.assertEqual(envs, views.filter_environments(envs, False))