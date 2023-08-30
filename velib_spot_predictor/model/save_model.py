import click
from joblib import dump

from velib_spot_predictor.data.load_data import load_raw
from velib_spot_predictor.model.train_model import train

@click.command()
@click.argument("data-path")
@click.argument("model-path")
def save_model(data_path: str, model_path: str) -> None:
    data = load_raw(data_path)
    model = train(data)
    dump(model, model_path)