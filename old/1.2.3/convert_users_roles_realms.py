import argparse
import json
import logging
from collections import OrderedDict

from convert_permission import convert_perms

FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

roles_ui_permissions = {
    "admin": ["*"],
    "ui-user": [],
    "search": ["fusion.search"],
    "collection-admin": ["fusion.admin", "fusion.admin.collections", "fusion.admin.collections.delete",
                         "fusion.admin.pipelines", "fusion.admin.index-pipelines.delete",
                         "fusion.admin.query-pipelines.delete", "fusion.admin.search", "fusion.search",
                         "fusion.dashboards", "fusion.relevancy-workbench"]
}

# Do not expand role inheritance for 'search' users. Instead we are adding the extra perms here
extra_permissions = {
    "search": [
        {"methods": ["GET", "POST", "PUT"], "path": "/prefs/apps/search/*"}
    ],
    "collection-admin": [
        {"methods": ["GET", "POST", "PUT"], "path": "/prefs/apps/search/*"},
        {"methods": ["GET"], "path": "/index-pipelines/**"}
    ]
}

proxy_zk_nodes = ["/role/", "/realm-config/", "/user/"]
base_roles = roles_ui_permissions.keys()
role_names_ids = dict()
role_names_users = dict()
realm_configs = dict()


def read_users_roles(dump_json):
    znodes = dump_json[1]
    znodes_data = dump_json[2]
    for znode in znodes:
        for proxy_node in proxy_zk_nodes:
            if proxy_node in znode:
                data = znodes_data[znode]
                data = json.loads(data)
                if proxy_node == "/user/":
                    # Users payloads can not have a 'role' always defined.
                    if "role" in data:
                        role = data["role"]
                        if role in role_names_users:
                            role_names_users[role].append(znode)
                        else:
                            role_names_users[role] = [znode]
                elif proxy_node == "/role/":
                    role = data["name"]
                    role_names_ids[role] = znode
                elif proxy_node == "/realm-config/":
                    data = znodes_data[znode]
                    data = json.loads(data)
                    realm_type = data.get("realm-type") or data.get("realmType")
                    if realm_type in realm_configs:
                        realm_configs[realm_type].append(znode)
                    else:
                        realm_configs[realm_type] = [znode]


def modify_user_roles_data(dump, introspect_filename):
    for role_name in role_names_ids:
        role_id = role_names_ids[role_name]
        data = dump[2][role_id]
        role_data_json = json.loads(data)
        inherited_from = role_data_json["extends"]
        if role_name in role_names_users:
            """
                Modify user information.
                Remove 'role' in the payload
                Add 'role-names' array with any inheritance from the role
            """
            users = role_names_users[role_name]
            roles_for_users_to_inherit = []
            if inherited_from is not None and len(inherited_from) > 0:
                for parent in inherited_from:
                    roles_for_users_to_inherit.append(parent)
            for user in users:
                user_data = dump[2][user]
                user_data_json = json.loads(user_data)
                logger.debug("User information: {}".format(user_data_json))
                del user_data_json["role"]
                user_data_json["role-names"] = [role_name] + roles_for_users_to_inherit
                # Check if the user has any permissions and convert them to new format
                if len(user_data_json["permissions"]) > 0:
                    new_permissions = get_new_permissions(user_data_json["permissions"], introspect_filename)
                    user_data_json["permissions"] = new_permissions
                logger.debug("Updated user information: {}".format(user_data_json))
                dump[2][user] = json.dumps(user_data_json)
                logger.info("Updated zknode {}".format(user))
                dump[3].append(user)
        del role_data_json["extends"]
        if role_name in roles_ui_permissions:
            role_data_json["ui-permissions"] = roles_ui_permissions[role_name]
        else:
            # For non-standard roles
            role_data_json["ui-permissions"] = []
        permissions = role_data_json["permissions"]
        new_permissions = get_new_permissions(permissions, introspect_filename)
        logger.debug("Role information: {}".format(data))
        role_data_json["permissions"] = new_permissions
        # Add the extra permissions
        if role_name in extra_permissions:
            role_data_json["permissions"] = role_data_json["permissions"] + extra_permissions[role_name]
        logger.debug("Updated role information: {}".format(role_data_json))
        logger.info("Updated zknode {}".format(role_id))
        dump[2][role_id] = json.dumps(role_data_json)
        dump[3].append(role_id)
    return dump


def get_new_permissions(permissions, introspect_filename):
    new_permissions = list()
    for permission in permissions:
        try:
            converted_perms = convert_perms(permission, introspect_filename)
            if isinstance(converted_perms, list):
                new_permissions = new_permissions + converted_perms
            elif isinstance(converted_perms, str):
                new_permissions.append(converted_perms)
            else:
                logger.warn("Unknown data type of permission {}. '{}'".format(converted_perms, type(converted_perms)))
        except Exception as e:
            logger.error("Caught error while processing permission: '{}'".format(permission))
            logger.error("Exception is {}".format(e))
            pass
    return new_permissions


def modify_ldap_realms_data(dump):
    if "ldap" in realm_configs:
        # Modify LDAP stuff
        for ldap_config_id in realm_configs["ldap"]:
            data = dump[2][ldap_config_id]
            ldap_config = json.loads(data)
            if "config" in ldap_config:
                if "bind-dn" not in ldap_config["config"] or "bindDn" in ldap_config["config"]:
                    if ("user-id-attr" in ldap_config["config"] and "user-base-dn" in ldap_config["config"]) or \
                            ("userIdAttr" in ldap_config["config"] and "userBaseDn" in ldap_config["config"]):
                        user_id_attr = ldap_config["config"].get("user-id-attr") or ldap_config["config"].get("userIdAttr")
                        user_base_dn = ldap_config["config"].get("user-base-dn") or ldap_config["config"].get("userBaseDn")
                        bind_dn_template = user_id_attr + "={}," + user_base_dn
                        if "userIdAttr" in ldap_config["config"] and "userBaseDn" in ldap_config["config"]:
                            ldap_config["config"]["login"] = {"bindDnTemplate": bind_dn_template}
                            del ldap_config["config"]["userIdAttr"]
                            del ldap_config["config"]["userBaseDn"]
                        else:
                            ldap_config["config"]["login"] = {"bind-dn-template": bind_dn_template}
                            del ldap_config["config"]["user-id-attr"]
                            del ldap_config["config"]["user-base-dn"]
                    else:
                        logger.warn("Could not find 'user-id-attr' and/or 'user-base-dn' in ldap realm config {}".format(ldap_config))
                else:
                    base_dn = ldap_config["config"]["base-dn"]
                    ldap_config["config"]["login"] = {"bind-dn-template": base_dn}
                    del ldap_config["config"]["base-dn"]
            else:
                logger.warn("Could not find 'config' in ldap realm config {}".format(ldap_config))
            logger.info("Updated zknode {}".format(ldap_config_id))
            dump[2][ldap_config_id] = json.dumps(ldap_config)
            dump[3].append(ldap_config_id)
    elif "kerberos" in realm_configs:
        logger.info("No changes for Kerberos yet")
    return dump


def read_convert_dump_file(filename, introspect_filename, output_filename):
    # TODO: Validate the existance of the file
    f = open(filename)
    dump = json.load(f, object_pairs_hook=OrderedDict)

    # Check if the file is in right format at the object level
    # assert len(dump) == 3
    # assert isinstance(dump[1], list)
    # assert isinstance(dump[2], dict)

    # Create an extra item in the dump JSON file to store the id's of the zknodes that we have changed
    if len(dump) == 3:
        dump.append(list())

    read_users_roles(dump)
    new_dump = modify_user_roles_data(dump, introspect_filename)
    new_dump = modify_ldap_realms_data(new_dump)
    write_file(new_dump, output_filename)


def write_file(new_dump, output_filename):
    with open(output_filename, "aw") as jsonfile:
        json.dump(new_dump, jsonfile, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert users and roles from 1.2 to 1.4")
    parser.add_argument('zkdump_filename', type=str, help="The ZK dump file")
    parser.add_argument('introspect_filename', type=str, help="File name of the introspect")
    parser.add_argument('output_filename', type=str, help="Output dump file name")

    args = parser.parse_args()
    read_convert_dump_file(args.zkdump_filename, args.introspect_filename, args.output_filename)
