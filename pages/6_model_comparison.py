import streamlit as st
import pandas as pd
from utils.plots import get_comparison_bar_fig, get_radar_fig

st.title("⚖️ Model Comparison")
st.markdown("Extensive architectural benchmark establishing **EfficientNet-B0** as the champion model.")

models = ["Custom CNN", "Enhanced CNN", "ResNet-18", "MobileNetV2", "EfficientNet-B0", "EfficientNetV2-S"]
accs = [0.9167, 0.9257, 0.9189, 0.9212, 0.9279, 0.9234]
aucs = [0.9741, 0.9785, 0.9738, 0.9734, 0.9711, 0.9631]
f1s  = [0.88, 0.92, 0.89, 0.90, 0.94, 0.93]
precs= [0.91, 0.92, 0.93, 0.92, 0.94, 0.94]
recs = [0.96, 0.97, 0.94, 0.95, 0.94, 0.95]

tab1, tab2 = st.tabs(["Performance Metrics", "Radar Benchmark"])

with tab1:
    st.subheader("Benchmark Results")
    df = pd.DataFrame({
        "Model Architecture": models,
        "Accuracy": [f"{v:.4f}" for v in accs],
        "AUC-ROC": [f"{v:.4f}" for v in aucs],
        "F1-Score": [f"{v:.4f}" for v in f1s],
        "Precision": [f"{v:.2f}" for v in precs],
        "Recall": [f"{v:.2f}" for v in recs],
    })
    
    def highlight_max(s):
        is_max = s == s.max()
        return ['background-color: #1e3a8a' if v else '' for v in is_max]
        
    st.dataframe(df.style.apply(highlight_max, subset=["Accuracy", "AUC-ROC", "F1-Score"]), use_container_width=True)
    
    buf = get_comparison_bar_fig(accs, aucs, f1s, models)
    st.image(buf, use_container_width=True)

with tab2:
    st.subheader("Architectural Strengths")
    attrs_list = [[accs[i], precs[i], recs[i], f1s[i], aucs[i]] for i in range(len(models))]
    buf2 = get_radar_fig(models, attrs_list)
    
    colA, colB = st.columns([1, 2])
    colB.image(buf2, use_container_width=True)
    with colA:
        st.markdown("""
        **Champion: EfficientNet-B0**
        
        It achieved the ultimate balance across metrics with an F1-Score of **0.94**.
        While Enhanced CNN hit the highest AUC and Recall, EfficientNet-B0 reduced false positives significantly by increasing precision to **0.94**, making it ideal for the highly imbalanced mapping task.
        """)
