#!/usr/bin/env python

from distutils.version import StrictVersion

from src.utils.class_loader import ClassLoader
from src.utils.zookeeper_client import ZookeeperClient
from src.utils.resource_manager import ResourceManager
from src.utils.variables_helper import VariablesHelper
from src.utils.constants import *

import logging
import re
import sys
import json

class ConnectorsMigrator:

  def __init__(self):
    self.class_loader = ClassLoader()
    self.zk_fusion_host = VariablesHelper.get_fusion_zookeeper_host()
    self.zk_fusion_node = VariablesHelper.get_fusion_zookeeper_node()
    self.fusion_version = VariablesHelper.get_fusion_version()
    self.old_fusion_version = VariablesHelper.get_old_fusion_version()
    self.zookeeper_client = ZookeeperClient(self.zk_fusion_host)

  def start(self, data_source_to_migrate):
    migrators_file = ResourceManager.get_resource(MIGRATORS_FILE)
    zk_connectors_node = "{}/{}".format(self.zk_fusion_node, "lucid/connectors")
    zk_datasources_node = "{}/{}".format(zk_connectors_node, "datasources")
    self.zookeeper_client.start()

    if not self.zookeeper_client.exists(zk_connectors_node):
      return

    if not self.zookeeper_client.exists(zk_datasources_node):
      return

    if len(data_source_to_migrate) == 1 and data_source_to_migrate[0] == "all":
      children = self.zookeeper_client.get_children(zk_datasources_node)
    else:
      children = data_source_to_migrate

      for child in children:
        child_node = "{}/{}".format(zk_datasources_node, child)
        if not self.zookeeper_client.exists(child_node):
          logging.info("Node {} does not exist".format(child_node))
          return

    for child in children:
      data_source_node = "{}/{}".format(zk_datasources_node, child)
      data_source = self.zookeeper_client.get_as_json(data_source_node)
      ds_type = data_source["type"]

      logging.info("Trying to migrate datasource: %s, type: %s", child, ds_type)

      ds_version = self.old_fusion_version
      ds_migrators = migrators_file.get(ds_type, None)
      if ds_migrators and isinstance(ds_migrators, list):
        classname = None
        for counter, ds_migrator in enumerate(ds_migrators):
          classname = None
          # Match the migrator based on the current and old version
          migrator_clz = ds_migrator["migrator"]
          base_version = ds_migrator["base_version"]
          target_version = ds_migrator["target_version"]
          if StrictVersion(base_version) <= StrictVersion(ds_version) <= StrictVersion(target_version):
            classname = migrator_clz
            if classname is None:
              logging.info("No classname found for datasource type '{}' between version {} and new version {}".format(ds_type, ds_version, self.fusion_version))
              continue
            migrator = self.class_loader.get_instance(classname)
            # Start the migration
            if migrator is None:
              logging.error("Migrator '{}' does not exist or the classname is malformed".format(classname))
              continue
            logging.info("Executing {}.migrate(data_source)".format(classname))
            updated_datasource = migrator.migrate(data_source)
            ds_version = target_version
            # Only updated in ZK when it's the last migrator
            if counter == len(ds_migrators) - 1:
              self.zookeeper_client.set_as_json(data_source_node, updated_datasource)
          else:
            logging.info("No migrator found for version '{}' and new version '{}' for type".format(ds_version, self.fusion_version, ds_type))
            continue

class ConnectorsMigrator3x:

    def __init__(self, config, zk):
        self.class_loader = ClassLoader()
        self.zk_fusion_host = config["fusion.zk.connect"]
        self.zk_fusion_node = config["api.namespace"]
        self.fusion_version = VariablesHelper.get_fusion_version()
        self.old_fusion_version = VariablesHelper.get_old_fusion_version()
        self.zk_client = zk
        self.deprecated_types = ["logstash"]

    def start(self, data_source_to_migrate):
        migrators_file = ResourceManager.get_resource(MIGRATORS_FILE)
        connectors_znode = "{}/connectors".format(self.zk_fusion_node)
        datasources_znode = "{}/datasources".format(connectors_znode)

        if not self.zk_client.exists(connectors_znode):
            logging.info("Connectors znode path {} does not exist. No migrations to perform".format(connectors_znode))
            return
        else:
            if not self.zk_client.exists(datasources_znode):
                logging.info("Connectors znode path {} does not exist. No migrations to perform".format(datasources_znode))
                return

        if data_source_to_migrate is None or len(data_source_to_migrate) == 0 or data_source_to_migrate[0] == "all":
            children = self.zk_client.get_children(datasources_znode)
        else:
            children = data_source_to_migrate
            for child in children:
                child_node = "{}/{}".format(datasources_znode, child)
                if not self.zk_client.exists(child_node):
                    logging.info("Node {} does not exist".format(child_node))
                    return

        for child in children:
            data_source_node = "{}/{}".format(datasources_znode, child)
            value, zstat = self.zk_client.get(data_source_node)
            data_source = json.loads(value)
            ds_type = data_source["type"]

            logging.info("Trying to migrate datasource: %s, type: %s", child, ds_type)

            # Remove the deprecated datasources
            if ds_type in self.deprecated_types:
                logging.info("Removing deprecated datasource '{}' of type '{}'".format(child, ds_type))
                self.zk_client.delete(data_source_node)
                continue

            ds_version = self.old_fusion_version
            ds_migrators = migrators_file.get(ds_type, None)
            if ds_migrators and isinstance(ds_migrators, list):
                classname = None
                for counter, ds_migrator in enumerate(ds_migrators):
                    classname = None
                    # Match the migrator based on the current and old version
                    migrator_clz = ds_migrator["migrator"]
                    base_version = ds_migrator["base_version"]
                    target_version = ds_migrator["target_version"]
                    if StrictVersion(base_version) <= StrictVersion(ds_version) <= StrictVersion(target_version):
                        classname = migrator_clz
                        if classname is None:
                            logging.debug("No classname found for datasource type '{}' between version {} and new version {}".format(ds_type, ds_version, self.fusion_version))
                            continue
                        migrator = self.class_loader.get_instance(classname)
                        # Start the migration
                        if migrator is None:
                            logging.error("Migrator '{}' does not exist or the classname is malformed".format(classname))
                            continue
                        logging.info("Executing {}.migrate(data_source)".format(classname))
                        updated_datasource = migrator.migrate(data_source)
                        ds_version = target_version
                        # Only updated in ZK when it's the last migrator
                        if counter == len(ds_migrators) - 1:
                            # print counter, len(ds_migrators)
                            logging.info("Updating Datasource POJO for id '{}' and type '{}'".format(child, ds_type))
                            self.zk_client.set(data_source_node, value=json.dumps(updated_datasource))
                    else:
                        logging.debug("No migrator found for datasource '{}' version '{}' and new version '{}' for type '{}'".format(child, ds_version, self.fusion_version, ds_type))
                        continue
