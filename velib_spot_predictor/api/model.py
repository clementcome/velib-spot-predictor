from pydantic import BaseModel

class PredictionInput(BaseModel):
    id_station: int
    hour: int
    minute: int