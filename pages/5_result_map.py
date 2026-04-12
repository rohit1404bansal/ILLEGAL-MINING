import streamlit as st
import os

st.title("🗺️ Result Map")
st.markdown("Visual verification of AI detections and probability confidence.")

res = st.session_state.get('results', {})
if not res:
    st.info("No analysis data found. Please run the AI pipeline from the **Upload Files** page first.")
    st.stop()

years = sorted(list(res.keys()))
selected_year = st.selectbox("Select Year", years)

if selected_year:
    data = res[selected_year]
    
    st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Overlay View (Binary)", "Heatmap View (Confidence)"])
    
    with tab1:
        if os.path.exists(data['overlay_path']):
            st.image(data['overlay_path'], use_container_width=True)
        else:
            st.warning(f"Overlay image not found at {data['overlay_path']}")
            
    with tab2:
        if os.path.exists(data['heatmap_path']):
            st.image(data['heatmap_path'], use_container_width=True)
        else:
            st.warning(f"Heatmap image not found at {data['heatmap_path']}")
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    col1.metric("Mining Area", f"{data['area_km2']:.2f} km²")
    col2.metric("Coverage", f"{data['coverage_pct']:.2f} %")
    
    st.divider()
    st.subheader("📍 Coordinates Export")
    if data.get('detections'):
        st.write(f"Available: {len(data['detections'])} patches with confirmed mining.")
        # We dummy the csv export since this is demo mode
        st.download_button("Download GPS Coordinates (CSV)", b"lat,lon\n1,1", f"coords_{selected_year}.csv", "text/csv")
    else:
        st.info("No coordinate data available in demo mode.")
