from typing import Union, List
from traffic.core import Flight
from traffic.data import airports, navaids
from traffic.core.mixins import PointMixin

def has_landing_at(flight: Flight, ap: str) -> Union[Flight, None]:
    """
    Provided with a flight, returns the flight if it has a landing at the
    specified airport only if the flight does not contain a go-around, otherwise
    returns nothing. The function also adds the landing runway as an additional
    column to the flight data. Can be used with traffic pipe
    """
    if landing := flight.aligned_on_ils(ap).next():
        flight.data["rwy"] = landing.data.ILS.iloc[0]
        return flight
        

def aligned_navpoint(
    flight: Flight,
    navpoint: str,
    angle_precision: int = 1,
    time_precision: str = "2T",
    min_time: str = "30s",
    min_distance: int = 10,
):
    """
    Provided with a flight, returns the flight if it is aligned on the specified
    navpoint within the specified angle precision, time precision, minimum time and
    minimum distance, otherwise returns nothing. Can be used with traffic pipe.
    """
    if aligned := flight.aligned_on_navpoint(
        navpoint, angle_precision, time_precision, min_time, min_distance
    ).next():
        return flight
    
def  crop_after_th(
    flight: Flight, airport: str, altitude=3000
) -> Flight:
    """
    Crops the part of the flight after it passes the threshold of the specified runway
    of the specified airport. Designed to be used with traffic pipe.

    Parameters
    ----------
    flight : Flight
        Flight to be cropped
    airport : str
        ICAO code of the airport
    altitude : int, optional
        Altitude below which data is considered. For cases where the runway is overflown
        before the actual approach such as e.g. STAR BELUS3N at LSGG, by default 3000

    Returns
    -------
    Flight
        Cropped flight
    """
    try:
        runway = flight.data.rwy.iloc[0]
        # Turn the threshold position into a PointMixin object
        th = PointMixin()
        th.latitude = (
            airports[airport]
            .runways.data.query(f"name == '{runway}'")
            .latitude.iloc[0]
        )
        th.longitude = (
            airports[airport]
            .runways.data.query(f"name == '{runway}'")
            .longitude.iloc[0]
        )
        # Create a subset containing only the data points below the specified altitude, then
        # calculate the distance to the threshold for each of them
        flight_below_alt = flight.query(f"altitude < {altitude}")
        flight_below_alt = flight_below_alt.distance(th)
        # Get the timestamp of the closest point to the threshold
        min_ts = flight_below_alt.data.loc[
            flight_below_alt.data.distance.idxmin()
        ].timestamp
        # Return the flight with the part after the timestamp cropped
        return flight.before(min_ts)
    except:
        return None

def crop_before_wp(flight: Flight, wp) -> Flight:
    """
    Crops the part of the flight before it passes the specified waypoint. Designed to be
    used with traffic pipe.

    Parameters
    ----------
    flight : Flight
        Flight to be cropped
    wp : str
        Waypoint to crop the trajectory before

    Returns
    -------
    Flight
        Cropped flight
    """
    try:
        # For each data point of the flight, calculate the distance to the waypoint
        flight = flight.distance(wp)
        # Get the timestamp of the closest point to the waypoint
        min_ts = flight.data.loc[flight.data.distance.idxmin()].timestamp
        # Drop the distance column
        flight.data = flight.data.drop(columns=["distance"])
        # Return the flight with the part before the timestamp cropped
        return flight.after(min_ts)
    except:
        return None
    
def remove_ga(flight: Flight, airport: str) -> Union[Flight, None]:
    """
    Returns the flight if it does not contain a go-around at the specified
    airport, otherwise returns nothing. Designed to be used with traffic pipe.

    Parameters
    ----------
    flight : Flight
        Flight to be processed

    Returns
    -------
    Flight
        Flight without the go-around part
    """

    if flight.has(f'go_around("{airport}")') == False:
        return flight
    