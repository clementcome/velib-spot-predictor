# Velib Spot Predictor

This project aims at developing an end-to-end project using Paris Open Data on velib stations in order to predict the available Velib spots.

## Getting started

## Usage

### Launching the API
```bash
uvicorn velib_spot_predictor.api:app --reload
```

## Deployment

### Docker
Image is published in clementcome/velib repository.

### PyPI
Package is published under velib-spot-predictor package.

## Development

### Installation

To develop locally, clone the repo and in a virtual environment with python 3.9 and poetry installed, run the command `poetry install`.
