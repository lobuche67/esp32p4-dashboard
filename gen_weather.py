#!/usr/bin/env python3
import os

TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJjZGE1MDY1MDNhMjE0ZDU2OGM0NWUyOTFiZTdiNDY1MCIsImlhdCI6MTc4NzE1MzA5MSwiZXhwIjoyMTAyNTEzMDkxfQ"
    ".xPpAA16OiNYACz_M4sN4MLde7AMVsvdj6pH6DIQ1oJA"
)
AUTH = f"Bearer {TOKEN}"

ICONS = {
    "sunny":           "\U000F0599",
    "clear-night":     "\U000F0594",
    "partlycloudy":    "\U000F0595",
    "cloudy":          "\U000F0590",
    "fog":             "\U000F0591",
    "rainy":           "\U000F0597",
    "pouring":         "\U000F0596",
    "lightning":       "\U000F0593",
    "lightning-rainy": "\U000F067E",
    "snowy":           "\U000F0598",
    "snowy-rainy":     "\U000F067F",
    "windy":           "\U000F059D",
    "windy-variant":   "\U000F059E",
    "hail":            "\U000F0592",
    "exceptional":     "\U000F0CB0",
}

DEG = "\u00b0"
CLOUDY = ICONS["cloudy"]

# C++ icon lookup lines (indented for lambda)
def icon_lookup_cpp(indent="                    "):
    return "\n".join(
        f'{indent}if(cond=="{k}") cond="{v}";'
        for k, v in ICONS.items()
    )

# C++ condition lambda for current weather
def cond_lambda_cpp():
    return "\n".join(
        f'            if(x=="{k}") id(weather_icon_str)="{v}";'
        for k, v in ICONS.items()
    )

ICON_LOOKUP = icon_lookup_cpp()
COND_LAMBDA = cond_lambda_cpp()

def fc_row(n, y_row, y_div):
    fcn = f"fc{n}"
    div = ""
    if y_div is not None:
        div = f"""
              - obj:
                  align: TOP_MID
                  y: {y_div}
                  width: 400
                  height: 2
                  bg_color: 0x2A2D40
                  border_opa: TRANSP
                  shadow_opa: TRANSP
                  pad_all: 0
"""
    return (
        f"{div}"
        f"              - label:\n"
        f"                  id: lbl_{fcn}_day\n"
        f"                  align: TOP_LEFT\n"
        f"                  x: 0\n"
        f"                  y: {y_row}\n"
        f"                  text: \"+{n}h\"\n"
        f"                  text_font: MONTSERRAT_18\n"
        f"                  text_color: 0xC0C8E0\n"
        f"              - label:\n"
        f"                  id: lbl_{fcn}_condition\n"
        f"                  text_font: mdi_weather\n"
        f"                  align: TOP_MID\n"
        f"                  y: {y_row}\n"
        f"                  text: \"...\"\n"
        f"                  text_color: 0x9BA2BC\n"
        f"              - label:\n"
        f"                  id: lbl_{fcn}_hi\n"
        f"                  align: TOP_RIGHT\n"
        f"                  x: -50\n"
        f"                  y: {y_row}\n"
        f"                  text: \"--{DEG}\"\n"
        f"                  text_font: MONTSERRAT_18\n"
        f"                  text_color: 0xFFFFFF\n"
        f"              - label:\n"
        f"                  id: lbl_{fcn}_prob\n"
        f"                  align: TOP_RIGHT\n"
        f"                  x: 0\n"
        f"                  y: {y_row}\n"
        f"                  text: \"--%\"\n"
        f"                  text_font: MONTSERRAT_14\n"
        f"                  text_color: 0x4C9FFF"
    )

row_y = [60, 120, 180, 240, 300, 360]
div_y = [None, 100, 160, 220, 280, 340]
rows_yaml = "\n".join(fc_row(n+1, row_y[n], div_y[n]) for n in range(6))

globals_section = "\n".join(
    (
        f"  - id: fc{n}_time\n    type: std::string\n    initial_value: '\"+{n}h\"'\n"
        f"  - id: fc{n}_cond\n    type: std::string\n    initial_value: '\"...\"'\n"
        f"  - id: fc{n}_temp\n    type: std::string\n    initial_value: '\"--\"'\n"
        f"  - id: fc{n}_prob\n    type: std::string\n    initial_value: '\"\"'"
    )
    for n in range(1, 7)
)

# The main forecast fetch lambda - uses "condition":" pattern as anchor
FETCH_LAMBDA = (
    f"      - http_request.post:\n"
    f"          url: \"http://192.168.1.4:8123/api/services/weather/get_forecasts?return_response\"\n"
    f"          request_headers:\n"
    f"            Authorization: \"{AUTH}\"\n"
    f"            Content-Type: \"application/json\"\n"
    f"          body: '{{\"entity_id\":\"weather.googleweather\",\"type\":\"hourly\"}}'\n"
    f"          capture_response: true\n"
    f"          on_response:\n"
    f"            then:\n"
    f"              - lambda: |-\n"
    f"                  if (response->status_code != 200) {{\n"
    f"                    ESP_LOGW(\"forecast\", \"get_forecasts returned %d\", response->status_code);\n"
    f"                    return;\n"
    f"                  }}\n"
    f"                  lv_obj_t* day_lbls[6]  = {{id(lbl_fc1_day), id(lbl_