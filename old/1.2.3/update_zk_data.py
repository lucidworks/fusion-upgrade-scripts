import argparse
import logging
import os
import json

from kazoo.client import KazooClient

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def update_zk_data(exported_filename):
    if not os.path.exists(exported_filename):
        logger.error("Could not locate filename '{}'".format(exported_filename))
    f = open(exported_filename)
    dump_json = json.load(f)

    # Check if the JSON list has a 4th element with instance of list() that contains values of updated zknodes
    if len(dump_json) != 4:
        logger.warn("The exported file does not have an updated list of the params. Skipping any updates in ZK")

    if not isinstance(dump_json[3], list):
        logger.error("The 4th element in the JSON is not an instance of list. "
                     "It is of type '{}'".format(type(dump_json[3])))

    changed_zk_nodes = dump_json[3]

    for node in changed_zk_nodes:
        if zk.exists(node):
            data, stat = zk.get(node)
            # Get the data from the dump file and update ZK
            if node in dump_json[2]:
                updated_data = dump_json[2][node]
                zk.set(node, bytes(updated_data), version=stat.version)
                logger.info("Updated ZK node '{}'".format(node))
            else:
                logger.warn("Could not locate '{}' data in the exported file".format(node))

        else:
            logger.warn("Could not locate zknode '{}' in Zookeeper server '{}'".format(node, zk_host))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update the ZK data to the ZK server")
    parser.add_argument("zk_host", type=str, help="ZK Host string")
    parser.add_argument("exported_filename", type=str, help="Exported and updated file name")

    args = parser.parse_args()

    zk_host = args.zk_host
    exported_filename = args.exported_filename

    logger.info("connecting to " + zk_host)
    zk = KazooClient(hosts=zk_host, timeout=20.0)
    logger.info("gathering data")
    zk.start()

    update_zk_data(exported_filename)
