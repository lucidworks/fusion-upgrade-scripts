#!/usr/bin/env python

from src.utils.constants import *
from src.migrator.base_migrator import BaseMigrator

import logging

class SimpleSecurityTrimmingMigrator(BaseMigrator):

  def migrate(self, data_source):
    security_trimming = data_source[PROPERTIES].get(ENABLE_SECURITY_TRIMMING)

    if security_trimming is None or isinstance(security_trimming, dict):
      return data_source

    if isinstance(security_trimming, bool) and not security_trimming:
      del data_source[PROPERTIES][ENABLE_SECURITY_TRIMMING]
      return data_source

    data_source[PROPERTIES][ENABLE_SECURITY_TRIMMING] = {}

    return data_source