# predict_today.py

import joblib
import os
from text_cleaner import TextCleaner   # <-- FIXED import

MODEL_PATH = os.environ.get("LEAD_MODEL_PATH", "models/lead_pipeline.joblib")

def load_model(path=None):
    if path is None:
        path = MODEL_PATH
    if not os.path.exists(path):
        return None
    model = joblib.load(path)
    return model

def predict_probability(model, text):
    if model is None:
        raise RuntimeError("Model not loaded")
    try:
        prob = model.predict_proba([text])[0][1]
        return float(prob)
    except Exception:
        try:
            score = model.decision_function([text])[0]
            import math
            prob = 1 / (1 + math.exp(-score))
            return float(prob)
        except Exception:
            raise
