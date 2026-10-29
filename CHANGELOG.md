# Changelog

All notable changes to this project are documented here.

## [0.5.0]

### Added
- Every inverter parameter from the datalogger's web UI is now an entity: 20
  system settings and 29 grid-protection settings. Each one becomes a number,
  select or switch, with the official English and Portuguese names. They are
  written through the datalogger, with no login.
  - Enabled by default: connecting time, reconnecting time, PID recovery,
    rated active power limit and apparent power limit.
  - Disabled by default, because wrong values can take the inverter out of its
    grid code:
    - over-frequency derating (switch, F1–F3, P1–P3, curve, gradients, delays);
    - grid voltage rise suppression;
    - PV connection mode;
    - protection level, and every over/under-voltage and frequency threshold
      and trip time.
  - Protection settings carry an `applies` attribute that is false for levels
    above the active protection level.
- `intelbras_solar_local.set_parameter` action: writes any parameter by key or
  register, including the total yield adjustment. That one has no entity
  because it rewrites the lifetime counter.
- Power factor setting (number) and reactive power mode (select), from holding
  registers 5018 and 5035. Both are disabled by default.
- Datalogger *Reboot* button.
- Datalogger grid code, hotspot SSID and NTP server sensors. The last two are
  disabled by default.
- *IEC 104 server* binary sensor. The datalogger exposes an unauthenticated
  IEC 60870-5-104 server on port 2404, enabled here out of the box.
- Inverter *Rated reactive power* sensor.
- Fault attributes include the official fault description in Home Assistant's
  language.

### Fixed
- The Wi-Fi signal sensor sometimes dropped 20–30 dB for one reading, because
  it read the signal mid-scan. Fixed in `python-intelbras-solar-local` 0.4.0.
- After a restart, *Recorded faults* showed 0, and the datalogger extras could
  stay empty for 10 minutes when the first read failed. Unread data is now
  unknown, and a failed refresh is retried after 1 minute.

### Changed
- Requires `python-intelbras-solar-local` 0.4.0.

## [0.4.3]

### Fixed
- *Recorded faults* and *Last fault* could stay at 0 / unknown. The library
  fetched the whole history in one request, and the datalogger sometimes
  answered that with an empty list. `python-intelbras-solar-local` 0.3.2 pages
  through it instead.

## [0.4.2]

### Fixed
- The 10-minute refresh of the datalogger extras runs in the background. It
  used to block the regular poll, which took 54 s on one restart while the
  datalogger timed out. The Wi-Fi scan now runs last, because it briefly takes
  the datalogger's radio away.
- Removed the deprecated `via_device` link from the inverter to the
  datalogger. Recent Home Assistant versions warned about it. Existing
  installations keep the link already stored in the device registry.

## [0.4.1]

### Fixed
- The fault history and firmware versions could stay empty after a restart.
  The datalogger sometimes refused the WebSocket session that followed the
  previous one; `python-intelbras-solar-local` 0.3.1 now retries it.

## [0.4.0]

### Added
- Inverter: *Recorded faults* counts the faults in the datalogger's history.
  Its attributes break the count down by fault and list the 10 most recent
  events. *Last fault* holds the time of the latest one, with the fault name,
  code and level as attributes. The history goes back to December 2024 on the
  test unit and covers what the cloud lists as alerts.
- Diagnostics include the inverter info and the latest 50 fault events.

### Changed
- The ARM and DSP firmware sensors, and the inverter's device page, show the
  real firmware versions from the web UI (for example
  `SUNSTONE-S_01011.01.39`). The Modbus string `ARM_SUNSTONE-S_V11_V01_A` is
  the firmware family, not a version, and moves to the `family` attribute.
  The DSP sensor also carries the slave DSP and CPLD versions.
- Requires `python-intelbras-solar-local` 0.3.0.

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
