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

Make sure the Home assistant plugin "Workday" is installed on your HA installation if you only want to use the peak_interval refresh during working days.

add the following entry to the config file:

- peak_interval: between 7:30 and 9:30
- off_peak_interval: working hours
- night_interval: night

```yaml
sensor:
    - platform: upoffiz_parking
      name: Upoffiz Parking
      username: [username]
      password: [password]
      peak_interval: 300
      off_peak_interval: 600
      night_interval: 3600
```

