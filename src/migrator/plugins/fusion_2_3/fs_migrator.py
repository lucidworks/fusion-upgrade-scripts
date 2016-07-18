#!/usr/bin/env python

from src.utils.constants import *

class SmbMigrator():

  def migrate(self, data_source):
    properties = data_source[PROPERTIES]
    ad_url = properties.pop(AD_URL, DEFAULT_EMPTY)
    ad_principal = properties.pop(AD_PRINCIPAL, DEFAULT_EMPTY)
    ad_credentials = properties.pop(AD_CREDENTIALS, DEFAULT_EMPTY)
    ad_user_filter = properties.pop(AD_USER_FILTER, DEFAULT_EMPTY)
    ad_group_filter = properties.pop(AD_GROUP_FILTER, DEFAULT_EMPTY)
    ad_user_base_dn = properties.pop(AD_USER_BASE_DN, DEFAULT_EMPTY)
    ad_group_base_dn = properties.pop(AD_GROUP_BASE_DN, DEFAULT_EMPTY)
    ad_cache_groups = properties.pop(AD_CACHE_GROUPS, False)
    enable_sids_cache = properties.pop(ENABLE_SIDS_CACHE, True)
    max_cache_size = properties.pop(MAX_CACHE_SIZE, 1000)
    cache_expiration_time = properties.pop(CACHE_EXPIRATION_TIME, 7200)
    ad_read_token_groups = properties.pop(AD_READ_TOKEN_GROUPS, True)
    ad_context_factory = properties.pop(AD_CONTEXT_FACTORY, LDAP_CTX_FACTORY)
    ad_security_auth = properties.pop(AD_SECURITY_AUTH, SIMPLE)
    ad_referral = properties.pop(AD_REFERRAL, FOLLOW)
    ad_read_timeout = properties.pop(AD_READ_TIMEOUT, 5000)
    ad_connect_timeout = properties.pop(AD_CONNECT_TIMEOUT, 3000)
    security_trimming = properties.pop(ENABLE_SECURITY_TRIMMING, False)

    if isinstance(security_trimming, bool) and not security_trimming:
      return data_source

    if isinstance(security_trimming, dict):
      properties[ENABLE_SECURITY_TRIMMING] = security_trimming
      return data_source

    security_trimming = {}
    security_trimming[AD_URL] = ad_url
    security_trimming[AD_PRINCIPAL] = ad_principal
    security_trimming[AD_CREDENTIALS] = ad_credentials
    security_trimming[AD_USER_FILTER] = ad_user_filter
    security_trimming[AD_GROUP_FILTER] = ad_group_filter
    security_trimming[AD_USER_BASE_DN] = ad_user_base_dn
    security_trimming[AD_GROUP_BASE_DN] = ad_group_base_dn
    security_trimming[AD_CACHE_GROUPS] = ad_cache_groups
    security_trimming[ENABLE_SIDS_CACHE] = enable_sids_cache
    security_trimming[MAX_CACHE_SIZE] = max_cache_size
    security_trimming[CACHE_EXPIRATION_TIME] = cache_expiration_time
    security_trimming[AD_READ_TOKEN_GROUPS] = ad_read_token_groups
    security_trimming[AD_CONTEXT_FACTORY] = ad_context_factory
    security_trimming[AD_SECURITY_AUTH] = ad_security_auth
    security_trimming[AD_REFERRAL] = ad_referral
    security_trimming[AD_READ_TIMEOUT] = ad_read_timeout
    security_trimming[AD_CONNECT_TIMEOUT] = ad_connect_timeout
    properties[ENABLE_SECURITY_TRIMMING] = security_trimming

    return data_source
