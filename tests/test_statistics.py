"""Unit tests for BenchLM statistics engine."""

import pytest
import math
from benchlm.core.statistics import (
    compute_percentiles,
    compute_confidence_interval,
    compute_statistical_summary,
    compare_samples,
    detect_outliers,
    correlation_analysis,
    regression_analysis,
    anova_analysis,
    compute_trend,
    StatisticsEngine,
    PercentileResult,
    ConfidenceInterval,
    StatisticalSummary,
)


class TestPercentiles:
    """Tests for percentile computation."""

    def test_basic_percentiles(self):
        data = list(range(100))
        result = compute_percentiles(data)

        assert abs(result[50] - 49.5) < 0.1
        assert abs(result[90] - 89.1) < 0.1
        assert abs(result[95] - 94.05) < 0.1
        assert abs(result[99] - 98.01) < 0.1

    def test_empty_data(self):
        result = compute_percentiles([])
        assert result == {}

    def test_single_value(self):
        result = compute_percentiles([42])
        for p in [50, 90, 95, 99]:
            assert result[p] == 42


class TestConfidenceInterval:
    """Tests for confidence interval computation."""

    def test_t_distribution(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ci = compute_confidence_interval(data, confidence=0.95, method="t")

        assert ci.confidence == 0.95
        assert ci.method == "t-distribution"
        assert ci.lower < ci.upper
        assert ci.lower < 5.5 < ci.upper

    def test_normal_distribution(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ci = compute_confidence_interval(data, confidence=0.95, method="normal")

        assert ci.method == "normal"
        assert ci.lower < ci.upper

    def test_bootstrap_method(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ci = compute_confidence_interval(data, confidence=0.95, method="bootstrap")

        assert ci.method == "bootstrap"
        assert ci.lower < ci.upper

    def test_insufficient_data(self):
        ci = compute_confidence_interval([5], confidence=0.95)
        assert ci.lower == 0
        assert ci.upper == 0


class TestStatisticalSummary:
    """Tests for statistical summary computation."""

    def test_normal_data(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        summary = compute_statistical_summary(data)

        assert summary.count == 10
        assert summary.mean == 5.5
        assert summary.median == 5.5
        assert summary.min == 1
        assert summary.max == 10
        assert summary.variance > 0
        assert summary.std > 0

        assert summary.percentiles.p50 == 5.5
        assert summary.percentiles.p90 > summary.percentiles.p50
        assert summary.percentiles.p99 > summary.percentiles.p90

        assert summary.confidence_interval.lower < summary.mean < summary.confidence_interval.upper

    def test_empty_data(self):
        summary = compute_statistical_summary([])
        assert summary.count == 0
        assert summary.mean == 0

    def test_skewness_kurtosis(self):
        data = [1, 1, 1, 2, 2, 3, 3, 4, 5, 10, 20]
        summary = compute_statistical_summary(data)

        assert summary.skewness > 0
        assert summary.kurtosis != 0


class TestCompareSamples:
    """Tests for sample comparison."""

    def test_mann_whitney(self):
        sample1 = [1, 2, 3, 4, 5]
        sample2 = [6, 7, 8, 9, 10]
        result = compare_samples(sample1, sample2, test="mann-whitney")

        assert "p_value" in result
        assert result["significant"] is True
        assert "effect_size" in result

    def test_t_test(self):
        sample1 = [1, 2, 3, 4, 5]
        sample2 = [6, 7, 8, 9, 10]
        result = compare_samples(sample1, sample2, test="t-test")

        assert "p_value" in result
        assert result["significant"] is True
        assert "t_statistic" in result

    def test_wilcoxon_paired(self):
        sample1 = [1, 2, 3, 4, 5]
        sample2 = [2, 3, 4, 5, 6]
        result = compare_samples(sample1, sample2, test="wilcoxon")

        assert "p_value" in result
        assert "w_statistic" in result

    def test_wilcoxon_unequal_length(self):
        sample1 = [1, 2, 3]
        sample2 = [2, 3, 4, 5]
        result = compare_samples(sample1, sample2, test="wilcoxon")

        assert "error" in result

    def test_effect_size_interpretation(self):
        sample1 = [1, 2, 3]
        sample2 = [100, 101, 102]
        result = compare_samples(sample1, sample2)

        assert abs(result["effect_size"]) > 0.8
        assert result["effect_size_interpretation"] == "large"


class TestDetectOutliers:
    """Tests for outlier detection."""

    def test_iqr_method(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]
        outliers = detect_outliers(data, method="iqr")

        assert 9 in outliers

    def test_zscore_method(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 50]
        outliers = detect_outliers(data, method="zscore")

        assert 9 in outliers

    def test_no_outliers(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        outliers = detect_outliers(data, method="iqr")

        assert len(outliers) == 0


class TestCorrelationAnalysis:
    """Tests for correlation analysis."""

    def test_pearson_positive(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        result = correlation_analysis(x, y, method="pearson")

        assert result["correlation"] == 1.0
        assert result["significant"] is True
        assert result["interpretation"] == "very strong"

    def test_pearson_negative(self):
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        result = correlation_analysis(x, y, method="pearson")

        assert result["correlation"] == -1.0
        assert result["significant"] is True

    def test_spearman(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        result = correlation_analysis(x, y, method="spearman")

        assert result["correlation"] == -1.0


class TestRegressionAnalysis:
    """Tests for regression analysis."""

    def test_linear_regression(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        result = regression_analysis(x, y)

        assert abs(result["slope"] - 2.0) < 0.01
        assert abs(result["intercept"]) < 0.01
        assert result["r_squared"] == 1.0
        assert result["significant"] is True


class TestANOVA:
    """Tests for ANOVA analysis."""

    def test_significant_difference(self):
        group1 = [1, 2, 3]
        group2 = [4, 5, 6]
        group3 = [7, 8, 9]
        result = anova_analysis([group1, group2, group3])

        assert result["significant"] is True
        assert result["p_value"] < 0.05
        assert result["eta_squared"] > 0


class TestComputeTrend:
    """Tests for trend analysis."""

    def test_increasing_trend(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = compute_trend(data)

        assert result["mann_kendall"]["trend"] == "increasing"
        assert result["mann_kendall"]["significant"] is True
        assert result["slope_per_unit"] > 0

    def test_decreasing_trend(self):
        data = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        result = compute_trend(data)

        assert result["mann_kendall"]["trend"] == "decreasing"
        assert result["slope_per_unit"] < 0


class TestStatisticsEngine:
    """Tests for StatisticsEngine class."""

    def test_analyze_latency(self):
        engine = StatisticsEngine()
        latencies = [100000, 120000, 110000, 130000, 115000] * 20
        result = engine.analyze_latency(latencies)

        assert "ttft_ms" in result
        assert "ttft_p99_ms" in result
        assert "jitter_ms" in result
        assert "outliers" in result

    def test_analyze_throughput(self):
        engine = StatisticsEngine()
        tps = [80, 85, 82, 88, 83, 87, 84, 86] * 10
        result = engine.analyze_throughput(tps)

        assert "mean" in result
        assert "coefficient_of_variation" in result
        assert "stability" in result

    def test_analyze_scaling(self):
        engine = StatisticsEngine()
        concurrency = [1, 2, 4, 8]
        metrics = [
            [100, 102, 98],
            [190, 195, 185],
            [350, 360, 340],
            [600, 620, 580],
        ]
        result = engine.analyze_scaling(concurrency, metrics)

        assert "efficiency" in result
        assert "avg_efficiency" in result
        assert 0 < result["avg_efficiency"] <= 1

    def test_compare_models(self):
        engine = StatisticsEngine()
        model_data = {
            "ModelA": [80, 82, 81, 83],
            "ModelB": [90, 92, 89, 91],
            "ModelC": [70, 72, 71, 73],
        }
        result = engine.compare_models(model_data, "latency")

        assert "ModelA_vs_ModelB" in result
        assert "anova" in result
        assert "best_model" in result