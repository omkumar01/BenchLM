"""Unit tests for BenchLM scoring engine."""

import pytest
from benchlm.core.scorer import (
    ScoringEngine,
    ScoreWeights,
    GradeThresholds,
    CategoryScore,
    BenchmarkScore,
    EloRatingSystem,
    compute_pareto_frontier,
    compute_model_ranking,
)
from benchlm.core.metrics import (
    BenchmarkMetrics,
    LatencyMetrics,
    ThroughputMetrics,
    ResourceMetrics,
    ThermalMetrics,
    QualityMetrics,
    ReliabilityMetrics,
)


class TestScoreWeights:
    """Tests for ScoreWeights."""

    def test_default_weights(self):
        weights = ScoreWeights()
        total = weights.latency + weights.throughput + weights.quality + \
                weights.reliability + weights.memory + weights.energy + weights.context
        assert total == 100

    def test_validate(self):
        weights = ScoreWeights()
        assert weights.validate() is True

        weights.latency = 50
        assert weights.validate() is False

    def test_normalize(self):
        weights = ScoreWeights(latency=50, throughput=50, quality=50,
                               reliability=50, memory=50, energy=50, context=50)
        weights.normalize()
        total = weights.latency + weights.throughput + weights.quality + \
                weights.reliability + weights.memory + weights.energy + weights.context
        assert abs(total - 100) < 0.01


class TestGradeThresholds:
    """Tests for GradeThresholds."""

    def test_get_grade(self):
        thresholds = GradeThresholds()

        assert thresholds.get_grade(950) == "S+"
        assert thresholds.get_grade(949) == "S"
        assert thresholds.get_grade(900) == "S"
        assert thresholds.get_grade(899) == "A"
        assert thresholds.get_grade(800) == "A"
        assert thresholds.get_grade(799) == "B"
        assert thresholds.get_grade(700) == "B"
        assert thresholds.get_grade(699) == "C"
        assert thresholds.get_grade(600) == "C"
        assert thresholds.get_grade(599) == "D"
        assert thresholds.get_grade(0) == "D"


class TestCategoryScore:
    """Tests for CategoryScore."""

    def test_to_dict(self):
        score = CategoryScore(
            name="latency",
            raw_score=85.5,
            weighted_score=17.1,
            weight=20,
            details={"ttft_p50": 120}
        )

        d = score.to_dict()
        assert d["name"] == "latency"
        assert d["raw_score"] == 85.5
        assert d["weighted_score"] == 17.1
        assert d["weight"] == 20
        assert d["details"]["ttft_p50"] == 120


class TestBenchmarkScore:
    """Tests for BenchmarkScore."""

    def test_to_dict(self):
        score = BenchmarkScore(
            overall_score=847,
            grade="A",
            category_scores=[],
            weights=ScoreWeights(),
            thresholds=GradeThresholds(),
        )

        d = score.to_dict()
        assert d["overall_score"] == 847
        assert d["grade"] == "A"


def create_test_metrics() -> BenchmarkMetrics:
    """Create test benchmark metrics."""
    metrics = BenchmarkMetrics(
        run_id="test",
        model_name="TestModel",
        provider="test",
    )

    # Latency
    metrics.latency = LatencyMetrics(
        ttft_samples=[100000, 120000, 110000, 130000, 115000] * 20,
        tpot_samples=[10000, 12000, 11000, 13000, 11500] * 20,
    )
    metrics.latency.compute_percentiles()

    # Throughput
    metrics.throughput = ThroughputMetrics(
        tps_samples=[80, 85, 82, 88, 83, 87, 84, 86] * 10,
    )
    metrics.throughput.compute_all()

    # Resources
    metrics.resources = ResourceMetrics(
        vram_samples=[6000, 6100, 6200, 6150] * 25,
        ram_samples=[8000, 8100, 8200, 8150] * 25,
        gpu_util_samples=[70, 75, 80, 72] * 25,
        cpu_util_samples=[50, 55, 60, 52] * 25,
    )
    metrics.resources.compute_all()

    # Thermal
    metrics.thermal = ThermalMetrics(
        gpu_temp_samples=[65, 68, 70, 67] * 25,
        gpu_power_samples=[200, 220, 250, 210] * 25,
        cpu_power_samples=[80, 85, 90, 82] * 25,
    )
    metrics.thermal.compute_all()

    # Quality
    metrics.quality = QualityMetrics(
        accuracy=0.85,
        exact_match=0.82,
        f1_score=0.84,
        pass_at_1=0.75,
        retrieval_precision=0.9,
        json_validity=0.95,
        factuality_score=0.88,
    )

    # Reliability
    metrics.reliability = ReliabilityMetrics(
        total_requests=100,
        successful_requests=98,
        failed_requests=2,
        timeout_requests=1,
        oom_requests=0,
    )

    metrics.compute_all()

    return metrics


class TestScoringEngine:
    """Tests for ScoringEngine."""

    def test_compute_score(self):
        engine = ScoringEngine()
        metrics = create_test_metrics()

        score = engine.compute_score(metrics)

        assert 0 <= score.overall_score <= 1000
        assert score.grade in ["S+", "S", "A", "B", "C", "D"]
        assert len(score.category_scores) == 7

        # Check all categories present
        categories = {cs.name for cs in score.category_scores}
        expected = {"latency", "throughput", "quality", "reliability",
                    "memory", "energy", "context"}
        assert categories == expected

        # Check weighted scores sum to overall
        total_weighted = sum(cs.weighted_score for cs in score.category_scores)
        assert abs(total_weighted - score.overall_score) < 0.1

    def test_latency_score(self):
        engine = ScoringEngine()
        metrics = create_test_metrics()

        score = engine.compute_score(metrics)

        latency_cs = next(cs for cs in score.category_scores if cs.name == "latency")
        assert 0 <= latency_cs.raw_score <= 100
        assert latency_cs.weight == 20

    def test_throughput_score(self):
        engine = ScoringEngine()
        metrics = create_test_metrics()

        score = engine.compute_score(metrics)

        throughput_cs = next(cs for cs in score.category_scores if cs.name == "throughput")
        assert 0 <= throughput_cs.raw_score <= 100
        assert throughput_cs.weight == 20

    def test_quality_score(self):
        engine = ScoringEngine()
        metrics = create_test_metrics()

        score = engine.compute_score(metrics)

        quality_cs = next(cs for cs in score.category_scores if cs.name == "quality")
        assert 0 <= quality_cs.raw_score <= 100
        assert quality_cs.weight == 25

    def test_reliability_score(self):
        engine = ScoringEngine()
        metrics = create_test_metrics()

        score = engine.compute_score(metrics)

        reliability_cs = next(cs for cs in score.category_scores if cs.name == "reliability")
        assert 0 <= reliability_cs.raw_score <= 100
        assert reliability_cs.weight == 15

    def test_update_config(self):
        engine = ScoringEngine()
        new_weights = ScoreWeights(latency=30, throughput=30, quality=20,
                                   reliability=10, memory=5, energy=3, context=2)
        new_thresholds = GradeThresholds(s_plus=980, s=930, a=830, b=730, c=630)

        engine.update_config(new_weights, new_thresholds)

        assert engine.get_weights().latency == 30
        assert engine.get_thresholds().s_plus == 980


class TestEloRatingSystem:
    """Tests for EloRatingSystem."""

    def test_initial_rating(self):
        elo = EloRatingSystem(initial_rating=1500)
        assert elo.get_rating("NewModel") == 1500

    def test_set_rating(self):
        elo = EloRatingSystem()
        elo.set_rating("ModelA", 1600)
        assert elo.get_rating("ModelA") == 1600

    def test_update_ratings_win(self):
        elo = EloRatingSystem()
        elo.set_rating("ModelA", 1500)
        elo.set_rating("ModelB", 1500)

        new_a, new_b = elo.update_ratings("ModelA", "ModelB", 1.0)

        assert new_a > 1500
        assert new_b < 1500
        assert elo.get_rating("ModelA") == new_a
        assert elo.get_rating("ModelB") == new_b

    def test_update_ratings_draw(self):
        elo = EloRatingSystem()
        elo.set_rating("ModelA", 1500)
        elo.set_rating("ModelB", 1500)

        new_a, new_b = elo.update_ratings("ModelA", "ModelB", 0.5)

        assert new_a == 1500
        assert new_b == 1500

    def test_update_ratings_loss(self):
        elo = EloRatingSystem()
        elo.set_rating("ModelA", 1500)
        elo.set_rating("ModelB", 1500)

        new_a, new_b = elo.update_ratings("ModelA", "ModelB", 0.0)

        assert new_a < 1500
        assert new_b > 1500

    def test_win_probability(self):
        elo = EloRatingSystem()
        elo.set_rating("ModelA", 1600)
        elo.set_rating("ModelB", 1400)

        prob = elo.compute_win_probability("ModelA", "ModelB")
        assert prob > 0.5

        prob = elo.compute_win_probability("ModelB", "ModelA")
        assert prob < 0.5

    def test_get_rankings(self):
        elo = EloRatingSystem()
        elo.set_rating("ModelA", 1600)
        elo.set_rating("ModelB", 1400)
        elo.set_rating("ModelC", 1500)

        rankings = elo.get_rankings()

        assert len(rankings) == 3
        assert rankings[0]["model"] == "ModelA"
        assert rankings[0]["rank"] == 1
        assert rankings[1]["model"] == "ModelC"
        assert rankings[2]["model"] == "ModelB"

    def test_bulk_update(self):
        elo = EloRatingSystem()
        elo.set_rating("ModelA", 1500)
        elo.set_rating("ModelB", 1500)
        elo.set_rating("ModelC", 1500)

        results = [
            ("ModelA", "ModelB", 1.0),
            ("ModelA", "ModelC", 1.0),
            ("ModelB", "ModelC", 0.5),
        ]

        elo.bulk_update(results)

        assert elo.get_rating("ModelA") > 1500
        assert elo.get_rating("ModelB") < 1500
        assert elo.get_rating("ModelC") < 1500


class TestParetoFrontier:
    """Tests for Pareto frontier computation."""

    def test_basic_pareto(self):
        models = [
            {"name": "A", "latency": 100, "quality": 80},
            {"name": "B", "latency": 120, "quality": 85},
            {"name": "C", "latency": 90, "quality": 75},
            {"name": "D", "latency": 150, "quality": 90},
        ]

        pareto = compute_pareto_frontier(models, "latency", "quality")

        # A, B, D should be on frontier (C is dominated by A)
        pareto_names = {m["name"] for m in pareto}
        assert "A" in pareto_names
        assert "B" in pareto_names
        assert "D" in pareto_names
        assert "C" not in pareto_names

    def test_all_dominated(self):
        models = [
            {"name": "A", "latency": 100, "quality": 80},
            {"name": "B", "latency": 110, "quality": 75},
        ]

        pareto = compute_pareto_frontier(models, "latency", "quality")

        assert len(pareto) == 1
        assert pareto[0]["name"] == "A"


class TestModelRanking:
    """Tests for model ranking."""

    def test_basic_ranking(self):
        models = [
            {"name": "A", "latency": 100, "tps": 80},
            {"name": "B", "latency": 120, "tps": 90},
            {"name": "C", "latency": 90, "tps": 70},
        ]

        metrics = {"latency": 0.5, "tps": 0.5}
        higher_better = {"latency": False, "tps": True}

        ranked = compute_model_ranking(models, metrics, higher_better)

        assert len(ranked) == 3
        assert ranked[0]["rank"] == 1
        assert "composite_score" in ranked[0]

    def test_weighted_ranking(self):
        models = [
            {"name": "A", "latency": 100, "quality": 80},
            {"name": "B", "latency": 120, "quality": 90},
        ]

        # Quality matters more
        metrics = {"latency": 0.3, "quality": 0.7}
        higher_better = {"latency": False, "quality": True}

        ranked = compute_model_ranking(models, metrics, higher_better)

        # B should win due to higher quality weight
        assert ranked[0]["name"] == "B"