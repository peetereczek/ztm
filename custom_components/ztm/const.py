DOMAIN = "ztm_beta"

CONF_ATTRIBUTION = ("Dane dostarcza Miasto Stołeczne Warszawa, api.um.warszawa.pl")
ZTM_ENDPOINT = "https://api.um.warszawa.pl/api/action/dbtimetable_get/"
ZTM_DATA_ID = 'e923fa0e-d96c-43f9-ae6e-60518c9f3238'
CONF_API_KEY = 'api_key'
CONF_LINES = 'lines'
CONF_LINE_NUMBER = 'number'
CONF_STOP_ID = 'stop_id'
CONF_STOP_NUMBER = 'stop_number'
REQUEST_TIMEOUT = 10  # seconds
DEFAULT_ENTRIES = 3
SENSOR_ID_FORMAT = "{} {} from {} {}"
SENSOR_NAME_FORMAT = "{} {} z przystanku {} {}"
UNIT = 'min'
DEFAULT_NAME = "ZTM_BETA"
CONF_ENTRIES = 'entries'

COMPONENTS = {
    "sensor": "sensor",
}