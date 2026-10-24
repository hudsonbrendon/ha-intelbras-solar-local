# Changelog

All notable changes to this project are documented here.

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
