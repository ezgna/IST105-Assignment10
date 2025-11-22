import os
import random
from datetime import datetime

import requests
from django.shortcuts import render
from pymongo import MongoClient

from .forms import ContinentForm

# REST Countries API
REST_COUNTRIES_URL = "https://restcountries.com/v3.1/region/{region}"

# OpenWeatherMap API
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["geo_weather"]
history_collection = mongo_db["search_history"]


def home(request):
    """
    Home page view.

    - Display a form to select a continent.
    - When the form is submitted (POST):
        - Fetch the list of countries from the REST Countries API.
        - Randomly select up to 5 countries.
        - For each country, fetch current weather data for its capital city
          using the OpenWeatherMap API.
        - Save the search result to MongoDB.
        - Render the results page showing the selected countries and weather.
    """
    form = ContinentForm(request.POST or None)
    context = {"form": form}

    if request.method == "POST" and form.is_valid():
        continent_name = form.cleaned_data["continent"]
        # REST Countries API expects region in lowercase, e.g. "europe", "asia"
        region_param = continent_name.lower()

        # 1. Fetch country list from REST Countries API
        try:
            resp = requests.get(
                REST_COUNTRIES_URL.format(region=region_param),
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException:
            context["error"] = "Failed to fetch countries data."
            return render(request, "continent_form.html", context)

        countries_data = resp.json()
        if not countries_data:
            context["error"] = "No countries found for this continent."
            return render(request, "continent_form.html", context)

        # 2. Randomly select up to 5 countries
        sample = random.sample(countries_data, min(5, len(countries_data)))
        results = []

        for c in sample:
            name = c.get("name", {}).get("common", "Unknown")
            capital_list = c.get("capital") or []
            capital = capital_list[0] if capital_list else "N/A"
            population = c.get("population", "N/A")
            latlng = c.get("capitalInfo", {}).get("latlng") or c.get("latlng")

            weather_info = None

            # If the country has a capital and the API key is set, fetch weather
            if capital != "N/A" and OPENWEATHER_API_KEY:
                try:
                    w_resp = requests.get(
                        OPENWEATHER_URL,
                        params={
                            "q": capital,
                            "appid": OPENWEATHER_API_KEY,
                            "units": "metric",
                        },
                        timeout=10,
                    )
                    if w_resp.status_code == 200:
                        w_json = w_resp.json()
                        weather_info = {
                            "temp": w_json.get("main", {}).get("temp"),
                            "description": (
                                w_json.get("weather", [{}])[0].get("description")
                            ),
                        }
                except requests.RequestException:
                    # If weather fetch fails, do not crash the app; just skip weather data
                    pass

            results.append(
                {
                    "country": name,
                    "capital": capital,
                    "population": population,
                    "latlng": latlng,
                    "weather": weather_info,
                }
            )

        # 3. Save search history to MongoDB
        #    (If MongoDB is not available, ignore the error and keep the app running)
        try:
            history_collection.insert_one(
                {
                    "continent": continent_name,
                    "searched_at": datetime.utcnow(),
                    "results": results,
                }
            )
        except Exception:
            pass

        return render(
            request,
            "search_results.html",
            {
                "form": form,
                "continent": continent_name,
                "results": results,
            },
        )

    # GET request or invalid form: just show the form page
    return render(request, "continent_form.html", context)


def history_view(request):
    """
    Display search history.

    - Reads the latest 20 search records from MongoDB, ordered by search time
      (most recent first).
    - If MongoDB is not available, shows an empty history instead of crashing.
    """
    searches = []
    try:
        searches = list(
            history_collection.find().sort("searched_at", -1).limit(20)
        )
    except Exception:
        # If MongoDB is not reachable, just show an empty history
        pass

    return render(request, "history.html", {"searches": searches})