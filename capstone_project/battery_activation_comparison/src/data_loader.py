import os
import pandas as pd
import requests

def download_and_load_data(data_dir='data/', fallback_url='https://raw.githubusercontent.com/fmardero/battery_aging/master/discharge.csv'):
    """
    Downloads the battery discharge data from the GitHub repository if it doesn't exist locally,
    and loads it into a pandas DataFrame.
    """
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    csv_path = os.path.join(data_dir, 'discharge.csv')
    
    if not os.path.exists(csv_path):
        print(f"Downloading dataset from {fallback_url}...")
        response = requests.get(fallback_url, stream=True)
        response.raise_for_status()
        with open(csv_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
    else:
        print(f"Dataset found locally at {csv_path}.")
        
    print("Loading dataset into pandas DataFrame...")
    df = pd.read_csv(csv_path)
    print(f"Dataset loaded. Shape: {df.shape}")
    
    return df

if __name__ == "__main__":
    # Test script directly
    df = download_and_load_data('../data/')
    print(df.head())
