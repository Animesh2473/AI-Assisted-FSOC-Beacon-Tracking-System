
import os
import sys
import tempfile

import cv2
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fsoc_tracker.simulator import Simulation, DEFAULT_CONFIG
from fsoc_tracker.detector import BeaconDetector
from fsoc_tracker.tracker import CentroidKalmanTracker
from fsoc_tracker.performance import PerformanceLogger

st.set_page_config(
    page_title="FSOC Virtual Camera Tracking",
    page_icon="🛰️",
    layout="wide",
)

st.title("🛰️ FSOC Virtual Camera Tracking System")
st.caption(
    "AI-assisted coarse-alignment simulator for mobile Free Space Optical "
    "Communication terminals — SIH Problem Statement 4 (Dept. of Space / ISRO)"
)

tab_sim, tab_upload = st.tabs(["🎛️ Virtual Simulation", "📤 Upload Video"])


# ============================================================= shared helpers
def make_video(frames_rgb, fps=30, path="/tmp/tracking_output.mp4"):
    h, w = frames_rgb[0].shape[:2]
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for f in frames_rgb:
        writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
    writer.release()
    return path


# ============================================================ TAB 1: SIM MODE
with tab_sim:
    with st.sidebar:
        st.header("Scenario configuration")

        target_motion = st.selectbox(
            "Target motion",
            ["circular", "straight_line", "figure8", "random", "spiral", "sinusoidal"],
            index=0,
        )
        target_size = st.slider("Target size (px)", 5, 20, 10)
        target_speed = st.slider("Target speed (world px/s)", 20, 400, 150, step=10)

        st.divider()
        noise_choice = st.selectbox(
            "Noise", ["none", "gaussian", "salt_pepper", "poisson"], index=1
        )
        atmosphere = st.selectbox(
            "Atmospheric condition", ["clear", "haze", "fog", "rain", "low_light"], index=0
        )
        platform_motion = st.selectbox(
            "Platform motion", ["linear", "circular", "random", "spiral", "figure8"], index=0
        )
        camera_jitter_px = st.slider("Camera jitter (px)", 0, 20, 5)

        st.divider()
        num_frames = st.slider("Number of frames to simulate", 60, 900, 300, step=30)
        seed = st.number_input("Random seed", value=42, step=1)

        run_clicked = st.button("▶ Run simulation", type="primary", use_container_width=True)

    def build_config():
        cfg = dict(DEFAULT_CONFIG)
        cfg.update({
            "target_motion": target_motion,
            "target_size": target_size,
            "target_speed": float(target_speed),
            "noise_types": [] if noise_choice == "none" else [noise_choice],
            "atmosphere": atmosphere,
            "platform_motion": platform_motion,
            "camera_jitter_px": float(camera_jitter_px),
            "seed": int(seed),
        })
        return cfg

    @st.cache_data(show_spinner=False)
    def run_simulation(cfg_tuple, n_frames):
        cfg = dict(cfg_tuple)
        cfg["noise_types"] = list(cfg["noise_types"])
        sim = Simulation(cfg)

        frames, err_hist, locked_hist, time_hist = [], [], [], []

        def on_frame(result, i):
            vis = Simulation.annotate(result["frame"], result)
            frames.append(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
            time_hist.append(result["sim_time"])
            locked_hist.append(1 if result["locked"] else 0)
            gt = result["gt_frame_pos"]
            if gt is not None and result["locked"]:
                tx, ty = result["track_pos"]
                err_hist.append(float(np.hypot(tx - gt[0], ty - gt[1])))
            else:
                err_hist.append(np.nan)

        summary = sim.run(n_frames, on_frame=on_frame)
        csv_path = "/tmp/performance_log.csv"
        report_path = "/tmp/performance_report.txt"
        sim.perf.save_csv(csv_path)
        sim.perf.save_report(report_path)

        return frames, err_hist, locked_hist, time_hist, summary, csv_path, report_path

    if "sim_results" not in st.session_state:
        st.session_state["sim_results"] = None

    if run_clicked:
        cfg = build_config()
        cfg_tuple = tuple(sorted(
            (k, tuple(v) if isinstance(v, list) else v) for k, v in cfg.items()
        ))
        with st.spinner(f"Running {num_frames}-frame simulation..."):
            st.session_state["sim_results"] = run_simulation(cfg_tuple, num_frames)

    results = st.session_state["sim_results"]

    if results is None:
        st.info("Configure a scenario in the sidebar and click **Run simulation** to begin.")
    else:
        frames, err_hist, locked_hist, time_hist, summary, csv_path, report_path = results

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Tracking playback")
            frame_idx = st.slider("Frame", 0, len(frames) - 1, len(frames) // 2, key="sim_frame_slider")
            st.image(frames[frame_idx], use_container_width=True)

            with st.spinner("Encoding video..."):
                video_path = make_video(frames)
            with open(video_path, "rb") as f:
                video_bytes = f.read()
            st.video(video_bytes)
            st.download_button("⬇ Download tracking video (.mp4)", video_bytes,
                                file_name="tracking_output.mp4", mime="video/mp4",
                                key="sim_video_dl")

        with col2:
            st.subheader("Performance summary")
            for k, v in summary.items():
                st.metric(k.replace("_", " ").title(), v)

        st.subheader("Metrics over time")
        df = pd.DataFrame({
            "sim_time_s": time_hist,
            "tracking_error_px": err_hist,
            "locked": locked_hist,
        })
        m1, m2 = st.columns(2)
        with m1:
            st.caption("Tracking error (px) — spec limit is 10 px")
            st.line_chart(df.set_index("sim_time_s")["tracking_error_px"])
        with m2:
            st.caption("Lock status (1 = locked, 0 = searching)")
            st.line_chart(df.set_index("sim_time_s")["locked"])

        st.subheader("Deliverables")
        c1, c2 = st.columns(2)
        with c1:
            with open(csv_path, "rb") as f:
                st.download_button("⬇ Download performance_log.csv", f,
                                    file_name="performance_log.csv", mime="text/csv",
                                    key="sim_csv_dl")
        with c2:
            with open(report_path, "rb") as f:
                st.download_button("⬇ Download performance_report.txt", f,
                                    file_name="performance_report.txt", mime="text/plain",
                                    key="sim_report_dl")


# ========================================================= TAB 2: UPLOAD MODE
with tab_upload:
    st.subheader("Run detection + tracking on an uploaded video")
    st.caption(
        "Bypasses the virtual camera and runs the beacon detector + Kalman "
        "tracker directly on your video frames — the same evaluation path "
        "used for the SIH 'Benchmark Performance-2' judging stage."
    )

    uploaded_file = st.file_uploader(
        "Upload a video (.mp4, .avi, .mov)", type=["mp4", "avi", "mov", "mkv"]
    )

    colA, colB, colC = st.columns(3)
    with colA:
        min_area = st.number_input("Min blob area (px²)", value=9, min_value=1, step=1)
    with colB:
        max_area = st.number_input("Max blob area (px²)", value=2000, min_value=10, step=10)
    with colC:
        max_missed = st.number_input("Max missed frames before 'lost'", value=15, min_value=1, step=1)

    process_clicked = st.button("▶ Process video", type="primary",
                                 disabled=uploaded_file is None, use_container_width=True)

    if "upload_results" not in st.session_state:
        st.session_state["upload_results"] = None

    if process_clicked and uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_in:
            tmp_in.write(uploaded_file.read())
            in_path = tmp_in.name

        cap = cv2.VideoCapture(in_path)
        fps_in = cap.get(cv2.CAP_PROP_FPS) or 30
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        det = BeaconDetector(min_area=int(min_area), max_area=int(max_area))
        trk = CentroidKalmanTracker(max_missed_frames=int(max_missed))
        perf = PerformanceLogger()

        out_frames = []
        sim_time = 0.0
        dt = 1.0 / fps_in
        progress = st.progress(0.0, text="Processing frames...")

        frame_i = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            perf.start_frame()

            prior = trk.pos if trk.locked else None
            d = det.detect(frame, prior_pos=prior)
            det_xy = (d["cx"], d["cy"]) if d else None
            (tx, ty), locked = trk.update(det_xy)

            vis = frame.copy()
            h, w = vis.shape[:2]
            cv2.drawMarker(vis, (w // 2, h // 2), (0, 255, 255),
                            markerType=cv2.MARKER_CROSS, markerSize=14, thickness=1)
            color = (0, 255, 0) if locked else (0, 0, 255)
            cv2.circle(vis, (int(tx), int(ty)), 12, color, 2)
            cv2.putText(vis, "LOCKED" if locked else "SEARCHING", (8, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)
            out_frames.append(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))

            sim_time += dt
            perf.end_frame(locked, None, sim_time)

            frame_i += 1
            if total > 0:
                progress.progress(min(frame_i / total, 1.0),
                                   text=f"Processed {frame_i}/{total} frames")

        cap.release()
        progress.empty()

        summary = perf.summary()
        csv_path = "/tmp/upload_performance_log.csv"
        report_path = "/tmp/upload_performance_report.txt"
        perf.save_csv(csv_path)
        perf.save_report(report_path)

        st.session_state["upload_results"] = (out_frames, summary, csv_path, report_path, fps_in)

    up_results = st.session_state["upload_results"]

    if up_results is not None:
        out_frames, summary, csv_path, report_path, fps_in = up_results

        if not out_frames:
            st.warning("No frames were read from this video — check the file and try again.")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Tracking playback")
                idx = st.slider("Frame", 0, len(out_frames) - 1, 0, key="upload_frame_slider")
                st.image(out_frames[idx], use_container_width=True)

                with st.spinner("Encoding output video..."):
                    out_path = make_video(out_frames, fps=fps_in, path="/tmp/upload_tracking_output.mp4")
                with open(out_path, "rb") as f:
                    video_bytes = f.read()
                st.video(video_bytes)
                st.download_button("⬇ Download annotated video (.mp4)", video_bytes,
                                    file_name="upload_tracking_output.mp4", mime="video/mp4",
                                    key="upload_video_dl")

            with col2:
                st.subheader("Performance summary")
                for k, v in summary.items():
                    st.metric(k.replace("_", " ").title(), v)

            st.subheader("Deliverables")
            c1, c2 = st.columns(2)
            with c1:
                with open(csv_path, "rb") as f:
                    st.download_button("⬇ Download performance_log.csv", f,
                                        file_name="performance_log.csv", mime="text/csv",
                                        key="upload_csv_dl")
            with c2:
                with open(report_path, "rb") as f:
                    st.download_button("⬇ Download performance_report.txt", f,
                                        file_name="performance_report.txt", mime="text/plain",
                                        key="upload_report_dl")
    elif uploaded_file is None:
        st.info("Upload a video above, then click **Process video**.")
