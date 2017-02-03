
from convert_permission import convert_perms

test_permissions = [
    {
        "reports:#GET": [{"path": "/reports/**", "methods": ["GET"]}]
    },
    {
        "query-pipelines:#GET": [{"path": "/query-pipelines/**", "methods": ["GET"]}]
    },
    {
        "query-pipelines:getPipeline": [{"path": "/query-pipelines/*", "methods": ["GET"]}]
    },
    {
        "*": [{
            "methods": ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD'],
            "path": "/**"
        }]
    },
    {
        "query-pipelines:query:demo:collection=test": [{
            "methods": ["GET"],
            "path": "/query-pipelines/{id}/collections/{collection}/*",
            "params": {
                "id": ["demo"],
                "collection": ["test"]
            }
        }]
    },
    {
        "query-pipelines:getPipeline:demo": [{
            "methods": ["GET"],
            "path": "/query-pipelines/{id}",
            "params": {
                "id": ["demo"]
            }
        }]
    },
    {
        "query-pipelines:#GET:*:collection=demo": [{
            "methods": ["GET"],
            "path": "/query-pipelines/*/collections/{collection}/*",
            "params": {
                "collection": ["demo"]
            }
        }]
    }

]


def print_vars(a, b, c):
    print "Old permission:   {}".format(c)
    print "Expected {}. \n Got {}".format(a, b)

for permission in test_permissions:
    for old_permission, new_expected_permission in permission.items():
        new_permission = convert_perms(old_permission, "introspect.json")
        assert new_permission == new_expected_permission, print_vars(new_expected_permission, new_permission, old_permission)

