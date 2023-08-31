FROM velib_base

WORKDIR /app

# Copy the rest of the application code
COPY velib_spot_predictor /app/velib_spot_predictor
COPY README.md /app/README.md

# Install only current project
RUN poetry install --only-root
