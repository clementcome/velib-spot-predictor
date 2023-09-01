"""Submodule used for prediction."""
from joblib import load
from sklearn.base import RegressorMixin


def load_model(model_path: str) -> RegressorMixin:
    """Load a model from a joblib file.

    Parameters
    ----------
    model_path : str
        Path to the joblib file containing the model

    Returns
    -------
    RegressorMixin
        Model loaded from the joblib file
    """
    model = load(model_path)
    return model
