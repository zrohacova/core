=============================
Spotify
=============================
The Spotify integration lets you control your Spotify account playback and browse the Spotify media library from Home Assistant.

For the case of DAT265 / DIT588 Software evolution project, the Spotify integration is extended with a feature that shows recommended playlists based on the current weather as well as recommended playlists based on the current date. You get weather-based playlists by pressing the weather icon in the media library and you get date-based playlists by pressing the calendar icon in the media library. To make this work, you have to set up some integrations. It is described step by step below for each feature.

=============================
Playlist Recommendations Based on Weather
=============================

This integration provides dynamic playlist recommendations based on the current weather conditions where the Home Assistant is set up. To make this work, you'll need to set up the AccuWeather integration in your Home Assistant. Here's how to get started:

Prerequisites
-------------

Before you begin, make sure you have:

- A Home Assistant installation.
- An API key from AccuWeather.

Setup AccuWeather Integration in Home Assistant
-----------------------------------------------

Get an API Key
^^^^^^^^^^^^^^

- Visit the `AccuWeather APIs page <https://developer.accuweather.com/apis>`_.
- Sign up for an account, and get an API key by creating an application with the following settings:

    - Products
        - Core Weather
            Core Weather Limited Trial
        - Minute Cast
            None
    - Where will the API be used?
        Other
    - What will you be creating with this API?
        Internal App
    - What programming language is your APP written in?  
        Python
    - Is this for Business to Business or Business to Consumer use?
        Business to Business
    - Is this Worldwide or Country specific use?
        Worldwide

Configure the Integration
^^^^^^^^^^^^^^^^^^^^^^^^^

- In your Home Assistant, go to `Configuration` > `Integrations`.
- Click on the `+ Add Integration` button.
- Search for `AccuWeather` and select it.
- Enter your AccuWeather API key when prompted.
- Follow the on-screen instructions to complete the setup.

=============================
Playlist Recommendations Based on Holiday
=============================

The Spotify integration now contains a feature where users can receive playlist recommendations based on the date. This means that if a holiday is within a timeframe that you can select for yourself, the playlist recommendations are based on this holiday. If there is no holiday in the selected timeframe, the recommendations will be based on the current season, month, and weekday. To fetch the holidays of the desired country/countries, Google Calendar needs to be configured. This is done in the following steps: 

1. Visit https://calendar.google.com/calendar/ and make sure to be logged in 
2. Add regional holiday calendars by pressing the "+" next to “Other calendars” in the lower left corner, and choosing “Browse calendars of interest”
3. Select the regions of interest 
4. Configure Google Calendar in HomeAssistant by following this tutorial: https://www.youtube.com/watch?v=r2WbpxKDOD4 from 1:30 - 6:40 

Done! 
