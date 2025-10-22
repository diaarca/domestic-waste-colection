import datetime
from math import hypot
from typing import Any, List, Mapping, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
from itertools import chain
from enum import Enum
import colorsys
import csv
import json

from folium.folium import Map
from folium.map import Popup
from folium.vector_layers import CircleMarker, PolyLine
from folium.plugins.timestamped_geo_json import TimestampedGeoJson
from folium.plugins.fullscreen import Fullscreen
import requests
import polyline

# je suis la
# tiles to use for the map background, HOT tiles are prettier but the standart ones work better
# MAP_TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
MAP_TILES = "http://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"

# Size of the elements (in pixels)
TRACK_WIDTH = 2
TRACK_BG_WIDTH_OFFSET = 2
POINT_RADIUS = 8

# Saturation and value of the element colors (from 0 to 1)
TRACK_SV = (0.4, 0.4)
USED_TRACK_SV = (0.3, 0.9)
POINT_SV = (0.8, 0.9)

# Path definitions
DATA_DIR_PATH = Path(__file__).parent.resolve() / "data"
POINTS_FILE_PATH = DATA_DIR_PATH / "points.csv"
POINTS_DELIMITER = ";"

# OSRM Server to use to compute itineraries, demo OSRM server should be enough
OSRM_SERVER = "http://router.project-osrm.org"

# See OSRM documentation http://project-osrm.org/docs/v5.10.0/api
OSRM_ROUTE_REQUEST_TEMPLATE = (
    OSRM_SERVER + "/route/v1/driving/polyline({})?geometries=geojson&overview=full"
)


def hsv_to_hex(color: Tuple[float, float, float]):
    """Convert a hsv color (tuple of values between 0 and 1) to a hex color string"""
    return "#" + "".join(f"{int(255 * c):02x}" for c in colorsys.hsv_to_rgb(*color))


def approx_dist_to(p1: Tuple[float, float], p2: Tuple[float, float]):
    """Approximation for the distance in meters between two lat/lon, works for small distances in
    france"""
    return hypot((p1[0] - p2[0]) * 111194.9, (p1[1] - p2[1]) * 75905.5)


def timedelta_to_iso(tdelta: datetime.timedelta):
    """Convert a stlib timedelta to the iso period format"""
    tot_seconds = tdelta.total_seconds()
    days = int(tot_seconds // (3600 * 24))
    time = "".join(
        [
            f"{value}{symbol}"
            for (value, symbol) in [
                (int(tot_seconds // 3600 % 24), "H"),
                (int(tot_seconds // 60 % 60), "M"),
                (int(tot_seconds % 60), "S"),
            ]
            if value
        ]
    )
    return "P" + (f"{days}D" if days else "") + (f"T{time}" if time else "T0S")


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


@dataclass
class RoutePoint:
    latitude: float
    longitude: float
    service_time: datetime.timedelta


def compute_itinerary_and_duration(
    route: List[RoutePoint],
) -> Tuple[List[Tuple[float, float]], datetime.timedelta]:
    """Compute the list of waypoints that a route should follow, and its duration"""
    encoded_route: str = polyline.encode(((p.longitude, p.latitude) for p in route), geojson=True)  # type: ignore
    request = OSRM_ROUTE_REQUEST_TEMPLATE.format(encoded_route)
    result = requests.get(request)
    if result.status_code != 200:
        raise Exception(f"HTTP error, code {result.status_code}: {result.content}")
    json_result = json.loads(result.text)
    route_result = json_result["routes"][0]

    return [
        (lat, lon) for (lon, lat) in route_result["geometry"]["coordinates"]
    ], datetime.timedelta(seconds=route_result["duration"])


def load_routes(routes_file_path: Path, service_times_file_path: Path):
    """Read the routes file and the service time file and resturns the route points of each route"""
    with POINTS_FILE_PATH.open(mode="r", encoding="utf-8", newline="\n") as p_f:
        with service_times_file_path.open(mode="r", encoding="utf-8", newline="\n") as st_f:
            points = [
                RoutePoint(
                    latitude=float(p_row["latitude"]),
                    longitude=float(p_row["longitude"]),
                    service_time=datetime.timedelta(seconds=float(st_row["service_time"])),
                )
                for (p_row, st_row) in zip(
                    csv.DictReader(p_f, delimiter=POINTS_DELIMITER), csv.DictReader(st_f)
                )
            ]

    with routes_file_path.open(mode="r", encoding="utf-8", newline="\n") as p_f:
        raw_routes = validate_raw_routes(json.load(p_f))

    return [
        [
            points[raw_e]
            if isinstance(raw_e, int)
            else RoutePoint(
                latitude=raw_e[0], longitude=raw_e[1], service_time=datetime.timedelta()
            )
            for raw_e in raw_route
        ]
        for raw_route in raw_routes
    ]


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
    index: int
    n_route: int
    route: List[RoutePoint]

    def __post_init__(self):
        self.color = ItineraryColor(self.n_route, self.index)
        self.itinerary, self.duration = compute_itinerary_and_duration(self.route)
        self.start = self.itinerary[0]
        self.end = self.itinerary[-1]

    def add_track(self, map: Map):
        """Adds the track layer of the itinerary to the map given"""
        PolyLine(
            locations=self.itinerary,
            color="#000000",
            weight=TRACK_WIDTH + TRACK_BG_WIDTH_OFFSET,
            opacity=1,
        ).add_to(map)

        PolyLine(
            locations=self.itinerary,
            color=self.color.get(ItineraryElement.TRACK),
            weight=TRACK_WIDTH,
            opacity=1,
        ).add_to(map)

    def add_points(self, map: Map):
        """Addes the route points of the itinerary to the map given"""
        for (i, p) in enumerate(self.route):
            if i == 0:
                is_depot = True
                popup_content = f"Start of route {self.index}"
            elif i == len(self.route) - 1:
                is_depot = True
                popup_content = f"End of route {self.index}"
            else:
                is_depot = False
                popup_content = f"Point {i-1} of route {self.index}"
            CircleMarker(
                location=(p.latitude, p.longitude),
                radius=POINT_RADIUS,
                popup=Popup(popup_content),
                max_width=500,
                fill=True,
                color="#000000" if is_depot else self.color.get(ItineraryElement.POINT),
            ).add_to(map)

    def _get_itinerary_times(self):
        """Private method, return the list of timestamps of all the waypoints of the itinerary"""
        timedelta = self.duration / (len(self.itinerary) - 1)
        itinerary_index_service_time_map = {
            min(
                range(len(self.itinerary)),
                key=lambda i: approx_dist_to(self.itinerary[i], (p.latitude, p.longitude)),
            ): p.service_time
            for p in self.route
        }
        times: list[datetime.datetime] = []
        for i in range(len(self.itinerary)):
            times.append(
                (
                    times[-1] + timedelta
                    if len(times) > 0
                    else datetime.datetime.combine(datetime.datetime.now(), datetime.time(hour=8))
                )
                + itinerary_index_service_time_map.get(i, datetime.timedelta())
            )
        return [t.isoformat() for t in times]

    def get_itinerary_feature(self):
        """Return a geojson representing the trackstyle and it timing"""
        coordinates = [(lon, lat) for (lat, lon) in self.itinerary]
        geoJson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "times": self._get_itinerary_times(),
                        "style": {
                            "color": self.color.get(ItineraryElement.USED_TRACK),
                            "weight": TRACK_WIDTH,
                            "opacity": 1,
                        },
                        "icon": "circle",
                        "iconstyle": {
                            "weight": 3,
                            "radius": 5,
                            "fillOpacity": 1,
                        },
                    },
                    "geometry": {"type": "LineString", "coordinates": coordinates},
                }
            ],
        }
        return geoJson


def add_geojson(
    map: Map,
    features: List[Mapping[str, Any]],
    loop: bool,
    total_duration: datetime.timedelta,
    max_feature_duration: datetime.timedelta,
):
    """Adds a list of geojson features and adds the animation widget"""
    geoJson = {"type": "FeatureCollection", "features": features}
    max_feature_duration = max(
        datetime.datetime.fromisoformat(f["features"][0]["properties"]["times"][-1])
        - datetime.datetime.fromisoformat(f["features"][0]["properties"]["times"][0])
        for f in features
    )

    transition_time = datetime.timedelta(seconds=1 / 40)
    TimestampedGeoJson(
        data=geoJson,
        loop=loop,
        transition_time=1000 * transition_time.total_seconds(),
        period=timedelta_to_iso((transition_time / total_duration) * max_feature_duration),
        auto_play=False,
    ).add_to(map)


def create_map(
    routes_file_path: Path,
    service_times_file_path: Path,
    duration: datetime.timedelta = datetime.timedelta(seconds=20),
    loop: bool = True,
    show: Optional[List[int]] = None,
):
    """Returns an animated map showing the evolution of the routes.
    routes_file_path is a path to the file containing the positions of the route points.
    service_times_file_path is a path to the file containing the service time of each point.
    duration is the time it should take for longest route to finish its animation. if bool is set to
    True (default) the animate loops infinitly. show is the list of the indices of the route to
    display, if it is None or a an empty list, it shows all the itineraries.
    """

    routes = load_routes(routes_file_path, service_times_file_path)

    itineraries_repr = [
        ItineraryRepr(
            index=i,
            n_route=len(routes),
            route=route,
        )
        for (i, route) in enumerate(routes)
        if show is None or len(show) == 0 or i in show
    ]

    map = Map(tiles=MAP_TILES, attr=" ")
    Fullscreen(position="topright", title="Expand me").add_to(map)

    map.fit_bounds(bounds=list(chain.from_iterable(ir.itinerary for ir in itineraries_repr)))
    for ir in itineraries_repr:
        ir.add_track(map=map)
    add_geojson(
        map,
        features=[ir.get_itinerary_feature() for ir in itineraries_repr],
        loop=loop,
        total_duration=duration,
        max_feature_duration=max(ir.duration for ir in itineraries_repr),
    )
    for ir in itineraries_repr:
        ir.add_points(map=map)
    return map


map = create_map(
    routes_file_path=DATA_DIR_PATH / "exemple_routes.json",
    service_times_file_path=DATA_DIR_PATH / "exemple_points_service_time.csv",
    loop=False,
    duration=datetime.timedelta(seconds=15),
    show=[1, 2],
)
