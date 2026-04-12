import streamlit as st
import pandas as pd
from utils.plots import get_mining_trend_fig
import base64
import os

st.title("📊 Analysis & Reports")
st.markdown("Comprehensive processing results and site-specific risk assessments.")

res = st.session_state.get('results', {})
if not res:
    st.info("No analysis data found. Please run the AI pipeline from the **Upload Files** page first.")
    st.stop()

# Overall Trend Section
st.markdown("### 📈 Overall Area Trend")
trend_buf = get_mining_trend_fig(res)
st.image(trend_buf, use_container_width=True)

st.divider()

# Site Report Generation Section (Formerly Site Report page)
st.markdown("### 📋 Site Intelligence Report")
site_id = st.session_state.get('site_id', 'SITE-01')

years = sorted(list(res.keys()))
if len(years) > 0:
    latest_year = years[-1]
    latest_data = res[latest_year]
    baseline_year = years[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Site Designator", site_id)
    col2.metric(f"Current Footprint ({latest_year})", f"{latest_data['area_km2']:.2f} km²")
    
    if len(years) > 1:
        growth = latest_data['area_km2'] - res[baseline_year]['area_km2']
        growth_pct = (growth / res[baseline_year]['area_km2'] * 100) if res[baseline_year]['area_km2'] > 0 else 0
        col3.metric(f"Expansion since {baseline_year}", f"{growth:+.2f} km²", f"{growth_pct:+.1f}%", delta_color="inverse")
    
    # Risk Assessment
    val = latest_data['area_km2']
    if val > 170:
        risk = "🔴 CRITICAL (Active Expansion)"
    elif val > 100:
        risk = "🟠 MODERATE (Persistent Mining)"
    else:
        risk = "🟢 LOW (Minimal Activity)"
        
    st.markdown(f"**Risk Profile:** {risk}")
    
    # Yearly Summary Table
    df = pd.DataFrame([{
        "Year": y, 
        "Area (km²)": res[y]['area_km2'],
        "Coverage (%)": res[y]['coverage_pct']
    } for y in years])
    
    st.dataframe(df, use_container_width=True)
    
    # Download report
    report_text = f"""MINEWATCH SITE INTELLIGENCE REPORT
Date Generated: {pd.Timestamp.now().strftime('%Y-%m-%d')}
Site ID: {site_id}
Risk Profile: {risk.split()[1]}

== METRICS ==
"""
    for y in years:
        report_text += f"{y}: {res[y]['area_km2']:.2f} km^2\n"
        
    b64 = base64.b64encode(report_text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{site_id}_report.txt" class="stButton>button">📥 Download Text Report</a>'
    st.markdown(href, unsafe_allow_html=True)

