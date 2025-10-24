# case_study.py
# 16 June 2025

import json
import re
import time

from z3 import *

from src.ms_system import MicroserviceSystem
from validation.common.parse_args import readCommandLineArgs


def replaceRequestVariables(text):
    return re.sub(r'\{[^}]*\}', '{?}', text)


def roleNamesToBitstring(roleNames):
    bitstring = 0
    if "UnauthenticatedRole" in roleNames:
        bitstring |= 0b001
    if "user" in roleNames:
        bitstring |= 0b010
    if "admin" in roleNames:
        bitstring |= 0b100
    return bitstring


def evaluateRepositoryHelper(ACCESSES_GROUND_TRUTH, ACCESSES_RESULTS, access, result, i):
    if access is True and result == 1:
        ACCESSES_GROUND_TRUTH[i] += 1
        ACCESSES_RESULTS[i][0] += 1
        return True
    elif access is False and result == 0:
        ACCESSES_RESULTS[i][1] += 1
        return True
    elif access is False and result == 1:
        ACCESSES_RESULTS[i][2] += 1
        return False
    elif access is True and result == 0:
        ACCESSES_GROUND_TRUTH[i] += 1
        ACCESSES_RESULTS[i][3] += 1
        return False
    else:
        return False


def evaluateRepositories(system: MicroserviceSystem, path: str):
    ACCESSES_GROUND_TRUTH = [0, 0, 0, 0]  # Create, Read, Update, Delete
    ACCESSES_RESULTS = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]  # TP, TN, FP, FN
    valid = True

    expectedRepositories = set()
    actualRepositories = set()

    with open(path + "/ground_truth_CRUD_permissions.json", "r") as groundTruthFile:
        ground_truth = json.load(groundTruthFile)
        for func, repo in ground_truth.items():
            endpoint = system.findEndpointByFuncName(func)
            if endpoint is not None:
                for repoName, accesses in repo.items():
                    expectedRepositories.add(repoName)
                    found = False
                    for r in endpoint.repositories:
                        if repoName in r.name:
                            for access in accesses:
                                if access == "CREATE":
                                    valid = evaluateRepositoryHelper(ACCESSES_GROUND_TRUTH, ACCESSES_RESULTS,
                                                                     accesses[access],
                                                                     (r.accessedMethods & 0b1000) >> 3, 0) and valid
                                elif access == "READ":
                                    valid = evaluateRepositoryHelper(ACCESSES_GROUND_TRUTH, ACCESSES_RESULTS,
                                                                     accesses[access],
                                                                     (r.accessedMethods & 0b0100) >> 2, 1) and valid
                                elif access == "UPDATE":
                                    valid = evaluateRepositoryHelper(ACCESSES_GROUND_TRUTH, ACCESSES_RESULTS,
                                                                     accesses[access],
                                                                     (r.accessedMethods & 0b0010) >> 1, 2) and valid
                                else:
                                    valid = evaluateRepositoryHelper(ACCESSES_GROUND_TRUTH, ACCESSES_RESULTS,
                                                                     accesses[access],
                                                                     (r.accessedMethods & 0b00001), 3) and valid
                            actualRepositories.add(r.name)
                            found = True
                            break
                    if found is not True:
                        print(f"Failed to find {repoName} in {endpoint.name}")
                        valid = False
            else:
                print(f"Failed to find endpoint for {func}")
                valid = False

    valid = (len(actualRepositories) == len(expectedRepositories)) and valid

    print(f"Actual repository count: {len(actualRepositories)}")
    print(f"Expected repository count: {len(expectedRepositories)}")
    print(f"Actual repository accesses: {ACCESSES_RESULTS}")
    print(f"Expected repository accesses: {ACCESSES_GROUND_TRUTH}")

    if valid is True:
        print("VALIDATED: repositories!")
    else:
        print("INVALIDATED: repositories!")

    return valid


def evaluateEndpointRoles(path: str):
    valid = True

    with open(path + "/ground_truth_endpoint_roles.json", "r") as groundTruthFile:
        groundTruth = json.load(groundTruthFile)
        expectedCount = len(groundTruth)
        actualCount = 0
        correctCount = 0
        for key, value in groundTruth.items():
            end = msSystem.findEndpoint(replaceRequestVariables(key))
            if end is not None:
                roleBitstring = roleNamesToBitstring(value)
                if roleBitstring == end.allowedRoles:
                    correctCount += 1
                else:
                    print(f"{end.name}: Got {end.allowedRoles} role bitstring, expected {roleBitstring}")
                actualCount += 1

        print(f"Verified {actualCount} endpoints for roles")
        print(f"Expected correct endpoints for roles: {expectedCount}")
        print(f"Actual correct endpoints for roles: {correctCount}")

        valid = (actualCount == expectedCount and expectedCount == correctCount) and valid

        if valid is True:
            print("VALIDATED: endpoint roles!")
            return True
        else:
            print("INVALIDATED: endpoint roles!")
            return False


def evaluateEndpoints(system: MicroserviceSystem, path: str):
    expectedEndpointCount = 0
    actualEndpointCount = 0
    foundEndpointCount = 0
    valid = True
    with open(path + "/ground_truth_CRUD_permissions.json", "r") as groundTruthFile:
        groundTruth = json.load(groundTruthFile)
        for func in groundTruth:
            endpoint = system.findEndpointByFuncName(func)
            if endpoint is not None:
                foundEndpointCount += 1
            else:
                valid = False
            expectedEndpointCount += 1
    for m in system.microservices:
        for _ in m.endpoints:
            actualEndpointCount += 1
    if expectedEndpointCount != actualEndpointCount:
        valid = False
    if expectedEndpointCount != foundEndpointCount:
        valid = False

    print(f"Expected endpoints found: {expectedEndpointCount}")
    print(f"Actual endpoints found: {actualEndpointCount}")
    print(f"Found endpoints found: {foundEndpointCount}")

    if valid is True:
        print("VALIDATED: endpoint counts!")
    else:
        print("INVALIDATED: endpoint counts!")

    return valid


def evaluateSystemRoles(system: MicroserviceSystem):
    valid = len(system.systemRoles) == 3
    try:
        valid = valid and system.systemRoles[1] == "UnauthenticatedRole"
        valid = valid and system.systemRoles[2] == "user"
        valid = valid and system.systemRoles[4] == "admin"
    except KeyError:
        valid = False
    if valid is True:
        print("VALIDATED: system roles!")
        return True
    else:
        print("INVALIDATED: system roles!")
        return False


def evaluateSystemConnections(system: MicroserviceSystem, path: str):
    valid = True
    foundConnections = 0
    expectedConnections = 0
    actualConnections = 0

    with open(path + "/ground_truth_system_connections.json", "r") as groundTruthFile:
        groundTruth = json.load(groundTruthFile)
        services = groundTruth["services"]

        connections = []

        for service in services:
            for call in service["calls"]:
                for initiator in call["from"]:
                    connections.append((replaceRequestVariables(initiator),
                                        replaceRequestVariables(call["method"] + " " + call["endpoint"])))
                    expectedConnections += 1

        for connection in connections:
            # This called endpoint doesn't actually exist
            if (connection[1] == "POST /api/v1/orderservice/order/{?}"
                    or connection[1] == "POST /api/v1/orderOtherService/orderOther/{?}"):
                expectedConnections -= 1
                continue

            endpoint = system.findEndpoint(connection[0])
            if endpoint is None:
                valid = False
                print(f"Failed to find initial endpoint {connection[0]}")
            else:
                found = False
                for e2, conns in system.systemConnections.connectionMap.items():
                    if e2 == endpoint:
                        for conn in conns:
                            if conn.name == connection[1]:
                                found = True
                                break
                if found is False:
                    print(f"Failed to find final endpoint {connection[1]}.")
                    valid = False
                else:
                    foundConnections += 1

        for connections in system.systemConnections.connectionMap.values():
            actualConnections += len(connections)

        valid = (foundConnections == expectedConnections and foundConnections == actualConnections) and valid

        print(f"Actual connections: {actualConnections}")
        print(f"Expected connections: {expectedConnections}")
        print(f"Found connections: {foundConnections}")

    if valid is True:
        print("VALIDATED: system connections!")
        return True
    else:
        print("INVALIDATED: system connections!")
        return False


def evaluateMicroservices(system: MicroserviceSystem):
    if len(system.microservices) == 41:
        print("VALIDATED: microservice counts!")
        return True
    else:
        print("INVALIDATED: microservice counts!")
        return False


def evaluateSystemModel(system: MicroserviceSystem, path: str):
    # Scope: microservice system
    valid = True
    valid = evaluateSystemConnections(system, path) and valid
    valid = evaluateSystemRoles(system) and valid

    # Scope: microservices
    valid = evaluateMicroservices(system) and valid

    # Scope: endpoints
    valid = evaluateEndpoints(system, path) and valid
    valid = evaluateEndpointRoles(path) and valid

    # Scope: repositories
    valid = evaluateRepositories(system, path) and valid

    if valid is True:
        print("VALIDATED: microservice system!")
    else:
        print("INVALIDATED: microservice system!")
    return valid


if __name__ == "__main__":
    msSystem, _ = readCommandLineArgs(sys.argv)

    # Evaluation of system model
    evaluateSystemModel(msSystem, "data/validation")

