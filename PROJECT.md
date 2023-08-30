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
