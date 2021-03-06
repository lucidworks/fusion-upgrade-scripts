#!/usr/bin/env python

from kazoo.client import KazooClient
import json
import logging

class ZookeeperClient:
  def __init__(self, zk_host):
    self.zk = KazooClient(hosts=zk_host)

  def start(self):
    logging.info("Starting zookeeper client")
    self.zk.start()

  def exists(self, node_path):
    logging.info("Verifying zk node: %s", node_path)
    return self.zk.exists(node_path)

  def get_children(self, node_path):
    logging.info("Getting children for node: {}".format(node_path))

    return self.zk.get_children(node_path)

  def get_as_json(self, node_path):
    logging.info("Getting zk node: %s", node_path)
    (data, stats) = self.zk.get(node_path)
    return json.loads(data)

  def set_as_json(self, node_path, object):
    logging.info("Setting value to zk node: %s", node_path)
    self.zk.set(node_path, json.dumps(object, indent=2))
