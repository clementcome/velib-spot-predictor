"""Dash application for the front-end."""

import json
from datetime import time
from typing import Tuple

import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import geopandas as gpd
import pandas as pd
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash_extensions.javascript import assign
from shapely.geometry import Polygon

from velib_spot_predictor.data.geo import CatchmentAreaBuilderColumns
from velib_spot_predictor.data.load_data import (
    load_prepared,
    load_station_information,
)
from velib_spot_predictor.environment import Config


def filter_time(
    df_with_datetime: pd.DataFrame, hour: int, minute: int
) -> pd.DataFrame:
    """Filter the dataframe to keep only the rows with the given time.

    Parameters
    ----------
    df_with_datetime : pd.DataFrame
        The dataframe containing the datetime column
    hour : int
        The hour to keep
    minute : int
        The minute to keep

    Returns
    -------
    pd.DataFrame
        The filtered dataframe
    """
    return df_with_datetime[
        df_with_datetime["datetime"].dt.floor("min").dt.time
        == time(hour, minute)
    ]


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
        occupation_df[
            ["station_id", "num_bikes_available", "num_docks_available"]
        ],
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


initial_time = time(7, 40)

config = Config()
arrondissements = gpd.read_file(
    f"{config.DATA_FOLDER}/external/arrondissements.geojson"
)
occupation_df = load_prepared(
    f"{config.DATA_FOLDER}/interim/data_20230907.pkl"
)
station_information = load_station_information(
    f"{config.DATA_FOLDER}/raw/station_information.json"
)
station_catchment_area = (
    CatchmentAreaBuilderColumns(
        longitude="lon",
        latitude="lat",
    )
    .run(station_information)
    .set_crs("EPSG:4326")
)
occupation_df_time_original = filter_time(
    occupation_df, initial_time.hour, initial_time.minute
)
station_occupation = join_occupation_and_station_information(
    occupation_df_time_original,
    gpd.GeoDataFrame(
        station_information, geometry=station_catchment_area, crs="EPSG:4326"
    ),
)
station_information = gpd.GeoDataFrame(
    station_information,
    geometry=gpd.points_from_xy(
        station_information["lon"], station_information["lat"]
    ),
    crs="EPSG:4326",
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
                occupation_df_time[
                    ["capacity", "num_bikes_available", "num_docks_available"]
                ],
                geometry=gpd.points_from_xy(
                    occupation_df_time["lon"], occupation_df_time["lat"]
                ),
                crs="EPSG:4326",
            )
        )
        .groupby("geometry", as_index=False)
        .agg(
            {
                "c_ar": "first",
                "l_ar": "first",
                "capacity": "sum",
                "num_bikes_available": "sum",
                "num_docks_available": "sum",
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
style_arrondissements = dict(fillOpacity=0.3)
style_occupation = dict(weight=1, dashArray="10", color="red", fillOpacity=0.3)
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

app = dash.Dash(
    __name__,
    external_scripts=[chroma],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
server = app.server

arrondissements_layer = dl.GeoJSON(
    data=None,
    id="arrondissements",
    options=dict(style=style_handle),
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
    hoverStyle={"fillOpacity": 0.5},
    children=[dl.Popup(html.Div(id="occupation-popup"))],
)

app.layout = html.Div(
    [
        dcc.Store(id="arrondissements_data"),
        dcc.Store(id="occupation_data"),
        dcc.Store(id="polygon_arrondissement"),
        html.H1("Occupation des stations Vélib"),
        dbc.Input(value="07:40", id="time", type="text", placeholder="HH:MM"),
        dbc.Button("Changer l'heure", id="change-time"),
        html.Div(
            [dbc.Button("Reset map", id="reset")],
            style={"text-align": "right"},
        ),
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
        html.Div(id="graph"),
    ]
)


@app.callback(
    Output("arrondissements", "data"),
    Input("arrondissements_data", "data"),
)
def update_arrondissements_data(arrondissements_data):
    """Update the arrondissements layer."""
    return arrondissements_data


@app.callback(
    Output("arrondissements_data", "data"),
    Input("occupation_data", "data"),
)
def inject_arrondissements_data(occupation_df_time):
    """Update the arrondissements data with the occupation of the stations."""
    occupation_df_time = pd.DataFrame(occupation_df_time)
    arrondissements_with_occupation = get_arrondissements_with_occupation(
        arrondissements, occupation_df_time
    )
    arrondissements_with_occupation[
        "tooltip"
    ] = arrondissements_with_occupation["l_ar"]
    return json.loads(arrondissements_with_occupation.to_json())


@app.callback(
    Output("occupation_data", "data"),
    Input("change-time", "n_clicks"),
    State("time", "value"),
)
def update_occupation_data(n_clicks, time_str):
    """Update the occupation data with the given time."""
    if time_str is None:
        return occupation_df_time_original.to_dict(orient="records")
    hour, minute = extract_hour_minute(time_str)
    occupation_df_time = filter_time(occupation_df, hour, minute)
    return occupation_df_time.to_dict(orient="records")


@app.callback(
    Output("polygon_arrondissement", "data"),
    Input("arrondissements", "clickData"),
)
def update_click_arrondissements(feature):
    """Update the polygon_arrondissement with the clicked arrondissement."""
    if feature is None:
        return None
    return feature["geometry"]["coordinates"][0]


@app.callback(
    Output("occupation", "data"),
    Input("reset", "n_clicks"),
    Input("occupation_data", "data"),
    Input("polygon_arrondissement", "data"),
)
def update_occupation_layer(
    reset_n_clicks, occupation_df_time, polygon_arrondissement
):
    """Update the occupation layer with the clicked arrondissement."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return None

    prop_id = ctx.triggered[0]["prop_id"]
    if "reset" in prop_id:
        return None
    else:
        polygon = Polygon(polygon_arrondissement)
        occupation_df_time = pd.DataFrame(occupation_df_time)
        station_occupation_time = join_occupation_and_station_information(
            occupation_df_time,
            gpd.GeoDataFrame(
                station_information,
                geometry=station_catchment_area,
                crs="EPSG:4326",
            ),
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
def update_popup(feature):
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
)
def update_graph(feature):
    """Update the graph with the clicked station."""
    if feature is None:
        return None
    station_name = feature["properties"]["name"]
    occupation_df_station = occupation_df[
        occupation_df["name"] == station_name
    ]
    fig = px.line(
        occupation_df_station,
        x="datetime",
        y="num_bikes_available",
        title=f"Station {station_name}",
    )
    fig.add_hline(
        occupation_df_station["capacity"].iloc[0],
        line_dash="dash",
        annotation_text="Capacité maximale",  # Add the annotation text
        annotation_position="bottom right",
    )
    graph = dcc.Graph(figure=fig)
    return graph


if __name__ == "__main__":
    app.run(debug=True)
