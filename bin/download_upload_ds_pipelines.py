import base64
import argparse
import datetime
import json
import os

from kazoo.client import KazooClient
import requests

parser = argparse.ArgumentParser(description="Upgrade an existing Fusion installation to 2.1")
parser.add_argument("--zk-connect", required=True, help="ZooKeeper connect string for Fusion")
parser.add_argument("--action", required=True, help="Action to be performed (download, upload)")
parser.add_argument("--fusion-url", default="http://localhost:8764/api/apollo", help="URL of the Fusion proxy server")
parser.add_argument("--fusion-username", default="admin", help="Username to use when authenticating to the Fusion application (should be an admin)")
parser.add_argument("--fusion-password", default="password123", help="Password for the given Fusion user")

def fusion_session(url, username, password):
    headers = {"Content-type": "application/json"}
    data = {'username': username, 'password': password}

    s = requests.Session()
    resp = s.post("{0}/session".format(url), data=json.dumps(data), headers=headers)
    assert resp.status_code == 201, "Should see 201 back from the proxy, but got: {}\n{}".format(resp.status_code, resp.content)
    return s

def dump_json_to_workspace(workspace, name, zk_path):
    """
    Copy the JSON objects out of ZK and into a file in the workspace
    """
    if zk.exists("/lucid/{0}".format(zk_path)) is None:
        json.dump([], open("{0}/{1}.json".format(workspace, name), "w"))
        return

    ids = zk.get_children("/lucid/{0}".format(zk_path))
    objects = []
    for id in ids:
        (node, stat) = zk.get("/lucid/{0}/{1}".format(zk_path, id))
        objects.append(json.loads(node))

    with open("{0}/{1}.json".format(workspace, name), "w") as fp:
        json.dump(objects, fp)

def delete_paths(paths):
    """
        Delete zkpaths
    """
    for path in paths:
        full_path = "/lucid/{}".format(path)
        if zk.exists(full_path):
            print("Removing zpath {}".format(full_path))
            zk.delete(full_path, recursive=True)

def upgrade_from_json(workspace, session, name, api_path):
    """
    Run the upgrade logic across the JSON objects from the files in the workspace
    """
    with open("{0}/{1}.json".format(workspace, name), "r") as fp:
        objects = json.load(fp)

    for obj in objects:
        # Special case for datasources since the payloads are base64 encoded and we need to decode before submitting them
        if name == "datasources":
            obj = decode_password_json(obj)
            resp = session.post("{0}/{1}".format(args.fusion_url, api_path),
                           data=json.dumps(obj), headers={"Content-Type": "application/json"})
            assert resp.status_code == 200, "Expected 200, got {}\n{} from url {}".format(resp.status_code, resp.content, resp.url)
        else:
            resp = session.put("{0}/{1}/{2}".format(args.fusion_url, api_path, obj['id']),
                               data=json.dumps(obj), headers={"Content-Type": "application/json"})
            assert resp.status_code == 200, "Expected 200, got {}\n{} from url {}".format(resp.status_code, resp.content, resp.url)


def decode_password_json(payload):
    if "properties" in payload:
        if "password" in payload["properties"]:
            # Decode and return the object
            payload["properties"]["password"] = base64.b64decode(payload["properties"]["password"])
        return payload


def download_data(workspace):
    # Create a workspace
    os.mkdir(workspace)
    now = datetime.datetime.now()
    with open("{0}/README".format(workspace), "w") as fp:
        fp.write("Workspace created on {0}".format(now.isoformat()))

    print("Using {} as a temporary workspace".format(workspace))

    # Dump the JSON data
    dump_json_to_workspace(workspace, "index-pipelines", "index-pipelines")
    dump_json_to_workspace(workspace, "index-stages", "index-stages")
    dump_json_to_workspace(workspace, "query-pipelines", "query-pipelines")
    dump_json_to_workspace(workspace, "query-stages", "query-stages")
    dump_json_to_workspace(workspace, "datasources", "connectors/datasources")

    # Delete after downloading
    delete_paths(["index-pipelines", "index-stages", "query-pipelines", "query-stages", "connectors/datasources"])


def upload_data(workspace, session):
    upgrade_from_json(workspace, session, "index-pipelines", "apollo/index-pipelines")
    upgrade_from_json(workspace, session, "index-stages", "apollo/index-stages/instances")
    upgrade_from_json(workspace, session, "query-pipelines", "apollo/query-pipelines")
    upgrade_from_json(workspace, session, "query-stages", "apollo/query-stages/instances")
    upgrade_from_json(workspace, session, "datasources", "apollo/connectors/datasources")


if __name__ == "__main__":
    args = parser.parse_args()

    # Connect to ZK
    zk = KazooClient(hosts=args.zk_connect, read_only=True)
    zk.start()

    ws_name = "fusion_upgrade_2.1"
    action = args.action

    if action == "download":
        print("Downloading pipelines, stages and datasource")
        download_data(ws_name)
    elif action == "upload":
        # Start a new Fusion session
        session = fusion_session(args.fusion_url, args.fusion_username, args.fusion_password)

        print("Uploading pipelines, stages and datasource payloads")
        upload_data(ws_name, session)

