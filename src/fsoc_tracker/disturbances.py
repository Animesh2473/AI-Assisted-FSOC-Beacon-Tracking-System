"""Noise, atmospheric and platform-motion disturbance models."""
import numpy as np
import cv2


def add_salt_pepper(img, amount=0.10):
    """amount: fraction of pixels affected (spec: ~10%)."""
    out = img.copy()
    n = out.size
    num_salt = int(amount * n * 0.5)
    num_pepper = int(amount * n * 0.5)
    coords = [np.random.randint(0, i - 1, num_salt) for i in out.shape[:2]]
    out[coords[0], coords[1]] = 255
    coords = [np.random.randint(0, i - 1, num_pepper) for i in out.shape[:2]]
    out[coords[0], coords[1]] = 0
    return out


def add_gaussian(img, std=20):
    """std: max standard deviation of noise in pixel intensity (spec: <=20)."""
    noise = np.random.normal(0, std, img.shape).astype(np.float32)
    out = img.astype(np.float32) + noise
    return np.clip(out, 0, 255).astype(np.uint8)


def add_poisson(img):
    vals = len(np.unique(img))
    vals = 2 ** np.ceil(np.log2(vals)) if vals > 0 else 1
    noisy = np.random.poisson(img.astype(np.float32) * vals) / float(vals)
    return np.clip(noisy, 0, 255).astype(np.uint8)


def apply_atmospheric(img, condition="clear", intensity=0.5):
    """condition: clear | haze | fog | rain | low_light."""
    if condition == "clear":
        return img
    out = img.astype(np.float32)

    if condition == "haze":
        veil = 255 * intensity * 0.6
        out = out * (1 - intensity * 0.5) + veil

    elif condition == "fog":
        veil = 255 * (0.25 + 0.35 * intensity)
        out = out * (1 - intensity * 0.55) + veil

    elif condition == "low_light":
        out = out * (1 - 0.75 * intensity)

    elif condition == "rain":
        out = out * (1 - 0.25 * intensity)
        streaks = np.zeros_like(out)
        n_streaks = int(300 * intensity)
        h, w = out.shape[:2]
        for _ in range(n_streaks):
            x0 = np.random.randint(0, w)
            y0 = np.random.randint(0, h)
            length = np.random.randint(8, 18)
            cv2.line(streaks, (x0, y0), (x0 - 3, y0 + length), 200, 1)
        out = np.clip(out + streaks, 0, 255)

    return np.clip(out, 0, 255).astype(np.uint8)


def camera_jitter(offset_range_px=20):
    """Returns a random (dx, dy) pixel jitter to apply to the camera frame."""
    dx = np.random.uniform(-offset_range_px, offset_range_px)
    dy = np.random.uniform(-offset_range_px, offset_range_px)
    return dx, dy


class PlatformMotion:
    """Simulates host-platform drift/vibration applied to camera pointing."""

    MOTIONS = ("linear", "circular", "random", "spiral", "figure8")

    def __init__(self, mode="linear", max_px_per_frame=20):
        self.mode = mode if mode in self.MOTIONS else "linear"
        self.max_px = max_px_per_frame
        self.t = 0
        self._dir = np.random.uniform(-1, 1, 2)

    def step(self):
        self.t += 1
        m = self.mode
        if m == "linear":
            return self._dir[0] * self.max_px, self._dir[1] * self.max_px
        if m == "circular":
            import math
            a = self.t * 0.1
            return (self.max_px * math.cos(a), self.max_px * math.sin(a))
        if m == "figure8":
            import math
            a = self.t * 0.1
            return (self.max_px * math.sin(a), self.max_px * math.sin(2 * a) / 2)
        if m == "spiral":
            import math
            a = self.t * 0.1
            r = self.max_px * (0.2 + 0.8 * (0.5 + 0.5 * math.sin(0.05 * self.t)))
            return (r * math.cos(a), r * math.sin(a))
        # random
        return np.random.uniform(-self.max_px, self.max_px, 2)


def apply_disturbances(img, cfg):
    """Apply the configured pipeline of disturbances to a rendered frame.

    cfg keys (all optional):
      noise_types: list subset of {'salt_pepper','gaussian','poisson'}
      noise_std: gaussian std dev
      atmosphere: 'clear'|'haze'|'fog'|'rain'|'low_light'
      atmosphere_intensity: 0..1
    """
    out = img
    for n in cfg.get("noise_types", []):
        if n == "salt_pepper":
            out = add_salt_pepper(out, cfg.get("salt_pepper_amount", 0.10))
        elif n == "gaussian":
            out = add_gaussian(out, cfg.get("noise_std", 20))
        elif n == "poisson":
            out = add_poisson(out)
    out = apply_atmospheric(out, cfg.get("atmosphere", "clear"),
                             cfg.get("atmosphere_intensity", 0.5))
    return out
