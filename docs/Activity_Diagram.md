# Illegal Mining Detection Pipeline - Activity Diagram

## What this means for your program:
The phrase *"from raw tile ingestion through sliding-window inference to final area calculation"* perfectly describes the exact process happening in your `inference_batch_PERFECT_BACKUP.ipynb` and `inference_visualizer 1.ipynb` scripts.

Here is the breakdown of what it means in your code:
1. **Raw Tile Ingestion:** Loading the massive, high-resolution satellite imagery from the `data image big` folder into memory.
2. **Sliding-Window Inference:** The code cannot feed a gigantic image into the CNN all at once. Instead, it creates a "window" (e.g., 224x224 pixels) that "slides" across the large image grid by grid. For every single grid/patch, it asks the trained EfficientNet-B0 model: *"Is there illegal mining here?"*
3. **Final Area Calculation:** After scanning the entire grid, the program counts how many patches were flagged as "mining". Since you know the real-world dimensions of each pixel (spatial resolution), it multiplies the number of positive patches by the area per patch to calculate the total acreage/hectares of illegal mining.

---

## The Activity Diagram
*Note: You can copy and paste the code below into any Mermaid renderer (like Mermaid Live Editor or a Markdown file) to generate the visual flowchart.*

```mermaid
flowchart TD
    %% Define Styles
    classDef startEnd fill:#f9d0c4,stroke:#333,stroke-width:2px;
    classDef process fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef data fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;

    %% Nodes
    Start([Start Inference Pipeline]) ::: startEnd
    
    LoadImage[/"Raw Tile Ingestion\n(Load Satellite Image from 'data image big')"/] ::: data
    LoadModel[/"Load Trained CNN Model\n(e.g., EfficientNet-B0 from 'saved_models')"/] ::: data
    
    InitGrid["Initialize Grid / Sliding Window Parameters\n(e.g., 224x224 patch size)"] ::: process
    ExtractPatch["Extract Next Image Patch\n(Sliding Window)"] ::: process
    
    Preprocess["Preprocess Patch\n(Resize, Normalize)"] ::: process
    Predict["Model Inference\n(Predict Mining vs Non-Mining)"] ::: process
    
    CheckMining{"Is Mining Detected?"} ::: decision
    RecordPatch["Record Patch Coordinates\n& Increment Mining Counter"] ::: process
    
    CheckMore{"Are there more patches\nin the image?"} ::: decision
    
    CalcArea["Final Area Calculation\n(Total Mining Patches × Area per Patch)"] ::: process
    SaveResult[/"Output Result\n(Heatmap Visualization & Total Area)"/] ::: data
    
    End([End Simulation]) ::: startEnd

    %% Connections
    Start --> LoadImage
    Start --> LoadModel
    LoadImage --> InitGrid
    LoadModel --> InitGrid
    
    InitGrid --> ExtractPatch
    ExtractPatch --> Preprocess
    Preprocess --> Predict
    Predict --> CheckMining
    
    CheckMining -- Yes --> RecordPatch
    CheckMining -- No --> CheckMore
    RecordPatch --> CheckMore
    
    CheckMore -- Yes --> ExtractPatch
    CheckMore -- No --> CalcArea
    
    CalcArea --> SaveResult
    SaveResult --> End
```
