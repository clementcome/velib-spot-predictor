"""Methods used for training model."""
import pandas as pd
from sklearn.base import RegressorMixin
from sklearn.linear_model import LinearRegression


class Model(LinearRegression):
    """Model used for training."""

    pass


def train(data: pd.DataFrame) -> RegressorMixin:
    """
    Train a model to predict the number of available spots in a Velib station.

    Parameters
    ----------
    data : pd.DataFrame
        Data used for training

    Returns
    -------
    RegressorMixin
        Trained model
    """
    features = data[["Identifiant station", "Heure"]]
    y = data["Nombre bornettes libres"]
    model = Model()
    model.fit(features, y)
    return model
