import os
import json
import boto3
import requests
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
import pandas as pd

# Load environment variables
load_dotenv()


class WeatherDashboard:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        self.s3_client = boto3.client('s3')

    def create_bucket_if_not_exists(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Bucket {self.bucket_name} exists")
        except:
            print(f"Creating bucket {self.bucket_name}")
        try:
            # Simpler creation for us-east-1
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            print(f"Successfully created bucket {self.bucket_name}")
        except Exception as e:
            print(f"Error creating bucket: {e}")

    def fetch_weather(self, city):
        """Fetch weather data from OpenWeather API"""
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "imperial"
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None

    def save_to_s3(self, weather_data, city):
        """Save weather data to S3 bucket"""
        if not weather_data:
            return False

        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        file_name = f"weather-data/{city}-{timestamp}.json"

        try:
            weather_data['timestamp'] = timestamp
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=json.dumps(weather_data),
                ContentType='application/json'
            )
            print(f"Successfully saved data for {city} to S3")
            return True
        except Exception as e:
            print(f"Error saving to S3: {e}")
            return False


def main():

    dashboard = WeatherDashboard()

    dashboard.create_bucket_if_not_exists()

    cities = ["Philadelphia", "Seattle", "New York"]

    st.title("Weathercast")
    st.header("Know the weather right here, right now!")
    st.markdown("By Nuhu Kanga Ali")
    st.markdown("\n")
    st.divider()
    st.markdown("This weather app is built on the basis of the DevOps Challenge brought by the Cozy Cloud Crew.")
    st.markdown("Below, you'll see visuals for the distribution of the weather temperatures at different states.")
    st.markdown("The weather temperature is measured in Fahrenheit at a range from 0 to 100 degrees.")
    st.divider()

    weather_summary = []

    for city in cities:
        st.subheader(f"Weather in {city}")
        weather_data = dashboard.fetch_weather(city)
        if weather_data:
            temp = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            humidity = weather_data['main']['humidity']
            description = weather_data['weather'][0]['description']

            # Display data in Streamlit
            cols1, cols2, cols3 = st.columns(3)
            cols1.metric(label="Temperature (°F)", value=f"{temp:.1f}")
            cols2.metric(label="Feels Like (°F)", value=f"{feels_like:.1f}")
            cols3.metric(label="Humidity (%)", value=f"{humidity}%")
            st.text(f"Conditions: {description.capitalize()}")

            weather_summary.append({
                "City": city,
                "Temperature": temp,
                "Feels Like": feels_like,
                "Humidity": humidity,
                "Conditions": description.capitalize()
            })


        else:
            st.error(f"Failed to fetch weather data for {city}")
        st.divider()

    if weather_summary:
        st.subheader("Summary of Weather Data")
        df = pd.DataFrame(weather_summary)
        st.dataframe(df)




if __name__ == "__main__":
    main()