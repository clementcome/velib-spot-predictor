# Project

Description of how the project was built

## Set up

### Environment

For development purposes, `pyenv` and `poetry` are already installed on my PC (WSL).
Initialisation of the project: `poetry init`

Selecting python versions:
```bash
pyenv install 3.9.17
pyenv local 3.9.17
poetry env use 3.9
```

And then I added the desired packages using the command `poetry add --group=group package`.

### Docker

Docker images are saved into docker folder, split into to Dockerfile.base and other images for specific tasks.

#### Fetching data

Build images:
```bash
docker build -t clementcome/velib_base:v0.1.0 -f docker/Dockerfile.base .
docker build -t clementcome/velib:v0.1.0 -f docker/Dockerfile .
```

Run image:
```bash
docker run -v /home/clement/projects/velib-spot-predictor/data/raw/automated_fetching_v3:/data velib fetch_save_data /data
```

Push image to docker hub:
```bash
docker image push --all-tags clementcome/velib_base
docker image push --all-tags clementcome/velib
```

Using docker allows to schedule with crontab without having to wonder about execution environment. The crontab entry is:
```bash
* * * * * docker run -v /home/clement/projects/velib-spot-predictor/data/raw/automated_fetching_v3:/data velib fetch_save_data /data
```
test
