import requests
import logging

def kelvin_to_celsius(kel):
    return kel - 273.15

class WeatherAPI:
    def __init__(self, api_key):
        logging.basicConfig(filename="logs.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
        self.api_key = api_key

    def get_coords(self, city) -> tuple[float, float]:
        """
        Обращение к API OpenWeatherMap для получения координат города city. 
        ВАЖНО! API иногда не отвечает в течение какого-то времени, но аналога пока не найдено.

        :param city: Требуемый город на каком-либо языке
        :return: Кортеж, содержащий широту и долготу города city
        :raise requests.exceptions.Timeout: Если API не отвечает в течение 15 секунд
        """
        logging.debug(f"GET 'http://api.openweathermap.org/geo/1.0/direct?q={city.capitalize()}&&appid={self.api_key}'")
        r = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={city.capitalize()}&&appid={self.api_key}", timeout=15)
        json = r.json()
        return json[0]["lat"], json[0]["lon"]

    def get_weather(self, city) -> str:
        """
        Обращение к API Open-Meteo для получения погоды по координатам. Обращается к API OpenWeatherMap для получения координат требуемого города

        :param city: Требуемый город на каком-либо языке
        :return: Строка, содержащая требуемую информацию о погоде
        :raise requests.exceptions.Timeout: Если API не отвечает в течение 15 секунд
        """
        lat, lon = self.get_coords(city)
        logging.debug(f"GET 'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,cloud_cover,wind_speed_10m,wind_direction_10m&hourly=temperature_2m&wind_speed_unit=ms&forecast_days=1'")
        r = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,cloud_cover,wind_speed_10m,wind_direction_10m&hourly=temperature_2m&wind_speed_unit=ms&forecast_days=1", timeout=15)
        json = r.json()
        return f"""Погода в {city}:
Температура: {round(json["current"]["temperature_2m"], 1)} °C"""
    
class WeatherAPI_deprecated:
    def __init__(self, api_key):
        logging.basicConfig(filename="logs.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
        self.api_key = api_key

    def get_coords(self, city):
        logging.debug(f"GET 'http://api.openweathermap.org/geo/1.0/direct?q={city.capitalize()}&&appid={self.api_key}'")
        r = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={city.capitalize()}&&appid={self.api_key}", timeout=15)
        json = r.json()
        return json[0]["lat"], json[0]["lon"]

    def get_weather(self, city):
        lat, lon = self.get_coords(city)
        logging.debug(f"GET 'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}'")
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}", timeout=15)
        json = r.json()
        return f"""Погода в {city}:
Температура: {round(kelvin_to_celsius(json["main"]["temp"]), 1)} °C"""