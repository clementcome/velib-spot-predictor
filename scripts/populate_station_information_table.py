from velib_spot_predictor.data.database.context import DatabaseSession
from velib_spot_predictor.data.load_data import (
    load_station_information,
    save_station_information_to_sql,
)

station_information = load_station_information(
    "data/raw/station_information.json"
)
db_session = DatabaseSession()
with db_session as session:
    save_station_information_to_sql(station_information, db_session.engine)
