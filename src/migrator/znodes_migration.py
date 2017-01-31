import sys
import logging

class ZNodesMigrator:
    def __init__(self, config, zk):
        self.config = config
        self.zk = zk

    def start(self):
        self.migrate_solr_data()
        self.migrate_core_data()
        self.migrate_proxy_data()

    def migrate_solr_data(self):
        logging.info("Migrating Solr data to new ZK namespace {}".format(self.config["solr.namespace"]))
        solr_znodes = ["aliases.json", "clusterstate.json", "collections", "configs", "live_nodes", "overseer",
                       "overseer_elect", "security.json"]
        self.copy_znode_data(solr_znodes, "/", self.config["solr.namespace"])

    def migrate_core_data(self):
        logging.info("Migrating api data to new ZK namespace {}".format(self.config["api.namespace"]))
        old_core_znode_root = "/lucid"
        if not self.zk.exists(old_core_znode_root):
            sys.exit("Could not find zkpath '{}'".format(old_core_znode_root))
        self.copy_znode_data(self.zk.get_children(old_core_znode_root), old_core_znode_root, self.config["api.namespace"])

    def migrate_proxy_data(self):
        logging.info("Migrating proxy data to new ZK namespace {}".format(self.config["proxy.namespace"]))
        old_core_znode_root = "/lucid-apollo-admin"
        if not self.zk.exists(old_core_znode_root):
            sys.exit("Could not find zkpath '{}'".format(old_core_znode_root))
        self.copy_znode_data(self.zk.get_children(old_core_znode_root), old_core_znode_root, self.config["proxy.namespace"])

    def copy_znode_data(self, znodes, old_root, new_root):
        for node_name in znodes:
            logging.debug("Migrating znode '{}' data from old path '{}' to new path '{}'".format(node_name, old_root, new_root))
            znode_fullpath = "{}/{}".format(old_root, node_name)
            if self.zk.exists(znode_fullpath):
                value, zstat = self.zk.get(znode_fullpath)
                new_fullpath = "{}/{}".format(new_root, node_name)
                self.migrate_znode_data(new_fullpath, value)
                children = self.zk.get_children(znode_fullpath)
                self.copy_znode_data(children, znode_fullpath, "{}/{}".format(new_root, node_name))
            else:
                logging.error("Znode path '{}' does not exist".format(znode_fullpath))

    def migrate_znode_data(self, path, data):
        if not self.zk.exists(path):
            logging.debug("not copying znode '{}' since it already exists".format(path))
            real_path = self.zk.create(path, value=data, makepath=True)
