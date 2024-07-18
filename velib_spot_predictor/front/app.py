"""Dash application for the front-end."""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple

import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import geopandas as gpd
import pandas as pd
import plotly.express as px
import requests
from dash import Input, Output, State, dcc, html
from dash_extensions.javascript import assign
from shapely import Polygon

from velib_spot_predictor.data.geo import (
    CatchmentAreaBuilderColumns,
    CatchmentAreaBuilderGeometry,
)

VELIB_API_URL = os.environ.get("VELIB_API_URL", "http://localhost:8000")


communes = gpd.read_file("data/external/communes-ile-de-france.geojson")


# Join the availability and station information
def join_occupation_and_station_information(
    occupation_df: pd.DataFrame,
    station_information_catchment_area: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Join the availability and station information.

    Parameters
    ----------
    occupation_df : pd.DataFrame
        The dataframe containing the availability
    station_information_catchment_area : gpd.GeoDataFrame
        The dataframe containing the station information and the catchment area


    Returns
    -------
    gpd.GeoDataFrame
        The dataframe containing the availability and the station information
    """
    station_occupation = station_information_catchment_area.merge(
        occupation_df[["station_id", "num_bikes_available"]],
        on="station_id",
        how="right",
    )
    station_occupation["occupation"] = (
        100
        * station_occupation["num_bikes_available"]
        / station_occupation["capacity"]
    )
    station_occupation["tooltip"] = station_occupation["name"]
    return station_occupation


def extract_hour_minute(time_str: str) -> Tuple[int, int]:
    """Extract the hour and minute from a string.

    Parameters
    ----------
    time_str : str
        The string containing the time

    Returns
    -------
    Tuple[int, int]
        The hour and minute
    """
    return int(time_str.split(":")[0]), int(time_str.split(":")[1])


def _get_catchment_area(station_information: pd.DataFrame) -> gpd.GeoSeries:
    return (
        CatchmentAreaBuilderColumns(
            longitude="lon",
            latitude="lat",
        )
        .run(station_information)
        .set_crs("EPSG:4326")
    )


def _get_geo_information() -> gpd.GeoDataFrame:
    url = f"{VELIB_API_URL}/data/stations"
    data = requests.get(url, timeout=30).json()
    station_information = pd.DataFrame.from_records(data)
    geo_station_information = gpd.GeoDataFrame(
        station_information,
        geometry=gpd.points_from_xy(
            station_information["lon"], station_information["lat"]
        ),
        crs="EPSG:4326",
    )
    return geo_station_information


def _get_occupation(
    status_datetime: Optional[datetime] = None,
) -> pd.DataFrame:
    url = f"{VELIB_API_URL}/data/status/datetime?"
    if status_datetime:
        url += f"status_datetime={status_datetime}"
    data = requests.get(url, timeout=30).json()
    return pd.DataFrame(
        {"station_id": data["station_id"], data["value"]: data["values"]}
    )


def _get_station_occupation(
    occupation: pd.DataFrame,
    station_information: gpd.GeoDataFrame,
    catchment_area: pd.DataFrame,
) -> gpd.GeoDataFrame:
    return join_occupation_and_station_information(
        occupation,
        gpd.GeoDataFrame(
            pd.DataFrame(station_information),
            geometry=catchment_area,
            crs="EPSG:4326",
        ),
    )


def get_arrondissements_with_occupation(
    arrondissements: gpd.GeoDataFrame, occupation_df_time: pd.DataFrame
) -> gpd.GeoDataFrame:
    """Get the arrondissements with the occupation of the stations.

    Parameters
    ----------
    arrondissements : gpd.GeoDataFrame
        The arrondissements
    occupation_df_time : pd.DataFrame
        The dataframe containing the occupation of the stations


    Returns
    -------
    gpd.GeoDataFrame
        The arrondissements with the occupation of the stations
    """
    arrondissements_with_occupation = (
        arrondissements.sjoin(
            gpd.GeoDataFrame(
                occupation_df_time[["capacity", "num_bikes_available"]],
                geometry=gpd.points_from_xy(
                    occupation_df_time["lon"], occupation_df_time["lat"]
                ),
                crs="EPSG:4326",
            )
        )
        .groupby("geometry", as_index=False)
        .agg(
            {
                "capacity": "sum",
                "num_bikes_available": "sum",
            }
        )
    )
    arrondissements_with_occupation = gpd.GeoDataFrame(
        arrondissements_with_occupation,
        geometry=arrondissements_with_occupation["geometry"],
    )
    arrondissements_with_occupation["occupation"] = 100 * (
        arrondissements_with_occupation["num_bikes_available"]
        / arrondissements_with_occupation["capacity"]
    )
    return arrondissements_with_occupation


colorscale = ["yellow", "green"]
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"
color_prop = "occupation"
vmin = 0
vmax = 100
colorbar = dl.Colorbar(
    colorscale=colorscale,
    width=20,
    height=150,
    min=0,
    max=vmax,
    unit="usage %",
)
style_arrondissements = dict(fillOpacity=0.2)
style_occupation = dict(weight=1, dashArray="10", color="red", fillOpacity=0.3)

app = dash.Dash(
    "__main__",
    external_scripts=[chroma],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.enable_dev_tools(debug=True)
server = app.server

style_handle = assign(
    """
    function(feature, context){
        console.log(context.hideout);
        console.log(feature);
        const {min, max, colorscale, style, colorProp} = context.hideout;
        const csc = chroma.scale(colorscale).domain([min, max]);
        style.color = csc(feature.properties[colorProp]);
        return style;
    }
    """
)
arrondissements_layer = dl.GeoJSON(
    data=None,
    id="arrondissements",
    style=style_handle,
    hideout=dict(
        min=vmin,
        max=vmax,
        colorscale=colorscale,
        style=style_arrondissements,
        colorProp=color_prop,
    ),
    hoverStyle={"weight": 5},
    zoomToBoundsOnClick=True,
)


occupation_layer = dl.GeoJSON(
    data=None,
    id="occupation",
    options=dict(style=style_handle),
    hideout=dict(
        min=vmin,
        max=vmax,
        colorscale=colorscale,
        style=style_occupation,
        colorProp=color_prop,
    ),
    hoverStyle={"fillOpacity": 0.4},
    children=[dl.Popup(html.Div(id="occupation-popup"))],
)

app.layout = html.Div(
    [
        dcc.Store(
            id="station_information", data=_get_geo_information().to_json()
        ),
        dcc.Store(id="catchment_area"),
        dcc.Store(id="arrondissements_data"),
        dcc.Store(id="occupation_data"),
        dcc.Store(id="polygon_arrondissement"),
        dbc.Container(
            [
                dbc.Row([html.H1("Occupation des stations Vélib"), html.Hr()]),
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Input(
                                    id="datetime", type="datetime-local"
                                ),
                            ),
                            dbc.Col(
                                dbc.Button("Reset map", id="reset"),
                                style={"text-align": "right"},
                            ),
                        ]
                    ),
                    md=8,
                    xs=12,
                ),
                html.Div(style={"height": "10px"}),
                dbc.Row(
                    [
                        dbc.Col(
                            dl.Map(
                                [
                                    dl.TileLayer(),
                                    arrondissements_layer,
                                    occupation_layer,
                                    colorbar,
                                ],
                                center=[48.8566, 2.3522],
                                zoom=12,
                                style={"width": "100%", "height": "500px"},
                                id="map",
                            ),
                            md=8,
                            xs=12,
                        ),
                        dbc.Col(
                            dcc.Loading(
                                html.Div(id="graph", style={"height": "50vh"})
                            ),
                            md=4,
                            xs=12,
                        ),
                    ],
                ),
            ],
            fluid=True,
        ),
    ]
)


@app.callback(
    Output("catchment_area", "data"),
    Input("station_information", "data"),
)
def update_catchment_area(station_information_data: str) -> str:
    """Update the catchment area with the station information."""
    station_information = gpd.GeoDataFrame.from_features(
        json.loads(station_information_data)
    )
    catchment_area = (
        CatchmentAreaBuilderGeometry()
        .run(station_information)
        .set_crs("EPSG:4326")
    )
    return catchment_area.to_json()


@app.callback(
    Output("occupation_data", "data"),
    Input("datetime", "value"),
)
def update_occupation_data(datetime_str: Optional[str]) -> str:
    """Update the occupation data with the given time."""
    datetime_value = (
        datetime.fromisoformat(datetime_str) if datetime_str else None
    )
    return _get_occupation(datetime_value).to_json(orient="table")


@app.callback(
    Output("arrondissements", "data"),
    Input("occupation_data", "data"),
    State("station_information", "data"),
)
def update_arrondissements_data(
    occupation_data_json: str, station_information_json: str
) -> str:
    """Update the arrondissements with the occupation of the stations."""
    station_information = gpd.GeoDataFrame.from_features(
        json.loads(station_information_json)
    )
    occupation_data = pd.read_json(occupation_data_json, orient="table")
    occupation_with_capacity = occupation_data.merge(
        station_information[["station_id", "lat", "lon", "capacity"]],
        on="station_id",
    )
    arrondissements_data = communes
    arrondissements_with_occupation = get_arrondissements_with_occupation(
        arrondissements_data, occupation_with_capacity
    )
    return json.loads(arrondissements_with_occupation.to_json())


@app.callback(
    Output("polygon_arrondissement", "data"),
    Input("arrondissements", "clickData"),
)
def update_click_arrondissements(feature: dict) -> Optional[list]:
    """Update the polygon_arrondissement with the clicked arrondissement."""
    if feature is None:
        return None
    return feature["geometry"]["coordinates"][0]


@app.callback(
    Output("occupation", "data"),
    Input("reset", "n_clicks"),
    Input("occupation_data", "data"),
    Input("polygon_arrondissement", "data"),
    State("station_information", "data"),
    State("catchment_area", "data"),
)
def update_occupation_layer(
    reset_n_clicks: int,
    occupation_df_time_json: str,
    polygon_arrondissement: list,
    station_information_data: str,
    catchment_area_data: str,
) -> Optional[list]:
    """Update the occupation layer with the clicked arrondissement."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return None

    prop_id = ctx.triggered[0]["prop_id"]
    if "reset" in prop_id:
        return None
    if catchment_area_data is None:
        return None
    else:
        polygon = Polygon(polygon_arrondissement)
        occupation_df_time = pd.read_json(
            occupation_df_time_json, orient="table"
        )
        station_information = gpd.GeoDataFrame.from_features(
            json.loads(station_information_data)
        )
        station_catchment_area = gpd.GeoDataFrame.from_features(
            json.loads(catchment_area_data)
        ).geometry
        station_occupation_time = _get_station_occupation(
            occupation_df_time, station_information, station_catchment_area
        )
        intersection = station_occupation_time.intersection(polygon)
        station_intersection = station_occupation_time[
            ~intersection.is_empty
        ].copy()
        station_intersection.geometry = intersection[~intersection.is_empty]

        data = json.loads(station_intersection.to_json())
        return data


@app.callback(
    Output("occupation-popup", "children"),
    Input("occupation", "clickData"),
)
def update_popup(feature: dict) -> Optional[list]:
    """Update the popup with the clicked station."""
    if feature is None:
        return None
    _html = [
        html.H4(f"Station: {feature['properties']['name']}"),
        html.P(
            f"Nombre de vélos disponibles : "
            f"{feature['properties']['num_bikes_available']}"
            f"/{feature['properties']['capacity']}"
        ),
        html.P(f"Occupation: {feature['properties']['occupation']:.2f}%"),
    ]
    return _html


@app.callback(
    Output("graph", "children"),
    Input("occupation", "clickData"),
    Input("datetime", "value"),
)
def update_graph(
    feature: dict,
    datetime_str: Optional[str],
) -> Optional[dcc.Graph]:
    """Update the graph with the clicked station."""
    if feature is None:
        return None
    station_id = feature["properties"]["station_id"]
    if datetime_str:
        end_datetime = datetime.fromisoformat(datetime_str)
    else:
        end_datetime = datetime.now()
    start_datetime = end_datetime - timedelta(hours=2)
    occupation_data = requests.get(
        f"{VELIB_API_URL}/data/status/station/{station_id}"
        f"?end_datetime={end_datetime}&start_datetime={start_datetime}",
        timeout=30,
    ).json()
    station_name = feature["properties"]["name"]
    occupation_df_station = pd.DataFrame(
        {
            "datetime": occupation_data["datetime"],
            "num_bikes_available": occupation_data["values"],
        }
    )
    fig = px.line(
        occupation_df_station,
        x="datetime",
        y="num_bikes_available",
        title=f"Station {station_name}",
        labels={
            "datetime": "Date et heure",
            "num_bikes_available": "Nombre de vélos",
        },
    )
    # Set the minimum to 0
    fig.update_yaxes(range=[0, feature["properties"]["capacity"] + 1])
    fig.add_hline(
        feature["properties"]["capacity"],
        line_dash="dash",
        annotation_text="Capacité maximale",  # Add the annotation text
        annotation_position="bottom right",
    )
    graph = dcc.Graph(figure=fig)
    return graph
