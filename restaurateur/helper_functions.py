import functools
import logging
from time import sleep

import requests
from django.conf import settings
from django.utils import timezone
from geopy import distance

from coordinatesapp.models import Location


def retry_on_failure(max_retries=5, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for retry_attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logging.warning(f"Failed to execute {func.__name__}. Retrying in {4 ** retry_attempt}s. Error: {e}")
                    sleep(4 ** retry_attempt)
            logging.error(f"Failed to execute {func.__name__} after {max_retries} attempts.")
        return wrapper
    return decorator


@retry_on_failure(max_retries=3, exceptions=(requests.ConnectionError))
def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_location(address):

    location, created = Location.objects.get_or_create(
        address=address,
        defaults={
            "last_fetched": timezone.now()
        }
    )
    if created or None in (location.lon, location.lat):
        coords = fetch_coordinates(settings.YANDEX_API_KEY, location.address)
        if coords:
            location.lon, location.lat = coords
            location.save()
    return location


def calculate_distance(location_1, location_2):
    coordinates_1 = location_1.lat, location_1.lon
    coordinates_2 = location_2.lat, location_2.lon
    if None not in coordinates_1 and None not in coordinates_2:
        return str(round(distance.distance(coordinates_1, coordinates_2).km, 2)) + " км"
    else:
        return "Ошибка определения координат"
