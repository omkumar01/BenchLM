"""Statistics engine for BenchLM - computes statistical summaries and analysis."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from statistics import mean, median, stdev, variance
from scipy import stats
import numpy as np


@dataclass
class PercentileResult:
    """Result of percentile computation."""

    p50: float
    p75: float
    p90: float
    p95: float
    p99: float
    p99_9: float


@dataclass
class ConfidenceInterval:
    """Confidence interval result."""

    lower: float
    upper: float
    confidence: float = 0.95
    method: str = "t-distribution"


@dataclass
class StatisticalSummary:
    """Complete statistical summary."""

    count: int
    mean: float
    median: float
    std: float
    variance: float
    min: float
    max: float
    percentiles: PercentileResult
    confidence_interval: ConfidenceInterval
    skewness: float
    kurtosis: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "mean": self.mean,
            "median": self.median,
            "std": self.std,
            "variance": self.variance,
            "min": self.min,
            "max": self.max,
            "percentiles": {
                "p50": self.percentiles.p50,
                "p75": self.percentiles.p75,
                "p90": self.percentiles.p90,
                "p95": self.percentiles.p95,
                "p99": self.percentiles.p99,
                "p99_9": self.percentiles.p99_9,
            },
            "confidence_interval": {
                "lower": self.confidence_interval.lower,
                "upper": self.confidence_interval.upper,
                "confidence": self.confidence_interval.confidence,
            },
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
        }


def compute_percentiles(data: List[float], percentiles: List[float] = None) -> Dict[float, float]:
    """Compute percentiles for data."""
    if not data:
        return {}

    if percentiles is None:
        percentiles = [50, 75, 90, 95, 99, 99.9]

    sorted_data = sorted(data)
    n = len(sorted_data)

    result = {}
    for p in percentiles:
        idx = (n - 1) * p / 100
        if idx.is_integer():
            result[p] = sorted_data[int(idx)]
        else:
            lower = sorted_data[int(idx)]
            upper = sorted_data[int(idx) + 1]
            result[p] = lower + (upper - lower) * (idx - int(idx))

    return result


def compute_confidence_interval(
    data: List[float],
    confidence: float = 0.95,
    method: str = "t"
) -> ConfidenceInterval:
    """Compute confidence interval for mean."""
    if not data or len(data) < 2:
        return ConfidenceInterval(0, 0, confidence, method)

    n = len(data)
    m = mean(data)
    se = stdev(data) / math.sqrt(n) if n > 1 else 0

    if method == "t":
        # t-distribution
        from scipy.stats import t
        t_critical = t.ppf((1 + confidence) / 2, n - 1)
        margin = t_critical * se
    elif method == "normal":
        # Normal distribution (z-score)
        from scipy.stats import norm
        z_critical = norm.ppf((1 + confidence) / 2)
        margin = z_critical * se
    elif method == "bootstrap":
        # Bootstrap percentile method
        bootstrapped_means = []
        for _ in range(1000):
            sample = np.random.choice(data, n, replace=True)
            bootstrapped_means.append(mean(sample))
        alpha = (1 - confidence) / 2
        lower = np.percentile(bootstrapped_means, alpha * 100)
        upper = np.percentile(bootstrapped_means, (1 - alpha) * 100)
        return ConfidenceInterval(lower, upper, confidence, "bootstrap")
    else:
        raise ValueError(f"Unknown method: {method}")

    return ConfidenceInterval(m - margin, m + margin, confidence, method)


def compute_statistical_summary(data: List[float]) -> StatisticalSummary:
    """Compute complete statistical summary."""
    if not data:
        return StatisticalSummary(
            count=0, mean=0, median=0, std=0, variance=0,
            min=0, max=0,
            percentiles=PercentileResult(0, 0, 0, 0, 0, 0),
            confidence_interval=ConfidenceInterval(0, 0),
            skewness=0, kurtosis=0,
        )

    n = len(data)
    m = mean(data)
    med = median(data)
    std = stdev(data) if n > 1 else 0
    var = variance(data) if n > 1 else 0
    min_val = min(data)
    max_val = max(data)

    # Percentiles
    p = compute_percentiles(data)
    percentiles = PercentileResult(
        p50=p.get(50, 0),
        p75=p.get(75, 0),
        p90=p.get(90, 0),
        p95=p.get(95, 0),
        p99=p.get(99, 0),
        p99_9=p.get(99.9, 0),
    )

    # Confidence interval
    ci = compute_confidence_interval(data)

    # Skewness and kurtosis
    if n >= 3:
        skewness = stats.skew(data)
        kurtosis = stats.kurtosis(data)
    else:
        skewness = 0
        kurtosis = 0

    return StatisticalSummary(
        count=n,
        mean=m,
        median=med,
        std=std,
        variance=var,
        min=min_val,
        max=max_val,
        percentiles=percentiles,
        confidence_interval=ci,
        skewness=skewness,
        kurtosis=kurtosis,
    )


def compare_samples(
    sample1: List[float],
    sample2: List[float],
    test: str = "mann-whitney"
) -> Dict[str, Any]:
    """Compare two samples statistically."""
    if not sample1 or not sample2:
        return {"error": "Empty samples"}

    result = {
        "sample1": compute_statistical_summary(sample1).to_dict(),
        "sample2": compute_statistical_summary(sample2).to_dict(),
    }

    if test == "mann-whitney":
        # Mann-Whitney U test (non-parametric)
        u_stat, p_value = stats.mannwhitneyu(sample1, sample2, alternative='two-sided')
        result["test"] = "mann-whitney"
        result["u_statistic"] = u_stat
        result["p_value"] = p_value
        result["significant"] = p_value < 0.05

    elif test == "t-test":
        # Independent t-test
        t_stat, p_value = stats.ttest_ind(sample1, sample2, equal_var=False)
        result["test"] = "t-test"
        result["t_statistic"] = t_stat
        result["p_value"] = p_value
        result["significant"] = p_value < 0.05

    elif test == "wilcoxon":
        # Wilcoxon signed-rank test (paired)
        if len(sample1) == len(sample2):
            w_stat, p_value = stats.wilcoxon(sample1, sample2)
            result["test"] = "wilcoxon"
            result["w_statistic"] = w_stat
            result["p_value"] = p_value
            result["significant"] = p_value < 0.05
        else:
            result["error"] = "Samples must have equal length for Wilcoxon test"

    # Effect size (Cohen's d)
    pooled_std = math.sqrt((stdev(sample1)**2 + stdev(sample2)**2) / 2)
    if pooled_std > 0:
        cohens_d = (mean(sample1) - mean(sample2)) / pooled_std
        result["effect_size"] = cohens_d
        result["effect_size_interpretation"] = (
            "negligible" if abs(cohens_d) < 0.2 else
            "small" if abs(cohens_d) < 0.5 else
            "medium" if abs(cohens_d) < 0.8 else
            "large"
        )

    return result


def detect_outliers(data: List[float], method: str = "iqr") -> List[int]:
    """Detect outlier indices in data."""
    if not data:
        return []

    if method == "iqr":
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return [i for i, v in enumerate(data) if v < lower or v > upper]

    elif method == "zscore":
        m = mean(data)
        s = stdev(data) if len(data) > 1 else 0
        if s == 0:
            return []
        return [i for i, v in enumerate(data) if abs((v - m) / s) > 3]

    elif method == "modified_zscore":
        # Using median and MAD
        med = median(data)
        mad = median([abs(x - med) for x in data])
        if mad == 0:
            return []
        return [i for i, v in enumerate(data) if abs(0.6745 * (v - med) / mad) > 3.5]

    return []


def correlation_analysis(
    x: List[float],
    y: List[float],
    method: str = "pearson"
) -> Dict[str, Any]:
    """Compute correlation between two variables."""
    if len(x) != len(y) or not x:
        return {"error": "Invalid input"}

    if method == "pearson":
        r, p = stats.pearsonr(x, y)
    elif method == "spearman":
        r, p = stats.spearmanr(x, y)
    elif method == "kendall":
        r, p = stats.kendalltau(x, y)
    else:
        raise ValueError(f"Unknown method: {method}")

    return {
        "correlation": r,
        "p_value": p,
        "significant": p < 0.05,
        "method": method,
        "n": len(x),
        "interpretation": (
            "negligible" if abs(r) < 0.1 else
            "weak" if abs(r) < 0.3 else
            "moderate" if abs(r) < 0.5 else
            "strong" if abs(r) < 0.7 else
            "very strong"
        ),
    }


def regression_analysis(
    x: List[float],
    y: List[float]
) -> Dict[str, Any]:
    """Linear regression analysis."""
    if len(x) != len(y) or len(x) < 2:
        return {"error": "Invalid input"}

    slope, intercept, r, p, se = stats.linregress(x, y)

    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r**2,
        "r": r,
        "p_value": p,
        "std_error": se,
        "equation": f"y = {slope:.4f}x + {intercept:.4f}",
        "significant": p < 0.05,
    }


def anova_analysis(groups: List[List[float]]) -> Dict[str, Any]:
    """One-way ANOVA."""
    if not groups or any(not g for g in groups):
        return {"error": "Invalid groups"}

    f_stat, p_value = stats.f_oneway(*groups)

    # Effect size (eta-squared)
    all_values = [v for g in groups for v in g]
    grand_mean = mean(all_values)
    ss_between = sum(len(g) * (mean(g) - grand_mean)**2 for g in groups)
    ss_total = sum((v - grand_mean)**2 for v in all_values)
    eta_squared = ss_between / ss_total if ss_total > 0 else 0

    return {
        "f_statistic": f_stat,
        "p_value": p_value,
        "significant": p_value < 0.05,
        "eta_squared": eta_squared,
        "groups": len(groups),
        "total_n": len(all_values),
    }


def compute_trend(data: List[float], timestamps: List[float] = None) -> Dict[str, Any]:
    """Compute trend analysis for time series data."""
    if not data or len(data) < 2:
        return {"error": "Insufficient data"}

    if timestamps is None:
        timestamps = list(range(len(data)))

    # Linear regression for trend
    reg = regression_analysis(timestamps, data)

    # Mann-Kendall trend test
    n = len(data)
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            if data[j] > data[i]:
                s += 1
            elif data[j] < data[i]:
                s -= 1

    # Variance of S
    var_s = n * (n - 1) * (2 * n + 5) / 18
    if var_s > 0:
        z = (s - 1) / math.sqrt(var_s) if s > 0 else (s + 1) / math.sqrt(var_s) if s < 0 else 0
        from scipy.stats import norm
        p_value = 2 * (1 - norm.cdf(abs(z)))
    else:
        z = 0
        p_value = 1

    return {
        "linear_trend": reg,
        "mann_kendall": {
            "s": s,
            "z": z,
            "p_value": p_value,
            "trend": "increasing" if s > 0 else "decreasing" if s < 0 else "no trend",
            "significant": p_value < 0.05,
        },
        "slope_per_unit": reg.get("slope", 0),
    }


class StatisticsEngine:
    """High-level statistics engine for benchmark analysis."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def analyze_latency(self, latencies: List[int]) -> Dict[str, Any]:
        """Analyze latency samples (microseconds)."""
        if not latencies:
            return {}

        # Convert to milliseconds for readability
        latencies_ms = [l / 1000 for l in latencies]

        summary = compute_statistical_summary(latencies_ms)
        result = summary.to_dict()

        # Add latency-specific metrics
        result["ttft_ms"] = result["mean"]
        result["ttft_p99_ms"] = result["percentiles"]["p99"]
        result["jitter_ms"] = summary.percentiles.p99_9 - summary.percentiles.p50

        # Outlier detection
        outliers = detect_outliers(latencies_ms)
        result["outliers"] = {
            "count": len(outliers),
            "indices": outliers,
            "percentage": len(outliers) / len(latencies) * 100,
        }

        return result

    def analyze_throughput(self, tps_samples: List[float]) -> Dict[str, Any]:
        """Analyze throughput samples (tokens/second)."""
        if not tps_samples:
            return {}

        summary = compute_statistical_summary(tps_samples)
        result = summary.to_dict()

        # Stability metrics
        cv = summary.std / summary.mean if summary.mean > 0 else 0  # Coefficient of variation
        result["coefficient_of_variation"] = cv
        result["stability"] = "stable" if cv < 0.1 else "moderate" if cv < 0.2 else "unstable"

        return result

    def analyze_scaling(
        self,
        concurrency_levels: List[int],
        metrics: List[List[float]]
    ) -> Dict[str, Any]:
        """Analyze scaling behavior across concurrency levels."""
        if len(concurrency_levels) != len(metrics):
            return {"error": "Mismatched inputs"}

        # Compute mean metric at each level
        means = [mean(m) for m in metrics if m]
        if not means:
            return {}

        # Linear scaling efficiency
        ideal = [means[0] * (c / concurrency_levels[0]) for c in concurrency_levels]
        efficiency = [m / i if i > 0 else 0 for m, i in zip(means, ideal)]

        return {
            "concurrency_levels": concurrency_levels,
            "means": means,
            "ideal_scaling": ideal,
            "efficiency": efficiency,
            "avg_efficiency": mean(efficiency) if efficiency else 0,
            "max_efficiency": max(efficiency) if efficiency else 0,
        }

    def compare_models(
        self,
        model_data: Dict[str, List[float]],
        metric_name: str = "latency"
    ) -> Dict[str, Any]:
        """Compare multiple models statistically."""
        if len(model_data) < 2:
            return {"error": "Need at least 2 models"}

        models = list(model_data.keys())
        results = {}

        # Pairwise comparisons
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                m1, m2 = models[i], models[j]
                comparison = compare_samples(model_data[m1], model_data[m2])
                results[f"{m1}_vs_{m2}"] = comparison

        # ANOVA for overall difference
        groups = [model_data[m] for m in models]
        anova = anova_analysis(groups)
        results["anova"] = anova

        # Best model
        best_model = max(models, key=lambda m: mean(model_data[m]) if metric_name == "throughput" else -mean(model_data[m]))
        results["best_model"] = best_model

        return results