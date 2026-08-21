# ESP32-P4 Swipeable Dashboard

4-page swipeable ESPHome dashboard for the **Guition JC-ESP32P4-M3 / JC1060P470C** (1024×600 MIPI DSI touchscreen) running Home Assistant integration.

---

## Pages

| # | Page | Features |
|---|------|---------|
| 0 | **Weather** | Current icon (48px, left) · temperature (48px, right) · condition label · humidity · feels-like · wind · rain · 6-row hourly forecast with MDI icons |
| 1 | **Music** | Album art (Navidrome/UPnP via HA) · track/artist/album (CJK multilang) · volume bar with −/+ · play/pause/prev/next · screen auto-wakes on playback |
| 2 | **Home** | Standing fan · TV LED · Floor lamp · Evening Work scene |
| 3 | **Photo** | Immich random slideshow — optional album UUID filter |

### Status bar (top, always visible)
- **Left**: Current page name — updates on every swipe or dot tap
- **Center**: 4 navigation dots — tap any dot to jump to that page
- **Right**: Clock (HH:MM, Asia/Bangkok)

### Navigation
- Swipe left → next page
- Swipe right → previous page
- Tap nav dots to jump directly

---

## File structure

```
esp32p4-dashboard/
├── dashboard.yaml              ← compile this file
├── secrets.yaml                ← your credentials (copy from .template, gitignored)
├── secrets.yaml.template       ← template with placeholder values
├── materialdesignicons.ttf     ← MDI icon font for weather condition glyphs
├── fonts/
│   ├── NotoSansCJK-Regular.ttf ← CJK / Korean / Vietnamese base (32,964 glyphs)
│   └── ThonburiUI-Regular.ttf  ← Thai script supplement (87 glyphs)
└── pages/
    ├── weather.yaml            ← Page 0: current conditions + 6h hourly forecast
    ├── music.yaml              ← Page 1: music player with album art
    ├── home_ctrl.yaml          ← Page 2: home device controls
    └── photo.yaml              ← Page 3: Immich photo slideshow

External component (referenced by absolute path):
    espframe-main/components/remote_image/
    (from https://github.com/jtenniswood/espframe)
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

Fields in `secrets.yaml` (copy from `secrets.yaml.template`):
```yaml
wifi_ssid: "YourWiFiName"
wifi_password: "YourWiFiPassword"
api_key: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
ota_password: "yourOtaPassword"

# Immich photo server
immich_url: "https://your-immich-instance"
immich_api_key: "your-immich-api-key"
immich_album_uuid: ""          # empty = random from all; UUID = specific album
```

### 3. Update entity IDs

Edit each page YAML to match your Home Assistant entities:

| File | Entity to change |
|------|-----------------|
| `pages/weather.yaml` | `weather.googleweather` |
| `pages/music.yaml` | `media_player.lifeboat_jukebox_upnp_av` |
| `pages/home_ctrl.yaml` | fan, light, scene entity IDs |

Also update the HA IP (`192.168.1.4`) and long-lived token in `pages/music.yaml` boot fetch.

### 4. Set up hourly forecast sensors in HA

The hourly forecast panel reads 6 virtual HA sensors (`sensor.forecast_h1` to `sensor.forecast_h6`) updated every 5 minutes by a Home Assistant template trigger.

Add `ha_google_weather_hourly_forecast.yaml` to your HA `configuration.yaml`:

```yaml
# configuration.yaml
template: !include ha_google_weather_hourly_forecast.yaml
```

Or paste its contents under the `template:` key directly. Then restart HA and verify in **Developer Tools → States** that `sensor.forecast_h1` through `sensor.forecast_h6` appear.

Sensor state format: `"HH:MM,condition,temp,precip_prob"` e.g. `"14:00,rainy,29,40"`

> **`gen_weather.py`** and **`gen_weather_yaml.py`** are code-generation tools used during development to regenerate `pages/weather.yaml`. You do not need to run them for normal use.

### 5. Flash

```bash
cd esp32p4-dashboard

# OTA (device already on WiFi):
esphome run dashboard.yaml

# First-time USB flash:
esphome run dashboard.yaml --device /dev/ttyUSB0
```

---

## Immich photo slideshow (Page 3)

- Set `immich_url` and `immich_api_key` in `secrets.yaml`
- Leave `immich_album_uuid: ""` to show random photos from your entire library
- Set `immich_album_uuid: "your-album-uuid"` to restrict to a specific album
- Find the album UUID from the Immich URL: `https://your-immich/albums/{uuid}`
- Tap the photo to load the next one immediately
- Also controllable via the **Dashboard Next Photo** button exposed to HA

---

## Home Assistant entities exposed

The dashboard exposes these entities via the native ESPHome API (appear automatically in HA):

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.esp32p4_dashboard_dashboard_page` | Text sensor | Current active page name, updates every second |
| `button.esp32p4_dashboard_dashboard_next_photo` | Button | Trigger next Immich photo remotely |
| `select.esp32p4_dashboard_dashboard_navigate` | Select | Navigate to Weather / Music / Home / Photo from HA |
| `light.esp32p4_dashboard_backlight` | Light | Backlight on/off + brightness slider |

### Auto screen-wake on music

When `music_state` transitions to `playing` **and** the screen is currently off (5-minute idle timeout), the device automatically:
1. Turns the backlight on at 100%
2. Navigates to the Music page

If the screen is already on, nothing changes — music plays without interrupting the current page.

---

## Multi-language music display

Song title, artist, and album support **Korean, Japanese, Chinese, Vietnamese, and Thai** characters using the bundled `NotoSansCJK-Regular.ttf` + `ThonburiUI-Regular.ttf` fonts.

- **Korean** (Hangul): U+AC00–D7A3 (11,172 syllables)
- **Chinese/Japanese** (CJK Unified Ideographs): U+4E00–9FFF
- **Japanese** (Hiragana + Katakana): U+3040–30FF
- **Vietnamese**: Latin Extended A/B + Additional (partial, what NotoSansCJK covers)
- **Thai**: from ThonburiUI, U+0E01–0E5B (87 characters)

Font size: 22px for all three labels (title/artist/album) — single size chosen to fit within the 7.9MB OTA flash partition.

> **Note:** The `fonts/` directory contains 14MB `NotoSansCJK-Regular.ttf`. ESPHome subsets this at build time to only the requested glyphs, producing a ~3MB font bitmap in the final firmware.

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

### Weather hourly forecast: the hidden 1000-byte body limit

**Problem**: HA's `weather.get_forecasts` service returns ~9,302 bytes. ESPHome's `http_request` `capture_response` body is hardcoded at **1,000 bytes** regardless of `buffer_size_rx`.

**Solution**: Store forecasts in 6 compact virtual HA sensor states (`sensor.forecast_h1` to `sensor.forecast_h6`) formatted as `"HH:MM,condition,temp,precip_prob"` (e.g. `"14:00,rainy,29,40"`). Each `/api/states` response is ~400 bytes — well within the limit.

### Album art: remote_image component

Built-in `online_image` has persistent LVGL refresh issues. Uses the `espframe` custom `remote_image` component instead.

Critical config:
```yaml
type: RGB565
byte_order: little_endian   # required for MIPI DSI
formats: [JPEG]
buffer_size: 200000         # must exceed image size (album art = 70–130 KB)
request_headers:
  x-api-key: "${immich_api_key}"   # required for Immich thumbnail auth
```

### Album art: LVGL image widget refresh

After `remote_image` downloads, LVGL still shows the stale image (cached descriptor). `lv_image_set_src` must be called from a context with full LVGL headers.

The `on_download_finished` callback runs without LVGL headers — calling `lv_image_set_src` there causes a compile error. **Solution**: flag + 500ms interval pattern:

```yaml
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
```

### CJK font: TTC → TTF extraction required

ESPHome only supports `.ttf`, `.otf`, `.woff`, `.bdf`, `.pcf` — not `.ttc` (TrueType Collection). Extract with fonttools:

```python
from fontTools.ttLib import TTCollection
ttc = TTCollection('/path/to/NotoSansCJK.ttc')
ttc[0].save('fonts/NotoSansCJK-Regular.ttf')
```

ESPHome's `glyphs` field requires **actual character strings** (not hex range notation like `"0x4E00-0x9FFF"`). Generate cmap-filtered strings to avoid missing-glyph validation errors:

```python
from fontTools.ttLib import TTFont
cmap = TTFont('fonts/NotoSansCJK-Regular.ttf').getBestCmap()
chars = ''.join(chr(c) for c in range(0x4E00, 0xA000) if c in cmap)
```

### Known pitfalls

| Issue | Fix |
|-------|-----|
| `execute_from_psram: true` | NEVER enable — causes boot crash |
| `.ttc` font files | Not supported — extract TTF with fonttools |
| `glyphs: ["0x4E00-0x9FFF"]` | Invalid — must be actual character strings |
| Flash overflow with multiple font sizes | Use single font size (22px) for CJK; 3 sizes = ~9.7MB, exceeds 7.9MB partition |
| OTA safe_mode rollback | Firmware must run >60s before safe_mode clears |
| `capture_response` body truncated | http_request body capped at ~1000 bytes regardless of `buffer_size_rx` |
| LVGL image not refreshing | Use flag + interval pattern (see album art section) |
| Immich thumbnail 401 | Add `request_headers: x-api-key` to `remote_image` definition |
| Immich album filter | Use `albumIds: ["uuid"]` array, not `albumId: "uuid"` string |

---

## MDI weather icons

Loaded from `materialdesignicons.ttf` as font ids `mdi_weather` (22px) and `mdi_weather_large` (48px).

HA condition strings map to MDI Unicode private-use codepoints:

| Condition | Glyph |
|-----------|-------|
| `sunny` | U+F0599 |
| `clear-night` | U+F0594 |
| `partlycloudy` | U+F0595 |
| `cloudy` | U+F0590 |
| `fog` | U+F0591 |
| `rainy` | U+F0597 |
| `pouring` | U+F0596 |
| `lightning` | U+F0593 |
| `lightning-rainy` | U+F067E |
| `snowy` | U+F0598 |
| `snowy-rainy` | U+F067F |
| `windy` | U+F059D |
| `windy-variant` | U+F059E |
| `hail` | U+F0592 |
| `exceptional` | U+F0CB0 |

---

## Web UI & API

| Access | Address |
|--------|---------|
| Web dashboard | `http://esp32p4-dashboard.local` |
| OTA via web | `http://esp32p4-dashboard.local` |
| ESPHome API | `esp32p4-dashboard.local:6053` (noise encrypted) |
