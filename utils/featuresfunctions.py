# functions used to build features for the linear regression
# The functions are ment to be applied on pandas dataframes

import numpy as np
import pytz
from traffic.data.weather import metar

# Aircraft body type identification
ac_body_dict = {
    "Widebody": ["B763", "A333", "B789", "A332", "A333", "B772"],
    "Narrowbody": ["A320", "BCS3", "A20N", "A319", "BCS1", "A21N", "B738", "A321", "A20N", "A21N"],
    "Regional Jet": ["E190", "CRJ9", "E195", "DH8D"],
    "Business jets": ["PC12", "C56X", "F2TH", "PC24", "C68A", "E55P"],
}

def body_type(typecode):
    for key, value in ac_body_dict.items():
        if typecode in value:
            return key
    return None

# Season identification
# DataFrame must have a day an mond columns
def get_season(date):
    # Extract month and day
    month = date.month
    day = date.day
    
    # Define the seasons based on month and day
    if (month == 12 and day >= 21) or (month in [1, 2]) or (month == 3 and day < 20):
        return 'Winter'
    elif (month == 3 and day >= 20) or (month in [4, 5]) or (month == 6 and day < 21):
        return 'Spring'
    elif (month == 6 and day >= 21) or (month in [7, 8]) or (month == 9 and day < 23):
        return 'Summer'
    elif (month == 9 and day >= 23) or (month in [10, 11]) or (month == 12 and day < 21):
        return 'Fall'
    
# Peak hours identification for each airport
def is_rush_hour_EDDM(date):
    
    # Extract hour: everything in UTC
    hour = date.hour
    minute = date.minute
    time_in_minutes = hour * 60 + minute
    
    if (5 * 60 <= time_in_minutes <= 6 * 60) or \
       (7 * 60 <= time_in_minutes <= 9 * 60) or \
       (11 * 60 <= time_in_minutes <= 14 * 60) or \
       (16 * 60 <= time_in_minutes <= 20 * 60):
        return True
    else:
        return False
    
def is_rush_hour_LIRF(date):
    rome_tz = pytz.timezone('Europe/Rome')
    
    # Extract hour: Rome AIP in Local Time
    hour = date.tz_convert(rome_tz).hour
    minute = date.tz_convert(rome_tz).minute
    time_in_minutes = hour * 60 + minute
    
    if (6 * 60 + 30 <= time_in_minutes <= 9 * 60) or \
       (11 * 60 <= time_in_minutes <= 14 * 60) or \
       (16 * 60 + 30 <= time_in_minutes <= 18 * 60) or \
       (19 * 60 <= time_in_minutes <= 21 * 60):
        return True
    else:
        return False
    
def is_rush_hour_LSGG(date):
    
    # Extract hour everything in UTC
    hour = date.hour
    minute = date.minute
    time_in_minutes = hour * 60 + minute
    
    if (7 * 60 <= time_in_minutes <= 10 * 60) or \
       (11 * 60 <= time_in_minutes <= 13 * 60) or \
       (14 * 60 <= time_in_minutes <= 17 * 60) or \
       (20 * 60 <= time_in_minutes <= 21 * 60):
        return True
    else:
        return False
    

#Meteo data downloading
def get_meteo_data(row, airport):
    start = row.start
    stop = row.stop
    
    meteo = metar.METAR(airport).get(
        start = start,
        stop = stop,
    )
    
    def safe_mean(values):
        valid_values = [val.value() for val in values if val is not None]
        return np.mean(valid_values) if valid_values else None  # Return None if no valid values
    
    wind_dir = safe_mean(meteo.wind_dir.values)
    wind_speed = safe_mean(meteo.wind_speed.values)
    vis = safe_mean(meteo.vis.values) / 1000 # In km
    temp = safe_mean(meteo.temp.values)
    press = safe_mean(meteo.press.values) - 1013 # relative to standard pressure
    
    return wind_dir, wind_speed, vis, temp, press
