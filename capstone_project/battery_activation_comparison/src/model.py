import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LeakyReLU, PReLU, Activation

def mish(x):
    """
    Mish activation function: x * tanh(softplus(x))
    """
    return x * tf.math.tanh(tf.math.softplus(x))

def swish(x):
    """
    Swish activation function: x * sigmoid(x)
    """
    return x * tf.math.sigmoid(x)

def build_model(activation_name, input_dim):
    """
    Builds the model with the specified activation function.
    Architecture: Dense(128) -> Dense(64) -> Dense(32) -> Dense(1)
    """
    model = Sequential()
    
    # helper for adding activation cleanly
    def get_activation_layer(act_name):
        act_name = act_name.lower()
        if act_name == 'leaky_relu':
            return LeakyReLU(alpha=0.3)
        elif act_name == 'prelu':
            return PReLU()
        elif act_name == 'mish':
            return Activation(mish)
        elif act_name == 'swish':
            return Activation(swish)
        else:
            # For 'tanh', 'relu', 'elu', 'gelu', 'sigmoid'
            return Activation(act_name)

    # Input Layer + Hidden 1
    model.add(Dense(128, input_shape=(input_dim,)))
    model.add(get_activation_layer(activation_name))
    
    # Hidden 2
    model.add(Dense(64))
    model.add(get_activation_layer(activation_name))
    
    # Hidden 3
    model.add(Dense(32))
    model.add(get_activation_layer(activation_name))
    
    # Output Layer (Linear for Regression)
    model.add(Dense(1, activation='linear'))
    
    return model
