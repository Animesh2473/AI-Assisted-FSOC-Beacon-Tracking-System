"""Kalman-filter based centroid tracker with lock/loss state machine."""
import cv2
import numpy as np


class CentroidKalmanTracker:
    """
    Constant-velocity Kalman filter over image-plane (x, y).
    Maintains a 'locked' state and counts consecutive missed detections to
    decide when the target is considered lost (needs re-acquisition).
    """

    def __init__(self, max_missed_frames=15, process_noise=1e-2, meas_noise=1e-1):
        self.kf = cv2.KalmanFilter(4, 2)
        self.kf.transitionMatrix = np.array([[1, 0, 1, 0],
                                              [0, 1, 0, 1],
                                              [0, 0, 1, 0],
                                              [0, 0, 0, 1]], np.float32)
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                               [0, 1, 0, 0]], np.float32)
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * process_noise
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * meas_noise

        self.max_missed = max_missed_frames
        self.missed = 0
        self.locked = False
        self.initialized = False
        self.frames_since_reacquire_start = 0
        self.pos = None

    def _init_state(self, x, y):
        self.kf.statePre = np.array([[x], [y], [0], [0]], np.float32)
        self.kf.statePost = np.array([[x], [y], [0], [0]], np.float32)
        self.initialized = True

    def predict(self):
        pred = self.kf.predict()
        return float(pred[0, 0]), float(pred[1, 0])

    def update(self, detection):
        """detection: (x, y) tuple, or None if no detection this frame."""
        predicted = self.predict()

        if detection is not None:
            if not self.initialized:
                self._init_state(*detection)
            meas = np.array([[np.float32(detection[0])], [np.float32(detection[1])]])
            corrected = self.kf.correct(meas)
            self.pos = (float(corrected[0, 0]), float(corrected[1, 0]))
            self.missed = 0
            self.locked = True
        else:
            self.missed += 1
            self.pos = predicted
            if self.missed > self.max_missed:
                self.locked = False

        return self.pos, self.locked
