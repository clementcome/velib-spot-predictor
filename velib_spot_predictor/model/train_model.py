import pandas as pd
from sklearn.base import RegressorMixin
from sklearn.linear_model import LinearRegression


def train(data: pd.DataFrame) -> RegressorMixin:
    features = data[["Identifiant station", "Heure"]]
    y = data["Nombre bornettes libres"]
    model = LinearRegression()
    model.fit(features, y)
    return model
