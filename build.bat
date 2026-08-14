@echo off
REM BenchLM Build Script for Windows
REM Run from Developer Command Prompt or PowerShell

setlocal enabledelayedexpansion

echo ==========================================
echo BenchLM Build Script for Windows
echo ==========================================

REM Configuration
set PROJECT_ROOT=%~dp0
set BUILD_DIR=%PROJECT_ROOT%build
set DIST_DIR=%PROJECT_ROOT%dist

REM Default values
set BUILD_TARGET=all
set CLEAN=false
set VERBOSE=false

REM Parse arguments
:parse_args
if "%~1"=="" goto :parse_done
if "%~1"=="--target" (
    set BUILD_TARGET=%~2
    shift /2
    goto :parse_args
)
if "%~1"=="--clean" (
    set CLEAN=true
    shift
    goto :parse_args
)
if "%~1"=="--verbose" (
    set VERBOSE=true
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    echo Usage: build.bat [options]
    echo Options:
    echo   --target TARGET    Build target: all, windows, linux, macos, android, ios, web
    echo   --clean            Clean build directory before building
    echo   --verbose          Verbose output
    echo   --help             Show this help
    exit /b 0
)
echo Unknown option: %~1
exit /b 1
:parse_done

REM Colors (using ANSI codes if supported)
for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[0;32m"
set "YELLOW=%ESC%[1;33m"
set "RED=%ESC%[0;31m"
set "NC=%ESC%[0m"

echo Starting BenchLM build...
echo Target: %BUILD_TARGET%
echo Project root: %PROJECT_ROOT%

REM Check Python
echo Checking dependencies...
python --version 2>nul || (
    echo %RED%[ERROR]%NC% Python is not installed or not in PATH
    exit /b 1
)

REM Check uv or pip
uv --version 2>nul && set PACKAGE_MANAGER=uv || (
    pip --version 2>nul && set PACKAGE_MANAGER=pip || (
        echo %RED%[ERROR]%NC% Neither uv nor pip found
        exit /b 1
    )
)

echo Using %PACKAGE_MANAGER% for package management

REM Clean if requested
if "%CLEAN%"=="true" (
    echo Cleaning build directories...
    if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
    if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
    echo Clean complete
)

REM Install dependencies
echo Installing dependencies...
if "%PACKAGE_MANAGER%"=="uv" (
    uv sync --all-extras
) else (
    pip install -e ".[all]"
)

echo Dependencies installed

REM Build function
:build_target
set TARGET=%1
echo Building for %TARGET%...

cd /d "%PROJECT_ROOT%"

if "%TARGET%"=="windows" (
    flet build windows %VERBOSE_FLAG%
) else if "%TARGET%"=="linux" (
    flet build linux %VERBOSE_FLAG%
) else if "%TARGET%"=="macos" (
    flet build macos %VERBOSE_FLAG%
) else if "%TARGET%"=="android" (
    flet build android %VERBOSE_FLAG%
) else if "%TARGET%"=="ios" (
    flet build ios %VERBOSE_FLAG%
) else if "%TARGET%"=="web" (
    flet build web %VERBOSE_FLAG%
) else (
    echo %RED%[ERROR]%NC% Unknown target: %TARGET%
    exit /b 1
)

echo Build for %TARGET% complete
goto :eof

REM Main build logic
if "%BUILD_TARGET%"=="all" (
    REM Build for Windows (current platform)
    call :build_target windows
) else (
    call :build_target %BUILD_TARGET%
)

echo.
echo %GREEN%Build completed successfully!%NC%
echo Output: %DIST_DIR%
exit /b 0