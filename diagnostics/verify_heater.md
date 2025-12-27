# Eryone Thinker X400 - Heater Failure Diagnostic Report

**Date of Incident:** December 20, 2025 (~10:45 AM EST / 15:45 UTC)  
**Print Duration at Failure:** 2 days, 11 hours (~62 hours)  
**Error Message:** "Heater extruder not heating at expected rate"  
**Report Date:** December 24, 2025

---

## Executive Summary

A long-duration print failed after approximately 62 hours with Klipper's `verify_heater` thermal protection triggering a shutdown. Log analysis shows stable temperature readings up until the log truncation point, with no gradual degradation pattern. A secondary configuration issue was discovered: the motherboard cooling fan is configured as a manual `output_pin` rather than an automatic `controller_fan`, meaning it may not run during prints unless explicitly commanded.

---

## 1. Incident Details

### Error Context

- **Klipper Module:** `verify_heater` (thermal runaway protection)
- **Target Temperature:** 255°C (extruder)
- **Bed Temperature:** 75°C
- **Print Material:** Likely high-temp (ABS/ASA based on temps and chamber heating)

### What This Error Means

The `verify_heater` module monitors heater performance and triggers a shutdown if:

1. The heater cannot reach target temperature within `heating_gain` degrees over `check_gain_time` seconds
2. The heater cannot maintain temperature within expected parameters
3. The actual heating rate drops below the expected curve

This is a **safety feature** to prevent thermal runaway (fire risk) from:

- Failed heater cartridge
- Loose thermistor
- Heater wire damage
- PWM output failure

---

## 2. Log Analysis

### 2.1 Temperature Readings Before Failure

The last recorded statistics from `klippy.log.2025-12-20` show:

| Parameter | Value | Status |
|-----------|-------|--------|
| Extruder Target | 255°C | Normal |
| Extruder Actual | 255.4°C | ✅ Stable at target |
| Extruder PWM | 0.371 (37.1%) | ✅ Normal duty cycle |
| Bed Target | 75°C | Normal |
| Bed Actual | 75.0°C | ✅ Stable |
| Print Time | 223,864 seconds | ~62.2 hours |

**Key Observation:** Temperature readings were stable and at target immediately before the log ends. No gradual temperature drift or erratic readings were captured.

### 2.2 Communication Health

| Metric | Main MCU | EECAN (Toolhead) | Status |
|--------|----------|------------------|--------|
| bytes_retransmit | 3,647 | 768 | ✅ Very low over 62h |
| bytes_invalid | 0 | 0 | ✅ Perfect |
| srtt (round-trip) | 0.001s | 0.001s | ✅ Excellent |
| rto (timeout) | 0.025s | 0.025s | ✅ Normal |

**Conclusion:** CAN bus communication was healthy. No evidence of communication timeouts or packet loss that would affect heater control.

### 2.3 System Resources

| Metric | Value | Status |
|--------|-------|--------|
| System Load | 0.92 - 1.00 | ⚠️ Elevated (was 0.17-0.25 earlier) |
| Memory Available | 156,428 KB | ✅ Adequate |
| CPU Time | 40,278 seconds | Normal for duration |

**Note:** System load was elevated at the end of the log, but this alone would not cause a heater-specific error.

### 2.4 Log Truncation Issue

The klippy.log ends abruptly with:

```
Dumping gcode input 0 blocks
```

This indicates Klipper began its shutdown sequence, but the actual error message was not captured. Possible reasons:

- Log rotation occurred before error was flushed to disk
- Process terminated before log buffer was written
- Error was displayed on screen but not fully logged

---

## 3. Hardware Configuration Review

### 3.1 Extruder Heater Configuration

From `EECAN.cfg`:

```ini
[extruder]
heater_pin: EECAN:gpio27
sensor_pin: EECAN:gpio26
sensor_type: Generic 3950
max_temp: 305
max_power: 1
```

### 3.2 Default verify_heater Settings

Klipper's default `verify_heater` parameters (not explicitly configured):

```ini
[verify_heater extruder]
max_error: 120          # Cumulative temperature error threshold
check_gain_time: 20     # Seconds to check heating progress
heating_gain: 2         # Minimum degrees gained per check_gain_time
hysteresis: 5           # Degrees below target before considered "not heating"
```

**Assessment:** Default settings are appropriate for most configurations. No explicit override was found in the config files.

---

## 4. Motherboard Fan Configuration Issue

### 4.1 Current Configuration (Problematic)

```ini
[output_pin Board_FAN]
pin: PA2
pwm: True
value: 0.0
cycle_time: 0.001
hardware_pwm: false
```

### 4.2 Problem Analysis

| Issue | Impact |
|-------|--------|
| Defined as `output_pin` not `controller_fan` | No automatic activation |
| `value: 0.0` at startup | Fan OFF by default |
| Manual control only | Depends on macros to turn on |

### 4.3 When the Fan Actually Runs

Based on config analysis:

| Scenario | Fan State | Source |
|----------|-----------|--------|
| Printer startup | ❌ OFF | `value: 0.0` default |
| Homing (G28) | ✅ ON (80%) | `homing_override` macro |
| During print | ❓ UNKNOWN | Depends on start gcode |
| `ck` macro (factory test) | ✅ ON (50%) | Explicit `SET_PIN` |
| Print end | ❌ OFF | `PRINT_END` macro |

### 4.4 Manual Test Results

**Test Command:**

```gcode
SET_PIN PIN=Board_FAN VALUE=1.0
```

**Result:** ✅ **Fan spins as expected**

**Conclusion:** The fan hardware is functional. Pin PA2 MOSFET is working. The issue is configuration, not hardware.

### 4.5 Risk Assessment

| Scenario | Risk Level | Explanation |
|----------|------------|-------------|
| Short prints | Low | Motherboard may not overheat |
| Long prints (multi-day) | **HIGH** | Sustained driver heat could damage components |
| High ambient temp | **HIGH** | Reduced passive cooling |
| Enclosed chamber | **CRITICAL** | Chamber heat + no active cooling |

---

## 5. Root Cause Analysis

### 5.1 Possible Causes for Heater Error

| Cause | Likelihood | Evidence |
|-------|------------|----------|
| **Thermistor intermittent fault** | Medium | No gradual drift in logs, could be momentary |
| **Thermistor wiring fatigue** | Medium | 62h of continuous motion could stress wires |
| **Heater cartridge degradation** | Low | PWM was normal (37%), not maxed out |
| **Heat creep / partial clog** | Low | Would show sustained high PWM first |
| **CAN bus communication loss** | Very Low | Stats show excellent communication |
| **Motherboard overheat (fan off)** | Low | Would cause MCU timeout, not heater-specific error |

### 5.2 Why Motherboard/Driver Overheat is NOT the Primary Cause

The MKS SKIPR has TMC2209 stepper drivers with heatsinks for X, Y, Z, Z1, Z2, Z3 axes. However, even if these overheated due to lack of fan cooling:

#### Architecture Separation

| Component | Location | Controls |
|-----------|----------|----------|
| TMC2209 (X,Y,Z) | Main board | Axis motors only |
| STM32F407 MCU | Main board | CAN master, motion planning |
| **TMC2209 (Extruder)** | **EECAN board** | Extruder motor |
| **Heater MOSFET** | **EECAN board** | Heater cartridge |
| **Thermistor ADC** | **EECAN board** | Temperature sensing |

#### Error Type Analysis

| Failure Scenario | Expected Klipper Error | Match? |
|------------------|------------------------|--------|
| TMC2209 driver overheat | `TMC 'stepper_x' overtemp` | ❌ |
| Main MCU (STM32) overheat | `MCU shutdown`, `Timer too close` | ❌ |
| CAN bus communication loss | `Lost communication with MCU 'EECAN'` | ❌ |
| Main board power instability | `MCU shutdown` or reboot | ❌ |
| **Thermistor/heater fault** | **`Heater not heating at expected rate`** | ✅ |

#### Why the Heater is Independent

1. **Autonomous Operation:** Once Klipper sends a PWM duty cycle to EECAN, the RP2040 maintains that heater output independently. Main board health doesn't affect moment-to-moment heater control.

2. **Separate Power Path:** The heater draws power through the EECAN board's MOSFET, not through the main board.

3. **Local Sensing:** Temperature is read by EECAN's ADC and transmitted via CAN. A main board issue wouldn't create false temperature readings.

4. **CAN Was Healthy:** Logs show excellent CAN communication (low retransmits, stable timing) right up until the end.

#### What Main Board Overheat WOULD Cause

If the TMC drivers or STM32 overheated:

- **Motor stalls** or missed steps (visible as layer shifts)
- **TMC driver errors** in the log
- **MCU timeout** causing full printer shutdown
- **Erratic motion** before shutdown

None of these match the observed `verify_heater` error, which specifically indicates the **toolhead's thermistor reading didn't match expected heating behavior**.

**Conclusion:** The motherboard fan issue should still be fixed for long-term reliability, but it did not cause this specific heater error. The fault is almost certainly in the toolhead (thermistor, heater, or wiring in the cable chain).

---

## 6. Recommendations

### 6.1 Immediate Actions

1. **Inspect thermistor wiring** at the toolhead for:
   - Chafing against moving parts
   - Loose connections in the EECAN terminal block
   - Heat damage to insulation

2. **Check heater cartridge wiring** for:
   - Secure crimps/connections
   - Signs of arcing or heat damage

3. **Test thermistor resistance** (should be ~100kΩ at 25°C for Generic 3950)

### 6.2 Configuration Changes

#### Fix Motherboard Fan (Recommended)

Replace the current `[output_pin Board_FAN]` configuration with:

```ini
[controller_fan motherboard_fan]
pin: PA2
max_power: 1.0
shutdown_speed: 0.0
kick_start_time: 0.5
stepper: stepper_x, stepper_y, stepper_z, extruder
idle_timeout: 60
```

**Benefits:**

- Automatically activates when any motor is running
- Automatically shuts off after idle timeout
- No macro changes required
- Better protection for long prints

#### Optional: Add Explicit verify_heater Tuning

For very long prints, slightly relaxed settings may reduce false positives:

```ini
[verify_heater extruder]
max_error: 180
check_gain_time: 30
heating_gain: 2
hysteresis: 10
```

⚠️ **Caution:** Only implement after confirming hardware is sound. Relaxing these settings reduces thermal runaway protection sensitivity.

### 6.3 Monitoring for Future Prints

1. **Check txqueuelen persistence** - Ensure `ifconfig can0 txqueuelen 1024` is applied at boot
2. **Monitor temperatures** via OctoEverywhere or similar during long prints
3. **Consider adding temperature logging** to capture data at failure time

---

## 7. Files Reviewed

| File | Purpose | Key Findings |
|------|---------|--------------|
| `klippy.log.2025-12-20` | Runtime log | Stable temps, truncated before error |
| `moonraker.log.2025-12-20` | API server log | Normal operation, no Klipper state change captured |
| `config/x400.cfg` | Printer macros | Board_FAN as output_pin, homing_override turns fan on |
| `config/EECAN.cfg` | Toolhead config | Heater on gpio27, thermistor on gpio26 |
| `config-v1/printer.cfg` | User's config | Custom PID values, input shaper settings |

---

## 8. Appendix: Relevant Log Excerpts

### Last Stats Entry Before Truncation

```
Stats 225224.2: gcodein=0  mcu: mcu_awake=0.043 ...
heater_bed: target=75 temp=75.0 pwm=0.205 sysload=0.92 
print_time=223864.041 buffer_time=3.294 print_stall=0 
extruder: target=255 temp=255.4 pwm=0.371
```

### Board_FAN Activation in homing_override

```ini
gcode: 
    M400 
    {% if 'x' not in printer.toolhead.homed_axes and 'y' not in printer.toolhead.homed_axes %}
       SET_PIN PIN=Board_FAN VALUE=0.8   # <-- Only here
       ...
```

---

*Report generated from log analysis and configuration review. Hardware inspection recommended before resuming multi-day prints.*
