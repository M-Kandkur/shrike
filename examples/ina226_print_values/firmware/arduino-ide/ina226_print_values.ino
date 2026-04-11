/**
 * Example: INA226 Current / Voltage / Power Monitor – Print Values
 *
 * Reads bus voltage, shunt voltage, current and power from an INA226
 * connected over I2C and prints them to the Serial Monitor every second.
 *
 * Wiring (RP2040 / RP2350 on Shrike):
 *   INA226 SDA  → GPIO 0  (I2C0 SDA, or any I2C-capable pin)
 *   INA226 SCL  → GPIO 1  (I2C0 SCL)
 *   INA226 VCC  → 3V3
 *   INA226 GND  → GND
 *   INA226 A0   → GND   (sets I2C address to 0x40)
 *   INA226 A1   → GND
 *
 * Shunt resistor: 0.1 Ω
 * Max expected current: 3.2768 A (Current_LSB = 100 µA)
 */

#include <Wire.h>

// ---------- INA226 register map ----------
#define INA226_ADDR        0x40

#define REG_CONFIG         0x00
#define REG_SHUNT_V        0x01
#define REG_BUS_V          0x02
#define REG_POWER          0x03
#define REG_CURRENT        0x04
#define REG_CALIBRATION    0x05

// ---------- calibration constants ----------
// R_shunt = 0.1 Ω,  Current_LSB = 100 µA
// Cal = 0.00512 / (Current_LSB_A * R_shunt)
//     = 0.00512 / (0.0001 * 0.1) = 512
#define CAL_VALUE          512

#define CURRENT_LSB_mA     0.1f      // 100 µA = 0.1 mA per LSB
#define BUS_V_LSB_V        0.00125f  // 1.25 mV per LSB
#define SHUNT_V_LSB_mV     0.0025f   // 2.5 µV = 0.0025 mV per LSB
// Power LSB = 25 × Current_LSB_A = 25 × 0.0001 A = 0.0025 W = 2.5 mW
#define POWER_LSB_mW       2.5f

// ---------- helpers ----------

static void writeReg(uint8_t reg, uint16_t value) {
  Wire.beginTransmission(INA226_ADDR);
  Wire.write(reg);
  Wire.write((uint8_t)(value >> 8));
  Wire.write((uint8_t)(value & 0xFF));
  Wire.endTransmission();
}

static uint16_t readReg(uint8_t reg) {
  Wire.beginTransmission(INA226_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)INA226_ADDR, (uint8_t)2);
  uint16_t value = 0;
  if (Wire.available() >= 2) {
    value  = (uint16_t)Wire.read() << 8;
    value |= (uint16_t)Wire.read();
  }
  return value;
}

static int16_t readRegSigned(uint8_t reg) {
  return (int16_t)readReg(reg);
}

// ---------- setup ----------

void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  Wire.setSDA(0);
  Wire.setSCL(1);
  Wire.begin();
  Wire.setClock(400000);

  // Configure INA226:
  //   avg=1 sample, bus conv=1.1ms, shunt conv=1.1ms, mode=continuous
  writeReg(REG_CONFIG, 0x4127);
  writeReg(REG_CALIBRATION, CAL_VALUE);

  // Verify presence
  uint16_t cfg = readReg(REG_CONFIG);
  if (cfg == 0xFFFF || cfg == 0x0000) {
    Serial.println("INA226 not found. Check wiring.");
    while (true) {}
  }

  Serial.println("INA226 initialised. Reading values...\n");
  Serial.println("Bus Voltage (V) | Shunt Voltage (mV) | Current (mA) | Power (mW)");
  Serial.println("----------------------------------------------------------------------");
}

// ---------- loop ----------

void loop() {
  float busV   = (float)readReg(REG_BUS_V)       * BUS_V_LSB_V;
  float shuntV = (float)readRegSigned(REG_SHUNT_V) * SHUNT_V_LSB_mV;
  float current = (float)readRegSigned(REG_CURRENT) * CURRENT_LSB_mA;
  float power   = (float)readReg(REG_POWER)         * POWER_LSB_mW;

  char buf[120];
  snprintf(buf, sizeof(buf),
           "  %6.3f          |  %8.3f          |  %8.3f    |  %8.3f",
           busV, shuntV, current, power);
  Serial.println(buf);

  delay(1000);
}
