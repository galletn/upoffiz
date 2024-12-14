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

add the following entry to the config file:

```yaml
    - platform: upoffiz_parking
      name: Upoffiz Parking
      username: [username]
      password: [password]
```

From now on please use the vacuum entity, I will no longer update the sensor integration as more is possible with the vacuum entity
