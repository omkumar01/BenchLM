#!/bin/bash
# BenchLM Development Setup & Test Script
# Usage: ./setup_and_test.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  BenchLM Development Setup & Test      ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# LM Studio Configuration
LM_STUDIO_HOST="http://172.29.32.1:1234"
LM_STUDIO_MODEL="nvidia/nemotron-3-nano-4b"

echo -e "${YELLOW}LM Studio Configuration:${NC}"
echo -e "  Host: ${LM_STUDIO_HOST}"
echo -e "  Model: ${LM_STUDIO_MODEL}"
echo ""

# Step 1: Check/install uv
echo -e "${GREEN}[1/7] Checking uv...${NC}"
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "uv found: $(uv --version)"
fi

# Step 2: Create virtual environment
echo -e "${GREEN}[2/7] Creating virtual environment...${NC}"
if [ -d "${VENV_DIR}" ]; then
    echo "Virtual environment already exists, removing..."
    rm -rf "${VENV_DIR}"
fi
uv venv "${VENV_DIR}" --python 3.13
echo "Virtual environment created at ${VENV_DIR}"

# Step 3: Activate virtual environment
echo -e "${GREEN}[3/7] Activating virtual environment...${NC}"
source "${VENV_DIR}/bin/activate"
echo "Python: $(python --version)"
echo "Pip: $(pip --version)"

# Step 4: Install dependencies
echo -e "${GREEN}[4/7] Installing dependencies...${NC}"
uv pip install -e ".[all]" --extra dev
echo "Dependencies installed"

# Step 5: Verify LM Studio connection
echo -e "${GREEN}[5/7] Verifying LM Studio connection...${NC}"
echo "Testing connection to ${LM_STUDIO_HOST}/v1/models..."

if curl -s -f "${LM_STUDIO_HOST}/v1/models" > /dev/null; then
    echo -e "${GREEN}��� LM Studio is reachable${NC}"
    MODELS=$(curl -s "${LM_STUDIO_HOST}/v1/models" | python -m json.tool)
    echo "Available models:"
    echo "${MODELS}"
else
    echo -e "${RED}��� Cannot connect to LM Studio at ${LM_STUDIO_HOST}${NC}"
    echo "Please ensure:"
    echo "  1. LM Studio is running"
    echo "  2. Local server is started (click 'Start Server' in LM Studio)"
    echo "  3. Server is bound to 0.0.0.0:1234 (not just localhost)"
    echo "  4. Model '${LM_STUDIO_MODEL}' is loaded"
    exit 1
fi

# Step 6: Check if model is available
echo -e "${GREEN}[6/7] Checking model availability...${NC}"
if curl -s "${LM_STUDIO_HOST}/v1/models" | grep -q "nemotron-3-nano-4b"; then
    echo -e "${GREEN}��� Model 'nvidia/nemotron-3-nano-4b' is available${NC}"
else
    echo -e "${YELLOW}��� Model 'nvidia/nemotron-3-nano-4b' not found in loaded models${NC}"
    echo "Please load the model in LM Studio before running benchmarks"
fi

# Step 7: Run a quick test
echo -e "${GREEN}[7/7] Running quick benchmark test...${NC}"
cd "${PROJECT_ROOT}"

# Create a test config for LM Studio
cat > /tmp/test_config.yaml << EOF
app:
  theme: "dark"
  accent_color: "#6366F1"
  data_dir: "~/.benchlm"
  log_level: "INFO"

benchmark:
  default_provider: "lmstudio"
  lmstudio_host: "${LM_STUDIO_HOST}"
  temperature: 0.7
  top_p: 0.9
  max_tokens: 512
  iterations: 2
  warmup_runs: 1
  concurrent_users: 1
  streaming: true
  prompt_dataset: "builtin:general"

quality_benchmarks:
  mmlu: false
  humaneval: false
  gsm8k: false
  needle: false
  instruction_following: false
  reliability: false

ui:
  hardware_poll_interval: 500
  temperature_poll_interval: 1000
  power_poll_interval: 1000

hardware:
  gpu_backend: "auto"
EOF

echo "Running quick benchmark (2 iterations)..."
python -c "
import asyncio
import sys
sys.path.insert(0, '${PROJECT_ROOT}')

from benchlm.config import Config
from benchlm.providers.registry import initialize_providers, get_provider_registry
from benchlm.core.engine import get_benchmark_engine
from benchlm.core.config import BenchmarkConfig, BenchmarkPreset

async def test():
    # Load config
    config = Config.from_yaml('/tmp/test_config.yaml')
    
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
    from benchlm.providers.base import GenerationRequest, GenerationConfig
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
    print('\\n��� All tests passed!')
else:
    print('\\n��� Tests failed!')
    sys.exit(1)
"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Setup complete! BenchLM is ready to use.${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "To run the app:"
echo "  source ${VENV_DIR}/bin/activate"
echo "  benchlm"
echo ""
echo "Or run benchmarks programmatically:"
echo "  python -c \"from benchlm.core.engine import get_benchmark_engine; ...\""
echo ""
echo "Configuration file: /tmp/test_config.yaml (copy to config.yaml to persist)"