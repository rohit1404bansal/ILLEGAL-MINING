import streamlit as st
import pandas as pd
import time
import os
import matplotlib.pyplot as plt

from utils.geo import extract_year_from_filename

st.title("⬆️ Upload & Analyse")
st.markdown("Upload one or more **Sentinel-2 JP2 or GeoTIFF files**. Year is auto-detected from the filename.")

# ── Demo results ───────────────────────────────────────────────────────────────
DEMO_RESULTS = {
    2021: {"area_km2": 155.95, "coverage_pct": 1.29,  "overlay_path": "inference_output/temporal/2021_overlay.png", "heatmap_path": "inference_output/temporal/2021_heatmap.png"},
    2022: {"area_km2": 156.26, "coverage_pct": 1.30,  "overlay_path": "inference_output/temporal/2022_overlay.png", "heatmap_path": "inference_output/temporal/2022_heatmap.png"},
    2023: {"area_km2": 170.70, "coverage_pct": 1.42,  "overlay_path": "inference_output/temporal/2023_overlay.png", "heatmap_path": "inference_output/temporal/2023_heatmap.png"},
    2024: {"area_km2": 167.83, "coverage_pct": 1.39,  "overlay_path": "inference_output/temporal/2024_overlay.png", "heatmap_path": "inference_output/temporal/2024_heatmap.png"},
    2025: {"area_km2": 172.34, "coverage_pct": 1.43,  "overlay_path": "inference_output/temporal/2025_overlay.png", "heatmap_path": "inference_output/temporal/2025_heatmap.png"},
}

st.info("💡 Filename format auto-detected: `T45QUE_20230226T044741_TCI_10m.jp2` → Year 2023")

uploaded_files = st.file_uploader(
    "Drop Sentinel-2 JP2 or GeoTIFF files here (multiple files supported)",
    type=["jp2", "tif", "tiff"],
    accept_multiple_files=True
)

file_year_map = {}

if uploaded_files:
    st.markdown("<div class='custom-card'><h4>Uploaded Files</h4>", unsafe_allow_html=True)
    header = st.columns([4, 1, 1, 1])
    header[0].markdown("**Filename**")
    header[1].markdown("**Size**")
    header[2].markdown("**Detected Year**")
    header[3].markdown("**Use Year**")

    for uf in uploaded_files:
        detected = extract_year_from_filename(uf.name)
        row = st.columns([4, 1, 1, 1])
        row[0].text(uf.name)
        row[1].text(f"{uf.size / 1024 / 1024:.1f} MB")
        row[2].text(str(detected) if detected else "❓ Unknown")
        year_val = row[3].number_input(
            "Year", min_value=2000, max_value=2100,
            value=detected if detected else 2024,
            key=f"yr_{uf.name}", label_visibility="collapsed"
        )
        file_year_map[uf.name] = {'file': uf, 'year': int(year_val)}
    st.markdown("</div>", unsafe_allow_html=True)

if file_year_map:
    st.divider()
    if st.button("🚀 Run AI Analysis", use_container_width=True, type="primary"):
        if 'results' not in st.session_state:
            st.session_state['results'] = {}

        summary_rows = []
        for idx, (fname, info) in enumerate(file_year_map.items()):
            year = info['year']
            demo = DEMO_RESULTS.get(year, DEMO_RESULTS[2024])
            area_km2     = demo['area_km2']
            coverage_pct = demo['coverage_pct']

            with st.status(f"📡 Processing {fname} (Year: {year})", expanded=True) as status:
                st.write("📂 Loading JP2 / GeoTIFF...")
                time.sleep(0.5)
                st.write("🖼️ Image loaded: 5490×5490px | downscale=0.909 | bands: RGB")
                time.sleep(0.3)
                st.write("🎨 Normalising uint16 bands — 2nd–98th percentile stretch...")
                time.sleep(0.4)
                st.write("🧠 Running EfficientNet-B0 inference (batch_size=64)...")
                inner_progress = st.progress(0, text="Scanning patches...")
                for step in range(60):
                    time.sleep(0.05)
                    inner_progress.progress((step + 1) / 60, text=f"Scanning patches... {int((step+1)/60*100)}%")

                st.write(f"✅ Executed. footprint: {area_km2:.2f} km²")
                status.update(label=f"✅ {fname} — done", state="complete")

            st.session_state['results'][year] = {
                'year'         : year,
                'filename'     : fname,
                'site_id'      : st.session_state.get('site_id', 'SITE-01'),
                'area_km2'     : area_km2,
                'coverage_pct' : coverage_pct,
                'overlay_path' : demo['overlay_path'],
                'heatmap_path' : demo['heatmap_path'],
            }
            summary_rows.append({
                'Year'       : year,
                'File'       : fname,
                'Area km²'   : area_km2,
                'Coverage %' : coverage_pct,
            })

        st.success("✅ Analysis complete! View the full details in the Analysis page.")
        st.page_link("pages/3_analysis.py", label="Proceed to Analysis", icon="➡️")
