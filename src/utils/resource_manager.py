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
    source_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(source_dir, "../resources/{}".
                        format(filename))
    logging.info("Loading file from path {}".format(path))
    with open(path) as data_file:
      return json.load(data_file)
