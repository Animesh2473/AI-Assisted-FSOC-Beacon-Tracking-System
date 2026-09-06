"""Basic sanity tests for the fsoc_tracker package."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fsoc_tracker.simulator import Simulation, DEFAULT_CONFIG
from fsoc_tracker.target import Target
from fsoc_tracker.detector import BeaconDetector
from fsoc_tracker.tracker import CentroidKalmanTracker


def test_target_motions_run():
    for motion in Target.MOTIONS:
        t = Target(motion=motion, seed=1)
        for _ in range(30):
            x, y = t.step(1 / 30)
            assert 0 <= x <= t.W
            assert 0 <= y <= t.H


def test_tracker_predict_without_detection():
    trk = CentroidKalmanTracker()
    pos, locked = trk.update(None)
    assert locked is False
    assert pos is not None


def test_tracker_locks_on_detection():
    trk = CentroidKalmanTracker()
    for _ in range(3):
        pos, locked = trk.update((100.0, 50.0))
    assert locked is True
    assert abs(pos[0] - 100.0) < 5
    assert abs(pos[1] - 50.0) < 5


def test_detector_ignores_pure_noise():
    import numpy as np
    det = BeaconDetector()
    noise_frame = (np.random.normal(5, 5, (480, 640))).clip(0, 255).astype("uint8")
    assert det.detect(noise_frame) is None


def test_simulation_runs_and_locks():
    cfg = dict(DEFAULT_CONFIG)
    sim = Simulation(cfg)
    summary = sim.run(90)
    assert summary["total_frames"] == 90
    assert summary["lock_retention_rate_pct"] > 50


def test_simulation_all_motions_smoke():
    for motion in ["straight_line", "circular", "figure8", "random", "spiral", "sinusoidal"]:
        cfg = dict(DEFAULT_CONFIG)
        cfg["target_motion"] = motion
        summary = Simulation(cfg).run(30)
        assert summary["total_frames"] == 30


def test_performance_report_fields():
    cfg = dict(DEFAULT_CONFIG)
    sim = Simulation(cfg)
    sim.run(30)
    s = sim.perf.summary()
    for key in ["avg_fps", "lock_retention_rate_pct", "target_loss_pct",
                "simulation_duration_s", "total_frames"]:
        assert key in s
