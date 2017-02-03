#!/usr/bin/env python
"""
   Script to convert user-information in ZK to compatible format in 1.4
"""
import argparse
import logging
import json

FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def convert_old_permissions(service_name, method_names, params, type_method_http=True):
    """
        Method to convert old permissions from 1.2.x and 1.3 to the new format in 1.4
        Examples:

           Permission format in 1.4

                1. [{
                   'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']
                   'path': '/**'
                }]

                2. [
                        {   'methods': ['GET'], u'path': '/system/**'},
                        {   'methods': ['GET'], u'path': '/history/**'},
                        {   'methods': ['GET'], u'path': '/connectors/**'},
                        {   'methods': ['PUT'], u'path': '/usage/**'},
                        {   'methods': ['GET'], u'path': '/reports/**'},
                        {   'methods': ['GET'], u'path': '/solrAdmin/**'},
                        {   'methods': ['GET'], u'path': '/nodes/**'},
                        {   'methods': ['POST'], u'path': '/reports/**'},
                        {   'methods': ['GET'], u'path': '/collections/**'},
                        {   'methods': ['PATCH'],
                            'params': { 'id': ['#ID']},
                            'path': u'/users/{id}'
                        },
                        {   'methods': ['GET'], 'path': '/searchCluster/**'}
                  ]

           Permission format prior to 1.4

              1. ['*']

              2. [
                     'solrAdmin,searchCluster,nodes,hosts,collections,history,reports,system,connectors:#GET',
                     'reports:#POST',
                     'usage:#PUT',
                     'users:#PATCH:#ID'
                 ]


        TODO: Can 'method_names' be null ?
        Handle permissions with '*' as service_name in another method that invokes this method
    """
    new_format = {'methods': [], 'path': None}
    logger.debug("Converting old permission: service: {0}, method: {1}, params: {2}".format(service_name, method_names, params))
    if service_name != "users" and service_name != "*":
        service_info = get_service_info_from_introspect(service_name)
        if service_info is not None:
            root_uri = service_info['uri']
            if method_names == ['*'] and params is None:
                new_format['methods'] = all_methods
                new_format['path'] = "{}/**".format(root_uri)
                return new_format
            else:
                if method_names == ['*']:
                    method_names = all_methods
                    logger.debug("Modified method_names to '{}'".format(method_names))
                if type_method_http:
                    # Deal with the http verb methods
                    if params is None:
                        for method in method_names:
                            new_format['methods'].append(method)
                            new_format['path'] = "{}/**".format(root_uri)
                        return new_format
                    else:
                        # Handle permissions with http method and params
                        verb_methods = service_info.get("verb_methods")
                        logger.debug("verb methods are {}".format(verb_methods))
                        perms = []
                        for verb_name in method_names:
                            logger.debug("looking up method '{}' in service '{}'".format(verb_name, service_name))
                            methods = verb_methods.get(verb_name)
                            logger.debug("Verb info for method '{}' in service '{}' is {}".format(verb_name, service_name, methods))
                            if methods is not None:
                                for method_info in methods:
                                    logger.debug("Method info for method '{}' is {}".format(verb_name, method_info))
                                    matched_atleast_one_param = False
                                    path = method_info["uri"]
                                    if "pathParams" in method_info and len(method_info.get("pathParams")) > 0:
                                        replace_params_with_wildcard = []
                                        all_params = []
                                        for each_param in method_info["pathParams"]:
                                            all_params.append(each_param["name"])
                                        set_params = frozenset(params)
                                        set_all_methods = frozenset(all_params)
                                        # Make sure atleast one param has an intersection
                                        if not set_params.isdisjoint(set_all_methods):
                                            matched_atleast_one_param = True
                                            replace_params_with_wildcard = set_all_methods.difference(set_params)
                                            for param_name in set_params:
                                                if params[param_name] == ["*"]:
                                                    path = path.replace("{" + param_name + "}", "*")

                                        if matched_atleast_one_param:
                                            for non_matched_param in replace_params_with_wildcard:
                                                path = path.replace("{" + non_matched_param + "}", "*")
                                            perms.append({"methods": [verb_name], "path": path, "params": params})

                        return perms
                else:
                    # Deal with actual resource method names from introspect
                    perms = []
                    for method_info in service_info.get("methods"):
                        if method_info["name"] in method_names:
                            logger.debug("Evaluating method {}".format(method_info["name"]))
                            verb_name = method_info["verb"]
                            path = method_info["uri"]
                            matched_atleast_one_param = False
                            if "pathParams" in method_info and len(method_info.get("pathParams")) > 0:
                                replace_params_with_wildcard = []
                                all_params = []
                                # Get all path params for this method
                                for each_param in method_info["pathParams"]:
                                    all_params.append(each_param["name"])
                                if params is not None:
                                    set_params = frozenset(params)
                                    set_all_methods = frozenset(all_params)
                                    # Make sure params have an intersection
                                    if not set_params.isdisjoint(set_all_methods):
                                        matched_atleast_one_param = True
                                        replace_params_with_wildcard = set_all_methods.difference(set_params)
                                        for param_name in set_params:
                                            if params[param_name] == ["*"]:
                                                path = path.replace("{" + param_name + "}", "*")
                                else:
                                    replace_params_with_wildcard = all_params
                                if matched_atleast_one_param or params is None:
                                    for non_matched_param in replace_params_with_wildcard:
                                        path = path.replace("{" + non_matched_param + "}", "*")
                                    if params is not None:
                                        perms.append({"methods": [verb_name], "path": path, "params": params})
                                    else:
                                        perms.append({"methods": [verb_name], "path": path})
                            else:
                                perms.append({"methods": [verb_name], "path": path})
                    return perms
        else:
            logger.warn("Could not find service name '{}' in the introspect".format(service_name))
            return []
    elif service_name == "*":
        for method in method_names:
            new_format['methods'].append(method)
        new_format['path'] = global_path
        return new_format
    elif service_name == "users" and method_names == ["PATCH"] and params == {"id": ["#ID"]}:
        return {"methods": ["PATCH"], "params": {"id": ['#ID']}, "path": "/users/{id}"}
    elif service_name == "users" and method_names == ["PATCH"]:
        logger.error("No params specified with the permission. {}:{}".format(service_name, method_names))


def get_service_info_from_introspect(service_name):
    service_name = "{}::v1".format(service_name)
    if service_name in introspect:
        service_info = introspect.get(service_name)
        return service_info
    else:
        return None


def get_introspect_data(filename):
    f = open(filename)
    global introspect
    introspect = json.load(f)
    introspect["{}::v1".format("searchAppPrefs")] = search_app_prefs
    for service_name in introspect:
       # Re-format the methods so that the uri's can be accessed via verb's
        introspect[service_name]["verb_methods"] = reformat_methods_in_service(introspect[service_name])
        introspect[service_name]["method_names"] = reformat1_methods_in_service(introspect[service_name])
    return introspect


def reformat_methods_in_service(service_info):
    methods = {}
    for method_info in service_info["methods"]:
        verb = method_info.get("verb")
        payload = {"uri": method_info.get("uri"), "pathParams": method_info.get("pathParams")}
        if verb in methods:
            methods[verb].append(payload)
        else:
            methods[verb] = [payload]
    return methods


def reformat1_methods_in_service(service_info):
    methods = {}
    for method_info in service_info["methods"]:
        method_name = method_info.get("name")
        methods[method_name] = method_info
    return methods


def parse_old_permission(perm):
    split_values = perm.split(":")
    len_values = len(split_values)
    logger.debug("Parsing old permission: {}".format(perm))
    if len_values == 1 and split_values[0] == '*':
        return [{'methods': all_methods, 'path': global_path}]
    elif len_values == 1:
        services = split_values[0]
        converted_perms = []
        for service in services.split(","):
            converted_perm = convert_old_permissions(service, None, None)
            converted_perms.append(converted_perm)
        return converted_perms
    elif len_values >= 2:
        converted_perms = []
        services = split_values[0]
        method = split_values[1]
        type_methods_http = False
        if method is None or method == '':
            method = '*'

        if len_values == 2:
            for service in services.split(","):
                method_splits = method.split(",")
                for method in method_splits:
                    if method is None or method == '':
                        continue
                    method_name, type_methods_http = check_each_method(method)

                    converted_perm = convert_old_permissions(service, [method_name], None, type_method_http=type_methods_http)
                    if converted_perm is not None:
                        if isinstance(converted_perm, list):
                            converted_perms = converted_perms + converted_perm
                        else:
                            converted_perms.append(converted_perm)
            return converted_perms
        elif len_values == 3 or len_values == 4:
            params = dict()
            # TODO: Would it be possible to have a permission `collections,query-pipelines:#GET:demo` ?
            if split_values[2] is None or split_values[2] == "":
                split_values[2] = "*"
            if len_values == 4:
                split_params = split_values[3].split(" ")
                if split_params is not None:
                    for split_param in split_params:
                        if len(split_param.split("=")) > 1:
                            param_name = split_param.split("=")[0]
                            param_values = split_param.split("=")[1].split(",")
                            params[param_name] = param_values
            for service in services.split(","):
                if service in id_mappings:
                    if service is None or service == '':
                        continue
                    # Give priority if a value is defined on the params explicitly
                    if id_mappings.get(service) not in params:
                        if split_values[2] == '' or split_values[2] is None:
                            params[id_mappings.get(service)] = ['*']
                        else:
                            params[id_mappings.get(service)] = split_values[2].split(",")
                else:
                    logger.warn("Unknown id entity  '{}' for service '{}'. Permission string '{}'".format(split_values[2], service, perm))
                method_splits = method.split(",")
                for method in method_splits:
                    if method is None or method == '':
                        continue
                    method_name, type_methods_http = check_each_method(method)
                    converted_perm = convert_old_permissions(service, [method_name], params, type_method_http=type_methods_http)
                    if converted_perm is not None:
                        if isinstance(converted_perm, list):
                            converted_perms = converted_perms + converted_perm
                        else:
                            converted_perms.append(converted_perm)
            return converted_perms


def check_each_method(method_name):
    if method_name[0] == "#":
        return method_name[1:], True
    elif method_name == "*":
        return method_name, True
    else:
        return method_name, False


def convert_perms(old_perm, introspect_filename):
    global introspect
    introspect = get_introspect_data(introspect_filename)
    converted_perms = parse_old_permission(old_perm)

    for converted_perm in converted_perms:
        logger.debug("Converted perm is {}".format(converted_perm))
        if 'params' in converted_perm:
            param_to_remove = []
            for param in converted_perm["params"]:
                if converted_perm["params"][param] == ["*"]:
                    param_to_remove.append(param)
            index = converted_perms.index(converted_perm)
            for param in param_to_remove:
                del converted_perms[index]['params'][param]
    return converted_perms


# TODO: Special handling of 'search' role and the uri '/prefs/apps/search/*' is needed for 'search', 'admin' role
"""
    GET /prefs/apps/search/* is for read-only search users
    POST, PUT /prefs/apps/search/* for search, collection-admin roles
"""

id_mappings = {
    "configurations": "key",
    "reports": "report",
    "features": "feature",
    "history": "item",
    "introspect": "service",
    "blobs": "id",
    "collections": "collection",
    "query-stages": "id",
    "query-pipelines": "id",
    "index-pipelines": "id",
    "scheduler": "id",
    "usage": "key",
    "searchCluster": "id",
    "index-profiles": "alias",
    "query-profiles": "alias",
    "users": "id",
    "searchAppPrefs": "id"
}

all_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']
global_path = "/**"
introspect = None

search_app_prefs = {
    "name": "searchAppPrefs",
    "uri": "/prefs",
    "methods": [ {
        "uri": "/prefs/apps/search",
        "name": "getSearchAppPrefs",
        "verb": "GET",
        "pathParams": [],
        "queryParams": []
    }, {
        "uri": "/prefs/apps/search/{id}",
        "name": "getSearchAppPref",
        "verb": "GET",
        "pathParams": [{
            "name": "id",
            "type": "String"
        }],
        "queryParams": []
    }, {
        "uri": "/prefs/apps/search",
        "name": "createSearchAppPref",
        "verb": "POST",
        "pathParams": [],
        "queryParams": []
    }, {
        "uri": "/prefs/apps/search/{id}",
        "name": "updateSearchAppPref",
        "verb": "PUT",
        "pathParams": [{
            "name": "id",
            "type": "String"
                       }],
        "queryParams": []
    }, {
        "uri": "/prefs/apps/search/{id}",
        "name": "deleteSearchAppPref",
        "verb": "DELETE",
        "pathParams": [{
             "name": "id",
             "type": "String"
                       }],
        "queryParams": []
    }
    ]
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert permission from 1.2 to 1.4 format. Example: 'reports:#POST'")
    parser.add_argument('introspect_filename', type=str, help="The filename with introspect JSON")
    parser.add_argument('old_permission', type=str, help="The permission format prior to 1.4. Example: 'reports:#POST'")
    args = parser.parse_args()

    old_permission = args.old_permission
    introspect_filename = args.introspect_filename
    logger.info("old permission: '{}' ".format(old_permission))
    logger.info("New permissions after conversion: \n {}".format(convert_perms(old_permission, introspect_filename)))
