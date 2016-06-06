#!/usr/bin/env python

import os
import json
import re
import logging

class ResourceManager:
  def __init__(self):
    pass

  @staticmethod
  def get_resource(filename):
    source_dir = os.path.dirname(__file__)
    path = os.path.join(source_dir, "../resources/{}".
                        format(filename))
    with open(path) as data_file:
      return json.load(data_file)