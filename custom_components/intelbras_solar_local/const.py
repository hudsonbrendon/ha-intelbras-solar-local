"""Constants for the Intelbras Solar Local integration."""

from __future__ import annotations

# Re-export protocol constants from the library so platform modules can keep
# their `from .const import ...` imports in one place.
from intelbras_solar_local import (  # noqa: F401
    DEFAULT_PORT,
    DEFAULT_UNIT,
    WORK_STATES,
)

DOMAIN = "intelbras_solar_local"

DEFAULT_NAME = "Intelbras Solar Local"
MANUFACTURER = "Intelbras (Sungrow)"

CONF_UNIT = "unit"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 15
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 600

# Plant options (calculated sensors)
CONF_ENERGY_PRICE = "energy_price"  # BRL per kWh; 0 disables the savings sensors
CONF_INSTALLED_CAPACITY = "installed_capacity"  # kWp; 0 uses the inverter rating
CONF_CO2_FACTOR = "co2_factor"  # kg CO2 avoided per kWh
DEFAULT_ENERGY_PRICE = 0.0
DEFAULT_INSTALLED_CAPACITY = 0.0
# Same factors as the Intelbras Solar Plus app, so both report the same numbers.
DEFAULT_CO2_FACTOR = 0.3406
COAL_KG_PER_KWH = 0.4
# The app's "trees saved" equals tonnes of CO2 avoided.
TREES_PER_KG_CO2 = 0.001

# Device kinds an entity can belong to
DEVICE_INVERTER = "inverter"
DEVICE_DATALOGGER = "datalogger"
DEVICE_PLANT = "plant"

# Inverter parameters (python-intelbras-solar-local keys) exposed as entities:
# key -> (translation key, enabled by default). Platform follows the parameter:
# enable/disable options -> switch, other options -> select, else number. Grid
# protection and grid-support settings ship disabled: wrong values can take the
# inverter out of its grid code. Total yield adjustment is only reachable
# through the set_parameter action, since it rewrites the lifetime counter.
PARAMETERS: dict[str, tuple[str, bool]] = {
    "standby_time": ("connecting_time", True),
    "fault_recovery_time": ("reconnecting_time", True),
    "power_grid_voltage": ("grid_voltage_rise_suppression", False),
    "pid_night_repair": ("pid_recovery", True),
    "frequency_drop_status_param": ("overfrequency_derating", False),
    "config_key_1001939": ("overfrequency_derating_f1", False),
    "config_key_1001940": ("overfrequency_derating_f2", False),
    "config_key_1001941": ("overfrequency_derating_f3", False),
    "config_key_1001942": ("overfrequency_derating_p1", False),
    "config_key_1001943": ("overfrequency_derating_p2", False),
    "config_key_1001944": ("overfrequency_derating_p3", False),
    "over_frequency_drop_recovery_point": (
        "overfrequency_derating_recovery_frequency",
        False,
    ),
    "over_frequency_drop_curve": ("overfrequency_derating_curve", False),
    "over_frequency_drop_active_rate": ("overfrequency_derating_gradient", False),
    "over_frequency_drop_wait_restore_time": (
        "overfrequency_derating_recovery_delay",
        False,
    ),
    "over_frequency_drop_active_restore_rate": (
        "overfrequency_derating_recovery_gradient",
        False,
    ),
    "over_frequency_drop_response_time": (
        "overfrequency_derating_response_time",
        False,
    ),
    "rated_power_active": ("rated_active_power_limit", True),
    "point_20191226_24": ("apparent_power_limit", True),
    "pv_access_mode": ("pv_connection_mode", False),
    "protection_series": ("protection_level", False),
    "overvoltage_protection_recovery_value": (
        "overvoltage_reconnection_voltage",
        False,
    ),
    "undervoltage_protection_recovery_value": (
        "undervoltage_reconnection_voltage",
        False,
    ),
    "overfrequency_protection_recovery_value": (
        "overfrequency_reconnection_frequency",
        False,
    ),
    "underfrequency_protection_recovery_value": (
        "underfrequency_reconnection_frequency",
        False,
    ),
    "undervoltage_single_protect_value": (
        "undervoltage_level_1_protection_value",
        False,
    ),
    "overvoltage_single_protect_value": ("overvoltage_level_1_protection_value", False),
    "underfrequency_single_protect_value": (
        "underfrequency_level_1_protection_value",
        False,
    ),
    "overfrequency_single_protect_value": (
        "overfrequency_level_1_protection_value",
        False,
    ),
    "undervoltage_level2_protect_value": (
        "undervoltage_level_2_protection_value",
        False,
    ),
    "overvoltage_level2_protect_value": ("overvoltage_level_2_protection_value", False),
    "underfrequency_level2_protect_value": (
        "underfrequency_level_2_protection_value",
        False,
    ),
    "overfrequency_level2_protect_value": (
        "overfrequency_level_2_protection_value",
        False,
    ),
    "undervoltage_level3_protect_value": (
        "undervoltage_level_3_protection_value",
        False,
    ),
    "overvoltage_level3_protect_value": ("overvoltage_level_3_protection_value", False),
    "underfrequency_level3_protect_value": (
        "underfrequency_level_3_protection_value",
        False,
    ),
    "overfrequency_level3_protect_value": (
        "overfrequency_level_3_protection_value",
        False,
    ),
    "undervoltage_level1_protect_time": ("undervoltage_level_1_tripping_time", False),
    "overvoltage_level1_protect_time": ("overvoltage_level_1_tripping_time", False),
    "underfrequency_level1_protect_time": (
        "underfrequency_level_1_tripping_time",
        False,
    ),
    "overfrequency_level1_protect_time": ("overfrequency_level_1_tripping_time", False),
    "undervoltage_level2_protect_time": ("undervoltage_level_2_tripping_time", False),
    "overvoltage_level2_protect_time": ("overvoltage_level_2_tripping_time", False),
    "underfrequency_level2_protect_time": (
        "underfrequency_level_2_tripping_time",
        False,
    ),
    "overfrequency_level2_protect_time": ("overfrequency_level_2_tripping_time", False),
    "undervoltage_level3_protect_time": ("undervoltage_level_3_tripping_time", False),
    "overvoltage_level3_protect_time": ("overvoltage_level_3_tripping_time", False),
    "underfrequency_level3_protect_time": (
        "underfrequency_level_3_tripping_time",
        False,
    ),
    "overfrequency_level3_protect_time": ("overfrequency_level_3_tripping_time", False),
}
PARAMETER_ACTION_ONLY = {"set_total_power"}

# Reactive power modes offered by the reactive mode select.
REACTIVE_MODE_OPTIONS = ["off", "power_factor", "qt", "q_p", "q_u"]

# Official fault names (web UI language files), by FAULT_NAMES slug.
FAULT_TEXT: dict[str, tuple[str, str]] = {
    "grid_over_voltage": ("Grid Overvoltage", "Sobretensão da rede"),
    "grid_under_voltage": ("Grid Undervoltage", "Subtensão da rede"),
    "grid_over_frequency": ("Grid Overfrequency", "Sobrefrequência da rede"),
    "grid_under_frequency": ("Grid Underfrequency", "Subfrequência da rede"),
    "grid_interruption": ("Grid Power Outage", "Queda da rede"),
    "leakage_current": ("Excessive Leakage Current", "Corrente de fuga excessiva"),
    "grid_abnormal": ("Grid Abnormal", "Rede anormal"),
    "grid_voltage_unbalance": (
        "Grid Voltage Imbalance",
        "Desequilíbrio de tensão da rede",
    ),
    "pv_reverse_connection_fault": (
        "PV Reverse Connection Fault",
        "Polaridade reversa na entrada",
    ),
    "pv_reverse_connection_alarm": (
        "PV Reverse Connection Alarm",
        "Alarme de conexão reversa do arranjo FV",
    ),
    "pv_abnormal_alarm": ("PV Abnormal Alarm", "Anomalias no arranjo FV"),
    "ambient_over_temperature": (
        "Excessively High Ambient Temperature",
        "Temperatura ambiente excessivamente elevada",
    ),
    "ambient_under_temperature": (
        "Excessively Low Ambient Temperature",
        "Temperatura ambiente excessivamente baixa",
    ),
    "insulation_resistance": (
        "Low System Insulation Resistance",
        "Baixa resistência de isolamento do sist.",
    ),
    "ground_fault": ("Grounding Cable Fault", "Falha no cabo de aterramento"),
    "afci_error": ("AFCI Fault", "Falha de AFCI"),
    "backup_load_overpower": (
        "Backup Load Overpower Fault",
        "Falha de sobrepotência de carga fora da rede",
    ),
    "meter_reverse_connection": (
        "Meter/CT reverse connection alarm",
        "Conexão reversa do medidor/TC",
    ),
    "meter_communication": (
        "Meter Communication Abnormal Alarm",
        "Alerta de anomalia de comunicação do medidor",
    ),
    "grid_conflict": (
        "Grid Conflict",
        "Conflito de configuração do tipo de conexão à rede",
    ),
    "parallel_communication": (
        "Parallel Communication Alarm",
        "Alarme na comunicação paralela entre inversores",
    ),
    "bms_communication": ("BMS Communication Fault", "Falha de comunicação do BMS"),
    "battery_reverse_polarity": (
        "Abnormal Battery Connection",
        "Conexão anormal da bateria",
    ),
    "battery_alarm": ("Battery Alarm", "Alarme de bateria"),
    "battery_fault": ("Battery Fault", "Falha de bateria"),
    "pv_overvoltage": ("PV Overvoltage Fault", "Falha de sobretensão FV"),
    "mppt_reverse_connection": ("MPPT reverse connection", "Conexão inversa do MPPT"),
    "boost_capacitor_overvoltage_alarm": (
        "Boost Capacitor Overvoltage Alarm",
        "Alarme de sobretensão nos capacitores do circuito boost",
    ),
    "boost_capacitor_overvoltage_fault": (
        "Boost Capacitor Overvoltage Fault",
        "Sobretensão nos capacitores do circuito boost",
    ),
    "string_current_backfeed": (
        "String Current Backfeed",
        "Alarme de circulação de corrente reversa",
    ),
    "abnormal_shutdown": (
        "System Shutdown Abnormal",
        "Desligamento anormal do sistema",
    ),
    "pv_grounding_fault": ("PV Grounding Fault", "Falha de aterramento nos módulos FV"),
    "hardware_fault": ("System Hardware Fault", "Falha no hardware do sistema"),
    "system_alarm": ("System Alarm", "Alarme do sistema"),
    "system_fault": ("System Fault", "Anomalia de operação do sistema"),
    "external_power_supply": (
        "External Power Supply Abnormal",
        "Fornecimento de potência externa anormal",
    ),
}
