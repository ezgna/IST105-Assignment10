# Geo Weather Adventure (IST105 Assignment 10)

Django app that lets users pick a continent, fetch 5 random countries (REST Countries API), get weather for each capital (OpenWeatherMap API), and save the search history in MongoDB.

## Tech

- Python 3.9+
- Django 4.2
- requests
- pymongo
- MongoDB
- python-dotenv

## Env vars (`assignment10/.env`)

OPENWEATHERMAP_API_KEY=your_openweather_api_key
MONGO_URI=mongodb://<mongo-host-or-ip>:27017

## Set up

git clone https://github.com/ezgna/IST105-Assignment10.git
cd IST105-Assignment10

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cd assignment10
python manage.py migrate
python manage.py runserver