=============================
Spotify
=============================
The Spotify integration lets you control your Spotify account playback and browse the Spotify media library from Home Assistant.

For the case of DAT265 / DIT588 Software evolution project, the Spotify integration is extended with a feature that shows recommended playlists based on the current weather as well as recommended playlists based on the current date. You get weather-based playlists by pressing the weather icon in the media library and you get date-based playlists by pressing the calendar icon in the media library. To make this work, you have to set up some integrations. It is described step by step below for each feature.

=============================
Playlist Recommendations Based on Weather
=============================

This integration provides dynamic playlist recommendations based on the current weather conditions where the Home Assistant is set up. To make this work, you'll need to set up the AccuWeather integration in your Home Assistant. Here's how to get started:

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

The Spotify integration now contains a feature where users can receive playlist recommendations based on the date. This means that if a holiday is within a timeframe that you can select for yourself, the playlist recommendations are based on this holiday. If there is no holiday in the selected timeframe, the recommendations will be based on the current season, month, and weekday.

In the current version, there remains a limitation regarding the season of the user’s country location. The season recommendation works for the countries having the four seasons winter, summer, autumn and spring. However, it remains as future work to expand the solution for finding accurate seasons for countries located at the poles, or in the tropical/subtropical regions.

In order to fetch the holidays of the desired country/countries, Google Calendar needs to be configured. This is done in the following steps:

1. Visit https://calendar.google.com/calendar/ and make sure to be logged in
2. Add regional holiday calendars by pressing the "+" next to “Other calendars” in the lower left corner, and choosing “Browse calendars of interest”
3. Select the regions of interest
4. Configure Google Calendar in HomeAssistant by following this tutorial: https://www.youtube.com/watch?v=r2WbpxKDOD4 from 1:30 - 6:40

=============================
Setting Up Core with Customized Icons
=============================

To integrate the new icons introduced in the Spotify integration, it's crucial to set up the Core changes. Follow the instructions below:

1. Clone the core repository with the customized icons:
   ```bash
   git clone -b change_gui_icons https://github.com/zrohacova/core.git
2. Navigate to the core directory:
   ```bash
   cd core
3. Follow the instructions for setting up the Home Assistant development environment outlined in the official documentation: https://developers.home-assistant.io/docs/development_environment

=============================
Setting Up Frontend with Customized Icons
=============================

To enjoy the new icons introduced in the Spotify integration, it's essential to set up the Frontend changes. Follow the instructions below:

1. Clone the frontend repository with the customized icons:
   ```bash
   git clone -b gui_icon_change https://github.com/zrohacova/frontend.git
2. Navigate to the frontend directory:
   ```bash
   cd frontend
3. Follow the instructions for setting up the frontend development environment outlined in the official documentation: https://developers.home-assistant.io/docs/frontend/development/
4. Once the development environment is set up, you can build and test the changes in your Home Assistant instance.
5. Make sure to restart Home Assistant to see the updated frontend.

Done!
