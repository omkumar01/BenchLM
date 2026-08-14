@echo off
REM BenchLM Development Setup & Test Script for Windows
REM Usage: setup_and_test.bat

setlocal enabledelayedexpansion

REM Colors (ANSI)
for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[0;32m"
set "YELLOW=%ESC%[1;33m"
set "RED=%ESC%[0;31m"
set "BLUE=%ESC%[0;34m"
set "NC=%ESC%[0m"

set "PROJECT_ROOT=%~dp0"
set "VENV_DIR=%PROJECT_ROOT%.venv"

echo %BLUE%========================================%NC%
echo %BLUE%  BenchLM Development Setup & Test      %NC%
echo %BLUE%========================================%NC%
echo.

REM LM Studio Configuration
set "LM_STUDIO_HOST=http://172.29.32.1:1234"
set "LM_STUDIO_MODEL=nvidia/nemotron-3-nano-4b"

echo %YELLOW%LM Studio Configuration:%NC%
echo   Host: %LM_STUDIO_HOST%
echo   Model: %LM_STUDIO_MODEL%
echo.

REM Step 1: Check/install uv
echo %GREEN%[1/7] Checking uv...%NC%
uv --version 2>nul || (
    echo Installing uv...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
)
echo uv found: & uv --version

REM Step 2: Create virtual environment
echo %GREEN%[2/7] Creating virtual environment...%NC%
if exist "%VENV_DIR%" (
    echo Virtual environment already exists, removing...
    rmdir /s /q "%VENV_DIR%"
)
uv venv "%VENV_DIR%" --python 3.13
echo Virtual environment created at %VENV_DIR%

REM Step 3: Activate virtual environment
echo %GREEN%[3/7] Activating virtual environment...%NC%
call "%VENV_DIR%\Scripts\activate.bat"
echo Python: & python --version
echo Pip: & pip --version

REM Step 4: Install dependencies
echo %GREEN%[4/7] Installing dependencies...%NC%
uv pip install -e ".[all]" --extra dev
echo Dependencies installed

REM Step 5: Verify LM Studio connection
echo %GREEN%[5/7] Verifying LM Studio connection...%NC%
echo Testing connection to %LM_STUDIO_HOST%/v1/models...

curl -s -f "%LM_STUDIO_HOST%/v1/models" >nul 2>&1
if errorlevel 1 (
    echo %RED%[X] Cannot connect to LM Studio at %LM_STUDIO_HOST%%NC%
    echo Please ensure:
    echo   1. LM Studio is running
    echo   2. Local server is started (click 'Start Server' in LM Studio)
    echo   3. Server is bound to 0.0.0.0:1234 (not just localhost)
    echo   4. Model '%LM_STUDIO_MODEL%' is loaded
    exit /b 1
) else (
    echo %GREEN%[OK] LM Studio is reachable%NC%
    curl -s "%LM_STUDIO_HOST%/v1/models" | python -m json.tool
)

REM Step 6: Check if model is available
echo %GREEN%[6/7] Checking model availability...%NC%
curl -s "%LM_STUDIO_HOST%/v1/models" | findstr /i "nemotron-3-nano-4b" >nul
if errorlevel 1 (
    echo %YELLOW%[!] Model '%LM_STUDIO_MODEL%' not found in loaded models%NC%
    echo Please load the model in LM Studio before running benchmarks
) else (
    echo %GREEN%[OK] Model '%LM_STUDIO_MODEL%' is available%NC%
)

REM Step 7: Run a quick test
echo %GREEN%[7/7] Running quick benchmark test...%NC%
cd /d "%PROJECT_ROOT%"

REM Create a test config for LM Studio
set "TEST_CONFIG=%TEMP%\test_config.yaml"
(
echo app:
echo   theme: "dark"
echo   accent_color: "#6366F1"
echo   data_dir: "~/.benchlm"
echo   log_level: "INFO"
echo.
echo benchmark:
echo   default_provider: "lmstudio"
echo   lmstudio_host: "%LM_STUDIO_HOST%"
echo   temperature: 0.7
echo   top_p: 0.9
echo   max_tokens: 512
echo   iterations: 2
echo   warmup_runs: 1
echo   concurrent_users: 1
echo   streaming: true
echo   prompt_dataset: "builtin:general"
echo.
echo quality_benchmarks:
echo   mmlu: false
echo   humaneval: false
echo   gsm8k: false
echo   needle: false
echo   instruction_following: false
echo   reliability: false
echo.
echo ui:
echo   hardware_poll_interval: 500
echo   temperature_poll_interval: 1000
echo   power_poll_interval: 1000
echo.
echo hardware:
echo   gpu_backend: "auto"
) > "%TEST_CONFIG%"

echo Running quick benchmark (2 iterations)...
python -c "
import asyncio
import sys
sys.path.insert(0, r'%PROJECT_ROOT%')

from benchlm.config import Config
from benchlm.providers.registry import initialize_providers, get_provider_registry
from benchlm.providers.base import GenerationRequest, GenerationConfig

async def test():
    # Load config
    config = Config.from_yaml(r'%TEST_CONFIG%')
    
    # Initialize providers
    await initialize_providers(config)
    
    # Get provider
    registry = get_provider_registry()
    provider = registry.get_provider_by_type('lmstudio')
    if not provider:
        print('LM Studio provider not found!')
        return False
    
    # Test connection
    health = await provider.health_check()
    print(f'Provider health: {health.healthy} - {health.error or \"OK\"}')
    if not health.healthy:
        return False
    
    # List models
    models = await provider.list_models()
    print(f'Available models: {[m.name for m in models]}')
    
    # Quick generation test
    request = GenerationRequest(
        prompt='Say hello in one sentence.',
        model='nvidia/nemotron-3-nano-4b',
        config=GenerationConfig(temperature=0.7, max_tokens=100, stream=False)
    )
    response = await provider.generate(request)
    print(f'Test generation: {response.text[:100]}...')
    print(f'Tokens: {response.prompt_tokens} + {response.completion_tokens} = {response.total_tokens}')
    
    return True

result = asyncio.run(test())
if result:
    print('\n[OK] All tests passed!')
else:
    print('\n[X] Tests failed!')
    sys.exit(1)
"

echo.
echo %BLUE%========================================%NC%
echo %GREEN%Setup complete! BenchLM is ready to use.%NC%
echo %BLUE%========================================%NC%
echo.
echo To run the app:
echo   call %VENV_DIR%\Scripts\activate.bat
echo   benchlm
echo.
echo Or run benchmarks programmatically:
echo   python -c "from benchlm.core.engine import get_benchmark_engine; ..."
echo.
echo Configuration file: %TEST_CONFIG% (copy to config.yaml to persist)