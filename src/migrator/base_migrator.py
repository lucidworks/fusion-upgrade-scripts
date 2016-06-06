from src.utils.constants import *

import logging

class BaseMigrator:

  def delete_properties(self, data_source, properties):
    for property in properties:
      try:
        del data_source[PROPERTIES][property]
      except:
        logging.error("Could not delete property: %s", property)
        continue
    return data_source