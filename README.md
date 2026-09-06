# 🚀 ASTRA-PAT — AI-Assisted FSOC Beacon Tracking System

**AI-assisted virtual camera tracking system for coarse alignment of mobile Free Space Optical Communication (FSOC) terminals.**

> **Smart India Hackathon — Problem Statement 4**
> **Department of Space / ISRO**

## 🌐 Live Demo

### ▶️ Try the application online

**[🚀 Launch ASTRA-PAT — Live Streamlit Demo](https://ai-assisted-fsoc-beacon-tracking-system.streamlit.app/)**

No installation is required. Open the link and experiment with different target-motion, noise, atmospheric, jitter, and platform-motion conditions directly in your browser.

---

## 📌 Overview

**ASTRA-PAT** is a software-based simulation of the **coarse Pointing, Acquisition & Tracking (PAT)** stage used in Free Space Optical Communication systems.

The project simulates a mobile optical terminal trying to detect and continuously track a moving optical beacon using a virtual pan-tilt camera.

The system combines:

* 🎯 Moving optical beacon simulation
* 📷 Virtual pan-tilt camera
* 🌫️ Atmospheric disturbances
* 📡 Platform motion
* 📳 Camera jitter
* 🔊 Image noise
* 👁️ Computer-vision based beacon detection
* 🧠 Kalman-filter based tracking
* 🎛️ Closed-loop pan-tilt control
* 📊 Real-time performance monitoring

The objective is to maintain the optical beacon close to the camera boresight despite disturbances and target movement.

---

## 🎯 Problem Statement

Free Space Optical Communication uses highly directional optical/laser beams. For reliable communication, the transmitting and receiving terminals must remain accurately aligned.

Mobile terminals can experience:

* Platform movement
* Mechanical vibration
* Camera jitter
* Atmospheric degradation
* Target motion
* Sensor noise
* Temporary loss of the optical beacon

ASTRA-PAT provides a software test environment for studying how a vision-based tracking system can acquire, track, and reacquire a moving optical beacon under these conditions.

---

## 🔄 System Architecture

```text
                 ┌─────────────────────┐
                 │   Moving Optical    │
                 │       Beacon        │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Virtual Camera    │
                 │   Pan / Tilt + FOV  │
                 └──────────┬──────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │       Disturbances          │
              │                             │
              │ Noise / Fog / Haze / Rain  │
              │ Jitter / Platform Motion   │
              └─────────────┬───────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Beacon Detector     │
                 │ Computer Vision     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Kalman Tracker    │
                 │ Position Prediction │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Pan-Tilt Controller │
                 │     PD Control      │
                 └──────────┬──────────┘
                            │
                            ▼
                    Camera Reorients
                            │
                            └──────────────►
                              Closed Loop
```

---

## 🧠 How It Works

### 1. Target Generation

The system generates a virtual optical beacon with configurable motion patterns.

Examples include:

* Linear movement
* Circular movement
* Sinusoidal movement
* Random/variable motion

The target position changes over time to simulate a mobile FSOC terminal.

---

### 2. Virtual Camera

The virtual camera simulates a pan-tilt optical terminal.

It models:

* Camera resolution
* Field of View (FOV)
* Pan angle
* Tilt angle
* Maximum pan/tilt speed
* Camera boresight

The camera continuously observes the simulated environment.

---

### 3. Environmental and Platform Disturbances

Real-world conditions are simulated to make the tracking problem more realistic.

Available disturbances include:

* Gaussian noise
* Salt-and-pepper noise
* Poisson noise
* Clear atmosphere
* Haze
* Fog
* Rain
* Low-light conditions
* Camera jitter
* Platform motion

This allows the tracking algorithm to be tested under different operating conditions.

---

### 4. Beacon Detection

The detector processes each camera frame and estimates the beacon's image coordinates.

The current baseline uses a computer-vision pipeline based on:

```text
Image
  ↓
Pre-processing
  ↓
Adaptive Thresholding
  ↓
Contour Detection
  ↓
Candidate Filtering
  ↓
Beacon Centroid
```

The detector produces the estimated `(x, y)` position of the beacon.

---

### 5. Kalman Filter Tracking

The detected beacon position can contain noise or temporarily fluctuate.

The Kalman filter combines:

* Previous target position
* Target velocity
* Current measurement

to estimate the target's current position and movement.

This provides a smoother tracking signal for the controller.

---

### 6. Pan-Tilt Control

The controller calculates the error between the camera center and the detected target.

```text
             Target
                🔴
                │
                │ Tracking Error
                │
                ▼
             🟡 Camera
                Center
```

The controller generates pan and tilt commands to reduce this error.

The loop continuously repeats:

```text
Detect → Track → Calculate Error → Move Camera → Detect Again
```

This creates a closed-loop tracking system.

---

## 📊 Performance Metrics

ASTRA-PAT records important tracking-performance parameters:

| Metric                  | Description                                      |
| ----------------------- | ------------------------------------------------ |
| **FPS**                 | Simulation/processing speed                      |
| **Tracking Error**      | Distance between target and camera center        |
| **Lock Retention Rate** | Percentage of time the target remains locked     |
| **Acquisition Time**    | Time required to initially acquire the target    |
| **Re-acquisition Time** | Time required to recover after losing the target |
| **Lock Status**         | Current tracking state                           |

The system can generate:

* `performance_log.csv`
* `performance_report.txt`
* Tracking-error graphs
* Lock-status graphs
* Annotated tracking video

---

## 🖥️ Live Web Application

The project includes a Streamlit-based web interface.

### Features

* Target-motion controls
* Noise controls
* Atmospheric-condition controls
* Platform-motion controls
* Camera jitter controls
* Frame-count configuration
* Tracking video playback
* Tracking-error visualization
* Lock-status visualization
* Performance metrics
* Downloadable CSV logs
* Downloadable performance reports

### 🌐 Open the live application

**[Launch ASTRA-PAT](https://ai-assisted-fsoc-beacon-tracking-system.streamlit.app/)**

---

## 📂 Project Structure

```text
fsoc-virtual-tracking/
│
├── src/
│   └── fsoc_tracker/
│       ├── target.py
│       ├── camera.py
│       ├── disturbances.py
│       ├── detector.py
│       ├── tracker.py
│       ├── controller.py
│       ├── performance.py
│       └── simulator.py
│
├── app/
│   ├── gui_app.py
│   └── streamlit_app.py
│
├── notebooks/
│   └── FSOC_Virtual_Tracking_Colab.ipynb
│
├── config/
│   └── default_config.yaml
│
├── tests/
│   └── test_basic.py
│
├── docs/
│   ├── sample_frame.png
│   ├── sample_tracking.mp4
│   └── sample_performance_report.txt
│
├── requirements.txt
├── setup.py
└── README.md
```

---

# 🚀 Getting Started

## Option A — Use the Online Demo

The easiest option is to use the deployed application.

👉 **[Open the live Streamlit application](https://ai-assisted-fsoc-beacon-tracking-system.streamlit.app/)**

No local installation is required.

---

## Option B — Run in Google Colab

The project includes a Colab notebook for demonstration and evaluation.

### 1. Open the notebook

```text
notebooks/FSOC_Virtual_Tracking_Colab.ipynb
```

Open it using Google Colab.

### 2. Configure the repository

In Cell 1, set:

```python
REPO_URL = "https://github.com/<your-username>/fsoc-virtual-tracking"
```

Then run the notebook from top to bottom.

### 3. Configure the simulation

The notebook provides controls for:

* Target motion
* Noise
* Atmospheric conditions
* Platform motion
* Camera jitter
* Number of frames

### 4. Generated outputs

The notebook generates:

```text
tracking_output.mp4
performance_log.csv
performance_report.txt
```

It also displays tracking-error and lock-status graphs.

---

## Option C — Run Locally

### Clone the repository

```bash
git clone <your-repo-url>
cd fsoc-virtual-tracking
```

### Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### Run the desktop application

```bash
python app/gui_app.py
```

### Run the simulation directly

```bash
python -c "
from fsoc_tracker.simulator import Simulation, DEFAULT_CONFIG
sim = Simulation(dict(DEFAULT_CONFIG))
print(sim.run(300))
"
```

### Run tests

```bash
pytest tests/ -q
```

---

# 🌐 Run the Streamlit Application Locally

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app/streamlit_app.py
```

The application will open in your browser.

---

# ☁️ Streamlit Deployment

The project can be deployed using Streamlit Community Cloud.

Required files:

```text
requirements.txt
packages.txt
app/streamlit_app.py
```

The application is currently deployed at:

**https://ai-assisted-fsoc-beacon-tracking-system.streamlit.app/**

---

# ⚙️ Configuration

Configuration is available in:

```text
config/default_config.yaml
```

Parameters include:

* World/screen dimensions
* Camera resolution
* Camera FOV
* Maximum pan speed
* Maximum tilt speed
* Target size
* Target motion
* Noise type
* Atmospheric condition
* Camera jitter
* Platform motion

Example disturbance conditions:

```text
Clear
Haze
Fog
Rain
Low Light
```

---

# 🎥 Sample Output

The `docs/` directory contains example outputs.

### Annotated tracking frame

```text
🟢 Green circle  → Target successfully tracked
🔴 Red indicator  → Searching / target not locked
🟡 Yellow cross  → Camera center / boresight
```

### Sample files

```text
docs/sample_frame.png
docs/sample_tracking.mp4
docs/sample_performance_report.txt
```

---

# 🤖 AI / Computer Vision Component

The current implementation uses a traditional computer-vision detector based on adaptive thresholding and contour analysis.

The architecture is designed so that the detector can be replaced with an AI-based model such as:

```text
YOLO / CNN Detector
        ↓
Beacon Bounding Box
        ↓
Centroid
        ↓
Kalman Filter
        ↓
Pan-Tilt Controller
```

This allows future integration of a trained object-detection model for more robust beacon detection under challenging visual conditions.

---

# 🎯 Future Improvements

Possible future improvements include:

* [ ] YOLO/CNN-based beacon detector
* [ ] Deep-learning based target classification
* [ ] More realistic atmospheric turbulence
* [ ] Optical scintillation simulation
* [ ] Adaptive controller tuning
* [ ] Multi-target detection
* [ ] Real camera integration
* [ ] Hardware pan-tilt integration
* [ ] Hardware-in-the-loop testing
* [ ] Real laser/optical beacon experiments
* [ ] Advanced Kalman/Extended Kalman filtering

---

# 🧪 Testing

The project includes automated tests covering:

* Target motion models
* Detector noise rejection
* Tracker lock behavior
* End-to-end simulation
* Basic system functionality

Run:

```bash
pytest tests/ -q
```

---

# 📦 Standalone Windows Application

A standalone executable can be created using PyInstaller:

```bash
pip install pyinstaller
```

Then:

```bash
pyinstaller --onefile --name FSOC_VirtualTracker app/gui_app.py
```

The generated executable can be distributed as the **Software Application** deliverable.

---

# 🛰️ Application Relevance

This project demonstrates a software simulation of technologies relevant to:

* Free Space Optical Communication
* Optical Pointing, Acquisition & Tracking
* Satellite-to-satellite communication
* Ground-to-satellite optical links
* Mobile optical terminals
* Autonomous optical tracking
* Computer vision based pointing systems

The system provides a controllable environment for evaluating tracking algorithms before deployment on physical optical hardware.

---

# 🏆 Smart India Hackathon

**Problem Area:** Free Space Optical Communication

**Organization:** Department of Space / ISRO

**Focus:** Coarse alignment and tracking of mobile FSOC terminals

The project demonstrates how computer vision, state estimation, and feedback control can be combined to maintain alignment with a moving optical beacon.

---

# 👨‍💻 Project

**ASTRA-PAT — AI-Assisted FSOC Beacon Tracking System**

### Live Demo

🚀 **https://ai-assisted-fsoc-beacon-tracking-system.streamlit.app/**

---

## 📜 License

Add the appropriate license for your project here.

For example:

```text
MIT License
```

if you decide to release the project under the MIT License.
