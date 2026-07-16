<p align="center">
	<img src="https://github.com/deltaecho07/hass-meteoswiss-rain-radar/blob/2903bedef066b9e1f0c1d4b676f891c9c393cc87/custom_components/meteoswiss_rain_radar/brand/logo.png" width="300">
</p>

# MeteoSwiss Rain Radar Integration for Home Assistant

This integration allows you to get near-real time precipitation data into Home Assistant.

## Current Funcionality

The integration currently supports the following features:

- Loading the latest available precipitation image from the Meteosuisse Open Government Data Service.

- Based on your home location and configuration, it will calculate whether there is precipitation within the given radius. There is also a distance sensor to the nearest precipitation.

## Installation

### HACS

1. Install HACS: [HACS User Documentation](https://hacs.xyz/docs/use/)
2. Go to the HACS page in your Home Assistant instance
3. Click on the three dots in the top right-hand corner and select 'Custom Repositories...'
4. Enter 'https://github.com/deltaecho07/hass-meteoswiss-rain-radar' into Repository field and select the type 'Integration'
5. Click 'Add'
6. Search for 'MeteoSwiss Rain Radar' and download the integration
7. Restart Home Assistant

### Configuration

Once you have successfully added it through HACS, you can continue with the following steps

1. Go to Settings > Integrations
2. Click 'Add Integration'
3. Search for 'MeteoSwiss Rain Radar' and select it
4. If required, modify the detection radius and threshold
5. Press 'OK' to add the integration

## FAQ

### Where can I find more information about MeteoSwiss's open government data products?

All freely available data can be found [here](https://opendatadocs.meteoswiss.ch).
