1. HOW THE FILES ARE CONNECTED (PIPELINE ARCHITECTURE)

The project is divided into three main phases: Data Preparation, Model Training, and Inference/Dashboard.

[Phase 1: Data Preparation]
-> extract_patches.ipynb : This is the starting point. It takes raw, high-resolution satellite imagery (from the 'data image big' folder) and slices them into smaller, manageable image patches for the neural network. Outputs are saved and structured into the 'cnn dataset' folder.

[Phase 2: Model Training]
Once patches are extracted, the models are trained using the images in the 'cnn dataset':
-> train_cnn_model.ipynb : Trains the baseline Convolutional Neural Network.
-> train_transfer_models.ipynb : Trains the advanced models using Transfer Learning (e.g., EfficientNet-B0).
-> train_enhanced_models.ipynb : Applies data augmentation and enhanced techniques to improve accuracy and handle seasonal changes (clouds/flooding).

[Phase 3: Inference & Dashboard]
After models are trained and weights are saved in 'saved_models/', the following files are used to run predictions and visualize the data:
-> inference_batch_PERFECT_BACKUP.ipynb : Runs batch processing on multiple satellite images to generate geographical heatmaps of mining activity over time.
-> inference_visualizer 1.ipynb : A visual tool to see side-by-side comparisons of raw imagery vs. model predictions.
-> temporal_analysis.ipynb : Analyzes the change in mining activity over different years.

[Web Application]
-> app.py & server.py : The Streamlit-based web dashboard (MineWatch). It provides a user interface to upload new images and view detection results in real-time.


2. WHICH FILES TO RUN (AND IN WHAT ORDER)


If you want to test the entire pipeline from scratch, run the files in this order:

STEP 1: Run `extract_patches.ipynb` to prepare the dataset.
STEP 2: Run `train_transfer_models.ipynb` to train the deep learning model.
STEP 3: Run `inference_batch_PERFECT_BACKUP.ipynb` to test the model's accuracy on new images.

If you just want to run the User Interface (MineWatch Dashboard):
1. Open a terminal.
2. Ensure you have Streamlit installed (pip install streamlit).
3. Run the command: `streamlit run app.py`


