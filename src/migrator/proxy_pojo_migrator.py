import json
import logging

def update_initmeta_pojo(config, zk):
    initmeta_znode_path = "{}/sys/init-meta".format(config["proxy.namespace"])
    if not zk.exists(initmeta_znode_path):
        logging.warn("init-meta POJO does not exist at zpath '{}'".format(initmeta_znode_path))

    # Read the payload from Zookeeper
    value, zstat = zk.get(initmeta_znode_path)
    deser_payload = json.loads(value)
    deser_payload["datasets-installed-at"] = deser_payload.get("initialized-at")
    deser_payload["initial-db-installed-at"] = deser_payload.get("initialized-at")

    logging.info("Updating init-meta payload at path '{}'".format(initmeta_znode_path))
    # Write the updated payload to Zookeeper
    zk.set(initmeta_znode_path, value=json.dumps(deser_payload))
