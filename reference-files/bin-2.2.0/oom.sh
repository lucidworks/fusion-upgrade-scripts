#!/bin/bash
#
# An -XX:OnOutOfMemoryError script for Fusion components

component=$1

BIN=`dirname "${BASH_SOURCE-$0}"`
SCRIPT=`basename "${BASH_SOURCE-$0}"`
export FUSION_HOME=`cd "${BIN}/.."; pwd`
PID_FILE="$FUSION_HOME/var/$component/$component.pid"
NOW=$(date +"%F%T")
LOG_FILE="$FUSION_HOME/var/log/$component/oom_killer-$NOW.log"
exec 1>$LOG_FILE
exec 2>&1

if ! (echo "$component" | egrep -q -e '^(solr|connectors|api|ui)$') then
  echo "invalid argument '$component'; should be solr, connectors api or ui"
  exit 1
fi

if [ ! -e "$PID_FILE" ]; then
  echo "No pid file $PID_FILE"
  exit 1
fi
PID=$(cat "$PID_FILE")

echo "Running OOM killer script for process $PID for Fusion $component"
kill -9 $PID
echo "Killed process $PID"
