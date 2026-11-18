import json

from weather_provider_api.weather.utils.file_helpers import get_var_map_file_location

file_to_use = get_var_map_file_location("arome_var_map.json")

with open(file_to_use) as _f:
    arome_factors: dict[str, str] = json.load(_f)
