from src.utils.constants import *
import base64
import binascii


class MongoDBMigrator:
  def migrate(self, datasource):
    host = datasource[PROPERTIES].pop(HOST, DEFAULT_EMPTY)
    port = datasource[PROPERTIES].pop(PORT, -1)

    if host != DEFAULT_EMPTY and port != -1:
      list_hosts = []
      list_hosts.append({HOST: host, PORT: port})
      datasource[PROPERTIES][LIST_HOSTS] = list_hosts

    username = datasource[PROPERTIES].pop(USERNAME, DEFAULT_EMPTY)
    password = datasource[PROPERTIES].pop(PASSWORD, DEFAULT_EMPTY)
    collections = datasource[PROPERTIES].get(COLLECTIONS, "")

    try:
      if password != DEFAULT_EMPTY:
        password = base64.decodestring(password)
    except binascii.Error:
      pass

    if username != DEFAULT_EMPTY and password != DEFAULT_EMPTY:
      list_credentials = []
      list_credentials.append(
        {DATABASE: "admin" if collections == "*.*" else DEFAULT_EMPTY, USERNAME: username, PASSWORD: password})
      datasource[PROPERTIES][LIST_CREDENTIALS] = list_credentials

    return datasource