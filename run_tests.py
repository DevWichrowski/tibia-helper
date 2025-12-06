#!/usr/bin/env python3
"""
Health Monitor Test Runner

Complete test suite for the health monitoring system.
Runs both basic and comprehensive critical healing tests.
"""

import subprocess
import sys
import os

def run_tests():
    """Run complete health monitor test suite"""
    print("🧪 COMPLETE HEALTH MONITOR TEST SUITE")
    print("=" * 60)
    print()
    
    test_files = [
        ('Basic Tests', 'tests/test_health_monitor_simple.py'),
        ('Comprehensive Critical Tests', 'tests/test_health_monitor_comprehensive.py'),
        ('Extended Health Tests', 'tests/test_health_monitor_extended.py'),
        ('Auto-Haste Tests', 'tests/test_auto_haste.py'),
        ('Skinner Tests', 'tests/test_skinner.py'),
    ]
    
    all_passed = True
    
    for test_name, test_file in test_files:
        print(f"🔬 Running {test_name}...")
        
        try:
            result = subprocess.run([
                sys.executable, test_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {test_name} - ALL PASSED!")
                
                # Count tests from output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'Ran ' in line and ' tests in ' in line:
                        print(f"   {line.strip()}")
                        break
                        
            else:
                print(f"❌ {test_name} - FAILED!")
                print("Output:", result.stdout[-500:])  # Last 500 chars
                all_passed = False
                
        except Exception as e:
            print(f"❌ Error running {test_name}: {e}")
            all_passed = False
        
        print()
    
    # Final summary
    if all_passed:
        print("🎯 COMPLETE TEST SUITE RESULTS:")
        print("=" * 40)
        print("✅ ALL TESTS PASSED!")
        print()
        print("🛡️ Your health monitoring system is BATTLE-TESTED")
        print("🚨 Critical healing priority verified")
        print("💊 Moderate healing logic confirmed")
        print("🎯 Boundary conditions tested")
        print("🔢 Floating point precision fixed")
        print("💀 Near-death survival scenarios tested")
        print("⚔️ Combat damage sequences verified") 
        print("🔄 Recovery scenarios working")
        print("🛠️ Edge cases and error handling robust")
        print("⚡ Auto-Haste functionality verified")
        print("🔪 Skinner right-click logic tested")
        print()
        print("🎮 READY FOR GAME MONITORING - WILL KEEP YOU ALIVE!")
        
    else:
        print("❌ SOME TESTS FAILED!")
        print()
        print("🚨 DO NOT USE UNTIL ALL TESTS PASS!")
        print("🚨 SYSTEM MAY NOT PROTECT YOU CORRECTLY!")
        
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 