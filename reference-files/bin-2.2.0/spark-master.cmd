@echo off

IF "%OS%"=="Windows_NT" setlocal enabledelayedexpansion enableextensions

set SDIR=%~dp0
IF "%SDIR:~-1%"=="\" set SDIR=%SDIR:~0,-1%
set FUSION_HOME=%SDIR%\..
pushd %FUSION_HOME%
set FUSION_HOME=%CD%
popd

IF "%FUSION_COMMON%"=="" set "FUSION_COMMON=%FUSION_HOME%\conf\config.cmd"
IF EXIST "%FUSION_COMMON%" CALL "%FUSION_COMMON%"

@REM --------------------------------------------------------------------------------------
@REM Define service specific vars here needed (after importing common vars)
@REM --------------------------------------------------------------------------------------
set SERVICE_PORT=%SPARK_MASTER_PORT%
set "JAVA_OPTIONS=-Djava.net.preferIPv4Stack=true -Xmx512m -Dapple.awt.UIElement=true"

set "JETTY_BASE=%FUSION_HOME%\jetty\api"
set "LOG_DIR=%FUSION_HOME%\var\log\spark-master"
set FUSION_SERVICE_NAME=Fusion Spark Master
set "APP_DIR=%FUSION_HOME%\apps\spark"
set "SPARK_HOME=%FUSION_HOME%\apps\spark-dist"
set "HADOOP_HOME=%FUSION_HOME%\apps\spark\hadoop"

goto check_java

:check_java
IF DEFINED SOLR_JAVA_HOME set "JAVA_HOME=%SOLR_JAVA_HOME%"

REM Try to detect JAVA_HOME from the registry
IF NOT DEFINED JAVA_HOME (
 FOR /F "skip=2 tokens=2*" %%A IN ('REG QUERY "HKLM\Software\JavaSoft\Java Development Kit" /v CurrentVersion') DO set CurVer=%%B
 FOR /F "skip=2 tokens=2*" %%A IN ('REG QUERY "HKLM\Software\JavaSoft\Java Development Kit\!CurVer!" /v JavaHome') DO (
   set JAVA_HOME=%%B
   @echo Detected JAVA_HOME=%%B
 )
)

IF NOT DEFINED JAVA_HOME goto need_java_home
set JAVA_HOME=%JAVA_HOME:"=%
@rem Remove trailing slash from JAVA_HOME if found
if "%JAVA_HOME:~-1%"=="\" SET JAVA_HOME=%JAVA_HOME:~0,-1%

if "%JAVA_HOME:~-1%"==" " SET JAVA_HOME=%JAVA_HOME:~0,-1%
set "JAVA=%JAVA_HOME%\bin\java.exe"
set "JAVAW=%JAVA_HOME%\bin\javaw.exe"
if not exist "%JAVA%" (
  @echo "%JAVA% does not exist; perhaps is your JAVA_HOME set wrong"
  goto done
)

set JAVAVER=
set JAVA_MAJOR=
set JAVA_BUILD=0
"%JAVA%" -version 2>&1 | findstr /i "version" > "%FUSION_HOME%\var\javavers" 
set /p JAVAVEROUT=<"%FUSION_HOME%\var\javavers"
del "%FUSION_HOME%\var\javavers"
for /f "tokens=3" %%g in ("!JAVAVEROUT!") do (
  set JAVAVER=%%g
  set JAVAVER=!JAVAVER:"=!
  for /f "delims=_ tokens=1-3" %%v in ("!JAVAVER!") do (
    set JAVA_MAJOR=!JAVAVER:~0,3!
    set /a JAVA_BUILD=%%w
  )
  for /f "delims=. tokens=2" %%g in ("!JAVA_MAJOR!") do (
    set /a JAVA_MINOR=%%g
  )
)
IF !JAVA_MINOR! LEQ 6 (
   goto need_java_vers
)
IF !JAVA_MINOR!==7 (
   set "JAVA_OPTIONS=!JAVA_OPTIONS! !MAX_PERM!"
)
IF "!JAVA_MAJOR!"=="1.7" (
  IF !JAVA_BUILD! GEQ 40 (
    IF !JAVA_BUILD! LEQ 51 (
      set "JAVA_OPTIONS=!JAVA_OPTIONS! -XX:-UseSuperWord"
      @echo WARNING: Java version !JAVAVER! has known bugs with Lucene and requires the -XX:-UseSuperWord flag. Please consider upgrading your JVM.
    )
  )
)

goto run_script

:run_script
IF [%1]==[] goto do_usage
IF "%1"=="-help" goto do_usage
IF "%1"=="/?" goto do_usage
IF "%1"=="start" goto do_safe_start
IF "%1"=="stop" goto do_stop
IF "%1"=="restart" goto do_restart
IF "%1"=="status" goto do_status
@echo ERROR: %1 not supported!
goto do_usage

:do_safe_start
For /f "tokens=5" %%j in ('netstat -aon ^| find "TCP " ^| find ":%SERVICE_PORT% "') do (
  IF NOT "%%j"=="0" (
    set "SCRIPT_ERROR=Process %%j is already listening on port %SERVICE_PORT%. If this is %FUSION_SERVICE_NAME%, please stop it first before starting (or use restart). If this is not %FUSION_SERVICE_NAME%, then please choose a different port."
    echo !SCRIPT_ERROR!
    exit /B 1
  )
)

if NOT EXIST "%LOG_DIR%" mkdir "%LOG_DIR%"

goto do_start

@REM --------------------------------------------------------------------------------------
@REM Start the Spark Master
@REM --------------------------------------------------------------------------------------
:do_start
set SPARK_MASTER_OPTS=!JAVA_OPTIONS! -Dcurator.zk.connect=%FUSION_ZK% -Dlog4j.configurationFile=file:"%APP_DIR%\conf\spark-master-log4j2.xml"
set SPARK_MASTER_OPTS=%SPARK_MASTER_OPTS% -Dfusion.spark.master.port=%SPARK_MASTER_PORT% -Dfusion.spark.master.ui.port=%SPARK_MASTER_UI_PORT%
set SPARK_MASTER_OPTS=%SPARK_MASTER_OPTS% -Dapollo.home="%FUSION_HOME%" -Dspark.home="%SPARK_HOME%" -Xloggc:"!LOG_DIR!"\gc_!SCRIPT_DATETIME!.log

START /B "%FUSION_SERVICE_NAME%" /D"%FUSION_HOME%" "%JAVAW%" -DSparkAgentVarDir="%FUSION_HOME%\var\spark-master" ^
-classpath "%APP_DIR%\lib\*" com.lucidworks.spark.SparkAgent "%APP_DIR%\bin\spark-master.bat"  > "%LOG_DIR%\run.out"

goto done

:do_status
For /f "tokens=5" %%j in ('netstat -aon ^| find "TCP " ^| find ":%SERVICE_PORT% "') do (
  IF NOT "%%j"=="0" (
    set SERVICE_PID=%%j
  )
)
IF [!SERVICE_PID!]==[] (
  echo %FUSION_SERVICE_NAME% not running
) ELSE (
  echo %FUSION_SERVICE_NAME% running on port %SERVICE_PORT% [pid: !SERVICE_PID!]
)
goto done

:do_stop

@REM Get the PID of the spark-master agent process
set AGENT_PID=0
For /F "Delims=" %%J In ('type "%FUSION_HOME%\var\spark-master\spark-master.pid"') do set AGENT_PID=%%~J
IF NOT "!AGENT_PID!"=="0" (
  taskkill /t /f /pid !AGENT_PID! > nul 2>&1
)
del "%FUSION_HOME%\var\spark-master\spark-master.pid"

@REM this is a standalone app, not Jetty, so STOP ports aren't an option.
For /f "tokens=5" %%j in ('netstat -aon ^| find "TCP " ^| find ":%SERVICE_PORT% "') do (
  IF NOT "%%j"=="0" (
    taskkill /t /f /pid %%j > nul 2>&1
  )
)
goto after_stop

:do_restart
goto do_stop

:do_usage
@echo.
@echo Usage: %0 [start, stop, restart, status]
goto done

:after_stop
IF "%1"=="restart" goto do_safe_start
goto done

:need_java_home
@echo Please set the JAVA_HOME environment variable to the path where you installed Java 1.7+
goto done

:need_java_vers
@echo Java 1.7 or later is required to run Fusion.
goto done

:done

ENDLOCAL
