# INA226 Current / Voltage / Power Monitor – Print Values

This example demonstrates how to read and print bus voltage, shunt voltage, current and power from a **Texas Instruments INA226** current/power monitor using the RP2040's I2C peripheral.

The INA226 connects directly to the RP2040 over I2C; no FPGA design is required for this example.

---

## Overview

The INA226 is a 16-bit, high-accuracy current/power monitor that communicates over I2C. It measures:

| Measurement   | Resolution  | Formula                         |
|---------------|-------------|---------------------------------|
| Bus voltage   | 1.25 mV/LSB | `Bus_V = raw × 1.25 mV`         |
| Shunt voltage | 2.5 µV/LSB  | `Shunt_V = raw × 2.5 µV`        |
| Current       | 100 µA/LSB  | `Current = raw × 100 µA`        |
| Power         | 2.5 mW/LSB  | `Power = raw × 2.5 mW`          |

Current and power readings require writing a **Calibration Register** value first:

```
Cal = 0.00512 / (Current_LSB_A × R_shunt)
    = 0.00512 / (0.0001 × 0.1) = 512
```

This example assumes a **0.1 Ω shunt resistor** and a maximum measurable current of ~3.28 A.

---

## Wiring

| INA226 Pin | Shrike / RP2040 Pin | Description          |
|------------|---------------------|----------------------|
| SDA        | GPIO 0              | I2C data             |
| SCL        | GPIO 1              | I2C clock            |
| VCC        | 3V3                 | Supply voltage       |
| GND        | GND                 | Ground               |
| A0         | GND                 | I2C address bit 0    |
| A1         | GND                 | I2C address bit 1    |
| IN+        | Load positive rail  | Current sense input+ |
| IN−        | Shunt resistor      | Current sense input− |

> **Note:** With A0 and A1 tied to GND the INA226 I2C address is **0x40**.

---

## Parameters

| Parameter      | Value      | Description                       |
|----------------|------------|-----------------------------------|
| `R_shunt`      | 0.1 Ω      | Shunt resistor value              |
| `Current_LSB`  | 100 µA     | Current resolution per LSB        |
| `CAL_VALUE`    | 512 (0x200)| Calibration register value        |
| `I2C Address`  | 0x40       | INA226 default address            |
| `I2C Frequency`| 400 kHz    | Fast-mode I2C clock               |

---

## Firmware

Two firmware implementations are provided:

- **MicroPython** – `firmware/micropython/ina226_print_values.py`
- **Arduino** – `firmware/arduino-ide/ina226_print_values.ino`

Both scan the I2C bus on startup, initialise the INA226, and then print a live table of measurements to the serial console every second.

### Expected Output

```
INA226 found at address 0x40
INA226 initialised. Reading values...

Bus Voltage:  4.998 V  |  Shunt Voltage:   5.025 mV  |  Current:   50.250 mA  |  Power:  251.250 mW
Bus Voltage:  4.997 V  |  Shunt Voltage:   5.000 mV  |  Current:   50.000 mA  |  Power:  250.000 mW
...
```

---

## More Things to Try

- Change the averaging mode in the configuration register to reduce noise.
- Set an alert threshold on the ALERT pin to trigger an interrupt when current exceeds a limit.
- Log the measurements to a CSV file on a USB flash drive using the `uos` module.
- Graph the data in real time with a serial plotter (e.g. Arduino IDE Serial Plotter).
