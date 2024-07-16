"""Models used in the API."""

from typing import Annotated

from pydantic import BaseModel, Field


class PredictionInput(BaseModel):
    """Input data for the prediction.

    Parameters
    ----------
    id_station : int
        Id of the station
    hour : conint(ge=0, lt=24)
        Hour of the day
    minute : conint(ge=0, lt=60)
        Minute of the hour
    """

    id_station: int
    hour: Annotated[int, Field(..., ge=0, lt=24)]
    minute: Annotated[int, Field(..., ge=0, lt=60)]


class PredictionOutput(BaseModel):
    """Output data for the prediction.

    Parameters
    ----------
    id_station : int
        Id of the station
    probability : confloat(ge=0, le=1)
        Probability of a spot being available
    """

    id_station: int
    prediction: Annotated[float, Field(ge=0)]
