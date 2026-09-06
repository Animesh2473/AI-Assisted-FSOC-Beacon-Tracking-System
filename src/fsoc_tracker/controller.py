"""Closes the tracking loop: converts pixel error to pan/tilt commands."""


class PTController:
    """Simple PD controller mapping image-plane pixel error to camera
    pan/tilt rate commands (deg/s)."""

    def __init__(self, image_size=(640, 480), fov_deg=(4.0, 3.0),
                 kp=2.5, kd=0.4, search_pattern="raster"):
        self.img_w, self.img_h = image_size
        self.fov_w_deg, self.fov_h_deg = fov_deg
        self.kp = kp
        self.kd = kd
        self.prev_err = (0.0, 0.0)
        self.search_pattern = search_pattern
        self._search_t = 0

    def _px_to_deg(self, px, total_px, total_deg):
        return (px / total_px) * total_deg

    def track(self, target_px_pos):
        """target_px_pos: (x, y) in image coords. Returns (dpan, dtilt) deg/s."""
        cx, cy = self.img_w / 2.0, self.img_h / 2.0
        ex_px = target_px_pos[0] - cx
        ey_px = target_px_pos[1] - cy
        ex_deg = self._px_to_deg(ex_px, self.img_w, self.fov_w_deg)
        ey_deg = self._px_to_deg(ey_px, self.img_h, self.fov_h_deg)

        dex = ex_deg - self.prev_err[0]
        dey = ey_deg - self.prev_err[1]
        self.prev_err = (ex_deg, ey_deg)

        dpan = self.kp * ex_deg + self.kd * dex
        dtilt = self.kp * ey_deg + self.kd * dey
        return dpan, dtilt

    def search(self):
        """Generates a simple raster search sweep when target is not locked,
        to re-acquire it. Returns (dpan, dtilt) deg/s."""
        self._search_t += 1
        period = 40
        phase = self._search_t % period
        dpan = 3.0 if (self._search_t // period) % 2 == 0 else -3.0
        dtilt = 0.6 if phase == 0 else 0.0
        return dpan, dtilt
