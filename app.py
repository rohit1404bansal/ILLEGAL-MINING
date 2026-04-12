import streamlit as st

st.set_page_config(page_title="MineWatch Engine", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS for "premium" look
st.markdown("""
<style>
    /* Styling to make it look less 'blind' and basic */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #30363d;
    }
    .stButton>button {
        border-radius: 8px;
        transition: all 0.2s ease-in-out;
        border: 1px solid #30363d;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
        border-color: #3498db;
    }
    [data-testid="stMetricValue"] {
        color: #3498db;
        font-weight: bold;
    }
    .custom-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Define pages for st.navigation
pg = st.navigation([
    st.Page("pages/1_home.py", title="Dashboard Home", icon="🏠"),
    st.Page("pages/2_upload.py", title="Upload Files", icon="⬆️"),
    st.Page("pages/3_analysis.py", title="Analysis & Reports", icon="📊"),
    st.Page("pages/4_temporal.py", title="Temporal Analysis", icon="📈"),
    st.Page("pages/5_result_map.py", title="Result Map", icon="🗺️"),
    st.Page("pages/6_model_comparison.py", title="Model Comparison", icon="⚖️")
])

# Settings popover in sidebar
with st.sidebar:
    st.write("---")
    with st.popover("⚙️ Settings"):
        st.subheader("Analysis Configuration")
        settings = st.session_state.get('settings', {
            'threshold'  : 0.6,
            'patch_size' : 64,
            'stride'     : 32,
            'max_dim'    : 5000,
        })
        st.session_state['site_id'] = st.text_input("Site ID", value=st.session_state.get('site_id', 'SITE-01'))
        settings['threshold'] = st.slider("Confidence Threshold", 0.3, 0.9, settings['threshold'], 0.05)
        settings['max_dim'] = st.number_input("Max Image Dimension (px)", 1000, 15000, settings['max_dim'], 1000)
        st.session_state['settings'] = settings

pg.run()
