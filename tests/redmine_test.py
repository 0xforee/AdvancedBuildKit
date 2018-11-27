#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

# Copyright © 18-5-29 foree <foree@foree-pc>

# Distributed under terms of the MIT license.

# ===========================================

import unittest

from common.jenkins import JenkinsCacheHelper
from common import redmine


class DefaultTestCase(unittest.TestCase):
    def test(self):
        jenkins = JenkinsCacheHelper()
        self.assertTrue(isinstance(jenkins.load_jenkins_cache(), dict))

