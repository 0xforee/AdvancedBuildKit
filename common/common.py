#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 foree <foree@foree-pc>
#
# Distributed under terms of the MIT license.

"""
common function
"""
import os


def get_cur_path():
    return os.path.dirname(os.path.realpath(__file__))


def get_root_path():
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    soft_root_path = os.path.realpath(os.path.join(current_file_path, os.pardir))
    return soft_root_path
