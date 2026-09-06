"""
FSOC Virtual Camera Tracking System
------------------------------------
AI-assisted coarse-alignment simulator for mobile Free Space Optical
Communication (FSOC) terminals.

Modules:
    target        - moving beacon target with selectable motion models
    disturbances  - noise, atmospheric and platform-motion disturbance models
    camera        - virtual pan-tilt camera with configurable FOV/resolution
    detector      - computer-vision beacon detector
    tracker       - Kalman-filter based centroid tracker
    controller    - pan/tilt control loop (closes the tracking loop)
    performance   - real-time metrics + logging
    simulator     - top-level orchestrator wiring all modules together
"""

__version__ = "1.0.0"
