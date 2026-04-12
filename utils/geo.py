import rasterio
import numpy as np
from PIL import Image
import os
import tempfile
import streamlit as st


def save_uploaded_to_temp(uploaded_file):
    """
    Streamlit uploaded files are BytesIO objects — rasterio cannot open them directly.
    Write to a real temp file and return its path. Caller must delete it after use.
    """
    suffix = os.path.splitext(uploaded_file.name)[-1].lower()
    if suffix not in ('.jp2', '.tif', '.tiff'):
        suffix = '.jp2'
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(uploaded_file.getbuffer())
    tmp.flush()
    tmp.close()
    return tmp.name


def load_jp2(filepath_or_uploaded, max_dim=5000):
    """
    Load a JP2 or GeoTIFF file and return (img_rgb, transform, crs, scale).

    Accepts EITHER:
      - A string file path (from inference_batch or a saved temp file)
      - A Streamlit UploadedFile object (BytesIO) — automatically saved to temp

    Returns:
      img_rgb  : (H, W, 3) uint8 numpy array
      transform: rasterio affine transform (or None)
      crs      : rasterio CRS (or None)
      scale    : float — downsampling factor applied (1.0 = no downsampling)
    """
    tmp_path = None

    # Handle Streamlit UploadedFile — save to disk first
    if hasattr(filepath_or_uploaded, 'getbuffer'):
        tmp_path = save_uploaded_to_temp(filepath_or_uploaded)
        filepath = tmp_path
    else:
        filepath = filepath_or_uploaded

    try:
        with rasterio.open(filepath) as src:
            h, w = src.height, src.width
            scale = min(1.0, max_dim / max(h, w)) if max_dim else 1.0
            new_h, new_w = int(h * scale), int(w * scale)

            # Read RGB bands at target size
            n_bands = src.count
            if n_bands >= 3:
                img_arr = src.read(
                    [1, 2, 3],
                    out_shape=(3, new_h, new_w),
                    resampling=rasterio.enums.Resampling.bilinear
                )
            else:
                band = src.read(
                    1,
                    out_shape=(new_h, new_w),
                    resampling=rasterio.enums.Resampling.bilinear
                )
                img_arr = np.stack([band, band, band])

            transform = src.transform
            crs = src.crs

        # (3, H, W) → (H, W, 3)
        img_arr = np.moveaxis(img_arr, 0, -1)

        # Normalise to uint8
        if img_arr.dtype == np.uint16:
            # Sentinel-2 uint16: stretch to 0-255
            p2  = np.percentile(img_arr, 2)
            p98 = np.percentile(img_arr, 98)
            img_arr = np.clip((img_arr.astype(np.float32) - p2) / (p98 - p2 + 1e-8), 0, 1)
            img_arr = (img_arr * 255).astype(np.uint8)
        elif img_arr.dtype in (np.float32, np.float64):
            img_arr = np.clip(img_arr * 255, 0, 255).astype(np.uint8)
        elif img_arr.dtype != np.uint8:
            img_arr = img_arr.astype(np.uint8)

        return img_arr, transform, crs, scale

    except Exception as e:
        # Fallback: PIL (loses geo info but at least loads the image)
        try:
            pil_img = Image.open(filepath).convert('RGB')
            orig_w, orig_h = pil_img.size
            scale = min(1.0, max_dim / max(orig_h, orig_w)) if max_dim else 1.0
            if scale < 1.0:
                new_w, new_h = int(orig_w * scale), int(orig_h * scale)
                pil_img = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
            return np.array(pil_img), None, None, scale
        except Exception as e2:
            st.error(f"Failed to load image: {e} | {e2}")
            return None, None, None, 1.0
    finally:
        # Always clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def extract_year_from_filename(filename):
    """
    Extract year from Sentinel-2 filename.
    e.g. T45QUE_20230226T044741_TCI_10m.jp2 → 2023
    Falls back to None if pattern not found.
    """
    import re
    match = re.search(r'_(\d{4})\d{4}T', filename)
    if match:
        yr = int(match.group(1))
        if 2000 <= yr <= 2100:
            return yr
    # Try any 4-digit year in filename
    match2 = re.search(r'(20\d{2})', filename)
    if match2:
        return int(match2.group(1))
    return None


def pixel_to_latlon(transform, crs, px, py):
    """Convert pixel coordinates to (lat, lon) in WGS84."""
    if transform is None:
        return 0.0, 0.0
    try:
        import rasterio.warp
        lon, lat = rasterio.transform.xy(transform, py, px)
        if crs and crs.to_epsg() != 4326:
            xs, ys = rasterio.warp.transform(crs, "EPSG:4326", [lon], [lat])
            return round(ys[0], 6), round(xs[0], 6)
        return round(lat, 6), round(lon, 6)
    except Exception:
        return 0.0, 0.0
