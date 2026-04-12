from flask import Flask, jsonify, send_from_directory, request
import time
import os
import re

app = Flask(__name__, static_folder='frontend')

# Response caching and rate-limit middleware
from utils.cache import register_cache_middleware
register_cache_middleware(app)

# Exact Demo Results mapped from Streamlit inference caching
DEMO_RESULTS = {
    2021: {"area_km2": 155.95, "coverage_pct": 1.29,  "overlay_path": "inference_output/temporal/2021_overlay.png", "heatmap_path": "inference_output/temporal/2021_heatmap.png"},
    2022: {"area_km2": 156.26, "coverage_pct": 1.30,  "overlay_path": "inference_output/temporal/2022_overlay.png", "heatmap_path": "inference_output/temporal/2022_heatmap.png"},
    2023: {"area_km2": 170.70, "coverage_pct": 1.42,  "overlay_path": "inference_output/temporal/2023_overlay.png", "heatmap_path": "inference_output/temporal/2023_heatmap.png"},
    2024: {"area_km2": 167.83, "coverage_pct": 1.39,  "overlay_path": "inference_output/temporal/2024_overlay.png", "heatmap_path": "inference_output/temporal/2024_heatmap.png"},
    2025: {"area_km2": 172.34, "coverage_pct": 1.43,  "overlay_path": "inference_output/temporal/2025_overlay.png", "heatmap_path": "inference_output/temporal/2025_heatmap.png"},
}

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path.startswith('inference_output/'):
        return send_from_directory('inference_output', path.split('inference_output/')[1])
    return send_from_directory(app.static_folder, path)

@app.route('/api/analyze_batch', methods=['POST'])
def analyze_batch():
    results = []
    
    # Accept multiple files from FormData
    if 'files' in request.files:
        uploaded_files = request.files.getlist('files')
    elif 'file' in request.files:
        uploaded_files = [request.files['file']]
    else:
        uploaded_files = []
        
    for file in uploaded_files:
        filename = file.filename if file.filename else "unknown_file.jp2"
        target_year = 2024
        
        match = re.search(r'(20\d{2})', filename)
        if match:
            target_year = int(match.group(1))
            
        if target_year not in DEMO_RESULTS:
            target_year = min(DEMO_RESULTS.keys(), key=lambda y: abs(y - target_year))
            
        result = DEMO_RESULTS[target_year]
        baseline_year = min(DEMO_RESULTS.keys())
        expansion = round(result['area_km2'] - DEMO_RESULTS[baseline_year]['area_km2'], 2)
        risk_level = "CRITICAL" if expansion > 10 else "MODERATE" if expansion > 0 else "STABLE"
        
        results.append({
            "filename": filename,
            "year_detected": target_year,
            "current_footprint": result['area_km2'],
            "baseline_footprint": DEMO_RESULTS[baseline_year]['area_km2'],
            "expansion": expansion,
            "expansion_pct": round(result['coverage_pct'], 2),
            "risk": risk_level,
            "overlay_path": result['overlay_path'],
            "heatmap_path": result['heatmap_path']
        })
        
    return jsonify({
        "status": "success",
        "results": results
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    # Attempt to gracefully parse the uploaded file 
    target_year = 2024 # Default fallback
    filename = "unknown_file.jp2"
    
    if 'file' in request.files:
        file = request.files['file']
        if file.filename:
            filename = file.filename
            # Regex to simulate `utils.geo.extract_year_from_filename`
            match = re.search(r'(20\d{2})', filename)
            if match:
                target_year = int(match.group(1))
            
    # Guarantee year maps to a known Demo Result cache to prevent crash on random user files
    if target_year not in DEMO_RESULTS:
        target_year = min(DEMO_RESULTS.keys(), key=lambda y: abs(y - target_year))
        
    result = DEMO_RESULTS[target_year]
    baseline_year = 2021 if target_year != 2021 else 2021
    expansion = round(result['area_km2'] - DEMO_RESULTS[baseline_year]['area_km2'], 2)
    
    risk_level = "CRITICAL" if expansion > 10 else "MODERATE" if expansion > 0 else "STABLE"

    return jsonify({
        "status": "success",
        "filename": filename,
        "year_detected": target_year,
        "current_footprint": result['area_km2'],
        "baseline_footprint": DEMO_RESULTS[baseline_year]['area_km2'],
        "expansion": expansion,
        "expansion_pct": round(result['coverage_pct'], 2),
        "risk": risk_level,
        "overlay_path": result['overlay_path'],
        "heatmap_path": result['heatmap_path']
    })

@app.route('/api/change_matrix', methods=['GET'])
def get_change_matrix():
    """Exact data from 4_temporal.py Change Detection Matrix"""
    return jsonify({
        "matrix": [
            {"year": 2021, "persistent": None, "new_exp": 155.95, "recovered": None, "net": 155.95},
            {"year": 2022, "persistent": 120.50, "new_exp": 35.76, "recovered": 35.45, "net": 156.26},
            {"year": 2023, "persistent": 135.10, "new_exp": 35.60, "recovered": 21.16, "net": 170.70},
            {"year": 2024, "persistent": 145.50, "new_exp": 22.33, "recovered": 25.20, "net": 167.83},
            {"year": 2025, "persistent": 150.20, "new_exp": 22.14, "recovered": 17.63, "net": 172.34}
        ]
    })

@app.route('/api/model_benchmark', methods=['GET'])
def get_model_benchmark():
    """Exact data from 6_model_comparison.py"""
    return jsonify({
        "models": [
            {"name": "Custom CNN",       "accuracy": 0.9167, "auc": 0.9741, "f1": 0.88, "precision": 0.91, "recall": 0.96},
            {"name": "Enhanced CNN",     "accuracy": 0.9257, "auc": 0.9785, "f1": 0.92, "precision": 0.92, "recall": 0.97},
            {"name": "ResNet-18",        "accuracy": 0.9189, "auc": 0.9738, "f1": 0.89, "precision": 0.93, "recall": 0.94},
            {"name": "MobileNetV2",      "accuracy": 0.9212, "auc": 0.9734, "f1": 0.90, "precision": 0.92, "recall": 0.95},
            {"name": "EfficientNet-B0",  "accuracy": 0.9279, "auc": 0.9711, "f1": 0.94, "precision": 0.94, "recall": 0.94},
            {"name": "EfficientNetV2-S", "accuracy": 0.9234, "auc": 0.9631, "f1": 0.93, "precision": 0.94, "recall": 0.95}
        ],
        "champion": "EfficientNet-B0"
    })

@app.route('/api/temporal_metrics', methods=['GET'])
def get_temporal_metrics():
    return jsonify({
        "matrix": [
            {"year": 2021, "persistent": None, "new_exp": 155.95, "recovered": None, "net": 155.95},
            {"year": 2022, "persistent": 120.50, "new_exp": 35.76, "recovered": 35.45, "net": 156.26},
            {"year": 2023, "persistent": 135.10, "new_exp": 35.60, "recovered": 21.16, "net": 170.70},
            {"year": 2024, "persistent": 145.50, "new_exp": 22.33, "recovered": 25.20, "net": 167.83},
            {"year": 2025, "persistent": 150.20, "new_exp": 22.14, "recovered": 17.63, "net": 172.34}
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
