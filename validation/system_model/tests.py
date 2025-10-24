# tests.py
# 16 June 2025

from z3 import *

from src.ms_system import modelFromJSON, modelToJSON
from validation.common.test_system import getTestMicroserviceSystem

if __name__ == "__main__":
    # See if tests pass
    allPassed = True

    # TEST 1 - Test JSON input/output
    print("TEST 1")

    prepSystem = getTestMicroserviceSystem()
    modelToJSON("data/system-models/test.json", prepSystem)
    compSystem = modelFromJSON("data/system-models/test.json")
    if prepSystem == compSystem:
        print("TEST 1 passed!\n")
    else:
        print("TEST 1 failed!\n")
        allPassed = False

    if allPassed is True:
        print("All tests passed!\n")
    else:
        print("One or more tests failed!\n")
