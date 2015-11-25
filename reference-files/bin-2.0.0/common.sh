
if [ -z "$SCRIPT" ]; then echo "SCRIPT not set"; exit 1; fi
if [ -z "$FUSION_HOME" ]; then echo "FUSION_HOME not set"; exit 1; fi

# declare some arrays that get defined in config.sh
declare -a CONNECTORS_JAVA_OPTIONS
declare -a UI_JAVA_OPTIONS
declare -a SOLR_JAVA_OPTIONS
declare -a API_JAVA_OPTIONS
declare -a JAVA_OPTIONS
declare -a GC_TUNE
declare -a GC_LOG_OPTS

# port definitions are stored in config.sh
CONFIG_FILE="$FUSION_HOME/bin/config.sh"
if [ -f "$CONFIG_FILE" ]; then
  source "$CONFIG_FILE"
else
  echo "missing $CONFIG_FILE"
  exit 1
fi

DATEFORMAT="+%Y-%m-%d %H:%M:%SZ"
function output() {
  echo $(date -u "$DATEFORMAT") "$1"
}

function check_jetty_vars() {
  if [ -z "$FUSION_SERVICE_NAME" ]; then echo "FUSION_SERVICE_NAME not set"; exit 1; fi
  if [ -z "$PID_FILE" ]; then echo "PID_FILE not set"; exit 1; fi
  if [ -z "$LOG_DIR" ]; then echo "LOG_DIR not set"; exit 1; fi
}

function do_start() {
  check_java
  check_jetty_vars

  if [ ! -d "$LOG_DIR" ]; then
    output "Missing log dir '$LOG_DIR'; re-creating"
    if ! mkdir -p "$LOG_DIR"; then
      output "failed to create '$LOG_DIR'"
      exit 1
    fi
  fi

  if [ -f "$PID_FILE" ]; then
    pid=`cat "${PID_FILE}"`
    if kill -0 $pid &>/dev/null ; then
      output "process $pid from pid file $PID_FILE is running; not starting"
      return
    fi
  fi

  report_port "Starting"
  nohup "$FUSION_HOME/bin/$SCRIPT" "run" > "$LOG_DIR/run.out" 2>&1 </dev/null &
}

function do_status() {
  check_jetty_vars
  if [ -f "$PID_FILE" ]; then
    pid=`cat "${PID_FILE}"`
    if kill -0 $pid &>/dev/null; then
      output "process $pid from pid file $PID_FILE is running"
    else
      output "process $pid from pid file $PID_FILE is not running"
    fi
  else
    output "no pid file $PID_FILE"
  fi
}

function do_stop() {
  check_jetty_vars
  check_java
  extra_java_options

  if [ ! -f "$PID_FILE" ]; then
    output "no pid file $PID_FILE"
    return
  fi

  pid=`cat "${PID_FILE}"`
  if ! kill -0 $pid &>/dev/null ; then
    output "process $pid from pid file $PID_FILE is not running"
    rm "$PID_FILE"
    return
  fi

  output "Stopping $FUSION_SERVICE_NAME on port $HTTP_PORT"

  TRIED_JETTY_SHUTDOWN=""
  if [ ! -z "$JETTY_HOME" ]; then
    if "$JAVA" \
      "${JAVA_OPTIONS[@]}" \
      "-DSTOP.PORT=$STOP_PORT" \
      "-DSTOP.KEY=$STOP_KEY" \
      -jar "$JETTY_HOME/start.jar" \
      "jetty.home=$JETTY_HOME" \
      "jetty.base=$JETTY_BASE" \
      "$JETTY_BASE/etc/jetty-logging.xml" \
      "--stop" ; then
      sleep 6 # give the process time to exit after shutting the port
      TRIED_JETTY_SHUTDOWN=yes
    fi
  fi

  if kill -0 $pid &>/dev/null ; then
    if [ ! -z "$TRIED_JETTY_SHUTDOWN" ]; then
      output "process $pid from pid file $PID_FILE is running. Sending TERM signal"
    fi
    kill $pid
    sleep 5
    if kill -0 $pid &>/dev/null ; then
      output "process $pid from pid file $PID_FILE is still running. Sending KILL signal"
      kill -9 $pid &>/dev/null
      sleep 1
    fi
  fi
  if [ -f "$PID_FILE" ]; then
    rm "$PID_FILE"
  fi
}

function do_usage() {
  echo "Usage: $0 [start, stop, status, restart, run]"
  exit 1
}

function set_ports() {
  case "$PORT_NAME" in
    'api')
      HTTP_PORT=$API_PORT;
      STOP_PORT=$API_STOP_PORT;
      STOP_KEY=$API_STOP_KEY
      ;;
    'connectors')
      HTTP_PORT=$CONNECTORS_PORT;
      STOP_PORT=$CONNECTORS_STOP_PORT;
      STOP_KEY=$CONNECTORS_STOP_KEY
      ;;
    'solr')
      HTTP_PORT=$SOLR_PORT;
      STOP_PORT=$SOLR_STOP_PORT;
      STOP_KEY=$SOLR_STOP_KEY
      ;;
    'ui')
      HTTP_PORT=$UI_PORT;
      STOP_PORT=$UI_STOP_PORT;
      STOP_KEY=$UI_STOP_PORT
      ;;
    'spark-master')
      HTTP_PORT=$SPARK_MASTER_PORT
      ;;
    'spark-worker')
      HTTP_PORT=$SPARK_WORKER_PORT
      ;;
    'zookeeper')
      HTTP_PORT=$ZOOKEEPER_PORT
      ;;
    '')
      echo "PORT_NAME not set";
      exit 1
      ;;
  esac
}

function report_port() {
  msg="$1"
  if [ -z "$msg" ]; then
    msg="Running"
  fi
  output "$msg $FUSION_SERVICE_NAME on port $HTTP_PORT"
}

function check_java() {
  if [ -z "$JAVA_HOME" ]; then
    if ! JAVA=$(command -v java) ; then
      output "cannot find the java command. Install Oracle Java, adjust your PATH, or set JAVA_HOME."
      exit 1
    fi
  else
    JAVA="$JAVA_HOME/bin/java"
    if ! test -x "$JAVA" ; then
      echo "JAVA_HOME is set to $JAVA_HOME, but there is no $JAVA"
      exit 1
    fi
  fi
  JAVA_VERSION=$($JAVA -version 2>&1 | head -n 1 | sed 's/.* version "//' | sed 's/"$//' | sed 's/_.*//')
  if [ -z "$JAVA_VERSION" ]; then
    output "Cannot determine java version"
    exit 1
  fi
  JAVA_MAJOR=$(echo "$JAVA_VERSION" | sed 's/\..*//')
  if !(echo "$JAVA_MAJOR" | egrep -q '^[0-9]+$') ; then output "Cannot determine java major version"; exit 1; fi
  JAVA_MINOR=$(echo "$JAVA_VERSION" | sed 's/^[0-9].//' | sed 's/\..*//')
  if !(echo "$JAVA_MINOR" | egrep -q '^[0-9]+$') ; then output "Cannot determine java minor version"; exit 1; fi
  if (( "$JAVA_MAJOR" == "1"  )) && (( "$JAVA_MINOR" < 7 )) ; then
    output "This product requires at least Java 1.7"
    exit 1
  fi
}

function write_pid_file() {
    echo $$ > "$PID_FILE"
}

function extra_java_options() {

  # Workaround LUCENE-5212 per https://wiki.apache.org/lucene-java/JavaBugs
  JAVA_VERSION=$($JAVA -version 2>&1 | head -n 1 | sed 's/.* version "//' | sed 's/"$//' | sed 's/_.*//')
  if [ $JAVA_VERSION = '1.7.0' ]; then
    # Specific Java version hacking
    GC_TUNE=(-XX:CMSFullGCsBeforeCompaction=1 -XX:CMSTriggerPermRatio=80)
    PATCH_LEVEL=$($JAVA -version 2>&1 | head -n 1 | sed 's/.* version "//' | sed 's/"$//' | sed 's/^.*_//')
    if (( $PATCH_LEVEL >= 40 )) && (( $PATCH_LEVEL < 60 )); then
      JAVA_OPTIONS=("${JAVA_OPTIONS[@]}" "-XX:-UseSuperWord")
    fi
  fi

  # strip MaxPermSize for java 1.8
  if (( "$JAVA_MAJOR" == "1" )) && (( "$JAVA_MINOR" > 7 )); then
    # replace this option with the empty string
    JAVA_OPTIONS=("${JAVA_OPTIONS[@]/-XX:MaxPermSize=*}")
  fi
  # combine java options
  JAVA_OPTIONS=("${JAVA_OPTIONS[@]}" "${GC_TUNE[@]}" "${GC_LOG_OPTS[@]}" "-Xloggc:$LOG_DIR/gc.log")
  # strip empty options
  STRIPPED_JAVA_OPTIONS=()
  for (( i=0; i<${#JAVA_OPTIONS[@]}; i++ ));
  do
    if [ ! -z "${JAVA_OPTIONS[$i]}" ]; then
      STRIPPED_JAVA_OPTIONS[$i]="${JAVA_OPTIONS[$i]}"
    fi
  done
  JAVA_OPTIONS=("${STRIPPED_JAVA_OPTIONS[@]}")
}

function main() {
  arg="$1"
  cd "$FUSION_HOME"
  set_ports
  if [ "$arg" = "start" ]; then
    do_start
  elif [ "$arg" = "stop" ]; then
    do_stop
  elif [ "$arg" = "restart" ]; then
    do_stop
    sleep 1
    do_start
  elif [ "$arg" = "status" ]; then
    do_status
  elif [ "$arg" = "run" ]; then
    do_run
  elif [ "$arg" = "help" ]; then
    do_usage
  elif [ -z "$arg" ]; then
    do_run
  else
    echo "Unknown action: $arg"
    do_usage
  fi
}
