"""Computer-vision beacon-spot detector."""
import cv2
import numpy as np


class BeaconDetector:
    """Detects a bright beacon spot against a darker background.

    Pipeline: (optional blur) -> adaptive/Otsu threshold -> morphology ->
    contour extraction -> filter by area/circularity -> pick best candidate
    (largest, or closest to previous track if given).
    """

    def __init__(self, min_area=9, max_area=2000, blur_ksize=3,
                 use_otsu=False, fixed_thresh=140, min_peak_intensity=110):
        self.min_area = min_area
        self.max_area = max_area
        self.blur_ksize = blur_ksize
        self.use_otsu = use_otsu
        self.fixed_thresh = fixed_thresh
        # Guards against false-positive "detections" on pure sensor noise
        # when the real beacon is outside the FOV: require the brightest
        # pixel in frame to clear this level before trusting Otsu/threshold
        # output at all.
        self.min_peak_intensity = min_peak_intensity

    def detect(self, frame, prior_pos=None):
        """
        Args:
            frame: grayscale or BGR image (uint8).
            prior_pos: optional (x, y) predicted position to disambiguate
                       multiple candidates (nearest wins).
        Returns:
            dict(cx, cy, area, bbox) or None if nothing found.
        """
        if frame.ndim == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        if self.blur_ksize > 1:
            gray = cv2.GaussianBlur(gray, (self.blur_ksize, self.blur_ksize), 0)

        if int(gray.max()) < self.min_peak_intensity:
            # Nothing bright enough to plausibly be the beacon (e.g. target
            # currently outside FOV) -- avoid thresholding pure noise.
            return None

        if self.use_otsu:
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            # Adaptive-floor threshold: the beacon should stand out as a
            # statistical outlier above the local background, so this
            # tracks background brightness shifts caused by atmospheric
            # effects (haze/fog/low-light) rather than using one fixed
            # level for every condition.
            mean, std = float(gray.mean()), float(gray.std())
            thresh = min(250.0, max(self.fixed_thresh, mean + 4.0 * std))
            _, mask = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < self.min_area or area > self.max_area:
                continue
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            x, y, w, h = cv2.boundingRect(c)
            candidates.append({"cx": cx, "cy": cy, "area": area, "bbox": (x, y, w, h)})

        if not candidates:
            return None

        if prior_pos is not None:
            px, py = prior_pos
            candidates.sort(key=lambda d: (d["cx"] - px) ** 2 + (d["cy"] - py) ** 2)
            return candidates[0]

        candidates.sort(key=lambda d: -d["area"])
        return candidates[0]
