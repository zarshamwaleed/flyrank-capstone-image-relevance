#!/usr/bin/env python
import sys
import os
import pytest

# Add the app directory to path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/app')

def run_tests():
    print("=" * 60)
    print("🧪 RUNNING TEST SUITE")
    print("=" * 60)
    
    # Run all tests
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--maxfail=1",
        "--disable-warnings",
        "--no-cov"
    ])
    
    print("=" * 60)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"❌ {exit_code} TESTS FAILED")
    print("=" * 60)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    run_tests()
