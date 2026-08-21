# ESP32-P4 Swipeable Dashboard

4-page swipeable ESPHome dashboard for the **Guition JC-ESP32P4-M3 / JC1060P470C** (1024×600 MIPI DSI touchscreen) running Home Assistant integration.

---

## Pages

| # | Page | Features |
|---|------|---------|
| 0 | **Weather** | Current temp · MDI condition icon + text · humidity · wind · 4-row hourly forecast with MDI icons + temp |
| 1 | **Music** | Album art (Navidrome via HA) · track/artist/album · volume bar with −/+ controls · play/pause/prev/next |
| 2 | **Home** | Standing fan · TV LED · Floor lamp · Evening Work scene |
| 3 | **Photo** | Placeholder (ESPFrame photo page) |

### Status bar (top, always visible)
- **Left**: WiFi signal %
- **Center**: Clock (HH:MM, Asia/Bangkok)
- **Right**: Current page name — updates on every swipe

### Navigation bar (bottom, always visible)
- 4 dot indicators — tap any dot to jump to that page
- Swipe left → next page
- Swipe right → previous page

---

## File structure

```
esp32p4-dashboard/
├── dashboard.yaml              ← compile this file
├── secrets.yaml                ← your credentials (copy from .template)
├── secrets.yaml.template       ← template with placeholder values
├── materialdesignicons.ttf     ← MDI icon font for weather condition glyphs
└── pages/
    ├── weather.yaml            ← Page 0: weather + hourly forecast
    ├── music.yaml              ← Page 1: music player with album art
    ├── home_ctrl.yaml          ← Page 2: home device controls
    └── photo.yaml              ← Page 3: photo placeholder

External component (referenced by absolute path in music.yaml):
    espframe-main/components/remote_image/
    (from https://github.com/jtenniswood/espframe — custom image downloader)
```

---

## Quick start

### 1. Install ESPHome

```bash
pip install esphome  # 2026.7.4+
```

### 2. Configure secrets

```bash
cp secrets.yaml.template secrets.yaml
# Edit secrets.yaml with your values
```

Required fields:
```yaml
wifi_ssid: "YourSSID"
wifi_password: "YourPassword"
api_key: "your-esphome-api-encryption-key"
ota_password: "your-ota-password"
```

### 3. Update entity IDs

Edit each page YAML to match your Home Assistant setup:

| File | Entity to change |
|------|-----------------|
| `pages/weather.yaml` | `weather.forecast_home` |
| `pages/music.yaml` | `media_player.lifeboat_jukebox_upnp_av` |
| `pages/home_ctrl.yaml` | fan, light, scene entity IDs |

Also update the HA IP (`192.168.1.4`) and token in `dashboard.yaml` http_request headers and in `pages/music.yaml` boot fetch.

### 4. Seed forecast sensors in HA (once)

The hourly forecast panel uses 4 virtual HA state sensors. Run this once to create them, then the firmware auto-refreshes every 5 minutes:

```python
import json, urllib.request
from datetime import datetime, timezone, timedelta

TOKEN = "your-long-lived-ha-token"
HA = "http://192.168.1.4:8123"
TZ = timezone(timedelta(hours=7))  # change to your timezone offset

req = urllib.request.Request(
    f"{HA}/api/services/weather/get_forecasts?return_response",
    data=json.dumps({"entity_id":"weather.forecast_home","type":"hourly"}).encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as r:
    data = json.load(r)

fc = data["service_response"]["weather.forecast_home"]["forecast"]
for i in range(1, 5):
    h = fc[i]
    dt = datetime.fromisoformat(h["datetime"]).astimezone(TZ)
    state = f"{dt.strftime('%H:%M')},{h.get('condition','--')},{round(h.get('temperature',0))}"
    payload = json.dumps({"state": state}).encode()
    req2 = urllib.request.Request(
        f"{HA}/api/states/sensor.forecast_h{i}",
        data=payload,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req2)
    print(f"h{i}: {state}")
# Output: h1: 03:00,rainy,27  h2: 04:00,rainy,27  etc.
```

### 5. Flash

```bash
cd esp32p4-dashboard
# OTA (device on WiFi):
esphome upload dashboard.yaml --device 192.168.1.39

# First-time USB flash:
esphome run dashboard.yaml
```

---

## Hardware (confirmed working)

| Setting | Value |
|---------|-------|
| Board | `esp32-p4-evboard`, variant `ESP32P4` |
| CPU frequency | 360 MHz |
| `engineering_sample` | `true` (required) |
| PSRAM | hex mode, 200 MHz |
| Flash | 16 MB |
| Display | `mipi_dsi`, model `JC1060P470`, reset `GPIO05`, 2 DSI lanes, 750 Mbps |
| Display timing | `hsync_pulse_width: 20`, `color_order: RGB`, pixel clock 54 MHz |
| Buffer | 16-bit, 100% (full-frame LVGL buffer) |
| Touch | GT911, I2C SDA=`GPIO7` SCL=`GPIO8` 400 kHz, int=`GPIO21`, rst=`GPIO22`, addr=`0x5D` |
| Backlight | LEDC `GPIO23`, 100 Hz PWM, max 80% |
| WiFi | ESP32-C6 coprocessor via `esp32_hosted` SDIO |
| WiFi SDIO | cmd=`GPIO19`, clk=`GPIO18`, d0=`GPIO14`, d1=`GPIO15`, d2=`GPIO16`, d3=`GPIO17`, rst=`GPIO54` |
| LDO | Channel 3, 2.5 V adjustable |

---

## Architecture & lessons learned

### Swipe navigation

Uses two complementary mechanisms:
1. **LVGL `on_swipe_left/right`** — built-in LVGL gesture recognition
2. **Touchscreen `on_touch/on_update/on_release`** — manual swipe tracking (dx > 80px threshold)

Both call `lvgl.page.next/previous` and `script.execute: nav_dots_refresh`.

### Weather hourly forecast

**Problem**: HA's `weather.get_forecasts` service returns ~9,302 bytes. ESPHome's `http_request` `capture_response` body is hardcoded at **1,000 bytes** regardless of `buffer_size_rx` setting.

**Solution**: Store forecasts in 4 compact virtual HA sensor states (`sensor.forecast_h1` to `sensor.forecast_h4`) formatted as `"HH:MM,condition,temp"` (e.g. `"03:00,rainy,27
---

## Architecture and hard-won lessons

### Swipe navigation
Two mechanisms work simultaneously:
1. LVGL on_swipe_left/right - built-in LVGL gesture
2. GT911 on_touch/on_update/on_release - manual dx>80px threshold

Both update current_page, call lvgl.page.next/previous, and refresh nav dots.
status_page_name updates on both swipe AND dot tap (nav_go script).

### Weather forecast: the hidden 1000-byte body limit
ESPHome http_request capture_response is hardcoded at 1000 bytes max.
HA weather.get_forecasts returns ~9302 bytes -- always fails with IncompleteInput.

Solution: 4 compact virtual HA state sensors (sensor.forecast_h1 to h4)
- Format: "HH:MM,condition,temp" e.g. "03:00,rainy,27"  
- Each /api/states response is ~400 bytes -- well within limit
- UTC to local time conversion happens in Python seeding script
- Device fetches at boot+20s and every 5 minutes via http_request.get

### Album art: why remote_image not online_image
Built-in online_image component has permanent LVGL refresh issues.
Used espframe custom remote_image component instead.

Critical config:
  type: RGB565
  byte_order: little_endian   <- required for MIPI DSI
  formats: [JPEG]
  buffer_size: 200000         <- must exceed image size (album art = 86-128 KB)

HA native API does NOT push entity_picture on reconnect if unchanged.
Album art arrives ~30 seconds after boot via text_sensor.

### Album art: LVGL image widget refresh
After remote_image downloads, LVGL still shows stale image (cached descriptor).
lv_image_set_src must be called again from a context with full LVGL headers.

The on_download_finished callback runs in remote_image context WITHOUT LVGL headers.
Calling lv_image_set_src there gives "invalid use of incomplete type lv_obj_t".

Working solution (flag + interval in music.yaml):

  on_download_finished:
    - lambda: id(art_needs_refresh) = true;

  interval:
    - interval: 500ms
      then:
        - if:
            condition:
              lambda: return id(art_needs_refresh);
            then:
              - lambda: |-
                  id(art_needs_refresh) = false;
                  lv_image_set_src(album_art_widget, album_art_img);
                  lv_obj_invalidate(album_art_widget);

The interval lambda runs in main.cpp context where album_art_widget is a raw
lv_obj_t* and lv_image_set_src has full LVGL type definitions available.

### Known pitfalls

| Issue | Fix |
|-------|-----|
| execute_from_psram: true | NEVER enable -- causes boot crash |
| OTA safe_mode rollback | Firmware must run >60s. Album art at boot+30s is safe |
| buffer_size_rx ignored | http_request body always capped at 1000 bytes |
| status_clock shows "--:--" | Fixed: clock_tick script now also updates status_clock |
| status_page_name stuck | Fixed: on_swipe handlers now update it (not just nav_go) |
| WiFi shows "WiFi" on boot | Fixed: component.update: wifi_pct in on_boot |
| LVGL image not refreshing | Fixed: lv_image_set_src via interval flag pattern |

---

## MDI weather icons

Uses materialdesignicons.ttf loaded as font id: mdi_weather.
Condition strings from HA map to MDI Unicode private use area:

  sunny          -> U+F0599
  clear-night    -> U+F0594
  partlycloudy   -> U+F0595
  cloudy         -> U+F0590
  fog            -> U+F0591
  rainy          -> U+F0597
  pouring        -> U+F0596
  lightning      -> U+F0593
  lightning-rainy -> U+F067E
  snowy          -> U+F0598
  snowy-rainy    -> U+F067F
  windy          -> U+F059D
  windy-variant  -> U+F059E
  hail           -> U+F0592

Icon mapping happens in C++ lambda (weather.yaml) for both main condition
and each hourly forecast row.

---

## Web UI

Device accessible at http://esp32p4-dashboard.local (ESPHome web server)
OTA updates: http://esp32p4-dashboard.local (web server OTA)
ESPHome API: esp32p4-dashboard.local:6053 (noise encrypted)
