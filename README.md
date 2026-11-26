# ESP32 ASCII 电子鱼缸

用 ESP32-S3 和一块 1.54 寸 SPI 小屏，跑一个用字符画出来的小鱼缸：一条 `><(((o>` 纯 MicroPython，不需要额外的库。

> 灵感来自 Pete（@_re_pete）的 ASCII 电子鱼缸视频。本仓库是一个独立的复刻尝试，和原作者没有关系。

## 硬件

| 东西 | 说明 |
|---|---|
| 主控 | ESP32-S3 |
| 屏幕 | 1.54 寸 240×240 SPI 彩屏，ST7789 驱动，8 个引脚（带 CS） |

## 接线

| 屏幕引脚 | ESP32-S3 |
|---|---|
| GND | GND |
| VCC | 3V3 |
| SCL | GPIO4 |
| SDA | GPIO5 |
| RST | GPIO7 |
| DC | GPIO6 |
| CS | GPIO8 |
| BL | GPIO9 |

针脚可以在 `config.py` 里改。接线前请对照你自己板子上的丝印。

## 安装

1. **刷 MicroPython**：用 Thonny，解释器选 MicroPython (ESP32)，点 "Install or update MicroPython (esptool)"，芯片选 ESP32-S3，固件选 ESP32_GENERIC_S3。我用的是 v1.29.0。如果下载超时，可以手动下载 .bin 固件再刷。
2. **上传文件**：在 Thonny 里打开"视图 → 文件"，选中本仓库的所有 `.py` 文件，右键"上传到 /"。
3. **运行鱼缸**：运行 `main.py`。上传之后板子每次通电会自动运行它。

## 致谢

- Pete（@_re_pete）的 ASCII 电子鱼缸，是这个项目的灵感来源。
- 平滑字体的字符数据用 DejaVu Sans Mono Bold 渲染生成，DejaVu 字体的许可见 https://dejavu-fonts.github.io/License.html 。

## 许可证

见仓库里的 `LICENSE` 文件。
