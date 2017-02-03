import argparse
from collections import OrderedDict
import logging
import json
import pprint

import requests

import convert_users_roles_realms as convert_data

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

user_id_prefix = "/user/"
role_id_prefix = "/role/"
realm_id_prefix = "/realm-config/"


def combine_all_data():
    """
        Format the data from the three files in to a JSON format that looks like a ZK dump understood by
        convert_users_roles_realms.py
    :return:
    """
    dump = list()
    dump.append(dict())
    dump.append(list())
    dump.append(dict())
    dump.append(list())

    # Add users to the dump JSON
    for user in users_json:
        user_id = "{}{}".format(user_id_prefix, user["id"])
        dump[1].append(user_id)
        dump[2][user_id] = json.dumps(user)

    # Add roles to the dump JSON
    for role in roles_json:
        role_id = "{}{}".format(role_id_prefix, role["id"])
        dump[1].append(role_id)
        dump[2][role_id] = json.dumps(role)

    # Add realm config to the dump JSON
    for realm in realms_json:
        realm_id = "{}{}".format(realm_id_prefix, realm["id"])
        dump[1].append(realm_id)
        dump[2][realm_id] = json.dumps(realm)

    # logger.debug(pprint.pprint(dump, indent=2))
    return dump


def update_data(dump):
    convert_data.read_users_roles(dump)
    new_dump = convert_data.modify_user_roles_data(dump, introspect_filename)
    new_dump = convert_data.modify_ldap_realms_data(new_dump)
    return new_dump


def process_changed_data(new_dump):
    formatted_data = {
        "users": list(),
        "roles": list(),
        "realms": list()
    }
    if len(new_dump) >= 2:
        payloads = new_dump[2]
        for payload_id in payloads:
            if user_id_prefix in payload_id:
                formatted_data["users"].append(payloads[payload_id])
            elif role_id_prefix in payload_id:
                formatted_data["roles"].append(payloads[payload_id])
            elif realm_id_prefix in payload_id:
                formatted_data["realms"].append(payloads[payload_id])
            else:
                logger.info("Unknown id '{}'. No matches to user, role or realm prefixes".format(id))

    else:
        logger.error("Improper data format in the converted file. Data dump: {}".format(new_dump))
    return formatted_data


def upload_data(data):
    url = admin_url
    # logger.debug(pprint.pprint(data, indent=2))
    for user in data.get("users"):
        users_url = "{}/api/users".format(url)
        # Get a list of existing users
        r = requests.get(users_url)
        if r.status_code == 200:
            current_users = r.json()
            ids = list()
            for current_user in current_users:
                ids.append(current_user["username"])
            user_json = json.loads(user)
            # Create a new user only if this user does not exist in current installation
            if user_json["username"] not in ids:
                if "inheritedPermissions" in user_json:
                    del user_json["inheritedPermissions"]
                if "updatedAt" in user_json:
                    del user_json["updatedAt"]
                if "createdAt" in user_json:
                    del user_json["createdAt"]
                if "inheritedPermissions" in user_json:
                    del user_json["inheritedPermissions"]
                r = requests.post(users_url, data=json.dumps(user_json), headers={"Content-Type": "application/json"})
                if r.status_code == 200 or r.status_code == 201:
                    logger.info("Added user '{}' to the Admin".format(user_json["id"]))
                else:
                    logger.info("Unsuccessful request to url {}. Status code {}. Response text {}. Request data {}".format(r.url, r.status_code, r.text, user_json))
            else:
                logger.info("User '{}' already exists in Admin UI. Not creating again".format(user_json["name"]))
        else:
            logger.info("Unsuccessful request to url {}. Status code {}. Response text {}".format(r.url, r.status_code, r.text))

    # Create roles if they are not present already
    for role in data.get("roles"):
        roles_url = "{}/api/roles".format(url)
        # Get a list of existing users
        r = requests.get(roles_url)
        if r.status_code == 200:
            current_roles = r.json()
            ids = list()
            for current_role in current_roles:
                ids.append(current_role["name"])
            role_json = json.loads(role)
            # Create a new user only if this user does not exist in current installation
            if role_json["name"] not in ids:
                if "inheritedPermissions" in role_json:
                    del role_json["inheritedPermissions"]
                if "updatedAt" in role_json:
                    del role_json["updatedAt"]
                if "createdAt" in role_json:
                    del role_json["createdAt"]
                r = requests.post(roles_url, data=json.dumps(role_json), headers={"Content-Type": "application/json"})
                if r.status_code == 200 or r.status_code == 201:
                    logger.info("Added role '{}' to the Admin".format(role_json["name"]))
                else:
                    logger.info("Unsuccessful request to url {}. Status code {}. Response text {}. Request data {}".format(r.url, r.status_code, r.text, role_json))
            else:
                logger.info("Role name '{}' already exists in Admin UI. Not creating again".format(role_json["name"]))
        else:
            logger.info("Unsuccessful request to url {}. Status code {}. Response text {}".format(r.url, r.status_code, r.text))

    # Create realms if they do not exist already
    for realm in data.get("realms"):
        realms_url = "{}/api/realm-configs".format(url)
        # Get a list of existing users
        r = requests.get(realms_url)
        if r.status_code == 200:
            current_realms = r.json()
            ids = list()
            for current_realm in current_realms:
                ids.append(current_realm["name"])
            realm_json = json.loads(realm)
            # Create a new user only if this user does not exist in current installation
            if realm_json["name"] not in ids:
                if "inheritedPermissions" in realm_json:
                    del realm_json["inheritedPermissions"]
                if "updatedAt" in realm_json:
                    del realm_json["updatedAt"]
                if "createdAt" in realm_json:
                    del realm_json["createdAt"]
                r = requests.post(realms_url, data=json.dumps(realm_json), headers={"Content-Type": "application/json"})
                if r.status_code == 200 or r.status_code == 201:
                    logger.info("Added realm '{}' to the Admin".format(realm_json["name"]))
                else:
                    logger.info("Unsuccessful request to url {}. Status code {}. Response text {}. Request data {}".format(r.url, r.status_code, r.text, realm_json))
            else:
                logger.info("Realm '{}' already exists in Admin UI. Not creating again".format(realm_json["name"]))
        else:
            logger.info("Unsuccessful request to url {}. Status code {}. Response text {}".format(r.url, r.status_code, r.text))




def change_upload_data():
    dump = combine_all_data()
    changed_data = update_data(dump)
    formatted_data = process_changed_data(changed_data)
    upload_data(formatted_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read users, roles and realms "
                                                 "from file format and upload to 1.2.3 Fusion")
    parser.add_argument("roles_file", help="JSON file of roles")
    parser.add_argument("users_file", help="JSON file of users")
    parser.add_argument("realms_file", help="JSON file of realms")
    parser.add_argument("admin_url", help="Base URL of Admin UI with the credentials")
    parser.add_argument("introspect_filename", help="File name of the introspect")

    args = parser.parse_args()
    roles_file = args.roles_file
    users_file = args.users_file
    realms_file = args.realms_file
    admin_url = args.admin_url
    introspect_filename = args.introspect_filename

    roles_f = open(roles_file)
    roles_json = json.load(roles_f, object_pairs_hook=OrderedDict)

    users_f = open(users_file)
    users_json = json.load(users_f, object_pairs_hook=OrderedDict)

    realms_f = open(realms_file)
    realms_json = json.load(realms_f, object_pairs_hook=OrderedDict)

    change_upload_data()