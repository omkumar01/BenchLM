# BenchLM - Professional Offline LLM Benchmarking Suite

A fully offline, native, cross-platform LLM benchmarking application built with Python and Flet. BenchLM measures speed, latency, throughput, memory, hardware utilization, thermal behavior, quality, reliability, scalability, and statistical analysis of Large Language Models running locally.

## Features

### Core Benchmarking
- **Multi-provider support**: Ollama, llama.cpp, LM Studio, vLLM, TensorRT-LLM, OpenAI-compatible APIs
- **Comprehensive metrics**: TTFT, TPOT, inter-token latency, prefill/decode split, TPS, RPS, QPM
- **Resource monitoring**: CPU/GPU utilization, RAM/VRAM, power, temperature, memory bandwidth
- **Quality benchmarks**: MMLU, HumanEval, GSM8K, MBPP, Needle in Haystack, and more
- **Reliability testing**: Hallucination, factuality, consistency, determinism, error rates

### Analytics & Visualization
- **Interactive dashboards**: Live hardware gauges updating at 250ms intervals
- **Advanced charts**: Plotly-powered visualizations for latency, throughput, memory, thermal, quality
- **Multi-model comparison**: Overlay, side-by-side, radar charts, diff views, Pareto frontiers
- **Historical trends**: Version/daily/weekly trends, regression detection, moving averages
- **Leaderboards**: Elo ratings, speed vs quality scatter, global rankings

### Professional Features
- **Offline-first**: No internet required, all data stored locally in SQLite
- **Cross-platform**: Windows, macOS, Linux, Android, iOS via Flet
- **Export formats**: CSV, JSON, HTML, PDF, SQLite backup
- **Scoring engine**: Weighted 1000-point scale with grades (S+ to D)
- **Preset system**: Save and share benchmark configurations
- **Responsive UI**: Material 3 dark mode, glassmorphism, touch-friendly

## Quick Start

### Prerequisites
- Python 3.13+
- A local LLM server (Ollama, LM Studio, llama.cpp, or vLLM)

### Installation

```bash
# Clone the repository
git clone https://github.com/benchlm/benchlm.git
cd benchlm

# Install dependencies
pip install -e .

# Or with uv (recommended)
uv sync
```

### Configuration

Create a `config.yaml` file (auto-generated on first run):

```yaml
app:
  theme: "dark"
  accent_color: "#6366F1"

benchmark:
  default_provider: "ollama"
  ollama_host: "http://localhost:11434"
  iterations: 10
  warmup_runs: 2

hardware:
  gpu_backend: "auto"  # auto, pynvml, rocm-smi, intel-gpu-top
```

### Running

```bash
# Run the application
benchlm

# Or for development
benchlm-dev
```

## Project Structure

```
BenchLM/
├── app.py                    # Entry point
├── config.yaml               # Configuration
├── pyproject.toml            # Dependencies & build config
├── benchlm/
│   ├── config.py             # Pydantic Settings
│   ├── logging_config.py     # Loguru setup
│   ├── di.py                 # Dependency injection
│   ├── core/                 # Domain logic
│   ├── providers/            # LLM provider abstractions
│   ├── hardware/             # System monitoring
│   ├── quality/              # Quality benchmarks
│   ├── database/             # SQLite + SQLModel
│   ├── charts/               # Plotly chart generators
│   ├── exports/              # Export formats
│   ├── ui/                   # Flet UI
│   │   ├── theme.py          # Material 3 theme
│   │   ├── widgets/          # Reusable components
│   │   └── pages/            # 11 main pages
│   ├── datasets/             # Built-in datasets
│   ├── benchmarks/           # Benchmark presets
│   └── tests/                # Unit & integration tests
```

## Pages

1. **Dashboard** - Live hardware gauges, current model, active benchmark
2. **Models** - Provider tabs, installed models, multi-select for comparison
3. **Benchmark** - Configuration, presets, execution parameters
4. **Live Monitor** - Real-time charts during benchmark runs
5. **Results** - 13 tabs: Summary, Latency, Throughput, Memory, CPU/GPU, Thermal, Context, Concurrency, Quality, Reliability, Statistics, Raw Samples, Export
6. **Comparison** - Multi-model overlay, side-by-side, radar, diff, ranking
7. **History** - Run list, trends, regression detection
8. **Leaderboard** - Global rankings, Elo ratings, speed vs quality
9. **Datasets** - Built-in and custom prompt datasets
10. **Reports** - PDF/HTML/CSV/JSON report generation
11. **Settings** - Theme, providers, benchmark defaults, hardware, exports

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
ruff check .
mypy benchlm/
```

### Building Native Installers
```bash
# Windows
flet build windows

# macOS
flet build macos

# Linux
flet build linux

# Android
flet build android

# iOS
flet build ios
```

## Architecture

BenchLM follows **Clean Architecture** with dependency injection:

- **Core**: Pure Python domain logic (no external dependencies)
- **Providers**: Abstract interface for LLM providers
- **Hardware**: Cross-platform system monitoring
- **Database**: SQLModel + SQLite with async support
- **UI**: Flet with Material 3, responsive design
- **Charts**: Plotly offline rendering

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [Flet](https://flet.dev/) - Python UI framework
- [Plotly](https://plotly.com/) - Interactive charts
- [Polars](https://pola.rs/) - Fast DataFrames
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL databases in Python
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - LLM inference engine