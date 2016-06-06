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
set SERVICE_PORT=%ZOOKEEPER_PORT%

set "JAVA_OPTIONS=-Djava.net.preferIPv4Stack=true -Xmx2g -Dapple.awt.UIElement=true"

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


set LIB_DIR="%FUSION_HOME%\apps\zookeeper\lib"
"%JAVA%" %JAVA_OPTIONS% ^
-Dapollo.home="%FUSION_HOME%" ^
-cp "%LIB_DIR%/*" ^
org.apache.zookeeper.ZooKeeperMain -server "localhost:%ZOOKEEPER_PORT%"

goto done

:need_java_home
@echo Please set the JAVA_HOME environment variable to the path where you installed Java 1.7+
goto done

:need_java_vers
@echo Java 1.7 or later is required to run Fusion.
goto done

:done

ENDLOCAL
