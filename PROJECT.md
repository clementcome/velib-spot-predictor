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
docker build -t clementcome/velib_base:v0.1.0 -t clementcome/velib_base:latest  -f docker/Dockerfile.base .
docker build -t clementcome/velib:v0.1.0 -t clementcome/velib:latest -f docker/Dockerfile .
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

### Filling database with values
For now, database can be filled with values that are located in a local folder.
Before loading statuses of the stations, you need to fill the table with station information with the command `fill_station_information_table`.
Command used is `load_data_from_local_to_sql`.

Documentation of the previous commands is accessed with the usual `--help` flag.

## CI/CD pipeline

CI/CD pipeline:
- Validation
  - Linting
  - Testing
- Release control
- Version bumping
- Publishing
  - Docker image
  - Python package
