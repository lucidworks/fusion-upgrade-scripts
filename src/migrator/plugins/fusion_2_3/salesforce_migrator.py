#!/usr/bin/env python

from src.utils.constants import *

class SalesforceMigrator:

  def migrate(self, data_source):
    object_to_crawl = data_source[PROPERTIES].get(OBJECTS_TO_CRAWL)

    if isinstance(object_to_crawl, list):
      return data_source

    object_to_crawl_list = object_to_crawl.split(COMMA)
    data_source[PROPERTIES][OBJECTS_TO_CRAWL] = object_to_crawl_list

    return data_source