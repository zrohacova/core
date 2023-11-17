Playlist Recommendations Based on Weather
---------------------

This integration provides dynamic playlist recommendations based on the current weather conditions. To make this work, you'll need to set up the AccuWeather integration in your Home Assistant. Here's how to get started:

Prerequisites
---------------------

Before you begin, make sure you have:

A Home Assistant installation.

An API key from AccuWeather.

Setup AccuWeather Integration in Home Assistant
---------------------

Get an API Key:
Visit the AccuWeather APIs page. Sign up for an account and follow the instructions to generate your API key.

Configure the Integration:
In your Home Assistant, go to Configuration > Integrations.
Click on the + Add Integration button.
Search for AccuWeather and select it.
Enter your AccuWeather API key when prompted.
Follow the on-screen instructions to complete the setup.

Set the Weather Entity:
Once the AccuWeather integration is added, it will create a weather entity in Home Assistant.
Ensure that the entity ID is set to weather_home. If not, rename it in Home Assistant by clicking on the entity in the Entities list and changing the Entity ID.

Verify the Weather Entity
---------------------

To verify that the weather_home entity is correctly set up:

Go to Developer Tools > States in your Home Assistant.
In the Filter entities field, type weather.home.
You should see the weather.home entity with the current weather conditions.
