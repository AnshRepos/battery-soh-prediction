import time
import tensorflow as tf
from tensorflow.keras.optimizers import Adam
import numpy as np

class GradientNormCallback(tf.keras.callbacks.Callback):
    """
    Custom callback to record the global gradient norm at the end of each epoch.
    Helps analyze vanishing/exploding gradients.
    """
    def __init__(self, x_data, y_data):
        super(GradientNormCallback, self).__init__()
        self.x_data = tf.convert_to_tensor(x_data, dtype=tf.float32)
        self.y_data = tf.convert_to_tensor(y_data, dtype=tf.float32)
        self.gradient_norms = []

    def on_epoch_end(self, epoch, logs=None):
        with tf.GradientTape() as tape:
            y_pred = self.model(self.x_data, training=True)
            loss = self.model.compiled_loss(self.y_data, y_pred)
            
        gradients = tape.gradient(loss, self.model.trainable_weights)
        
        # Calculate global norm
        if gradients:
            global_norm = tf.linalg.global_norm([g for g in gradients if g is not None])
            self.gradient_norms.append(global_norm.numpy())
        else:
            self.gradient_norms.append(0.0)

def train_model(model, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
    """
    Compiles and trains the model, returning history and custom metrics.
    """
    model.compile(optimizer=Adam(), loss='mse', metrics=['mae', tf.keras.metrics.RootMeanSquaredError(name='rmse')])
    
    grad_callback = GradientNormCallback(X_train[:1000], y_train[:1000]) # Use a subset for gradient tracking to save time
    
    start_time = time.time()
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[grad_callback],
        verbose=0
    )
    end_time = time.time()
    
    training_time = end_time - start_time
    
    # Extract convergence speed: epochs to reach 90% of best val_loss
    best_val_loss = np.min(history.history['val_loss'])
    threshold = best_val_loss * 1.1 # Since it's loss, 90% performance is 10% higher than minimum
    convergence_epoch = epochs
    for i, val_loss in enumerate(history.history['val_loss']):
        if val_loss <= threshold:
            convergence_epoch = i + 1
            break
            
    results = {
        'history': history.history,
        'training_time': training_time,
        'gradient_norms': grad_callback.gradient_norms,
        'convergence_epoch': convergence_epoch
    }
    
    return model, results
