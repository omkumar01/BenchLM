# BenchLM Implementation Plan

## Project Overview
Build a fully offline, native, cross-platform LLM benchmarking application in Python using Flet with Plotly visualizations, SQLite persistence, and professional-grade features.

---

## Architecture Design

### Clean Architecture Layers
```
benchlm/
├── app.py                    # Entry point, DI container setup
├── core/                     # Domain logic (no external deps)
│   ├── benchmark_engine.py   # Orchestrates benchmark runs
│   ├── metrics_collector.py  # Collects hardware + LLM metrics
│   ├── scheduler.py          # Manages concurrent requests, warmup/cooldown
│   ├── statistics.py         # Statistical computations (percentiles, CI, etc.)
│   └── scorer.py             # Weighted scoring engine (1000-point scale)
├── providers/                # LLM provider abstractions
│   ├── base.py              # Abstract base class
│   ├── ollama.py
│   ├── llama_cpp.py
│   ├── lmstudio.py
│   ├── vllm.py
│   └── openai_compatible.py
├── hardware/                 # System monitoring
│   ├── cpu.py, gpu.py, memory.py, disk.py, battery.py, temperature.py
│   └── collector.py         # Unified hardware metrics collector
├── quality/                  # Quality benchmarks
│   ├── mmlu.py, humaneval.py, gsm8k.py, mbpp.py, needle.py
│   └── runner.py            # Quality benchmark orchestrator
├── database/                 # Persistence layer
│   ├── models.py            # SQLModel definitions
│   ├── repository.py        # Data access patterns
│   └── migrations.py        # Schema versioning
├── charts/                   # Plotly chart generators
│   ├── latency.py, throughput.py, memory.py, quality.py
│   ├── statistical.py, comparison.py, hardware.py, thermal.py
│   └── factory.py           # Chart factory for lazy loading
├── exports/                  # Export formats
│   ├── csv.py, json.py, html.py, pdf.py, sqlite_backup.py
├── ui/                       # Flet UI layer
│   ├── theme.py             # Material 3 dark/light theme, glassmorphism
│   ├── pages/               # 11 main pages
│   ├── widgets/             # Reusable components (gauges, cards, tables)
│   └── dialogs/             # Modals, settings, confirmations
├── datasets/                 # Built-in benchmark datasets
├── benchmarks/               # Benchmark presets/configurations
├── assets/                   # Icons, fonts, static files
��── tests/                    # Unit + integration tests
```

### Dependency Injection
- Use a simple DI container in `app.py` to wire implementations
- Providers, hardware collectors, database repo injected into benchmark engine
- Enables testing with mocks and easy provider swapping

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal**: Core infrastructure, database, configuration, basic UI shell

| Task | Deliverable |
|------|-------------|
| 1.1 Project structure & pyproject.toml | Poetry/uv config with all deps |
| 1.2 Configuration system (Pydantic Settings) | `config.yaml` with theme, polling, providers |
| 1.3 Logging (loguru) + DI container | Structured logging, service locator |
| 1.4 Database schema + migrations | SQLite tables: models, runs, prompts, token_events, hardware_samples, quality_scores, stats, comparisons |
| 1.5 Theme system | Material 3 dark mode, glassmorphism cards, responsive breakpoints |
| 1.6 App shell + navigation | 11-page navigation rail, responsive drawer |

### Phase 2: Provider Abstractions (Week 1-2)
**Goal**: Unified interface for all local LLM providers

| Task | Deliverable |
|------|-------------|
| 2.1 Base provider protocol | `LLMProvider` abstract class with stream/generate, model listing, health check |
| 2.2 Ollama provider | `/api/tags`, `/api/generate`, `/api/chat` endpoints |
| 2.3 llama.cpp provider | HTTP server mode + direct library binding |
| 2.4 LM Studio provider | OpenAI-compatible local server |
| 2.5 vLLM provider | OpenAI-compatible API |
| 2.6 OpenAI-compatible generic | For TensorRT-LLM, custom endpoints |
| 2.7 Provider registry + auto-detection | Scan localhost ports, detect running servers |

### Phase 3: Hardware Monitoring (Week 2)
**Goal**: Real-time system metrics at 250ms intervals

| Task | Deliverable |
|------|-------------|
| 3.1 CPU collector | psutil: per-core %, frequency, temp, power (RAPL) |
| 3.2 GPU collector | pynvml (NVIDIA), rocm-smi (AMD), intel-gpu-top (Intel) |
| 3.3 Memory collector | RAM, VRAM, swap, KV cache estimation |
| 3.4 Disk/Network/Battery | IOPS, throughput, battery %, charge rate |
| 3.5 Temperature collector | CPU package, GPU core, hotspot, VRAM temps |
| 3.6 Unified collector | Async loop, 250ms polling, ring buffer for 100k samples |

### Phase 4: Benchmark Engine (Week 2-3)
**Goal**: Core benchmark orchestration with all parameters

| Task | Deliverable |
|------|-------------|
| 4.1 Benchmark configuration model | Pydantic: prompts, temp, top-p/k, seed, max_tokens, batch, context, streaming, concurrency, iterations, warmup, cooldown |
| 4.2 Scheduler | Token-by-token streaming, concurrent user simulation, request queuing |
| 4.3 Metrics collector | TTFT, TPOT, inter-token latency, prefill/decode split, throughput (TPS, RPS, QPM) |
| 4.4 Statistics engine | Mean, median, std, min, max, P50/P90/P95/P99, 95% CI, jitter |
| 4.5 Resource tracking | Peak/avg VRAM/RAM, GPU/CPU %, memory bandwidth, PCIe, energy/token |
| 4.6 Warmup/cooldown logic | Configurable runs, thermal stabilization |

### Phase 5: Quality Benchmarks (Week 3)
**Goal**: Implement all quality evaluation suites

| Benchmark | Metrics |
|-----------|---------|
| MMLU / MMLU-Pro | Accuracy, EM, F1 |
| GPQA, ARC, HellaSwag, TruthfulQA, BIG-Bench | Accuracy |
| GSM8K, MATH | EM, reasoning steps |
| HumanEval / MBPP | Pass@1, Pass@5, Pass@10 |
| SWE-Bench / RepoBench | Compilation, test pass rate |
| Needle in Haystack | Retrieval precision/recall, context retention |
| Instruction Following | JSON/XML validity, schema compliance, tool call accuracy |
| Reliability | Hallucination, factuality, consistency, determinism, error rate |
| Safety | Toxicity, jailbreak resistance, prompt injection, PII, refusal correctness, bias |
| Agent Metrics | Task success, plan quality, tool precision/recall, workflow time |

### Phase 6: Chart System (Week 3-4)
**Goal**: All Plotly offline charts with lazy loading

| Category | Charts |
|----------|--------|
| Latency | TTFT line, E2E, per-token, P50/90/95/99, histogram, CDF |
| Throughput | TPS, prompt TPS, total TPS, over time, batch, concurrent |
| Memory | RAM/VRAM timeline, KV cache growth, stacked breakdown, peak |
| CPU/GPU | Utilization, per-core heatmap, GPU occupancy, memory bandwidth |
| Thermal | GPU/CPU temp, power, energy/token, perf/W, throttling timeline |
| Context | Context vs TTFT/TPS/Memory/Latency, KV cache vs context |
| Concurrency | Users vs latency/throughput, queue wait, active requests, scaling efficiency |
| Quality | Overall score, task scores, radar, Pass@k, accuracy comparison, win rate, Elo |
| Reliability | Success/failure, error categories, timeout/OOM frequency, variance, stability |
| Comparison | Leaderboard, speed vs quality scatter, bubble, Pareto, model size vs perf, quantization |
| Statistical | Box plot, violin, histogram, density, heatmap, correlation, scatter matrix, error bars |

### Phase 7: UI Pages (Week 4-5)
**Goal**: 11 professional pages with real-time updates

| Page | Key Features |
|------|--------------|
| **Dashboard** | Live hardware gauges (CPU, GPU, RAM, VRAM, temp, power), current model card, active benchmark status, 250ms updates |
| **Models** | Provider tabs, installed models table (quant, context, params, size), multi-select for comparison |
| **Benchmark** | Configuration form (all params), preset save/load, model multi-select, start/pause/resume |
| **Live Monitor** | Real-time charts during run: TPS stream, latency, hardware, thermal, token-by-token |
| **Results** | 13 tabs: Summary, Latency, Throughput, Memory, CPU/GPU, Thermal, Context, Concurrency, Quality, Reliability, Statistics, Raw Samples, Export |
| **Comparison** | Multi-model overlay, side-by-side, radar, diff view, ranking, Elo, Pareto |
| **History** | Run list with filters, version/daily/weekly trends, regression detection, moving averages |
| **Leaderboard** | Global ranking table, Elo ratings, speed/quality scatter, bubble charts |
| **Datasets** | Built-in dataset browser, custom prompt management, dataset validation |
| **Reports** | PDF/HTML/CSV/JSON export, report builder with sections |
| **Settings** | Theme, accent, polling interval, default provider/preset, export dir, hardware backend, mobile opt, units |

### Phase 8: Scoring & Export (Week 5)
**Goal**: Weighted scoring (1000 pts) + all export formats

| Component | Details |
|-----------|---------|
| Scoring Engine | Weights: Latency 20%, Throughput 20%, Quality 25%, Reliability 15%, Memory 10%, Energy 5%, Context 5% |
| Grades | S+ (950+), S (900), A (800), B (700), C (600), below = D |
| PDF Export | ReportLab/WeasyPrint: hardware, model info, all charts, statistics, leaderboard, radar, recommendations |
| HTML Export | Self-contained with embedded Plotly.js |
| CSV/JSON | Raw samples + computed statistics |
| SQLite Backup | Full database dump |

### Phase 9: Polish & Packaging (Week 5-6)
**Goal**: Production readiness

| Task | Deliverable |
|------|-------------|
| 9.1 Virtualized tables | Handle 100k+ rows, lazy load charts |
| 9.2 Error handling & recovery | Graceful degradation, benchmark resume |
| 9.3 Unit tests | Core: statistics, scheduler, scoring, providers (pytest) |
| 9.4 Integration tests | Full benchmark runs, DB persistence, exports |
| 9.5 Flet build config | `flet_build.yaml` for Windows, macOS, Linux, Android, iOS |
| 9.6 Build scripts | GitHub Actions / local scripts for all platforms |
| 9.7 Documentation | README, architecture docs, user guide |
| 9.8 Performance profiling | Memory leaks, UI responsiveness, 100k token events |

---

## Technical Decisions

### Key Libraries
| Purpose | Choice | Rationale |
|---------|--------|-----------|
| UI | Flet | Native packaging, Python-only, Material 3 |
| Charts | Plotly (offline) | Interactive, export to HTML/PNG, no server |
| Data | Polars | Fast, memory-efficient, streaming |
| DB | SQLite + SQLModel | Zero-config, type-safe, migrations |
| HTTP | httpx | Async, HTTP/2, connection pooling |
| Hardware | psutil + pynvml | Cross-platform, GPU support |
| Quality | evaluate + bert-score | Standard HF metrics |
| Config | Pydantic Settings | Type-safe, env/file config |
| Logging | loguru | Structured, rotation, serialization |

### Offline-First Guarantees
- No network calls except to local LLM endpoints (localhost)
- All datasets bundled in `assets/datasets/`
- Models downloaded separately by user (Ollama pull, etc.)
- No telemetry, analytics, or external CDN

### Performance Targets
- 100,000 token events in memory (ring buffer + Polars)
- 1,000 benchmark runs in DB (indexed queries)
- 250ms UI update loop (hardware), per-token (TPS)
- Virtualized tables for raw samples (10k+ rows)
- Lazy chart rendering (only visible tabs)

---

## Questions for Clarification

Before finalizing, I have a few questions:

1. **Provider Priority**: Which 2-3 providers should be implemented first for MVP? (Ollama + llama.cpp + LM Studio recommended)

2. **Quality Benchmarks Scope**: Implement all 15+ benchmarks in Phase 5, or start with core 5 (MMLU, HumanEval, GSM8K, Needle, Instruction Following) and add rest incrementally?

3. **PDF Engine**: Prefer `reportlab` (pure Python, more code) or `weasyprint` (HTML→PDF, needs system deps)?

4. **Mobile Target**: Android/iOS via Flet build - any specific UI adaptations needed beyond responsive layout?

5. **GPU Backend Priority**: NVIDIA (pynvml) first, then AMD/Intel? Or all three in Phase 3?

6. **Dataset Bundling**: Include MMLU/HumanEval/GSM8K datasets in repo (~50MB), or download on first run?

---

## Next Steps

Upon approval, I'll start with **Phase 1: Foundation** - setting up the project structure, configuration, database, theme system, and app shell with navigation. This creates the backbone for all subsequent phases.