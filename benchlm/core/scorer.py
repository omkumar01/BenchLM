"""Scoring engine for BenchLM - computes weighted overall scores and grades."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from benchlm.core.metrics import BenchmarkMetrics
from benchlm.config import get_config, ScoringConfig


@dataclass
class ScoreWeights:
    """Weights for each scoring category (sum = 100)."""

    latency: float = 20.0
    throughput: float = 20.0
    quality: float = 25.0
    reliability: float = 15.0
    memory: float = 10.0
    energy: float = 5.0
    context: float = 5.0

    def validate(self) -> bool:
        """Check if weights sum to 100."""
        total = (self.latency + self.throughput + self.quality +
                 self.reliability + self.memory + self.energy + self.context)
        return abs(total - 100.0) < 0.01

    def normalize(self):
        """Normalize weights to sum to 100."""
        total = (self.latency + self.throughput + self.quality +
                 self.reliability + self.memory + self.energy + self.context)
        if total > 0:
            factor = 100.0 / total
            self.latency *= factor
            self.throughput *= factor
            self.quality *= factor
            self.reliability *= factor
            self.memory *= factor
            self.energy *= factor
            self.context *= factor

    def to_dict(self) -> Dict[str, float]:
        return {
            "latency": self.latency,
            "throughput": self.throughput,
            "quality": self.quality,
            "reliability": self.reliability,
            "memory": self.memory,
            "energy": self.energy,
            "context": self.context,
        }


@dataclass
class GradeThresholds:
    """Score thresholds for letter grades."""

    s_plus: float = 950
    s: float = 900
    a: float = 800
    b: float = 700
    c: float = 600

    def get_grade(self, score: float) -> str:
        """Get letter grade for score."""
        if score >= self.s_plus:
            return "S+"
        elif score >= self.s:
            return "S"
        elif score >= self.a:
            return "A"
        elif score >= self.b:
            return "B"
        elif score >= self.c:
            return "C"
        else:
            return "D"

    def to_dict(self) -> Dict[str, float]:
        return {
            "S+": self.s_plus,
            "S": self.s,
            "A": self.a,
            "B": self.b,
            "C": self.c,
        }


@dataclass
class CategoryScore:
    """Score for a single category."""

    name: str
    raw_score: float  # 0-100
    weighted_score: float  # 0-weight
    weight: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "raw_score": self.raw_score,
            "weighted_score": self.weighted_score,
            "weight": self.weight,
            "details": self.details,
        }


@dataclass
class BenchmarkScore:
    """Complete benchmark score."""

    overall_score: float  # 0-1000
    grade: str
    category_scores: List[CategoryScore]
    weights: ScoreWeights
    thresholds: GradeThresholds
    percentile_rank: Optional[float] = None  # Among all runs
    elo_rating: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "grade": self.grade,
            "category_scores": [cs.to_dict() for cs in self.category_scores],
            "weights": self.weights.to_dict(),
            "thresholds": self.thresholds.to_dict(),
            "percentile_rank": self.percentile_rank,
            "elo_rating": self.elo_rating,
        }


class ScoringEngine:
    """Computes weighted scores for benchmark results."""

    def __init__(self, config: Optional[ScoringConfig] = None):
        self._config = config or get_config().scoring
        self._weights = ScoreWeights(
            latency=self._config.weights.latency,
            throughput=self._config.weights.throughput,
            quality=self._config.weights.quality,
            reliability=self._config.weights.reliability,
            memory=self._config.weights.memory,
            energy=self._config.weights.energy,
            context=self._config.weights.context,
        )
        self._thresholds = GradeThresholds(
            s_plus=self._config.grades.s_plus,
            s=self._config.grades.s,
            a=self._config.grades.a,
            b=self._config.grades.b,
            c=self._config.grades.c,
        )

    def compute_score(self, metrics: BenchmarkMetrics) -> BenchmarkScore:
        """Compute overall benchmark score from metrics."""

        # Compute category scores
        category_scores = [
            self._compute_latency_score(metrics),
            self._compute_throughput_score(metrics),
            self._compute_quality_score(metrics),
            self._compute_reliability_score(metrics),
            self._compute_memory_score(metrics),
            self._compute_energy_score(metrics),
            self._compute_context_score(metrics),
        ]

        # Calculate overall score
        overall = sum(cs.weighted_score for cs in category_scores)
        overall = max(0, min(1000, overall))  # Clamp to 0-1000

        # Determine grade
        grade = self._thresholds.get_grade(overall)

        return BenchmarkScore(
            overall_score=overall,
            grade=grade,
            category_scores=category_scores,
            weights=self._weights,
            thresholds=self._thresholds,
        )

    def _compute_latency_score(self, metrics: BenchmarkMetrics) -> CategoryScore:
        """Compute latency score (lower is better)."""
        lat = metrics.latency

        if not lat.ttft_samples:
            return CategoryScore("latency", 0, 0, self._weights.latency, {"error": "No latency data"})

        # Normalize: lower TTFT = higher score
        # Target: 50ms = 100, 200ms = 50, 500ms = 10, 1000ms = 0
        ttft_p50 = lat.ttft_p50 / 1000  # Convert to ms
        ttft_p99 = lat.ttft_p99 / 1000

        # Score based on P50 and P99
        p50_score = max(0, 100 - (ttft_p50 - 50) * 0.5)  # 50ms baseline
        p99_score = max(0, 100 - (ttft_p99 - 200) * 0.3)  # 200ms baseline

        # Combined latency score (weighted toward P99 for tail latency)
        raw_score = p50_score * 0.4 + p99_score * 0.6

        # Penalize high jitter
        if lat.tpot_stdev > 0:
            jitter_penalty = min(20, lat.tpot_stdev / lat.tpot_mean * 100) if lat.tpot_mean > 0 else 0
            raw_score = max(0, raw_score - jitter_penalty)

        raw_score = max(0, min(100, raw_score))
        weighted = raw_score * (self._weights.latency / 100)

        return CategoryScore(
            name="latency",
            raw_score=raw_score,
            weighted_score=weighted,
            weight=self._weights.latency,
            details={
                "ttft_p50_ms": lat.ttft_p50 / 1000,
                "ttft_p99_ms": lat.ttft_p99 / 1000,
                "tpot_mean_ms": lat.tpot_mean / 1000,
                "jitter_penalty": jitter_penalty if lat.tpot_stdev > 0 else 0,
            },
        )

    def _compute_throughput_score(self, metrics: BenchmarkMetrics) -> CategoryScore:
        """Compute throughput score (higher is better)."""
        thr = metrics.throughput

        if not thr.tps_samples:
            return CategoryScore("throughput", 0, 0, self._weights.throughput, {"error": "No throughput data"})

        tps = thr.output_tps_mean

        # Normalize: 100 TPS = 100, 50 TPS = 70, 20 TPS = 40, 10 TPS = 10
        if tps >= 100:
            raw_score = 100
        elif tps >= 50:
            raw_score = 70 + (tps - 50) * 0.6
        elif tps >= 20:
            raw_score = 40 + (tps - 20) * 1.0
        elif tps >= 10:
            raw_score = 10 + (tps - 10) * 3.0
        else:
            raw_score = max(0, tps)

        # Bonus for stability
        cv = thr.tps_stdev / tps if tps > 0 else 1
        stability_bonus = max(0, 10 - cv * 50)  # Up to 10 points for low CV
        raw_score = min(100, raw_score + stability_bonus)

        weighted = raw_score * (self._weights.throughput / 100)

        return CategoryScore(
            name="throughput",
            raw_score=raw_score,
            weighted_score=weighted,
            weight=self._weights.throughput,
            details={
                "output_tps_mean": thr.output_tps_mean,
                "output_tps_stdev": thr.output_tps_stdev,
                "stability_bonus": stability_bonus,
                "input_tps_mean": thr.input_tps_mean,
                "rps_mean": thr.rps_mean,
            },
        )

    def _compute_quality_score(self, metrics: BenchmarkMetrics) -> CategoryScore:
        """Compute quality score from quality benchmarks."""
        qual = metrics.quality

        # Collect available quality metrics
        scores = []
        details = {}

        if qual.accuracy is not None:
            scores.append(qual.accuracy * 100)
            details["accuracy"] = qual.accuracy

        if qual.exact_match is not None:
            scores.append(qual.exact_match * 100)
            details["exact_match"] = qual.exact_match

        if qual.f1_score is not None:
            scores.append(qual.f1_score * 100)
            details["f1"] = qual.f1_score

        if qual.pass_at_1 is not None:
            scores.append(qual.pass_at_1 * 100)
            details["pass_at_1"] = qual.pass_at_1

        if qual.pass_at_5 is not None:
            scores.append(qual.pass_at_5 * 100)
            details["pass_at_5"] = qual.pass_at_5

        if qual.pass_at_10 is not None:
            scores.append(qual.pass_at_10 * 100)
            details["pass_at_10"] = qual.pass_at_10

        if qual.retrieval_precision is not None:
            scores.append(qual.retrieval_precision * 100)
            details["needle_precision"] = qual.retrieval_precision

        if qual.json_validity is not None:
            scores.append(qual.json_validity * 100)
            details["json_validity"] = qual.json_validity

        if qual.factuality_score is not None:
            scores.append(qual.factuality_score * 100)
            details["factuality"] = qual.factuality_score

        if qual.toxicity_score is not None:
            # Lower toxicity is better
            scores.append((1 - qual.toxicity_score) * 100)
            details["toxicity"] = qual.toxicity_score

        if not scores:
            return CategoryScore("quality", 0, 0, self._weights.quality, {"error": "No quality data"})

        raw_score = mean(scores)
        weighted = raw_score * (self._weights.quality / 100)

        return CategoryScore(
            name="quality",
            raw_score=raw_score,
            weighted_score=weighted,
            weight=self._weights.quality,
            details=details,
        )

    def _compute_reliability_score(self, metrics: BenchmarkMetrics) -> CategoryScore:
        """Compute reliability score."""
        rel = metrics.reliability

        if rel.total_requests == 0:
            return CategoryScore("reliability", 0, 0, self._weights.reliability, {"error": "No reliability data"})

        # Base score from success rate
        success_score = rel.success_rate * 100

        # Penalties
        timeout_penalty = rel.timeout_rate * 50  # Up to 50 points
        oom_penalty = rel.oom_rate * 100  # Up to 100 points
        error_penalty = rel.failure_rate * 30

        raw_score = max(0, success_score - timeout_penalty - oom_penalty - error_penalty)

        # Bonus for determinism
        determinism_bonus = 0
        if rel.total_requests > 10:
            # Low variance = high determinism
            latency_var = rel.latency_variance
            throughput_var = rel.throughput_variance
            # Would need actual variance values
            pass

        raw_score = min(100, raw_score + determinism_bonus)
        weighted = raw_score * (self._weights.reliability / 100)

        return CategoryScore(
            name="reliability",
            raw_score=raw_score,
            weighted_score=weighted,
            weight=self._weights.reliability,
            details={
                "success_rate": rel.success_rate,
                "timeout_rate": rel.timeout_rate,
                "oom_rate": rel.oom_rate,
                "error_rate": rel.failure_rate,
                "error_categories": rel.error_categories,
            },
        )

    def _compute_memory_score(self, metrics: BenchmarkMetrics) -> CategoryScore:
        """Compute memory efficiency score."""
        res = metrics.resources

        if res.peak_vram_mb == 0 and res.peak_ram_mb == 0:
            return CategoryScore("memory", 0, 0, self._weights.memory, {"error": "No memory data"})

        # Score based on VRAM efficiency (lower peak is better for same model)
        # This is model-dependent, so we use relative scoring
        # For now, score based on utilization efficiency
        vram_score = 0
        if res.peak_vram_mb > 0 and res.avg_vram_mb > 0:
            # Efficiency = average / peak (closer to 1 is better)
            vram_efficiency = res.avg_vram_mb / res.peak_vram_mb
            vram_score = vram_efficiency * 100

        ram_score = 0
        if res.peak_ram_mb > 0 and res.avg_ram_mb > 0:
            ram_efficiency = res.avg_ram_mb / res.peak_ram_mb
            ram_score = ram_efficiency * 100

        # GPU utilization efficiency
        gpu_score = 0
        if res.avg_gpu_util > 0:
            gpu_score = min(100, res.avg_gpu_util * 1.2)  # Up to 100

        raw_score = (vram_score + ram_score + gpu_score) / 3
        weighted = raw_score * (self._weights.memory / 100)

        return CategoryScore(
            name="memory",
            raw_score=raw_score,
            weighted_score=weighted,
            weight=self._weights.memory,
            details={
                "peak_vram_mb": res.peak_vram_mb,
                "avg_vram_mb": res.avg_vram_mb,
                "vram_efficiency": res.avg_vram_mb / res.peak_vram_mb if res.peak_vram_mb > 0 else 0,
                "peak_ram_mb": res.peak_ram_mb,
                "avg_gpu_util": res.avg_gpu_util,
            },
        )

    def _compute_energy_score(self, metrics: BenchmarkMetrics) -> CategoryScore:
        """Compute energy efficiency score."""
        therm = metrics.thermal

        if therm.avg_energy_per_token <= 0:
            return CategoryScore("energy", 50, 50 * (self._weights.energy / 100), self._weights.energy,
                               {"note": "No energy data, using neutral score"})

        # Lower energy per token is better
        # Target: 0.1 J/token = 100, 0.5 = 70, 1.0 = 40, 2.0 = 10
        energy = therm.avg_energy_per_token

        if energy <= 0.1:
            raw_score = 100
        elif energy <= 0.5:
            raw_score = 70 + (0.5 - energy) * 75
        elif energy <= 1.0:
            raw_score = 40 + (1.0 - energy) * 60
        elif energy <= 2.0:
            raw_score = 10 + (2.0 - energy) * 30
        else:
            raw_score = max(0, 10 - (energy - 2.0) * 5)

        # Bonus for high performance per watt
        if therm.avg_perf_per_watt > 0:
            perf_watt = therm.avg_perf_per_watt
            if perf_watt > 5:
                raw_score = min(100, raw_score + 10)
            elif perf_watt > 2:
                raw_score = min(100, raw_score + 5)

        raw_score = max(0, min(100, raw_score))
        weighted = raw_score * (self._weights.energy / 100)

        return CategoryScore(
            name="energy",
            raw_score=raw_score,
            weighted_score=weighted,
            weight=self._weights.energy,
            details={
                "avg_energy_per_token_j": therm.avg_energy_per_token,
                "avg_gpu_power_w": therm.avg_gpu_power,
                "avg_cpu_power_w": therm.avg_cpu_power,
                "perf_per_watt": therm.avg_perf_per_watt,
                "throttling_events": therm.throttling_events,
            },
        )

    def _compute_context_score(self, metrics: BenchmarkMetrics) -> CategoryScore:
        """Compute context handling score."""
        # This would need context-specific benchmark results
        # For now, return a placeholder based on available data
        qual = metrics.quality

        scores = []
        details = {}

        if qual.retrieval_precision is not None:
            scores.append(qual.retrieval_precision * 100)
            details["retrieval_precision"] = qual.retrieval_precision

        if qual.retrieval_recall is not None:
            scores.append(qual.retrieval_recall * 100)
            details["retrieval_recall"] = qual.retrieval_recall

        if qual.context_retention is not None:
            scores.append(qual.context_retention * 100)
            details["context_retention"] = qual.context_retention

        if not scores:
            # Neutral score if no context data
            raw_score = 50
            details["note"] = "No context benchmark data"
        else:
            raw_score = mean(scores)

        raw_score = max(0, min(100, raw_score))
        weighted = raw_score * (self._weights.context / 100)

        return CategoryScore(
            name="context",
            raw_score=raw_score,
            weighted_score=weighted,
            weight=self._weights.context,
            details=details,
        )

    def update_config(self, weights: ScoreWeights, thresholds: GradeThresholds):
        """Update scoring configuration."""
        self._weights = weights
        self._thresholds = thresholds

    def get_weights(self) -> ScoreWeights:
        return self._weights

    def get_thresholds(self) -> GradeThresholds:
        return self._thresholds


class EloRatingSystem:
    """Elo rating system for model comparison."""

    def __init__(self, k_factor: float = 32, initial_rating: float = 1500):
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        self._ratings: Dict[str, float] = {}

    def get_rating(self, model_name: str) -> float:
        """Get current Elo rating for model."""
        return self._ratings.get(model_name, self.initial_rating)

    def set_rating(self, model_name: str, rating: float):
        """Set Elo rating for model."""
        self._ratings[model_name] = rating

    def update_ratings(self, model_a: str, model_b: str, score_a: float):
        """
        Update ratings after a match.

        Args:
            model_a: First model name
            model_b: Second model name
            score_a: Score for model A (1.0 = win, 0.5 = draw, 0.0 = loss)
        """
        rating_a = self.get_rating(model_a)
        rating_b = self.get_rating(model_b)

        # Expected scores
        expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
        expected_b = 1 - expected_a

        # Update ratings
        new_rating_a = rating_a + self.k_factor * (score_a - expected_a)
        new_rating_b = rating_b + self.k_factor * ((1 - score_a) - expected_b)

        self._ratings[model_a] = new_rating_a
        self._ratings[model_b] = new_rating_b

        return new_rating_a, new_rating_b

    def get_rankings(self) -> List[Dict[str, Any]]:
        """Get all models ranked by Elo rating."""
        sorted_models = sorted(
            self._ratings.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [
            {"rank": i + 1, "model": name, "elo": int(rating)}
            for i, (name, rating) in enumerate(sorted_models)
        ]

    def compute_win_probability(self, model_a: str, model_b: str) -> float:
        """Compute probability of model_a beating model_b."""
        rating_a = self.get_rating(model_a)
        rating_b = self.get_rating(model_b)
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def bulk_update(self, results: List[Tuple[str, str, float]]):
        """Update ratings from multiple match results."""
        for model_a, model_b, score_a in results:
            self.update_ratings(model_a, model_b, score_a)


def compute_pareto_frontier(
    models: List[Dict[str, Any]],
    x_metric: str,  # e.g., "latency" (lower better)
    y_metric: str,  # e.g., "throughput" (higher better)
) -> List[Dict[str, Any]]:
    """Compute Pareto frontier for model comparison."""
    if not models:
        return []

    # Sort by x metric (ascending for lower-better, descending for higher-better)
    # We assume x_metric is "lower is better" and y_metric is "higher is better"
    sorted_models = sorted(models, key=lambda m: m.get(x_metric, float('inf')))

    pareto = []
    best_y = -float('inf')

    for model in sorted_models:
        y = model.get(y_metric, -float('inf'))
        if y > best_y:
            pareto.append(model)
            best_y = y

    return pareto


def compute_model_ranking(
    models: List[Dict[str, Any]],
    metrics: Dict[str, float],  # metric_name -> weight
    higher_better: Dict[str, bool] = None
) -> List[Dict[str, Any]]:
    """Rank models by weighted composite score."""
    if not models:
        return []

    if higher_better is None:
        higher_better = {}

    # Normalize each metric to 0-1 scale
    for metric_name in metrics:
        values = [m.get(metric_name, 0) for m in models]
        min_v = min(values)
        max_v = max(values)
        range_v = max_v - min_v if max_v != min_v else 1

        for model in models:
            normalized = (model.get(metric_name, 0) - min_v) / range_v
            if not higher_better.get(metric_name, True):
                normalized = 1 - normalized
            model[f"normalized_{metric_name}"] = normalized

    # Compute weighted score
    for model in models:
        score = sum(
            model.get(f"normalized_{name}", 0) * weight
            for name, weight in metrics.items()
        )
        model["composite_score"] = score

    # Sort by composite score
    sorted_models = sorted(models, key=lambda m: m["composite_score"], reverse=True)

    # Add rank
    for i, model in enumerate(sorted_models):
        model["rank"] = i + 1

    return sorted_models