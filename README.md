# ZTM - Warsaw public transport sensor for Home Assistant
## Home Assistant (hass.io) custom component for Warsaw public transport.

This is continuation of work done by [@kabturek](https://github.com/kabturek). He was close to pull it as a official HA integration. You can find his pull request [here](https://github.com/home-assistant/home-assistant/pull/13561).

#### Description
The `ztm` sensor will give you information about departure times for bus/trams using [Warsaw Open Data](https://api.um.warszawa.pl/) API.

To access the data, you need an `api_key` that is provided after creating an account at [Otwarte dane po warszawsku](https://api.um.warszawa.pl/) -> Logowanie -> Rejestracja konta.

To activate the sensor you need the bus/tram `number`, `stop_id` and the `stop_number`. 
You can obtain `stop_id` and `stop_number` by searching for a stop at [ZTM](https://www.wtp.waw.pl/rozklady-jazdy/) website. 
In the url `wtp_st` param is the `stop_id` and `wtp_pt` param is `stop_number` (example stop: [Centrum 01](https://www.wtp.waw.pl/rozklady-jazdy/?wtp_dt=2020-01-30&wtp_md=5&wtp_ln=501&wtp_st=7013&wtp_pt=01&wtp_dr=B&wtp_vr=0&wtp_lm=1)).

<p class='note'>
You have to quote `stop_number` as it starts with the number 0.
</p>

#### Installation
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

The easiest way to install it is through [HACS (Home Assistant Community Store)](https://hacs.xyz/), add this repository in the HACS settings and download the integration.

If you want to do that manually, download the files from custom_components/ztm into your $homeassistant_config_dir/custom_components/ztm

Once downloaded and configured as per below information, you'll need to restart HomeAssistant to have the custom component and the sensors of ztm platform taken into consideration.

Then add the data to your `configuration.yaml` file as shown in the example:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: ztm
    api_key: YOUR_API_KEY
    lines:
      - number: 24
        stop_id: 5068
        stop_number: "03"
      - number: 23
        stop_id: 5068
        stop_number: "03"
```
#### Configuration:
```
api_key:
  description: API key
  required: true
  type: int
entries:
  description: Number of entries saved in sensor.attributes.departures
  required: false
  type: int
  default: 3
name:
  description: The first part of the sensor name
  required: false
  type: string
  default: ztm
return_type:
  description: Whether to return minutes to departure or actual time of departure
  required: false
  type: string (TIME_OF_DEPARTURE, TIME_TO_DEPART)
  default: TIME_TO_DEPART
lines:
  description: List of lines to monitor
  required: true
  type: map
  keys:
    number:
      description: Bus/tram line number
      required: true
      type: string (ex. N37 for night line, don't use "")
    stop_id:
      description: Id of the stop
      required: true
      type: int
    stop_number:
      description: Number of the stop (starts with 0 so use quotes)
      required: true
      type: string
```

I also advice to modify friendly_name for the sensor (in customizations), otherwise you will have 'not so nice' sensor name displayed:

![ztm_card](ztm.jpg)

For pretty custom card, displaying next departures of configured line, please take a look on custom card dedicated for that sensor: https://github.com/peetereczek/ztm_stop_card

The public data is coming from [Miasto Stołeczne Warszawa](http://api.um.warszawa.pl ). 
