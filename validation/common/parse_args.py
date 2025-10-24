# parse_args.py
# 17 June 2025

import time
import os
from typing import Tuple

from src.ms_system import modelFromJSON, modelToJSON, MicroserviceSystem
from src.ir_parser import getModelFromIRAndCode

def readCommandLineArgs(argv: list[str]) -> Tuple[MicroserviceSystem, bool]:
    GENERATED_SYSTEM_MODEL = "data/system-models/train-ticket-gen.json"
    GROUND_TRUTH_SYSTEM_MODEL = "data/system-models/train-ticket-gt.json"
    MODEL_TO_LOAD = GROUND_TRUTH_SYSTEM_MODEL
    DEBUG = False

    # Read command line argument
    if len(argv) > 1:
        arg = argv[1]

        if arg == "GENERATED_SYSTEM_MODEL":
            MODEL_TO_LOAD = GENERATED_SYSTEM_MODEL
        elif arg == "GENERATE_NEW_SYSTEM_MODEL":
            MODEL_TO_LOAD = None
        else:
            MODEL_TO_LOAD = GROUND_TRUTH_SYSTEM_MODEL

        if len(argv) > 2:
            arg = argv[2]
            if arg == "DEBUG":
                DEBUG = True

    # Create new or read existing system model
    if MODEL_TO_LOAD is not None and os.path.isfile(MODEL_TO_LOAD):
        print("Reading system model...")
        msSystem = modelFromJSON(MODEL_TO_LOAD)
    else:
        print("Generating system model...")
        start_time = time.perf_counter()
        msSystem = getModelFromIRAndCode("data/train-ticket/train-ticket-ir-a4ed2433b0b6ab6e0d60115fc19efecb2548c6cd"
                                         ".json",
                                         "data/train-ticket/train-ticket-a4ed2433b0b6ab6e0d60115fc19efecb2548c6cd")
        end_time = time.perf_counter()
        print(f"System model generated in {end_time-start_time} seconds")

        modelToJSON("data/system-models/train-ticket.json", msSystem)

    return msSystem, DEBUG
