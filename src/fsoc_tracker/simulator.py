"""Top-level orchestrator: wires target, camera, disturbances, detector,
tracker, controller and performance logger into one runnable simulation."""
import time
import numpy as np
import cv2

from .target import Target
from .camera import VirtualCamera
from .detector import BeaconDetector
from .tracker import CentroidKalmanTracker
from .controller import PTController
from .performance import PerformanceLogger
from . import disturbances as dist

DEFAULT_CONFIG = {
    "world_size": (2000, 2000),
    "camera_resolution": (640, 480),
    "camera_fov_deg": (4.0, 3.0),
    "camera_update_rate_hz": 30,
    "max_pan_speed": 5.0,
    "max_tilt_speed": 5.0,
    "target_shape": "square",
    "target_size": 10,
    "target_motion": "circular",
    "target_speed": 150.0,
    "num_targets": 1,
    "noise_types": ["gaussian"],
    "noise_std": 10,
    "salt_pepper_amount": 0.05,
    "atmosphere": "clear",
    "atmosphere_intensity": 0.4,
    "camera_jitter_px": 5,
    "platform_motion": "linear",
    "platform_motion_px": 5,
    "initial_cue_offset_px": 15,
    "seed": 42,
}


class Simulation:
    def __init__(self, config=None):
        self.cfg = {**DEFAULT_CONFIG, **(config or {})}
        np.random.seed(self.cfg["seed"])

        self.targets = [
            Target(world_size=self.cfg["world_size"],
                   motion=self.cfg["target_motion"],
                   size=self.cfg["target_size"],
                   shape=self.cfg["target_shape"],
                   speed=self.cfg["target_speed"],
                   seed=self.cfg["seed"] + i)
            for i in range(self.cfg["num_targets"])
        ]

        self.camera = VirtualCamera(
            world_size=self.cfg["world_size"],
            resolution=self.cfg["camera_resolution"],
            fov_deg=self.cfg["camera_fov_deg"],
            max_pan_speed=self.cfg["max_pan_speed"],
            max_tilt_speed=self.cfg["max_tilt_speed"],
            update_rate_hz=self.cfg["camera_update_rate_hz"],
        )

        # Initial pointing cue: real PAT systems slew to a coarse ephemeris
        # / GPS-derived estimate before the optical acquisition search takes
        # over. We seed the camera boresight near the target's start
        # position (with a deliberate offset) so the search/track loop has
        # a realistic starting point rather than an arbitrary blind spot.
        if self.targets:
            tx0, ty0 = self.targets[0].position
            cue_offset = self.cfg.get("initial_cue_offset_px", 60)
            self.camera.cx = tx0 + cue_offset
            self.camera.cy = ty0 + cue_offset

        self.detector = BeaconDetector()
        self.tracker = CentroidKalmanTracker()
        self.controller = PTController(
            image_size=self.cfg["camera_resolution"],
            fov_deg=self.cfg["camera_fov_deg"],
        )
        self.perf = PerformanceLogger()
        self.platform = dist.PlatformMotion(
            mode=self.cfg["platform_motion"],
            max_px_per_frame=self.cfg["platform_motion_px"],
        )

        self.sim_time = 0.0
        self.dt = 1.0 / self.cfg["camera_update_rate_hz"]

    def _render_world(self):
        W, H = self.cfg["world_size"]
        canvas = np.zeros((H, W), dtype=np.uint8)
        for t in self.targets:
            x, y = t.position
            half = t.size // 2
            if t.shape == "circle":
                cv2.circle(canvas, (int(x), int(y)), half, 255, -1)
            else:
                cv2.rectangle(canvas, (int(x - half), int(y - half)),
                              (int(x + half), int(y + half)), 255, -1)
        return canvas

    def step(self):
        """Advance the simulation by one frame. Returns a dict with the
        rendered frame, overlay info and running performance summary."""
        self.perf.start_frame()

        for t in self.targets:
            t.step(self.dt)

        world = self._render_world()

        plat_dx, plat_dy = self.platform.step()
        jitter_dx, jitter_dy = dist.camera_jitter(self.cfg["camera_jitter_px"])
        total_jitter = (plat_dx + jitter_dx, plat_dy + jitter_dy)

        raw_frame = self.camera.render(world, jitter=total_jitter)
        frame = dist.apply_disturbances(raw_frame, self.cfg)

        prior = self.tracker.pos if self.tracker.locked else None
        det = self.detector.detect(frame, prior_pos=prior)
        det_xy = (det["cx"], det["cy"]) if det else None

        (tx, ty), locked = self.tracker.update(det_xy)

        if locked:
            dpan, dtilt = self.controller.track((tx, ty))
        else:
            dpan, dtilt = self.controller.search()
        self.camera.move(dpan, dtilt, self.dt)

        # ground truth for error metric: primary target's true image position
        gt_frame_pos = self.camera.world_to_frame_coords(*self.targets[0].position)
        error_px = None
        if gt_frame_pos is not None and locked:
            error_px = float(np.hypot(tx - gt_frame_pos[0], ty - gt_frame_pos[1]))

        self.sim_time += self.dt
        self.perf.end_frame(locked, error_px, self.sim_time)

        return {
            "frame": frame,
            "detection": det,
            "track_pos": (tx, ty),
            "locked": locked,
            "gt_frame_pos": gt_frame_pos,
            "sim_time": self.sim_time,
            "summary": self.perf.summary(),
        }

    def run(self, num_frames, on_frame=None):
        """Run num_frames steps. Optionally calls on_frame(result_dict, i)."""
        for i in range(num_frames):
            result = self.step()
            if on_frame is not None:
                on_frame(result, i)
        return self.perf.summary()

    @staticmethod
    def annotate(frame, result):
        """Draw overlays (target lock box, crosshair, status) on a copy of frame."""
        vis = frame.copy()
        if vis.ndim == 2:
            vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
        h, w = vis.shape[:2]
        cv2.drawMarker(vis, (w // 2, h // 2), (0, 255, 255),
                        markerType=cv2.MARKER_CROSS, markerSize=14, thickness=1)

        tx, ty = result["track_pos"]
        color = (0, 255, 0) if result["locked"] else (0, 0, 255)
        cv2.circle(vis, (int(tx), int(ty)), 12, color, 2)
        status = "LOCKED" if result["locked"] else "SEARCHING"
        cv2.putText(vis, status, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)
        s = result["summary"]
        cv2.putText(vis, f"FPS:{s['avg_fps']:.1f}  t={result['sim_time']:.1f}s",
                    (8, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        return vis
