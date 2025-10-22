import datetime
import math
from typing import Any, List, Mapping, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
from itertools import chain
from enum import Enum
import colorsys
import csv
import json

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

# Path definitions
DATA_DIR_PATH = Path(__file__).parent.resolve() / "data" # data folder
POINTS_FILE_PATH = DATA_DIR_PATH / "points.csv" # collection point information file
POINTS_DELIMITER = ";" # delimiter of CSV file
MAP_DIR_PATH = Path(__file__).parent.resolve() / "maps" # map folder

# Saturation and value of the element colors (from 0 to 1)
TRACK_SV = (0.4, 0.4)
USED_TRACK_SV = (0.3, 0.9)
POINT_SV = (0.8, 0.9)


def load_area_map(mapfile : Path):
    """Read the JSON file containing the data on the roads and convert it into GeoDataFrame
    Parameters:
    mapfile: Path
        Path of the JSON file
    """
    df = pd.read_json(mapfile)
    map = gpd.GeoDataFrame.from_features(df["features"]) # convert json to GeoDataFrame
    return map


@dataclass
class RoutePoint:
    """Class representing a point of the route"""
    index : int # index of the route point in the array of points
    latitude: float
    longitude: float
    service_time: datetime.timedelta # service time of a point


def hsv_to_hex(color: Tuple[float, float, float]):
    """Convert a hsv color (tuple of values between 0 and 1) to a hex color string"""
    return "#" + "".join(f"{int(255 * c):02x}" for c in colorsys.hsv_to_rgb(*color))


class ItineraryElement(Enum):
    TRACK = 0
    USED_TRACK = 1
    POINT = 2


class ItineraryColor:
    ElementsSV: Mapping[ItineraryElement, Tuple[float, float]] = {
        ItineraryElement.TRACK: TRACK_SV,
        ItineraryElement.USED_TRACK: USED_TRACK_SV,
        ItineraryElement.POINT: POINT_SV,
    }

    def __init__(self, N: int, i: int):
        self.hue = i / N

    def get(self, obj: ItineraryElement):
        """Get the color associated to an element"""
        h = self.hue
        s, v = ItineraryColor.ElementsSV[obj]
        return hsv_to_hex((h, s, v))


@dataclass
class ItineraryRepr:
    """Class representing a route"""
    index: int # route index
    n_route: int # number of total routes
    route: List[RoutePoint] # array of points in the route
    distance: int # total distance of the route in meters
    duration: datetime # total duration of the route

    def __post_init__(self):
        self.color = ItineraryColor(self.n_route, self.index)

    def add_points_to_map(self, ax, display_pickup_order: bool, display_info: bool):
        """
        Add the route points of the itinerary to the given plot
        :param ax:
            Axe of the subplot
        :param display_pickup_order: bool
            True if the collection order is displayed on the map
        :param display_info: bool
            True if the distance and the duration of each route is displayed on the map
        """
        # plot collection points
        X = [pt.longitude for pt in self.route[1:-1]]
        Y = [pt.latitude for pt in self.route[1:-1]]
        label_routes = f"route {self.index}"
        if display_info:
            t = datetime.timedelta(seconds=self.duration.seconds)
            label_routes += f", distance {math.ceil(self.distance / 1000.0)} km, "f"duration {t}"
        ax.plot(X, Y, 'o', color=self.color.get(ItineraryElement.POINT), label=label_routes)

        if display_pickup_order:
            for (i, p) in enumerate(self.route[1:-1]):
                ax.text(p.longitude, p.latitude, str(i), color=self.color.get(ItineraryElement.POINT), fontsize=12)

        # plot starting depot
        ax.plot([self.route[0].longitude], [self.route[0].latitude], 's', color='blue')

        # plot ending depot
        ax.plot([self.route[-1].longitude], [self.route[-1].latitude], 's', color='blue')

        ax.legend(loc='upper center', shadow=True, fontsize='x-large')

    def compute_distance_and_duration(self, distances_json, durations_json):
        """
        Compute the total distance and duration of the route
        :param distances_json:
            Distance matrix in meters between the points
        :param durations_json:
            Duration matrix in meters between the points
        """
        # between collection points
        for i in range(0, len(self.route) - 1):
            start_point = self.route[i]
            end_point = self.route[i + 1]
            self.distance += distances_json[start_point.index][end_point.index]
            self.duration += datetime.timedelta(seconds=durations_json[start_point.index][end_point.index])
            if i > 0:
                self.duration += start_point.service_time


def load_json_file(file_path: Path):
    """
    Read JSON file
    :param file_path: Path
        Path of the JSON file
    :return: List
    """
    f = open(file_path)
    data = json.load(f)
    f.close()
    return data


def validate_raw_routes(routes: List[List[Union[List[float], int]]]):
    """Validate the content of the routes file"""
    try:
        assert isinstance(routes, list)
        for route in routes:
            assert isinstance(route, list)
            for e in route:
                if isinstance(e, list):
                    assert len(e) == 2
                    assert isinstance(e[0], (float, int))
                    assert isinstance(e[1], (float, int))
                elif isinstance(e, int):
                    pass
                else:
                    assert False
    except AssertionError:
        raise ValueError("Invalid routes")
    return routes


def load_points(service_times_file_path: Path):
    """
    Read the routes file and the service time file and resturns the route points of each route
    :param service_times_file_path: Path
        Path of the file containing the service time of each point
    :return: List(RoutePoint)
        Array of collection points and depot
    """
    points = []
    with POINTS_FILE_PATH.open(mode="r", encoding="utf-8", newline="\n") as p_f:
        with service_times_file_path.open(mode="r", encoding="utf-8", newline="\n") as st_f:
            points = [
                RoutePoint(
                    index=int(p_row["index"]),
                    latitude=float(p_row["latitude"]),
                    longitude=float(p_row["longitude"]),
                    service_time=datetime.timedelta(seconds=float(st_row["service_time"])),
                )
                for (p_row, st_row) in zip(
                    csv.DictReader(p_f, delimiter=POINTS_DELIMITER), csv.DictReader(st_f)
                )
            ]
    return points


def load_routes(routes_file_path: Path, points: list[RoutePoint]):
    """
    Read the routes
    :param routes_file_path: Path
        Path of the file containing the array of routes
    :param points: List(RoutePoint)
        Array containing the information on the collection points and the depot
    :return: List[List[RoutePoint]]
        Array containing the routes
    """
    with routes_file_path.open(mode="r", encoding="utf-8", newline="\n") as p_f:
        raw_routes = validate_raw_routes(json.load(p_f))

    return [
        [points[raw_e] for raw_e in raw_route]
        for raw_route in raw_routes
    ]


def display_cities(ax):
    color = 'brown'
    ax.text(6.4942451080053445, 44.56531777972838, "Embrun", color=color, fontsize=12)
    ax.text(6.336062218791804, 44.54240100616799, "Pruniere", color=color, fontsize=12)
    ax.text(6.434025914283782, 44.55704709744553, "Puy-Saniere", color=color, fontsize=12)
    ax.text(6.493626204548132, 44.538983054570785, "Baratier", color=color, fontsize=12)
    ax.text(6.3990878130943365, 44.52823961468994, "Savines-le-lac", color=color, fontsize=12)
    ax.text(6.545690825928485, 44.5121207387213, "Les orres", color=color, fontsize=12)
    ax.text(6.361992605818867, 44.504870773322025, "Pontis", color=color, fontsize=12)
    ax.text(6.527542180834633, 44.61321795110612, "Chateau-roux-les-alpes", color=color, fontsize=12)
    ax.text(6.2712469128472605, 44.54596159212191, "Chorges", color=color, fontsize=12)
    ax.text(6.365671485263661, 44.596192852916275, "Reallon", color=color, fontsize=12)



def create_map(
    routes_file_path: Path,
    service_times_file_path: Path,
    _display_pickup_order: bool,
    _display_info: bool
):
    """Returns a map showing the routes.
    routes_file_path is a path to the file containing the positions of the route points.
    service_times_file_path is a path to the file containing the service time of each point.
    """

    map = load_area_map(DATA_DIR_PATH / 'Serre-poncon.json')
    collection_points = load_points(DATA_DIR_PATH / "exemple_points_service_time.csv")
    routes = load_routes(routes_file_path, collection_points)
    distances_json = load_json_file(DATA_DIR_PATH / "distances.json")
    durations_json = load_json_file(DATA_DIR_PATH / "durations.json")

    itineraries_repr = [
        ItineraryRepr(
            index=i,
            n_route=len(routes),
            route=route,
            distance=0,
            duration=datetime.timedelta(seconds=0)
        )
        for (i, route) in enumerate(routes)
    ]

    fig, ax = plt.subplots()
    map.plot(ax = ax, linewidth = 1, edgecolor = 'grey')
    display_cities(ax)

    for itin in itineraries_repr:
        itin.compute_distance_and_duration(distances_json, durations_json)
        itin.add_points_to_map(ax=ax, display_pickup_order=_display_pickup_order, display_info=_display_info)



    f = plt.gcf()
    dpi = f.get_dpi()
    h, w = f.get_size_inches()
    f.set_size_inches(h * 3, w * 3)
    f.savefig(MAP_DIR_PATH / 'map_routes.png')


def main():
    create_map(
        # Path to a JSON file containing the routes, see README.md or `exemple_route.json` to understand the format.
        routes_file_path=DATA_DIR_PATH / "exemple_routes.json",
        # Path to a CSV file containing the service times, see README.md or the `exemple_points_service_time.csv`
        # to understnad the format.
        service_times_file_path=DATA_DIR_PATH / "exemple_points_service_time.csv",
        # indicate if the order of picking is displayed on the map or not
        _display_pickup_order=False,
        # indicate if the distance and duration of the routes are displayed on the map or not
        _display_info=True
    )

main()
