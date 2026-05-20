import numpy as np
import joblib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(BASE_DIR, "model.pkl"))
label_encoders = joblib.load(os.path.join(BASE_DIR, "label_encoders.pkl"))
top_features = joblib.load(os.path.join(BASE_DIR, "top_features.pkl"))


def encode_input(values):
    encoded = []

    for i, col in enumerate(top_features):
        val = values[i]

        if col in label_encoders:
            val = label_encoders[col].transform([str(val)])[0]

        encoded.append(val)

    return encoded


def model_predict(input_values):
    processed = encode_input(input_values)
    input_array = np.array(processed).reshape(1, -1)

    return float(model.predict(input_array)[0])