from src.utils.constants import *

class DummyMigrator:

  # datasource is a dictionary type in python.
  def migrate(self, datasource):
    collection = datasource[PROPERTIES].get(COLLECTION, None)

    # Update without modifications
    datasource[PROPERTIES][COLLECTION] = collection

    return datasource
