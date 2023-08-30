from joblib import load
from sklearn.base import RegressorMixin

def load_model(model_path: str) -> RegressorMixin:
    model = load(model_path)
    return model
