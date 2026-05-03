import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def preprocess_data(df, target_batteries=['B0005', 'B0006', 'B0007', 'B0018']):
    """
    Preprocesses the raw time-series data into cycle-level tabular data.
    """
    # Filter for target batteries
    df = df[df['Battery'].isin(target_batteries)].copy()
    df = df.dropna()
    
    # Aggregate data per cycle per battery
    # Features wanted: voltage, current, temperature, cycle number
    # Target: discharge capacity
    # Since the raw data has many rows per cycle, we'll take the mean of measurements
    # and the max of the capacity (since capacity represents the SOH for that cycle)
    
    # Assuming 'id_cycle' is the cycle number column in fmardero's dataset
    cycle_df = df.groupby(['Battery', 'id_cycle']).agg({
        'Voltage_measured': 'mean',
        'Current_measured': 'mean',
        'Temperature_measured': 'mean',
        'Capacity': 'max'
    }).reset_index()
    
    # Rename for clarity
    cycle_df = cycle_df.rename(columns={
        'id_cycle': 'cycle_number',
        'Voltage_measured': 'avg_voltage',
        'Current_measured': 'avg_current',
        'Temperature_measured': 'avg_temperature',
        'Capacity': 'soh_capacity'
    })
    
    # Features and target
    X = cycle_df[['cycle_number', 'avg_voltage', 'avg_current', 'avg_temperature']]
    y = cycle_df['soh_capacity']
    
    # Split: Train 70%, Validation 15%, Test 15%
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    # Target validation size relative to temp is 15 / (70 + 15) = 15/85 ~= 0.1764
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.17647, random_state=42)
    
    # Normalize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_val_scaled, X_test_scaled, y_train.values, y_val.values, y_test.values, scaler

if __name__ == "__main__":
    # For independent testing
    from data_loader import download_and_load_data
    df = download_and_load_data('../data/')
    X_tr, X_v, X_te, y_tr, y_v, y_te, scaler = preprocess_data(df)
    print("Train shapes:", X_tr.shape, y_tr.shape)
    print("Val shapes:", X_v.shape, y_v.shape)
    print("Test shapes:", X_te.shape, y_te.shape)
