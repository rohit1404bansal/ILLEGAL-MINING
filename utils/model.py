import streamlit as st
import torch
import torch.nn as nn
from torchvision import models, transforms
import numpy as np
from PIL import Image
import gc
import os
import matplotlib.pyplot as plt

@st.cache_resource
def load_model(model_path="saved_models/best_model.pth"):
    if not os.path.exists(model_path):
        st.warning(f"Model not found at {model_path}. Using untutored model for testing.")
    model = models.efficientnet_b0(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(1280, 256),
        nn.ReLU(inplace=True),
        nn.Dropout(0.4),
        nn.Linear(256, 2)
    )
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    return model

def get_transforms():
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
    ])

def run_inference(img_rgb, model, transform, patch_size=64, stride=32, batch_size=64, threshold=0.6, progress_bar=None, progress_text=None):
    h, w, _ = img_rgb.shape
    patches = []
    coords = []
    
    # Extract patches
    for y in range(0, h - patch_size + 1, stride):
        for x in range(0, w - patch_size + 1, stride):
            patch = img_rgb[y:y+patch_size, x:x+patch_size]
            pil_img = Image.fromarray(patch)
            t_img = transform(pil_img)
            patches.append(t_img)
            coords.append((y, x))
            
    n_patches = len(patches)
    prob_map = np.zeros((h, w), dtype=np.float32)
    counts = np.zeros((h, w), dtype=np.float32)
    detections = []
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    
    for i in range(0, n_patches, batch_size):
        batch = torch.stack(patches[i:i+batch_size]).to(device)
        with torch.no_grad():
            outputs = model(batch)
            probs = torch.nn.functional.softmax(outputs, dim=1)[:, 0].cpu().numpy() # Mining prob
            
        for b_idx in range(len(probs)):
            py, px = coords[i + b_idx]
            p = probs[b_idx]
            prob_map[py:py+patch_size, px:px+patch_size] += p
            counts[py:py+patch_size, px:px+patch_size] += 1
            if p >= threshold:
                detections.append({'y': py, 'x': px, 'prob': p})
                
        if progress_bar:
            progress_bar.progress(min(1.0, (i + batch_size) / n_patches), text=progress_text)
            
    prob_map = np.divide(prob_map, counts, out=np.zeros_like(prob_map), where=counts!=0)
    
    del patches, coords, counts
    gc.collect()
    
    return prob_map, detections

def make_overlay(img_rgb, prob_map, threshold=0.6):
    overlay = img_rgb.copy()
    mask = prob_map >= threshold
    overlay[mask] = [255, 0, 0] # Highlight mining as red
    return overlay
