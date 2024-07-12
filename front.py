"""Entry point for the front-end application."""

from velib_spot_predictor.front.app import app

server = app.server

if __name__ == "__main__":
    app.run(debug=True)
