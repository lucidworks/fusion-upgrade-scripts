#!/usr/bin/env python

import copy
from src.utils.constants import *

class SharepointMigrator:

    def migrate(self, data_source):
        salesforce_properties = data_source[PROPERTIES]

        copy_props = copy.deepcopy(salesforce_properties)
        for property in copy_props:
            if property.startswith("f.fs"):
                prop_value = salesforce_properties[property]
                del salesforce_properties[property]
                new_property = property.replace("f.fs", "f")
                salesforce_properties[new_property] = prop_value

        data_source[PROPERTIES] = salesforce_properties

        return data_source

