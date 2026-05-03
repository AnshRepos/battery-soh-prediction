# 🔋 Battery State-of-Health Prediction

## 📖 Overview
This project predicts the State-of-Health (SoH) of lithium-ion batteries using deep learning. It compares different activation functions (ReLU, Sigmoid, Tanh) to analyze their impact on model performance.

## 🎯 Objective
- Predict battery health accurately
- Compare activation functions
- Analyze training performance

## ⚙️ Features
- Deep learning model implementation
- Comparative analysis of activation functions
- Visualization of training results
- Performance metrics (MSE, RMSE)

## 🛠️ Tech Stack
- Python
- TensorFlow / Keras
- NumPy, Pandas
- Matplotlib

## 📊 Results
The model shows variation in performance depending on activation function used. ReLU demonstrated faster convergence in most cases.

## 📸 Output Screenshots
### Training Loss
![Training Loss](src/assets/plots/train_loss.png)

### Validation Loss
![Validation Loss](src/assets/plots/val_loss.png)

### RMSE
![RMSE](src/assets/plots/val_rmse.png)

## ▶️ How to Run
```bash
pip install -r requirements.txt
python main.py
battery-soh-prediction/
│
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── assets/
│   │   └── plots/
│
├── README.md
├── requirements.txt
├── .gitignore
