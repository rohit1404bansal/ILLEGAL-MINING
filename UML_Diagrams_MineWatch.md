# MineWatch System Architecture Diagrams (UML)

This document contains standardized software tracking charts formatted in Mermaid language. 
You can paste these blocks into online viewers like https://mermaid.live/ to generate instant flowchart images.

## 1. Use Case Diagram
Defines the actors and the specific actions they are permitted to execute in the system.

```mermaid
flowchart LR
    Actor((System Analyst))
    
    Actor --> UC1[Upload Sentinel-2 Imagery]
    Actor --> UC2[Adjust CNN Confidence Thresholds]
    Actor --> UC3[Initiate Bulk AI Inference]
    Actor --> UC4[Audit GIS Result Overlays]
    Actor --> UC5[Compare Multi-Year Temporal Maps]
    Actor --> UC6[Export Text Reports & CSVs]
```

## 2. Activity Diagram
Maps the logical step-by-step decision flowchart of what happens during the core process (Analysis).

```mermaid
flowchart TD
    Start((Start)) --> Upload[User Uploads JP2/TIF File]
    Upload --> Load[Streamlit Saves temporary file & Uses Rasterio]
    Load --> Norm[Normalize Sentinel-2 uint16 limits to 0-255]
    Norm --> CNN[Run CNN Sliding Window Inference]
    CNN --> Batching[Slice into 64x64 patches at 32px Stride]
    Batching --> Model((EfficientNet-B0))
    Model --> Heatmap[Aggregate Overlapping Pixels to Probability Map]
    Heatmap --> Threshold{Probability >= User Threshold?}
    Threshold -- Yes --> Mark[Mark Pixel as Illegal Mining]
    Threshold -- No --> Ignore[Mark Pixel as Natural Ground]
    Mark --> Stats[Calculate Geographic Area km²]
    Ignore --> Stats
    Stats --> Render[Save UI PNG Overlays & Stash into Session Cache]
    Render --> End((End))
```

## 3. Sequence Diagram
Shows the chronological sequence of requests between the User, the App Frontend, and the Python Backend across a standard temporal run.

```mermaid
sequenceDiagram
    participant User
    participant App as Streamlit UI 
    participant Geo as GeoUtils (Rasterio)
    participant CNN as ModelUtils (PyTorch)
    
    User->>App: Submits 'T45QUE_2023.jp2' over frontend
    App->>Geo: Hand off Memory Buffer
    Geo-->>App: Extract Geolocation & Return Image Array
    User->>App: Adjusts Parameters & Clicks "Run AI Analysis"
    App->>CNN: Trigger Model Execution
    activate CNN
    CNN->>CNN: Torch.Device Forward Pass Tracking
    CNN-->>App: Return Raw Detection Values & Matrix
    deactivate CNN
    App->>App: Execute Spatial Formulas (Area km²)
    App-->>User: Refresh Dashboard with Processed Results
```

## 4. Class / Component Diagram
Shows how your separate python files map together methodically.

```mermaid
classDiagram
    class AppMain{
        +dict st.session_state
        +st.navigation()
        +sidebar_popover()
    }
    class Page_Upload{
        +dict file_year_map
        +start_analysis_loop()
    }
    class Utils_Geo{
        +load_jp2(BytesIO, max_dim)
        +extract_year_from_filename(string)
        +pixel_to_latlon(crs, px, py)
    }
    class Utils_Model{
        +load_model(weights_path)
        +run_inference(array, patch_stride)
        +make_overlay_map()
    }
    class Utils_Plots{
        +get_mining_trend_fig()
        +get_expansion_fig()
        +get_radar_fig()
    }
    
    AppMain --> Page_Upload : Routes Traffic
    Page_Upload --> Utils_Geo : Image Translation
    Page_Upload --> Utils_Model : AI Classification
    AppMain --> Utils_Plots : Generates Graph Metrics
```

## 5. Data Architecture Flow
Traces the physical trajectory of data from a raw disk file to a localized graphical output.

```mermaid
flowchart LR
    subgraph Input
        A[ESA Sentinel-2 JP2/TIF]
    end
    subgraph Memory Processing
        B[Bilinear Downsampling]
        C[2nd-98th Percentile Contrast Stretching]
    end
    subgraph Analysis Engine
        D[Pytorch DataLoader Iterator]
        E((EfficientNet Classifier))
    end
    subgraph Data Sink
        F[Binary Mask Overlay PNG]
        G[Spatial Area Statistics]
    end
    
    A --> B --> C 
    C --> D --> E
    E --> F
    E --> G
```
