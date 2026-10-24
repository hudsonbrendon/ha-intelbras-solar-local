# Changelog

All notable changes to this project are documented here.

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
