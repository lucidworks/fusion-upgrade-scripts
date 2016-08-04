import re
import os

class VariablesHelper:

  FUSION_HOME = None
  FUSION_OLD_HOME = None
  FUSION_ZK = "FUSION_ZK"

  @staticmethod
  def ensure_fusion_home():

    VariablesHelper.FUSION_HOME = os.environ.get("FUSION_HOME")

    if VariablesHelper.FUSION_HOME is None:
      return False
    return True

  @staticmethod
  def ensure_old_fusion_home():

    VariablesHelper.FUSION_OLD_HOME = os.environ.get("FUSION_OLD_HOME")

    if VariablesHelper.FUSION_OLD_HOME is None:
      return False
    return True


  @staticmethod
  def get_variable(path, variable):
    with open(path) as config_data_file:
      data = config_data_file.read()
      result = re.search("{}=.+".format(variable), data)

      if result:
        return result.group(0).replace("{}=".format(variable), "").strip()
      else:
        return None

  @staticmethod
  def get_fusion_variable(variable):
    path = "{}/conf/config.sh".format(VariablesHelper.FUSION_HOME)
    return VariablesHelper.get_variable(path, variable)

  @staticmethod
  def get_fusion_version():
    path = "{}/fusion.build".format(VariablesHelper.FUSION_HOME)
    return VariablesHelper.get_variable(path, "fusion.version")

  @staticmethod
  def get_old_fusion_version():
    path = "{}/fusion.build".format(VariablesHelper.FUSION_OLD_HOME)
    return VariablesHelper.get_variable(path, "fusion.version")

  @staticmethod
  def get_fusion_zookeeper_host():
    zk_emsenble = VariablesHelper.get_fusion_variable(VariablesHelper.FUSION_ZK)
    result = zk_emsenble.split("/")
    return result[0]

  @staticmethod
  def get_fusion_zookeeper_node():
    zk_emsenble = VariablesHelper.get_fusion_variable(VariablesHelper.FUSION_ZK)
    result = zk_emsenble.split("/")
    return "" if len(result) <= 1 else "/{}".format(result[1])
