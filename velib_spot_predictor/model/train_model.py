import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.base import RegressorMixin

def train(data: pd.DataFrame) -> RegressorMixin:
    X = data[["Identifiant station", "Heure"]]
    y = data["Nombre bornettes libres"]
    model = LinearRegression()
    model.fit(X, y)
    return model
    