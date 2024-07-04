alembic upgrade head
curl https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json -o data/raw/station_information.json
fill_station_information_table data/raw/station_information.json