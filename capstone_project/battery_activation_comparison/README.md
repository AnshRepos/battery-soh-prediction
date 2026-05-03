# Battery SOH Activation Function Comparison

This project is a complete end-to-end deep learning pipeline built using Python and TensorFlow. The primary goal is to predict the State of Health (SOH) and remaining capacity of NASA's Li-ion batteries while comprehensively comparing the performance, convergence speed, and trainability metrics of various hidden layer activation functions.

## Dataset
Uses the NASA Ames Li-ion Battery Aging dataset, specifically fetching pre-processed cycle-level measurements from [fmardero/battery_aging](https://github.com/fmardero/battery_aging/blob/master/discharge.csv).
The models train on cycle data from batteries `B0005`, `B0006`, `B0007`, and `B0018`.

## Setup Instructions

### 1. Requirements

Ensure you have Python 3.8+ installed. It is recommended to use a virtual environment.

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Mac/Linux
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Running the Pipeline

Execute the main script. The script will automatically download the dataset (if not present), prepare the features, train 9 identical architectures evaluating different activations, and output final metrics.

```bash
python main.py
```

## Directory Structure

```
battery_activation_comparison/
│
├── data/              # Stores the raw discharge.csv
├── notebooks/         # (Optional) For EDA and experimentation
├── src/
│   ├── data_loader.py   # Downloads and loads dataset
│   ├── preprocessing.py # Prepares cyclical SOH features
│   ├── model.py         # Defines Neural network with Swish and Mish manually implemented
│   ├── train.py         # Training loop with GradientNormCallback
│   ├── utils.py         # Advanced visualization helpers
│   └── compare.py       # Orchestrates and logs entire pipeline run
│
├── plots/             # Contains output graphical comparisons
├── models/            # Saved `.h5` models by activation
├── results/           # JSON file containing structured model histories
├── requirements.txt
├── README.md
└── main.py
```

## Analyzed Activations
- `Tanh`
- `ReLU`
- `Leaky ReLU`
- `PReLU`
- `ELU`
- `Swish` (Manually integrated)
- `Mish` (Manually integrated)
- `GELU`
- `Sigmoid`

## Final Outputs
Inside `plots/`, you will find detailed graphics of:
- **Gradient norm tracking** (vital for identifying vanishing/exploding gradients)
- **Train and validation convergence plots**
- **Convergence speed benchmarks** (Epochs to 90% performance)
- **Bar charts mapping final RMSE scores** and Total Training times per activation.
