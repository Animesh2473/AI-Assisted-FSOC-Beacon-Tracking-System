# FSOC Virtual Camera Tracking System

**AI-assisted virtual camera tracking system for coarse alignment of mobile
Free Space Optical Communication (FSOC) terminals.**
(Smart India Hackathon — Problem Statement 4, Dept. of Space / ISRO)

Simulates the coarse-alignment stage of a laser PAT (Pointing, Acquisition &
Tracking) system entirely in software: a virtual scene with a moving optical
beacon, a virtual pan-tilt camera, realistic disturbances (noise, atmosphere,
jitter, platform motion), a computer-vision detector, a Kalman-filter
tracker, and a closed-loop pan-tilt controller — with real-time performance
logging (FPS, tracking error, lock retention rate, acquisition/re-acquisition
time).

## Project layout
```
fsoc-virtual-tracking/
├── src/fsoc_tracker/       # core simulation package
│   ├── target.py           # beacon motion models
│   ├── camera.py           # virtual pan-tilt camera / FOV model
│   ├── disturbances.py     # noise, atmosphere, jitter, platform motion
│   ├── detector.py         # CV beacon detector
│   ├── tracker.py          # Kalman-filter centroid tracker
│   ├── controller.py       # pan/tilt control loop
│   ├── performance.py      # metrics + logging
│   └── simulator.py        # orchestrates everything
├── app/gui_app.py          # standalone Tkinter desktop app
├── app/streamlit_app.py    # web app (deployable to Streamlit Cloud)
├── notebooks/FSOC_Virtual_Tracking_Colab.ipynb   # Colab runner
├── config/default_config.yaml
├── tests/test_basic.py
├── docs/                   # sample output frame/video/report
└── requirements.txt / setup.py
```

## Option A — Run in Google Colab (recommended for demo/eval)

1. Push this project to a GitHub repo (see **GitHub setup** below).
2. Open `notebooks/FSOC_Virtual_Tracking_Colab.ipynb` in Colab
   (`File → Upload notebook`, or open directly from GitHub via
   `File → Open notebook → GitHub`).
3. In **Cell 1**, set `REPO_URL` to your repo's URL, then run all cells
   top to bottom.
   - No GitHub? Use **Cell 1b** instead: zip the project folder, upload it
     via the Colab file browser, and unzip in-notebook.
4. Cell 3 exposes sliders/dropdowns (target motion, noise, atmosphere,
   platform motion, jitter, frame count) — edit and re-run from Cell 4 to
   try different scenarios.
5. The notebook plays the tracking video inline, saves `tracking_output.mp4`,
   plots tracking-error/lock-status graphs, and writes the mandatory
   `performance_log.csv` + `performance_report.txt` deliverables.
6. Cell 9 is optional: point `VIDEO_PATH` at an uploaded `.mp4` to run the
   detector+tracker directly on a real video feed (Benchmark Performance-2
   style evaluation, bypassing the virtual camera).

## Option B — Run locally

```bash
git clone <your-repo-url>
cd fsoc-virtual-tracking
pip install -r requirements.txt
pip install -e .

# Standalone GUI application
python app/gui_app.py

# Or run the simulation headlessly from Python
python -c "
from fsoc_tracker.simulator import Simulation, DEFAULT_CONFIG
sim = Simulation(dict(DEFAULT_CONFIG))
print(sim.run(300))
"

# Run tests
pytest tests/ -q
```

Build a standalone `.exe` (the "Software Application" deliverable):
```bash
pip install pyinstaller
pyinstaller --onefile --name FSOC_VirtualTracker app/gui_app.py
```

## Option C — Deploy as a web app on Streamlit

A ready-made web UI lives at `app/streamlit_app.py`: sidebar controls for
target motion/noise/atmosphere/platform motion, a playback slider, an
inline video, live metric charts, and download buttons for the video,
CSV log, and performance report.

**Run locally:**
```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

**Deploy free on Streamlit Community Cloud:**
1. Push this repo to GitHub (see **GitHub setup** below) — make sure
   `requirements.txt`, `packages.txt`, and `app/streamlit_app.py` are
   at the paths shown in this project's layout.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, pick this repo/branch, and set
   **Main file path** to `app/streamlit_app.py`.
4. Click **Deploy**. First build takes a couple of minutes (installs
   `packages.txt` system deps + `requirements.txt`).
5. You'll get a public URL like `https://<app-name>.streamlit.app`.

Notes:
- `requirements.txt` uses `opencv-python-headless` (not `opencv-python`) —
  required for cloud deployment since there's no display server.
- `packages.txt` installs `ffmpeg`/`libgl1` system packages the cloud
  environment needs for video encoding.
- `.streamlit/config.toml` sets a dark theme; edit or delete it to use
  Streamlit's default theme.



```bash
cd fsoc-virtual-tracking
git init
git add .
git commit -m "Initial commit: FSOC virtual camera tracking system"
git branch -M main
git remote add origin https://github.com/<your-username>/fsoc-virtual-tracking.git
git push -u origin main
```
Then update `REPO_URL` in the Colab notebook's first cell to match.

## Configurable parameters (config/default_config.yaml)
Matches the SIH reference parameter table: world/screen size, camera
resolution & FOV, max pan/tilt speed, target shape/size/motion, noise types
(Gaussian/salt-pepper/Poisson), atmospheric condition (clear/haze/fog/rain/
low-light), camera jitter, and platform motion pattern.

## Sample output
`docs/sample_frame.png` and `docs/sample_tracking.mp4` show an annotated
run (green circle = locked track, red = searching, yellow cross = image
center/boresight). `docs/sample_performance_report.txt` is an example
auto-generated performance log.

## Notes on the current baseline
- Detection uses an adaptive-threshold + contour pipeline (not a trained
  model) — swap in a CNN/YOLO detector in `detector.py` for the "AI methods"
  deliverable if desired.
- The PD pan/tilt controller in `controller.py` is a tunable baseline;
  gains (`kp`, `kd`) can be adjusted per scenario to reduce tracking error
  further toward the ≤10 px spec target.
- Tests (`tests/test_basic.py`) cover all motion models, detector noise
  rejection, tracker lock behavior, and end-to-end simulation runs.
