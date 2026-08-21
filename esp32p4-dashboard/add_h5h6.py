path = 'pages/weather.yaml'
txt = open(path).read()
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjZGE1MDY1MDNhMjE0ZDU2OGM0NWUyOTFiZTdiNDY1MCIsImlhdCI6MTc4NzE1MzA5MSwiZXhwIjoyMTAyNTEzMDkxfQ.xPpAA16OiNYACz_M4sN4MLde7AMVsvdj6pH6DIQ1oJA'

# Build a compact GET block for each slot
def make_get(n):
    return f"""      - http_request.get:
          url: "http://192.168.1.4:8123/api/states/sensor.forecast_h{n}"
          request_headers:
            Authorization: "Bearer {TOKEN}"
          capture_response: true
          on_response:
            then:
              - lambda: |-
                  if (response->status_code != 200) return;
                  auto s = body.find("\\"state\\":\\"");
                  if (s == std::string::npos) return;
                  s += 9;
                  auto e = body.find("\\"", s);
                  if (e == std::string::npos) return;
                  auto val = body.substr(s, e-s);
                  int c1 = val.find(',');
                  if (c1 == (int)std::string::npos) return;
                  int c2 = val.find(',', c1+1);
                  if (c2 == (int)std::string::npos) return;
                  int c3 = val.find(',', c2+1);
                  if (c3 == (int)std::string::npos) c3 = (int)val.size();
                  id(fc{n}_time) = val.substr(0, c1);
                  {{
                    std::string cond = val.substr(c1+1, c2-c1-1);
                    if(cond=="sunny") cond="\U000F0599";
                    if(cond=="clear-night") cond="\U000F0594";
                    if(cond=="partlycloudy") cond="\U000F0595";
                    if(cond=="cloudy") cond="\U000F0590";
                    if(cond=="fog") cond="\U000F0591";
                    if(cond=="rainy") cond="\U000F0597";
                    if(cond=="pouring") cond="\U000F0596";
                    if(cond=="lightning") cond="\U000F0593";
                    if(cond=="lightning-rainy") cond="\U000F067E";
                    if(cond=="snowy") cond="\U000F0598";
                    if(cond=="snowy-rainy") cond="\U000F067F";
                    if(cond=="windy") cond="\U000F059D";
                    if(cond=="windy-variant") cond="\U000F059E";
                    if(cond=="hail") cond="\U000F0592";
                    if(cond=="exceptional") cond="\U000F0F30";
                    id(fc{n}_cond) = cond;
                  }}
                  id(fc{n}_temp) = val.substr(c2+1, c3-c2-1) + "\u00b0";
                  id(fc{n}_prob) = c3 < (int)val.size() ? val.substr(c3+1) + "%" : "";
              - lvgl.label.update:
                  id: lbl_fc{n}_day
                  text: !lambda return id(fc{n}_time).c_str();
              - lvgl.label.update:
                  id: lbl_fc{n}_condition
                  text: !lambda return id(fc{n}_cond).c_str();
              - lvgl.label.update:
                  id: lbl_fc{n}_hi
                  text: !lambda return id(fc{n}_temp).c_str();
              - lvgl.label.update:
                  id: lbl_fc{n}_prob
                  text: !lambda return id(fc{n}_prob).c_str();"""

# 1. Insert h5/h6 GET calls before lvgl:
old_lvgl = '\nlvgl:\n  pages:'
new_before = '\n' + make_get(5) + '\n' + make_get(6) + '\n' + 'lvgl:\n  pages:'
if old_lvgl in txt:
    txt = txt.replace(old_lvgl, new_before)
    print('Added h5/h6 GET calls')

# 2. Add h5/h6 LVGL rows  
old_fc4_end = """              - label:
                  id: lbl_fc4_prob
                  align: TOP_RIGHT
                  x: 0
                  y: 240
                  text: "--%"
                  text_font: MONTSERRAT_14
                  text_color: 0x4C9FFF"""

def make_row(n, y_row, y_divider):
    div = ""
    if y_divider:
        div = f"""
              - obj:
                  align: TOP_MID
                  y: {y_divider}
                  width: 400
                  height: 2
                  bg_color: 0x2A2D40
                  border_opa: TRANSP
                  shadow_opa: TRANSP
                  pad_all: 0
"""
    return div + f"""              - label:
                  id: lbl_fc{n}_day
                  align: TOP_LEFT
                  x: 0
                  y: {y_row}
                  text: "+{n}h"
                  text_font: MONTSERRAT_18
                  text_color: 0xC0C8E0
              - label:
                  id: lbl_fc{n}_condition
                  text_font: mdi_weather
                  align: TOP_MID
                  y: {y_row}
                  text: "..."
                  text_color: 0x9BA2BC
              - label:
                  id: lbl_fc{n}_hi
                  align: TOP_RIGHT
                  x: -50
                  y: {y_row}
                  text: "--\u00b0"
                  text_font: MONTSERRAT_18
                  text_color: 0xFFFFFF
              - label:
                  id: lbl_fc{n}_prob
                  align: TOP_RIGHT
                  x: 0
                  y: {y_row}
                  text: "--%"
                  text_font: MONTSERRAT_14
                  text_color: 0x4C9FFF"""

new_fc4_end = old_fc4_end + make_row(5, 300, 270) + make_row(6, 360, 330)

if old_fc4_end in txt:
    txt = txt.replace(old_fc4_end, new_fc4_end)
    print('Added h5/h6 LVGL rows')
else:
    print('WARNING: fc4_prob row not found')

open(path, 'w').write(txt)
print('Done