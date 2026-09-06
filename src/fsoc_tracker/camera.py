"""Virtual pan-tilt camera with configurable FOV and resolution."""
import numpy as np
import cv2


class VirtualCamera:
    """
    Models a gimballed camera looking into a large 'world' scene.

    The camera's Field-of-View is expressed in degrees and mapped onto a
    rectangular crop window of the world scene (`px_per_deg` sets the
    scale). The crop is resampled to the configured output resolution,
    emulating a real focal-plane-array sensor.
    """

    def __init__(self, world_size=(2000, 2000), resolution=(640, 480),
                 fov_deg=(4.0, 3.0), px_per_deg=40.0,
                 max_pan_speed=5.0, max_tilt_speed=5.0,
                 update_rate_hz=30, mono=True):
        self.W, self.H = world_size
        self.res_w, self.res_h = resolution
        self.fov_w_deg, self.fov_h_deg = fov_deg
        self.px_per_deg = px_per_deg
        self.max_pan_speed = max_pan_speed   # deg/s
        self.max_tilt_speed = max_tilt_speed  # deg/s
        self.update_rate_hz = update_rate_hz
        self.mono = mono

        # camera boresight, in world-pixel coordinates. Starts at centre.
        self.cx = self.W / 2.0
        self.cy = self.H / 2.0

        self.win_w = self.fov_w_deg * self.px_per_deg
        self.win_h = self.fov_h_deg * self.px_per_deg

    def pan_tilt_deg_to_world_px(self, dpan_deg, dtilt_deg):
        return dpan_deg * self.px_per_deg, dtilt_deg * self.px_per_deg

    def move(self, dpan_deg, dtilt_deg, dt):
        """Command a pan/tilt rate (deg/s), clipped to max speed, for dt sec."""
        dpan_deg = float(np.clip(dpan_deg, -self.max_pan_speed, self.max_pan_speed))
        dtilt_deg = float(np.clip(dtilt_deg, -self.max_tilt_speed, self.max_tilt_speed))
        dx, dy = self.pan_tilt_deg_to_world_px(dpan_deg * dt, dtilt_deg * dt)
        self.cx += dx
        self.cy += dy
        half_w, half_h = self.win_w / 2, self.win_h / 2
        self.cx = min(max(self.cx, half_w), self.W - half_w)
        self.cy = min(max(self.cy, half_h), self.H - half_h)

    def world_to_frame_coords(self, wx, wy):
        """Convert world coords to this camera's current image coords.
        Returns None if outside FOV."""
        half_w, half_h = self.win_w / 2, self.win_h / 2
        left, top = self.cx - half_w, self.cy - half_h
        if not (left <= wx <= left + self.win_w and top <= wy <= top + self.win_h):
            return None
        fx = (wx - left) / self.win_w * self.res_w
        fy = (wy - top) / self.win_h * self.res_h
        return fx, fy

    def render(self, world_canvas, jitter=(0.0, 0.0)):
        """Crop+resize the world canvas according to current FOV window,
        with optional (dx,dy) camera jitter in world pixels."""
        half_w, half_h = self.win_w / 2, self.win_h / 2
        jx, jy = jitter
        left = int(round(self.cx - half_w + jx))
        top = int(round(self.cy - half_h + jy))
        left = max(0, min(left, self.W - int(self.win_w)))
        top = max(0, min(top, self.H - int(self.win_h)))
        crop = world_canvas[top:top + int(self.win_h), left:left + int(self.win_w)]
        if crop.shape[0] == 0 or crop.shape[1] == 0:
            crop = np.zeros((int(self.win_h), int(self.win_w)), dtype=np.uint8)
        frame = cv2.resize(crop, (self.res_w, self.res_h), interpolation=cv2.INTER_LINEAR)
        if not self.mono and frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        return frame
