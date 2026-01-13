# upoffiz

![image](https://github.com/user-attachments/assets/4b678fa2-676d-4b8e-af3f-76adf4393b07)


Home Assistant Upoffiz integration

## How to

#### Requirements

- account for upoffiz

#### Installations via HACS [![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

- In HACS, look for "upoffiz" and install and restart
- If integration was not found, please add custom repository `galletn/upoffiz` as integration

#### Setup

Make sure the Home assistant plugin "Workday" is installed on your HA installation if you want to refresh more frequently during the peak_interval hours based on the weekday and take public holidays into account.
This limits the amount of calls to the Upoffiz API.

Make sure to set property "use_workday: True" to use the Workday integration.
You can configure your own working days and holidays to take into account in the workday plugin. see https://www.home-assistant.io/integrations/workday/

if use_workday is not defined, it fails back to weekdays mon-fri.

Add the following entries to the config file:

- username: your upoffiz login used for the official mobile app
- password: your upoffix password
- peak_interval: refresh time in seconds between 7:30 and 9:30
- off_peak_interval: refresh time in seconds during working hours
- night_interval: refresh time in seconds during the night
- use_workday: accepts True, False or unset. Define if you want to use the workday integration from your home assistant installation.

```yaml
sensor:
    - platform: upoffiz_parking
      name: Upoffiz Parking
      username: [username]
      password: [password]
      peak_interval: 300
      off_peak_interval: 600
      night_interval: 3600
      use_workday: True
```

