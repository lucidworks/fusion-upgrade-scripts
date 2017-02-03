#!/usr/bin/env python
#
# Script to download data from ZK
#
import json, datetime
import argparse

from kazoo.client import KazooClient

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO: copy solr data dirs.
# what about:
#    "/collections/audit_logs/leader_elect/shard1/election/93685056321486848-core_node1-n_0000000001", 
#    "/collections/audit_logs/leaders", 
#    "/collections/audit_logs/leaders/shard1", 
#  lucid-apollo-admin - check mm
#  collections do -- check with elexy david


def walk(path = ""):
    if path in skipPaths:
        logger.debug("skipping '{}'".format(path))
        return
    logger.debug("walking '{}'".format(path))
    (value, znode_stat) = zk.get(path)
    paths.append(path)
    if value is not None:
        values[path] = value
        logger.debug(" value ({}): {}".format(type(value),value))
    for child in sorted(zk.get_children(path)):
        child_path = path + "/" + child
        walk(child_path)


def convert_to_json():
    logger.debug("converting data to json")
    meta = {
        "description": "zookeeper data dump for Fusion",
        "source": host,
        "when": str(datetime.datetime.now()),
    }
    data = [meta, paths, values]
    json_str = json.dumps(data, sort_keys=True, indent=2)
    return json_str


def write_to_file(data):
    logger.info("writing data to " + filename)
    with open(filename, 'w') as f:
        f.write(data)
    logger.info("done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse host and filename")
    parser.add_argument('host', type=str, default="localhost:9983", help="ZK address")
    parser.add_argument('filename', type=str, default="zk.out", help="Output file name")
    args = parser.parse_args()
    #host ='127.0.0.1:9983'
    host = args.host
    filename = args.filename

    # values is a dict with path to value mapping
    values={}
    # paths is a list of paths read from zk
    paths=[]

    skipPaths = ['/aliases.json', '/clusterstate.json', '/live_nodes', '/lucid/leaders', '/lucid/locks',
                '/lucid/services', '/lucid/stateful-jobs', '/overseer', '/overseer_elect', '/zookeeper',
                "/collections", "/configs"]

    logger.info("connecting to " + host)
    zk = KazooClient(hosts=host, timeout=20.0)
    logger.info("gathering data")
    zk.start()
    walk()
    zk.stop()
    json_str = convert_to_json()
    write_to_file(json_str)

