import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

def plot_history(histories, metric, ylabel, filename):
    plt.figure(figsize=(10, 6))
    for act, hist in histories.items():
        plt.plot(hist[metric], label=act)
    plt.title(f'{ylabel} vs Epochs')
    plt.xlabel('Epochs')
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join('plots', filename))
    plt.close()

def plot_bar_chart(data_dict, title, ylabel, filename):
    plt.figure(figsize=(10, 6))
    sns.barplot(x=list(data_dict.keys()), y=list(data_dict.values()))
    plt.title(title)
    plt.xlabel('Activation Function')
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join('plots', filename))
    plt.close()

def generate_all_plots(results):
    if not os.path.exists('plots'):
        os.makedirs('plots')
        
    histories = {k: v['history'] for k, v in results.items()}
    
    # 1. Training Loss vs Epoch
    plot_history(histories, 'loss', 'Training Loss (MSE)', 'train_loss.png')
    
    # 2. Validation Loss vs Epoch
    plot_history(histories, 'val_loss', 'Validation Loss (MSE)', 'val_loss.png')
    
    # 3. Training MAE vs Epoch
    plot_history(histories, 'mae', 'Training MAE', 'train_mae.png')
    
    # 4. Gradient Norms vs Epoch
    plt.figure(figsize=(10, 6))
    for act, res in results.items():
        plt.plot(res['gradient_norms'], label=act)
    plt.title('Global Gradient Norm vs Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('Gradient Norm')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join('plots', 'gradient_norms.png'))
    plt.close()
    
    # 5. Training Time Bar Chart
    times = {k: v['training_time'] for k, v in results.items()}
    plot_bar_chart(times, 'Training Time Comparison', 'Time (seconds)', 'training_time.png')
    
    # 6. Final RMSE Bar Chart
    rmses = {k: v['history']['val_rmse'][-1] for k, v in results.items()}
    plot_bar_chart(rmses, 'Final Validation RMSE Comparison', 'RMSE', 'val_rmse.png')
    
    # 7. Convergence Speed Summary
    convergence = {k: v['convergence_epoch'] for k, v in results.items()}
    plot_bar_chart(convergence, 'Convergence Speed (Epochs to 90% Best)', 'Epochs', 'convergence_speed.png')
