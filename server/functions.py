import os
import datetime
import json
import random
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load NinjasAPI key
NINJAS_API_KEY = os.getenv("NINJAS_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

random.seed(2024)

# Function to get the current location of the user
def get_current_location():
    try:
        response = requests.get("https://ipinfo.io")
        if response.status_code == 200:
            data = response.json()
            return {
                "city": data.get('city'),
                "region": data.get('region'),
                "country": data.get('country')
            }
        else:
            print(f"Error getting location: Status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting location: {e}")
        return None

# Function to get the weather based on the current location
def get_weather():
    location = get_current_location()
    location = location['city']
    print(f"Getting weather for {location}")
    api_key = WEATHER_API_KEY
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(data)
        return {
            "temperature": data['current']['temp_c'],
            "feels_like": data['current']['feelslike_c'],
            "humidity": data['current']['humidity'],
            "city": data['location']['name']
        }
    else:
        return "Unable to retrieve weather data."

# Weather forecast

# def get_weather(location):
#     api_key = NINJAS_API_KEY
#     city = location['city']
#     print(f"Getting weather for {city}")
#     try:
#         weather_url = "https://api.api-ninjas.com/v1/weather?city={}".format(city)
#         headers = {
#             "X-Api-Key": api_key
#         }
#         response = requests.get(weather_url, headers=headers)
#         if response.status_code == 200:
#             weather_data = response.json()
#             print(weather_data)
#             return {
#                 "temperature": weather_data['temp'],
#                 "feels_like": weather_data['feels_like'],
#                 "humidity": weather_data['humidity'],
#                 "city": city
#             }
#         else:
#             print(f"Error getting weather: Status code {response.status_code}")
#             return None
#     except Exception as e:
#         print(f"Error getting weather: {e}")
#         return None

######  TESTING AREA  ######

location_data = get_current_location()
if location_data:
    print(f"Location: {location_data['city']}, {location_data['region']}, {location_data['country']}")
    weather_data = get_weather()
    if weather_data:
        print(weather_data)
        
else:
    print("Failed to get location data")