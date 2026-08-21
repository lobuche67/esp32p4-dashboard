#!/usr/bin/env python3
"""Generates esp32p4-dashboard/pages/weather.yaml with all 6 hourly forecast sensors."""
import os

OUT = os.path.join(os.path.dirname(__file__), "pages", "weather.yaml")

ICONS = [
    ("sunny",           "\U000F0599"),
    ("clear-night",     "\U000F0594"),
    ("partlycloudy",    "\U000F0595"),
    ("cloudy",          "\U000F0590"),
    ("fog",             "\U000F0591"),
    ("rainy",           "\U000F0597"),
    ("pouring",         "\U000F0596"),
    ("lightning",       "\U000F0593"),
    ("lightning-rainy", "\U000F067E"),
    ("snowy",           "\U000F0598"),
    ("snowy-rainy",     "\U000F067F"),
    ("windy",           "\U000F059D"),
    ("windy-variant",   "\U000F059E"),
    ("hail",            "\U000F0592"),
    ("exceptional",     "\U000F0CB0"),
]

DEG = "\u00b0"

def icon_cond_lambda(indent="            "):
    return "\n".join(f'{indent}if(x=="{k}") id(weather_icon_str)="{v}";' for k, v in ICONS)

def icon_lookup_cpp(indent="              "):
    return "\n".join(f'{indent}if(cond=="{k}") cond="{v}";' for k, v in ICONS)

def forecast_text_sensor(n):
    fc = f"fc{n}"
    return f"""\
  - platform: homeassistant
    id: ha_forecast_h{n}
    entity_id: sensor.forecast_h{n}
    on_value:
      then:
        - lambda: |-
            auto val = x;
            int c1 = val.find(',');
            if (c1 == (int)std::string::npos) return;
            int c2 = val.find(',', c1+1);
            if (c2 == (int)std::string::npos) return;
            int c3 = val.find(',', c2+1);
            if (c3 == (int)std::string::npos) c3 = (int)val.size();
            id({fc}_time) = val.substr(0, c1);
            {{
              std::string cond = val.substr(c1+1, c2-c1-1);
{icon_lookup_cpp()}
              id({fc}_cond) = cond;
            }}
            id({fc}_temp) = val.substr(c2+1, c3-c2-1) + "{DEG}";
            id({fc}_prob) = c3 < (int)val.size() ? val.substr(c3+1) + "%" : "";
        - lvgl.label.update:
            id: lbl_{fc}_day
            text: !lambda return id({fc}_time).c_str();
        - lvgl.label.update:
            id: lbl_{fc}_condition
            text: !lambda return id({fc}_cond).c_str();
        - lvgl.label.update:
            id: lbl_{fc}_hi
            text: !lambda return id({fc}_temp).c_str();
        - lvgl.label.update:
            id: lbl_{fc}_prob
            text: !lambda return id({fc}_prob).c_str();
"""

def globals_section():
    lines = []
    for n in range(1, 7):
        fc = f"fc{n}"
        lines.append(f'  - id: {fc}_time\n    type: std::string\n    initial_value: \'"+{n}h"\'')
        lines.append(f'  - id: {fc}_cond\n    type: std::string\n    initial_value: \'"..."\'')
        lines.append(f'  - id: {fc}_temp\n    type: std::string\n    initial_value: \'"--"\'')
        lines.append(f'  - id: {fc}_prob\n    type: std::string\n    initial_value: \'""\'')
    return "\n".join(lines)

def fc_row_widgets(n, y_row, y_div):
    fc = f"fc{n}"
    div = ""
    if y_div is not None:
        div = f"""\
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
    return f"""{div}\
              - label:
                  id: lbl_{fc}_day
                  align: TOP_LEFT
                  x: 0
                  y: {y_row}
                  text: "+{n}h"
                  text_font: MONTSERRAT_18
                  text_color: 0xC0C8E0
              - label:
                  id: lbl_{fc}_condition
                  text_font: mdi_weather
                  align: TOP_MID
                  y: {y_row}
                  text: "..."
                  text_color: 0x9BA2BC
              - label:
                  id: lbl_{fc}_hi
                  align: TOP_RIGHT
                  x: -50
                  y: {y_row}
                  text: "--{DEG}"
                  text_font: MONTSERRAT_18
                  text_color: 0xFFFFFF
              - label:
                  id: lbl_{fc}_prob
                  align: TOP_RIGHT
                  x: 0
                  y: {y_row}
                  text: "--%"
                  text_font: MONTSERRAT_14
                  text_color: 0x4C9FFF"""

row_y  = [60, 120, 180, 240, 300, 360]
div_y  = [None, 100, 160, 220, 280, 340]
rows_yaml = "\n".join(fc_row_widgets(n+1, row_y[n], div_y[n]) for n in range(6))

out = f"""\
# PAGE 0 — Weather
# Current conditions come from weather.googleweather attributes (platform: homeassistant).
# Hourly forecast comes from template sensors sensor.forecast_h1..h6 created by
#   ha_google_weather_hourly_forecast.yaml — add that file to your HA config first.
# Each sensor state is the string:  "HH:MM,condition,temperature,precip_prob"
# Example:  "14:00,sunny,31,20"

# ── Current conditions sensors ────────────────────────────────────────────────
sensor:

  - platform: homeassistant
    id: weather_temp
    entity_id: weather.googleweather
    attribute: temperature
    on_value:
      then:
        - lvgl.label.update:
            id: lbl_weather_temp
            text:
              format: "%.0f{DEG}"
              args: [x]

  - platform: homeassistant
    id: weather_feels_like
    entity_id: weather.googleweather
    attribute: apparent_temperature
    on_value:
      then:
        - lvgl.label.update:
            id: lbl_weather_feels
            text