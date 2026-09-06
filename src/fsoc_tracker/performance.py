"""Real-time performance metrics collection and reporting."""
import csv
import time
import statistics as st


class PerformanceLogger:
    def __init__(self):
        self.t0 = time.time()
        self.frame_times = []
        self.errors = []          # tracking error in pixels, per frame (when locked)
        self.locked_flags = []    # bool per frame
        self.acquisition_time = None
        self._acquired_once = False
        self.reacquisition_times = []
        self._lost_since = None
        self.target_loss_frames = 0
        self.total_frames = 0
        self.rows = []

    def start_frame(self):
        self._frame_t0 = time.time()

    def end_frame(self, locked, error_px, sim_time_s):
        dt = time.time() - self._frame_t0
        self.frame_times.append(dt)
        self.total_frames += 1
        self.locked_flags.append(bool(locked))

        if locked:
            if error_px is not None:
                self.errors.append(error_px)
            if not self._acquired_once:
                self.acquisition_time = sim_time_s
                self._acquired_once = True
            if self._lost_since is not None:
                self.reacquisition_times.append(sim_time_s - self._lost_since)
                self._lost_since = None
        else:
            self.target_loss_frames += 1
            if self._acquired_once and self._lost_since is None:
                self._lost_since = sim_time_s

        self.rows.append({
            "frame": self.total_frames,
            "sim_time_s": round(sim_time_s, 4),
            "locked": int(locked),
            "tracking_error_px": round(error_px, 3) if error_px is not None else "",
            "frame_proc_time_s": round(dt, 5),
        })

    def summary(self):
        fps = 1.0 / st.mean(self.frame_times) if self.frame_times else 0.0
        avg_err = st.mean(self.errors) if self.errors else None
        max_err = max(self.errors) if self.errors else None
        lock_retention = (sum(self.locked_flags) / len(self.locked_flags) * 100
                           if self.locked_flags else 0.0)
        target_loss_pct = (self.target_loss_frames / self.total_frames * 100
                            if self.total_frames else 0.0)
        avg_reacq = st.mean(self.reacquisition_times) if self.reacquisition_times else None

        return {
            "simulation_duration_s": round(time.time() - self.t0, 2),
            "total_frames": self.total_frames,
            "avg_fps": round(fps, 2),
            "acquisition_time_s": round(self.acquisition_time, 3) if self.acquisition_time else None,
            "avg_tracking_error_px": round(avg_err, 3) if avg_err is not None else None,
            "max_tracking_error_px": round(max_err, 3) if max_err is not None else None,
            "lock_retention_rate_pct": round(lock_retention, 2),
            "target_loss_pct": round(target_loss_pct, 2),
            "avg_reacquisition_time_s": round(avg_reacq, 3) if avg_reacq is not None else None,
            "avg_processing_time_ms": round(st.mean(self.frame_times) * 1000, 3) if self.frame_times else 0,
        }

    def save_csv(self, path):
        if not self.rows:
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.rows[0].keys()))
            writer.writeheader()
            writer.writerows(self.rows)

    def save_report(self, path):
        s = self.summary()
        with open(path, "w") as f:
            f.write("FSOC Virtual Camera Tracking - Performance Report\n")
            f.write("=" * 52 + "\n")
            for k, v in s.items():
                f.write(f"{k:30s}: {v}\n")
