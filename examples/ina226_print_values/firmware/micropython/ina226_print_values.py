# INA226 Current / Voltage / Power Monitor - Print Values
# Reads bus voltage, shunt voltage, current and power from an
# INA226 over I2C and prints them to the REPL every second.
#
# Wiring (RP2040 / RP2350):
#   INA226 SDA  → GPIO 0   (I2C0 SDA)
#   INA226 SCL  → GPIO 1   (I2C0 SCL)
#   INA226 VCC  → 3V3
#   INA226 GND  → GND
#   INA226 A0   → GND  (sets I2C address to 0x40)
#   INA226 A1   → GND
#
# Shunt resistor used: 0.1 Ω
# Max expected current:  3.2768 A  (gives Current_LSB = 100 µA)

from machine import I2C, Pin
import time
import struct

# ---------- INA226 register addresses ----------
_REG_CONFIG     = 0x00
_REG_SHUNT_V    = 0x01
_REG_BUS_V      = 0x02
_REG_POWER      = 0x03
_REG_CURRENT    = 0x04
_REG_CALIBRATION = 0x05

# ---------- constants ----------
INA226_ADDR     = 0x40          # default address (A0=GND, A1=GND)

# Calibration for R_shunt = 0.1 Ω, Current_LSB = 100 µA (0.0001 A)
# Cal = 0.00512 / (Current_LSB * R_shunt)
#     = 0.00512 / (0.0001 * 0.1) = 512
_CAL_VALUE      = 512

# Resolution constants
_CURRENT_LSB_A  = 0.0001        # 100 µA per LSB
_BUS_V_LSB_V    = 0.00125       # 1.25 mV per LSB
_SHUNT_V_LSB_V  = 0.0000025     # 2.5 µV per LSB
# Power LSB = 25 × Current_LSB
_POWER_LSB_W    = 25 * _CURRENT_LSB_A  # 2.5 mW per LSB


def _write_reg(i2c, addr, reg, value):
    """Write a 16-bit big-endian value to a register."""
    data = struct.pack(">H", value)
    i2c.writeto_mem(addr, reg, data)


def _read_reg(i2c, addr, reg):
    """Read a 16-bit big-endian value from a register (unsigned)."""
    raw = i2c.readfrom_mem(addr, reg, 2)
    return struct.unpack(">H", raw)[0]


def _read_reg_signed(i2c, addr, reg):
    """Read a 16-bit big-endian value from a register (signed two's complement)."""
    raw = i2c.readfrom_mem(addr, reg, 2)
    value = struct.unpack(">H", raw)[0]
    if value >= 0x8000:
        value -= 0x10000
    return value


def ina226_init(i2c):
    """Configure the INA226 with default averaging and conversion times."""
    # Configuration word:
    #   Bits [15:13] reset             = 0b000
    #   Bits [11:9]  avg samples       = 0b000  (1 sample)
    #   Bits [8:6]   bus conv time     = 0b100  (1.1 ms)
    #   Bits [5:3]   shunt conv time   = 0b100  (1.1 ms)
    #   Bits [2:0]   mode              = 0b111  (continuous shunt+bus)
    config = 0x4127
    _write_reg(i2c, INA226_ADDR, _REG_CONFIG, config)
    _write_reg(i2c, INA226_ADDR, _REG_CALIBRATION, _CAL_VALUE)


def ina226_read(i2c):
    """Return (bus_voltage_V, shunt_voltage_mV, current_mA, power_mW)."""
    bus_raw    = _read_reg(i2c, INA226_ADDR, _REG_BUS_V)
    shunt_raw  = _read_reg_signed(i2c, INA226_ADDR, _REG_SHUNT_V)
    current_raw = _read_reg_signed(i2c, INA226_ADDR, _REG_CURRENT)
    power_raw  = _read_reg(i2c, INA226_ADDR, _REG_POWER)

    bus_v   = bus_raw    * _BUS_V_LSB_V          # V
    shunt_v = shunt_raw  * _SHUNT_V_LSB_V * 1000  # mV
    current = current_raw * _CURRENT_LSB_A * 1000  # mA
    power   = power_raw  * _POWER_LSB_W * 1000    # mW

    return bus_v, shunt_v, current, power


# ---------- main ----------

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400_000)

# Quick scan to verify the INA226 is present
devices = i2c.scan()
if INA226_ADDR not in devices:
    print("INA226 not found on I2C bus. Check wiring.")
    print("Devices found:", [hex(d) for d in devices])
else:
    print("INA226 found at address", hex(INA226_ADDR))
    ina226_init(i2c)
    print("INA226 initialised. Reading values...\n")

    while True:
        bus_v, shunt_v, current, power = ina226_read(i2c)
        print(
            "Bus Voltage: {:6.3f} V  |  Shunt Voltage: {:7.3f} mV  |"
            "  Current: {:8.3f} mA  |  Power: {:8.3f} mW".format(
                bus_v, shunt_v, current, power
            )
        )
        time.sleep(1)
