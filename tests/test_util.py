# -*- coding: utf-8 -*-
import unittest

from app import util


class TestUtil(unittest.TestCase):
    def test_get_in_dict(self):
        d = {"a": {"b": "value"}}
        self.assertEquals(d["a"], util.get_in_dict(["a"], d))
        self.assertEquals("value", util.get_in_dict(["a", "b"], d, "default"))
        self.assertEquals("default", util.get_in_dict(["c"], d, "default"))
        self.assertEquals(None, util.get_in_dict(["a", "b", "c"], d))
        self.assertEquals("default", util.get_in_dict(["a", "b", "c"], d, "default"))
        self.assertEquals(None, util.get_in_dict(["c"], d))
        self.assertEquals(None, util.get_in_dict(["c"], None))
        self.assertEquals("default", util.get_in_dict(["c"], None, "default"))
        self.assertEquals(None, util.get_in_dict(["c"], {}))
        self.assertEquals("default", util.get_in_dict(["c"], {}, "default"))
        self.assertEquals(None, util.get_in_dict(["c", None], d))
        self.assertEquals("default", util.get_in_dict(["c", None], d, "default"))
