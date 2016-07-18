#!/usr/bin/env python

from src.migrator.base_migrator import BaseMigrator
from src.utils.constants import *

class AndaSplitterMigrator():
  def migrate(self, data_source):
    properties = data_source[PROPERTIES]
    split_csv = properties.pop(SPLIT_CSV, False)
    csv_format = properties.pop(CSV_FORMAT, DEFAULT)
    csv_with_header = properties.pop(CSV_WITH_HEADER, True)
    csv_id_column = properties.pop(CSV_ID_COLUMN, DEFAULT_EMPTY)
    csv_delimeter_override = properties.pop(CSV_DELIMETER_OVERRIDE, COMMA)
    csv_comment_override = properties.pop(CSV_COMMENT_OVERRIDE, NUMBER)
    csv_characterset_override = properties.pop(CSV_CHARACTER_SET_OVERRIDE, UTF_8)

    if isinstance(split_csv, bool) and not split_csv:
      return data_source

    if isinstance(split_csv, dict):
      properties[SPLIT_CSV] = split_csv
      return data_source

    split_csv = {}
    split_csv[CSV_WITH_HEADER] = csv_with_header
    split_csv[CSV_FORMAT] = csv_format
    split_csv[CSV_ID_COLUMN] = csv_id_column
    split_csv[CSV_DELIMETER_OVERRIDE] = csv_delimeter_override
    split_csv[CSV_COMMENT_OVERRIDE] = csv_comment_override
    split_csv[CSV_CHARACTER_SET_OVERRIDE] = csv_characterset_override
    properties[SPLIT_CSV] = split_csv

    return data_source

class BasicAndaMigrator(BaseMigrator, AndaSplitterMigrator):
  def migrate(self, data_source):
    data_source = BaseMigrator.delete_properties(self, data_source,
                                                 [REEVALUATE_CRAWL_DB_ON_START,
                                                  TRACK_EMBEDDED_IDS])
    data_source = AndaSplitterMigrator.migrate(self, data_source)
    return data_source

class GitHubMigrator(BaseMigrator):
  def migrate(self, data_source):
    data_source = BaseMigrator.delete_properties(self, data_source,
                                                 [RETAIN_OUT_LINKS, REEVALUATE_CRAWL_DB_ON_START,
                                                  ALIAS_EXPIRATION,
                                                  FETCH_DELAY_MS_PER_HOST, LEGAL_URI_SCHEMES_PROP,
                                                  ENABLE_SECURITY_TRIMMING])
    return data_source

class JavascriptMigrator(BaseMigrator):
  def migrate(self, data_source):
    data_source = BaseMigrator.delete_properties(self, data_source,
                                                 [REEVALUATE_CRAWL_DB_ON_START,
                                                  TRACK_EMBEDDED_IDS,
                                                  FETCH_DELAY_MS_PER_HOST, LEGAL_URI_SCHEMES_PROP])
    return data_source

class SharepointMigrator(BaseMigrator, AndaSplitterMigrator):
  def migrate(self, data_source):
    data_source = BaseMigrator.delete_properties(self, data_source,
                                                 [RETAIN_OUT_LINKS, REEVALUATE_CRAWL_DB_ON_START,
                                                  TRACK_EMBEDDED_IDS, ALIAS_EXPIRATION,
                                                  FETCH_DELAY_MS_PER_HOST])
    data_source = AndaSplitterMigrator.migrate(self, data_source)
    properties = data_source[PROPERTIES]
    ldap_host = properties.pop(LDAP_HOST, DEFAULT_EMPTY)
    ldap_port = properties.pop(LDAP_PORT, 389)
    ldap_use_ssl = properties.pop(LDAP_USE_SSL, False)
    ldap_read_groups_type = properties.pop(LDAP_READ_GROUPS_TYPE, TOKEN_GROUPS)
    ldap_search_base = properties.pop(LDAP_SEARCH_BASE, DEFAULT_EMPTY)
    security_filter_cache = properties.pop(LDAP_SECURITY_FILTER_CACHE, True)
    cache_expiration_time = properties.pop(F_CACHE_EXPIRATION_TIME, 7200)
    cache_max_size = properties.pop(CACHE_MAX_SIZE, 1000)
    security_trimming = properties.pop(ENABLE_SECURITY_TRIMMING, False)

    if isinstance(security_trimming, bool) and not security_trimming:
      return data_source

    if isinstance(security_trimming, dict):
      properties[ENABLE_SECURITY_TRIMMING] = security_trimming
      return data_source

    security_trimming = {}
    security_trimming[LDAP_HOST] = ldap_host
    security_trimming[LDAP_PORT] = ldap_port
    security_trimming[LDAP_USE_SSL] = ldap_use_ssl
    security_trimming[LDAP_READ_GROUPS_TYPE] = ldap_read_groups_type
    security_trimming[LDAP_SEARCH_BASE] = ldap_search_base
    security_trimming[LDAP_SECURITY_FILTER_CACHE] = security_filter_cache
    security_trimming[F_CACHE_EXPIRATION_TIME] = cache_expiration_time
    security_trimming[CACHE_MAX_SIZE] = cache_max_size
    properties[ENABLE_SECURITY_TRIMMING] = security_trimming

    return data_source
