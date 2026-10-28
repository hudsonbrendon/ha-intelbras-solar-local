<p align="center">
  <img src="assets/intelbras.png" alt="Intelbras" width="360">
</p>

# Intelbras Solar Local for Home Assistant

[![Tests](https://github.com/hudsonbrendon/ha-intelbras-solar-local/actions/workflows/tests.yml/badge.svg)](https://github.com/hudsonbrendon/ha-intelbras-solar-local/actions/workflows/tests.yml)
[![Hassfest](https://github.com/hudsonbrendon/ha-intelbras-solar-local/actions/workflows/hassfest.yml/badge.svg)](https://github.com/hudsonbrendon/ha-intelbras-solar-local/actions/workflows/hassfest.yml)
[![Validate](https://github.com/hudsonbrendon/ha-intelbras-solar-local/actions/workflows/validate.yml/badge.svg)](https://github.com/hudsonbrendon/ha-intelbras-solar-local/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Release](https://img.shields.io/github/v/release/hudsonbrendon/ha-intelbras-solar-local)](https://github.com/hudsonbrendon/ha-intelbras-solar-local/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This integration monitors and controls an **Intelbras solar inverter** straight from your local network. It reads
power, energy, per-string (MPPT) data, grid values and inverter health, refreshing every 15 seconds. It can also start
or stop the inverter and set its power limit. There is no cloud and no account.

> Intelbras IONS inverters are rebranded **Sungrow** string inverters, and their Wi-Fi stick is a Sungrow **WiNet-S**.
> The integration reads the inverter over **Modbus TCP** (port `502`) and the datalogger over the **WebSocket** of its
> web UI (port `8082`). Neither interface needs a login. This project is not affiliated with Intelbras or Sungrow.

## Features

- **Power**: AC, DC, apparent and reactive power, plus power factor.
- **Energy**: today, this month, this year and lifetime, with 0.1 kWh resolution. The lifetime sensor is ready for the
  Energy dashboard.
- **Strings**: voltage, current and power for each MPPT input.
- **Grid**: voltage, current and frequency (0.01 Hz).
- **Health**:
  - work state (translated);
  - internal temperature, bus voltage and insulation resistance;
  - fault code;
  - a fault binary sensor that carries the active fault list from the datalogger;
  - the number of active alarms.
- **Three devices**, split the same way as the Intelbras cloud integration: **Inverter**, **Datalogger** and **Plant**.
- **Inverter extras**: efficiency (AC/DC), ARM and DSP firmware, and the grid-protection settings. The settings cover
  the over/under-voltage and frequency thresholds per level and their trip times.
- **Datalogger**: Wi-Fi signal (dBm) and network, Wi-Fi, cloud and Ethernet links, firmware and hardware versions,
  cloud server, and the time of the last record.
- **Plant (calculated)**:
  - savings in R$ today, this month, this year and in total;
  - CO₂ avoided, trees saved and coal saved;
  - specific yield (kWh/kWp) and utilization (%);
  - peak power of the day;
  - installed capacity, energy price and plant status.
- **Controls** (disabled by default):
  - turn the inverter on or off;
  - turn power limitation on or off, and set the power limit (%);
  - sync the inverter clock with Home Assistant.
- **Auto-discovery**: zeroconf picks up the WiNet-S on your network, and the entry follows the datalogger when its IP
  changes.
- **Night-aware**: the inverter powers down after sunset. The *Online* binary sensor then turns off and the other
  entities become unavailable. The log stays quiet overnight, and readings resume at sunrise.
- **Diagnostics**: the integration provides a diagnostics download, with the serial number redacted.
- **Localized**: available in English and Português (Brasil).

## Comparison with the cloud integration

[Solar Plus Intelbras](https://github.com/hudsonbrendon/HA-solar-plus-intelbras) reads the Intelbras cloud. That
integration's distinctive data is weather. This integration reads the hardware directly, takes the fault history from
the datalogger and calculates the plant figures locally. The two can run side by side.

| | Solar Plus Intelbras (cloud) | Intelbras Solar Local |
|---|---|---|
| Update rate | ~5 min | 15 s (configurable, minimum 5 s) |
| Works offline / without internet | ❌ | ✅ |
| AC power, daily and total energy | ✅ | ✅ |
| Monthly and yearly energy | ✅ | ✅ |
| DC, apparent and reactive power, power factor | ❌ | ✅ |
| Per-MPPT voltage, current and power | ❌ | ✅ |
| Grid voltage, current and frequency | ❌ | ✅ |
| Bus voltage, insulation resistance, fault code | ❌ | ✅ |
| Start/stop, power limit, clock sync | ❌ | ✅ |
| Savings (R$), CO₂, trees, coal, capacity, energy price | ✅ | ✅ (calculated locally) |
| Datalogger firmware, Wi-Fi signal | ✅ | ✅ |
| Inverter firmware (ARM/DSP), efficiency, grid-protection settings | ❌ | ✅ |
| Specific yield, utilization, peak power of the day | ❌ | ✅ |
| Fault / alert history | ✅ | ✅ (from the datalogger) |
| Weather | ✅ | ❌ |

## Architecture

All device communication is handled by the standalone Python library
[**python-intelbras-solar-local**](https://github.com/hudsonbrendon/python-intelbras-solar-local)
([PyPI](https://pypi.org/project/python-intelbras-solar-local/),
[docs and register map](https://hudsonbrendon.github.io/python-intelbras-solar-local/protocol/)). That library ships a
tiny asyncio Modbus TCP client, so it never clashes with the `pymodbus` version pinned by Home Assistant. The
integration itself only handles the Home Assistant side: the config flow, the coordinator and the entities.

## Requirements

- An Intelbras IONS inverter with the Wi-Fi datalogger connected to your network. Tested on the IONS-5K M5 with
  datalogger firmware `WIFI-SV300.001.03.P002`.
- The datalogger IP. Look for an Espressif device in your router's client list. A reserved IP is recommended.
- Home Assistant **2024.12** or newer.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hudsonbrendon&repository=ha-intelbras-solar-local&category=integration)

1. In Home Assistant, open **HACS → ⋮ (top right) → Custom repositories**.
2. Add `https://github.com/hudsonbrendon/ha-intelbras-solar-local` and choose the **Integration** category, or use the
   button above.
3. Search for **Intelbras Solar Local** in HACS, install it, and **restart Home Assistant**.

### Manual

1. Copy `custom_components/intelbras_solar_local/` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Setup

### Automatic discovery

The WiNet-S datalogger announces itself over mDNS (`WiNet-WebServer._http._tcp`, `board=WiNet-S`). After you install
the integration, Home Assistant shows **Intelbras inverter found** under **Settings → Devices & Services**. Click
**Configure**, choose a name, and you're done. If the datalogger later gets a new IP, the entry follows it
automatically.

### Manual

1. Go to **Settings → Devices & Services → Add Integration → Intelbras Solar Local**.
2. Enter the datalogger **IP address**. The defaults are Modbus port `502` and unit id `1`.

Add the integration during the day. At night the inverter is off and the connection test fails.

### Options

Open **Configure** on the integration to set:

| Option | Default | Used by |
|---|---|---|
| Scan interval | 15 s | Every reading |
| Energy price (R$/kWh) | 0, which leaves the savings sensors unknown | Savings sensors |
| Installed capacity (kWp) | 0, which falls back to the inverter rating | Specific yield, utilization |
| CO₂ avoided per kWh | 0.3406 kg, the factor the Intelbras app uses | CO₂, trees |

## Entities

Entity IDs follow the name you give the device (default `intelbras_solar_local`). They are generated in your Home
Assistant language: in Portuguese, for example, `sensor.<name>_potencia_ac`. The tables below use the English IDs.

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.<name>_ac_power` / `_dc_power` | Active AC output / total DC input (W) |
| `sensor.<name>_apparent_power` / `_reactive_power` / `_power_factor` | VA / var / PF |
| `sensor.<name>_energy_today` / `_energy_this_month` / `_energy_this_year` / `_total_energy` | kWh, `total_increasing` |
| `sensor.<name>_mppt1_power` / `_voltage` / `_current` (same for MPPT2) | Per-string DC values |
| `sensor.<name>_grid_voltage` / `_grid_current` / `_grid_frequency` | Grid side |
| `sensor.<name>_internal_temperature` | °C |
| `sensor.<name>_work_state` | Running, standby, derating, fault… |
| `sensor.<name>_bus_voltage`, `_insulation_resistance`, `_fault_code`, `_active_alarms` | Diagnostics |
| `sensor.<name>_running_time_today` / `_total_running_time` | Diagnostics |
| `sensor.<name>_nominal_power` | Diagnostics (kW) |
| `sensor.<name>_inverter_clock` | Diagnostics, disabled by default |
| `sensor.<name>_inverter_efficiency` | AC output / DC input (%) |
| `sensor.<name>_arm_firmware` / `_dsp_firmware` | Inverter firmware versions (diagnostics); slave DSP and CPLD as attributes |
| `sensor.<name>_recorded_faults` | Faults in the datalogger's history; attributes `by_fault` and the 10 most recent events |
| `sensor.<name>_last_fault` | Time of the latest fault; attributes `fault`, `code`, `level` |
| `sensor.<name>_grid_protection_levels` | Number of protection levels. Attributes hold every threshold (V/Hz) and trip time (s) |

### Datalogger sensors

| Entity | Description |
|--------|-------------|
| `sensor.<name>_datalogger_wi_fi_signal` / `_wi_fi_network` | RSSI (dBm) and SSID. Refreshed every 10 min with a ~3 s station scan |
| `sensor.<name>_datalogger_firmware` / `_hardware_version` | Datalogger versions |
| `sensor.<name>_datalogger_cloud_server` | Server the datalogger reports to (`app.isolarcloud.com`) |
| `sensor.<name>_datalogger_last_record` | Time of the last successful reading. Stays available overnight |

### Plant sensors (calculated)

| Entity | Description |
|--------|-------------|
| `sensor.<name>_plant_savings_today` / `_this_month` / `_this_year` / `_total_savings` | Energy × energy price (BRL) |
| `sensor.<name>_plant_co2_avoided` / `_trees_saved` / `_coal_saved` | Lifetime energy × CO₂ factor; trees = t CO₂; coal = 0.4 kg/kWh |
| `sensor.<name>_plant_specific_yield_today` | Energy today / installed capacity (kWh/kWp) |
| `sensor.<name>_plant_utilization` | AC power / installed capacity (%) |
| `sensor.<name>_plant_peak_power_today` | Highest AC power today, kept across restarts |
| `sensor.<name>_plant_installed_capacity` / `_energy_price` | From the options |
| `sensor.<name>_plant_status` | Normal / fault / offline |

### Binary sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.<name>_online` | On while the inverter answers; off at night |
| `binary_sensor.<name>_producing` | On while feeding the grid |
| `binary_sensor.<name>_fault` | Problem; attributes `fault_code` and `faults` (datalogger list) |
| `binary_sensor.<name>_datalogger_wi_fi` / `_datalogger_cloud` / `_datalogger_ethernet` | Datalogger links (Ethernet is disabled by default) |

### Controls (disabled by default)

Each of these writes to the inverter. Enable the ones you want under the device page.

| Entity | Description |
|--------|-------------|
| `switch.<name>_inverter_on` | Start/stop generation. **Off stops the inverter** until it is turned back on |
| `switch.<name>_power_limitation` | Enables the active power limit |
| `number.<name>_power_limit` | Power limit, 0–100 % of nominal power |
| `button.<name>_sync_inverter_clock` | Sets the inverter clock to Home Assistant's local time |

## Diagnostics

**Settings → Devices & Services → Intelbras Solar Local → ⋮ → Download diagnostics** downloads the config entry and the
latest inverter snapshot, with the serial number redacted.

## Notes & limitations

- **LAN only, no auth**: Modbus TCP and the datalogger WebSocket accept any client on the network by design. Keep the
  datalogger on a trusted network.
- **One Modbus client at a time**: the WiNet-S times out when several Modbus clients poll it together. Keep this
  integration as the only Modbus TCP client; the Intelbras cloud and app are unaffected. Single failed polls are
  tolerated: the inverter is reported offline only after 3 failures in a row.
- **Yearly energy** comes from a register whose meaning is inferred. It tracks the cloud's yearly value closely but not
  exactly.
- **Two MPPTs**: only two are exposed, as on the IONS-5K M5. Open an issue if your model has three.

## Credits

Integration and protocol reverse-engineering by [@hudsonbrendon](https://github.com/hudsonbrendon). The register map
follows Sungrow's public SG-RS Modbus documentation.

## License

[MIT](LICENSE)
