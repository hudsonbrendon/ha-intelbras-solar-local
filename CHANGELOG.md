# Changelog

All notable changes to this project are documented here.

## [0.3.0]

### Added
- Entities are split across three devices, matching the Intelbras cloud
  integration: **Inverter**, **Datalogger** (WiNet-S) and **Plant**. The
  inverter keeps its identifier, so existing entities stay where they are. The
  datalogger connectivity sensors move to the Datalogger device.
- Inverter: efficiency (AC/DC %), ARM and DSP firmware versions (the ARM
  version also shows on the device page), and grid protection levels. Grid
  protection carries the 29 over/under-voltage and frequency thresholds and
  trip times as attributes.
- Datalogger: Wi-Fi signal (dBm) and network, firmware, hardware version,
  cloud server, Ethernet link (disabled by default), and a last record
  timestamp that stays available overnight.
- Plant (calculated):
  - savings today, this month, this year and in total (BRL);
  - CO2 avoided, trees saved and coal saved;
  - specific yield today (kWh/kWp) and utilization (%);
  - peak power today, restored after a restart on the same day;
  - installed capacity, energy price and plant status (normal / fault / offline).
- Options: energy price (BRL/kWh), installed capacity (kWp; defaults to the
  inverter rating) and CO2 factor. The default CO2 factor is the one the
  Intelbras app uses, so the numbers match.
- The datalogger identity, the Wi-Fi signal (a ~3 s station scan) and the grid
  parameters refresh every 10 minutes, best-effort.

### Changed
- Requires `python-intelbras-solar-local` 0.2.0.

## [0.2.0]

### Added
- Zeroconf discovery. The WiNet-S datalogger announces
  `WiNet-WebServer._http._tcp.local.` with TXT `board=WiNet-S`, so Home
  Assistant now offers to add the inverter without typing an IP. The flow reads
  the inverter serial over Modbus to use as the unique id. When the datalogger
  gets a new IP from DHCP, the existing entry is updated to it automatically.

## [0.1.2]

### Fixed
- A poll that was already in flight when a control was written could bring the
  old value back about 0.1 s later. This was seen on the real power limit:
  100 → 90 → 100. For 3 s after a write, fields written by the controls now
  override whatever a poll reads.
- A single failed poll no longer marks the inverter offline and flips every
  entity to unavailable. The last reading is kept until 3 polls fail in a row.

### Changed
- Requires `python-intelbras-solar-local` 0.1.1. It raises
  `IntelbrasSolarProtocolError` on malformed Modbus frames instead of a bare
  `IndexError`, and starts transaction ids at random.

## [0.1.1]

### Fixed
- Controls (inverter on/off, power limitation, power limit, clock sync) showed the old
  value after a successful write. The WiNet-S takes about a second to reflect a
  holding-register write, so the immediate refresh read the previous value and the
  debouncer then held further refreshes. Entities now update optimistically on a
  successful write, and the next scheduled poll confirms the value. Verified on the
  real IONS-5K M5.

## [0.1.0]

### Added
- First release. Reads Intelbras (Sungrow WiNet-S) inverters locally through
  [`python-intelbras-solar-local`](https://github.com/hudsonbrendon/python-intelbras-solar-local)
  0.1.0: Modbus TCP for the inverter and the datalogger WebSocket for connectivity and faults.
- Sensors:
  - AC, DC, apparent and reactive power, and power factor;
  - energy today, this month, this year and in total;
  - voltage, current and power for MPPT1 and MPPT2;
  - grid voltage, current and frequency;
  - internal temperature and work state (enum);
  - diagnostics: bus voltage, insulation resistance, fault code, active alarms,
    running time, nominal power and inverter clock.
- Binary sensors: online, producing, fault (with the fault list), and datalogger Wi-Fi and cloud.
- Controls, disabled by default: inverter on/off, power limitation on/off, power limit (%) and a sync clock button.
- Config flow keyed on the inverter serial (the host is updated when re-added) and an options flow for the scan interval.
- Night handling: an unreachable inverter becomes `online=False` instead of a failed update.
- Diagnostics with the serial number redacted. English and Português (Brasil) translations.
