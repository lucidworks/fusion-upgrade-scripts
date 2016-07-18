#!/usr/bin/env python

from src.utils.constants import *

class SimpleSecurityTrimmingMigrator():

    def migrate(self, data_source):
        security_trimming = data_source[PROPERTIES].pop(ENABLE_SECURITY_TRIMMING, False)

        if isinstance(security_trimming, bool) and not security_trimming:
            return data_source

        data_source[PROPERTIES][ENABLE_SECURITY_TRIMMING] = {}

        return data_source
