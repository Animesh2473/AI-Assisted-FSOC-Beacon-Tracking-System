"""Moving optical-beacon target with selectable motion models."""
import math
import random


class Target:
    """A single beacon-spot target moving inside a 2D world (the 'scene')."""

    MOTIONS = (
        "straight_line", "circular", "figure8", "random",
        "spiral", "sinusoidal", "static",
    )

    def __init__(self, world_size=(2000, 2000), motion="circular",
                 size=10, shape="square", start_pos=None, speed=120.0,
                 seed=None):
        """
        Args:
            world_size: (W, H) size of the virtual scene in pixels.
            motion: one of Target.MOTIONS.
            size: side length (square) or diameter (circle) in pixels (5-20).
            shape: 'square' or 'circle'.
            start_pos: (x, y) initial location, or None for random/center.
            speed: nominal linear speed in world-pixels/second.
            seed: RNG seed for reproducible random motion.
        """
        self.W, self.H = world_size
        self.motion = motion if motion in self.MOTIONS else "circular"
        self.size = max(5, min(20, size))
        self.shape = shape
        self.speed = speed
        self.t = 0.0
        self._rng = random.Random(seed)

        self.cx, self.cy = self.W / 2.0, self.H / 2.0
        self.radius = min(self.W, self.H) * 0.3

        self._vx = self._rng.uniform(-1, 1)
        self._vy = self._rng.uniform(-1, 1)
        self._dir_change_timer = 0.0

        if start_pos is not None:
            self.x, self.y = start_pos
        else:
            # Initialize x,y consistent with the chosen motion's formula at
            # t=0, so the camera can be cued to the true starting position
            # without a discontinuous jump on the first step().
            self.x, self.y = self._compute(0.0)

    def _compute(self, t):
        """Return (x, y) for the parametric motions at simulation time t,
        WITHOUT mutating any state. Used both for t=0 initialization and
        internally by step(). straight_line/random are stateful/integrated
        and are not represented here (handled directly in step())."""
        m = self.motion
        if m == "circular":
            w = self.speed / max(self.radius, 1e-6)
            return self.cx + self.radius * math.cos(w * t), self.cy + self.radius * math.sin(w * t)
        if m == "figure8":
            w = self.speed / max(self.radius, 1e-6)
            return (self.cx + self.radius * math.sin(w * t),
                    self.cy + (self.radius / 2) * math.sin(2 * w * t))
        if m == "spiral":
            w = self.speed / max(self.radius, 1e-6)
            r = (self.radius * 0.15) + (self.radius * 0.85) * (0.5 + 0.5 * math.sin(0.15 * t))
            return self.cx + r * math.cos(w * t), self.cy + r * math.sin(w * t)
        if m == "sinusoidal":
            return self.cx - self.radius, self.cy
        # straight_line / random / static: start at scene centre by default
        return self.cx, self.cy

    def _clamp(self):
        m = self.size
        self.x = min(max(self.x, m), self.W - m)
        self.y = min(max(self.y, m), self.H - m)

    def step(self, dt):
        """Advance target position by dt seconds. Returns (x, y)."""
        self.t += dt
        m = self.motion

        if m == "static":
            pass

        elif m == "straight_line":
            self.x += self._vx * self.speed * dt
            self.y += self._vy * self.speed * dt
            if self.x <= self.size or self.x >= self.W - self.size:
                self._vx *= -1
            if self.y <= self.size or self.y >= self.H - self.size:
                self._vy *= -1

        elif m in ("circular", "figure8", "spiral"):
            self.x, self.y = self._compute(self.t)

        elif m == "sinusoidal":
            self.x += self.speed * dt
            self.y = self.cy + self.radius * 0.6 * math.sin(self.t * 1.5)
            if self.x >= self.W - self.size or self.x <= self.size:
                self.speed *= -1

        elif m == "random":
            self._dir_change_timer -= dt
            if self._dir_change_timer <= 0:
                self._vx = self._rng.uniform(-1, 1)
                self._vy = self._rng.uniform(-1, 1)
                self._dir_change_timer = self._rng.uniform(0.4, 1.5)
            self.x += self._vx * self.speed * dt
            self.y += self._vy * self.speed * dt

        self._clamp()
        return self.x, self.y

    @property
    def position(self):
        return self.x, self.y
