# Health Monitor Tests

This directory contains comprehensive tests for the HealthMonitor class, which is **critical for preventing death** in the game.

## 🧪 Test Coverage

### Critical Tests (Most Important)
- **Critical Healing Priority**: Ensures F6 is triggered when HP < 55%
- **Critical-First Logic**: Verifies critical healing is ALWAYS checked before moderate healing
- **Boundary Conditions**: Tests exact threshold values (549 vs 550 HP)

### Moderate Healing Tests
- **Moderate Healing Range**: F1 triggered when 55% ≤ HP < 75%
- **Moderate Only When Safe**: Ensures moderate healing only happens when NOT critical

### Safety Tests
- **Invalid HP Handling**: Safely handles None, 0, negative values
- **Cooldown Protection**: Prevents spam-clicking healing keys
- **Failure Counter**: Tracks consecutive OCR failures
- **Status Calculation**: Correct HP percentage and status display

## 🎯 Key Thresholds Tested

With Max HP = 1425 (real game values):
- **Critical**: HP < 783 (55%) → F6 Critical Heal
- **Moderate**: HP 783-1068 (55-75%) → F1 Moderate Heal  
- **Healthy**: HP ≥ 1069 (75%) → No Healing

## 🚨 Critical Safety Features Verified

1. **Death Prevention**: Critical healing (F6) is ALWAYS checked first
2. **No False Moderates**: A character with 30% HP will NEVER get F1 instead of F6
3. **Boundary Safety**: Exact threshold values work correctly
4. **Error Resilience**: Invalid data doesn't break the system

## 📋 Running Tests

```bash
# Run the comprehensive health monitor tests
python3 tests/test_health_monitor_simple.py

# Expected output: All tests pass with detailed descriptions
```

## ✅ Test Results

All tests must pass before deploying the health monitoring system. The tests verify that:

- **Your character will not die** due to incorrect healing logic
- **Critical situations are handled immediately** with F6
- **The system is robust** against errors and edge cases
- **Cooldowns prevent spam** but don't block critical heals

## 🔬 Test Philosophy

These tests follow the principle: **"If it's not tested, it's broken."**

Since the HealthMonitor is responsible for **life-or-death decisions** in the game, every critical path is thoroughly tested to ensure reliability. 