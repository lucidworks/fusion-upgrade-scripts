from src.utils.constants import *

class HadoopMigrator:
  def migrate(self, datasource):
    properties = datasource[PROPERTIES]
    job_jar_args = properties.pop(JOB_JAR_ARGS, DEFAULT_EMPTY)
    job_jar_args_list = job_jar_args.split()
    index = 1
    size = len(job_jar_args_list)
    mapper_args = []

    while index < size:
      key = job_jar_args_list[index]
      if key.startswith(DASH_D):
        if COMMIT_CLOSE in key or PIPELINE_URI in key:
          index += 1
          continue
        splitted = key.split(EQUAL)
        argument = {"arg_name": splitted[0][2:], "arg_value": splitted[1]}
        mapper_args.append(argument)
      elif key.startswith(DASH):
        value = job_jar_args_list[index + 1]
        if key == DASH_I:
          properties[HADOOP_INPUT] = value
        if key == DASH_CLS:
          if value == DIRECTORY_INGEST_MAPPER:
            properties[HADOOP_MAPPER] = DIRECTORY
          if value == CSV_INGEST_MAPPER:
            properties[HADOOP_MAPPER] = CSV
          if value == GROK_INGEST_MAPPER:
            properties[HADOOP_MAPPER] = GROK
          if value == REGEX_INGEST_MAPPER:
            properties[HADOOP_MAPPER] = REGEX
          if value == SEQUENCE_FILE_INGEST_MAPPER:
            properties[HADOOP_MAPPER] = SEQUENCE_FILE
          if value == SOLR_INGEST_MAPPER:
            properties[HADOOP_MAPPER] = SOLR_XML
          if value == WARC_INGEST_MAPPER:
            properties[HADOOP_MAPPER] = WARC
          if value == ZIP_INGEST_MAPPER:
            properties[HADOOP_MAPPER] = ZIP
        index += 1
      index += 1

    if len(mapper_args) > 0:
      properties[MAPPER_ARGS] = mapper_args

    run_kinit = bool(properties.pop(RUN_KINIT, False))
    kinit_user = properties.pop(KINIT_USER, DEFAULT_EMPTY)
    kinit_cache = properties.pop(KINIT_CACHE, DEFAULT_EMPTY)
    kinit_keytab = properties.pop(KINIT_KEYTAB, DEFAULT_EMPTY)

    if run_kinit:
      properties[KINIT_CACHE] = kinit_cache
      properties[KINIT_PRINCIPAL] = kinit_user
      properties[KINIT_KEYTAB] = kinit_keytab

    datasource[PROPERTIES] = properties
    return datasource
