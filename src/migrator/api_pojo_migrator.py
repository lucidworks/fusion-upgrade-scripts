import logging
import json
import sys

def update_searchcluster_pojo(config, zk):
    solr_zk_connect_string = config["solr.zk.connect"]
    searchcluster_znode_path = "{}/search-clusters/default".format(config["api.namespace"])
    if not zk.exists(searchcluster_znode_path):
        sys.exit("Search cluster POJO does not exist at zpath '{}'".format(searchcluster_znode_path))

    # Read the payload from Zookeeper
    value, zstat = zk.get(searchcluster_znode_path)
    deser_payload = json.loads(value)
    deser_payload["connectString"] = solr_zk_connect_string

    logging.info("Updating search-cluster payload at path '{}'".format(searchcluster_znode_path))
    # Write the updated payload to Zookeeper
    zk.set(searchcluster_znode_path, value=json.dumps(deser_payload))
