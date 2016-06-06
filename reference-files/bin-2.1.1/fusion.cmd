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
goto check_java

:do_start
@echo.
echo Starting Fusion ZooKeeper on port %ZOOKEEPER_PORT%
CALL "%FUSION_HOME%\bin\zookeeper.cmd" start
timeout /T 10
@echo.
echo Starting Fusion Solr on port %SOLR_PORT%
CALL "%FUSION_HOME%\bin\solr.cmd" start
timeout /T 25
@echo.
echo Starting Fusion Spark Master Service on port %SPARK_MASTER_PORT%
CALL "%FUSION_HOME%\bin\spark-master.cmd" start
timeout /T 1
@echo.
echo Starting Fusion Spark Worker Service on port %SPARK_WORKER_PORT%
CALL "%FUSION_HOME%\bin\spark-worker.cmd" start
timeout /T 1
@echo.
echo Starting Fusion API Service on port %API_PORT%
CALL "%FUSION_HOME%\bin\api.cmd" start
timeout /T 5
@echo.
echo Starting Fusion UI Service on port %UI_PORT%
CALL "%FUSION_HOME%\bin\ui.cmd" start
timeout /T 5
@echo.
echo Starting Fusion Connectors Service on port %CONNECTORS_PORT%
CALL "%FUSION_HOME%\bin\connectors.cmd" start
timeout /T 5
goto done

:do_restart
goto do_stop

:do_stop
@echo.
echo Stopping Fusion UI Service on port %UI_PORT%
CALL "%FUSION_HOME%\bin\ui.cmd" stop
@echo.
timeout /T 5
echo Stopping Fusion Connectors Service on port %CONNECTORS_PORT%
CALL "%FUSION_HOME%\bin\connectors.cmd" stop
@echo.
echo Stopping Fusion API Service on port %API_PORT%
CALL "%FUSION_HOME%\bin\api.cmd" stop
@echo.
timeout /T 5
echo Starting Fusion Spark Master Service on port %SPARK_MASTER_PORT%
CALL "%FUSION_HOME%\bin\spark-master.cmd" stop
@echo.
echo Starting Fusion Spark Worker Service on port %SPARK_WORKER_PORT%
CALL "%FUSION_HOME%\bin\spark-worker.cmd" stop
@echo.
echo Stopping Fusion Solr on port %SOLR_PORT%
CALL "%FUSION_HOME%\bin\solr.cmd" stop
timeout /T 5
echo Stopping Fusion ZooKeeper on port %ZOOKEEPER_PORT%
CALL "%FUSION_HOME%\bin\zookeeper.cmd" stop
goto after_stop

:do_status
CALL "%FUSION_HOME%\bin\zookeeper.cmd" status
CALL "%FUSION_HOME%\bin\solr.cmd" status
CALL "%FUSION_HOME%\bin\spark-master.cmd" status
CALL "%FUSION_HOME%\bin\spark-worker.cmd" status
CALL "%FUSION_HOME%\bin\api.cmd" status
CALL "%FUSION_HOME%\bin\connectors.cmd" status
CALL "%FUSION_HOME%\bin\ui.cmd" status
goto done

:after_stop
IF "%1"=="restart" goto do_start
goto done

:check_java
IF DEFINED SOLR_JAVA_HOME set "JAVA_HOME=%SOLR_JAVA_HOME%"

set "JAVA_OPTIONS=-Dapple.awt.UIElement=true"

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
if not exist "%JAVA%" (
  @echo "%JAVA% does not exist; perhaps is your JAVA_HOME set wrong"
  goto done
)

set JAVAVER=
set JAVA_MAJOR=
set JAVA_BUILD=0
"%JAVA%" -version 2>&1 | findstr /i "version" > javavers
set /p JAVAVEROUT=<javavers
del javavers
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
IF "%1"=="help" goto do_usage
IF "%1"=="-help" goto do_usage
IF "%1"=="/?" goto do_usage
IF "%1"=="start" goto do_start
IF "%1"=="stop" goto do_stop
IF "%1"=="restart" goto do_restart
IF "%1"=="status" goto do_status
@echo ERROR: %1 not supported!
goto do_usage

:do_usage
@echo.
@echo Usage: %0 [start, stop, restart, status]
goto done

:need_java_home
@echo Please set the JAVA_HOME environment variable to the path where you installed Java 1.7+
goto done

:need_java_vers
@echo Java 1.7 or later is required to run Fusion.
goto done

:done

ENDLOCAL
