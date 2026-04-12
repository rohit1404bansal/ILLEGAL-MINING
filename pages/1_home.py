import streamlit as st
import os

st.title("🛰️ MineWatch Engine")
st.markdown("<h3 style='color: #8b949e; margin-top: -10px;'>Intelligent Satellite Analysis for Illegal Mining Detection</h3>", unsafe_allow_html=True)

st.markdown("""
<div class='custom-card' style='text-align: center; margin-top: 20px; margin-bottom: 40px;'>
    <h2 style='color: #e6edf3;'>Welcome to the Dashboard</h2>
    <p style='font-size: 1.1em; color: #8b949e; max-width: 800px; margin: 0 auto;'>
        MineWatch leverages Advanced CNN architectures (EfficientNet-B0) to automate the detection, 
        tracking, and temporal analysis of illegal mining footprints using high-resolution Sentinel-2 imagery.
    </p>
</div>
""", unsafe_allow_html=True)

# Hero image or intro photos
col1, col2, col3 = st.columns(3)
with col1:
    if os.path.exists("inference_output/temporal/2021_overlay.png"):
         st.image("inference_output/temporal/2021_overlay.png", caption="AI Automated Detections", use_container_width=True)
with col2:
    if os.path.exists("inference_output/temporal/fig3_4class_change_map.png"):
         st.image("inference_output/temporal/fig3_4class_change_map.png", caption="Temporal Change Tracking", use_container_width=True)
with col3:
    if os.path.exists("inference_output/temporal/2025_heatmap.png"):
         st.image("inference_output/temporal/2025_heatmap.png", caption="Probability Heatmaps", use_container_width=True)

st.divider()

st.markdown("<div style='text-align: center;'><h3>Ready to analyse new imagery?</h3></div>", unsafe_allow_html=True)

col_center = st.columns([1, 2, 1])[1]
with col_center:
    if st.button("🚀 Upload & Analyse Files", use_container_width=True):
        st.switch_page("pages/2_upload.py")
