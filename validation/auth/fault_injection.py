# fault_injection.py
# 3 October 2025

import random

from z3 import *

from src.solvers.auth_solver import AuthorizationConsistencySolver
from src.ms_system import MicroserviceSystem, modelFromJSON, modelToJSON

def generateFaultInjectedSystem(msSystemFixed: MicroserviceSystem, numFaults: int, faultType: str) -> tuple[MicroserviceSystem, str]:
    msSystem = copy.deepcopy(msSystemFixed)

    # Keep log for readability
    log = ""

    # Prepare aspects for random selection
    endpoints = []
    dataEntities = []

    permittedRoles = list(range(0, int(math.pow(2, len(msSystem.systemRoles)))))
    permittedOperations = list(range(0, int(math.pow(2, 4))))  # 4 for create, read, update, delete

    for microservice in msSystem.microservices:
        for endpoint in microservice.endpoints:
            endpoints.append(endpoint)
            for de in endpoint.repositories:
                dataEntities.append(de)

    # Inject faults
    match faultType:
        case "permittedRole":
            sample = random.sample(endpoints, numFaults)
            for e in sample:
                pr = copy.deepcopy(permittedRoles)
                pr.remove(e.allowedRoles)
                prev = e.allowedRoles
                e.allowedRoles = random.choice(pr)
                log += f"Endpoint authorized roles for {e.name} changed from {prev} => {e.allowedRoles}.\n"
        case "dataOperation":
            sample = random.sample(dataEntities, numFaults)
            for d in sample:
                po = copy.deepcopy(permittedOperations)
                po.remove(d.accessedMethods)
                prev = d.accessedMethods
                pr = copy.deepcopy(permittedRoles)
                pr.remove(d.parent.allowedRoles)
                prev2 = d.parent.allowedRoles
                d.accessedMethods = random.choice(po)
                d.parent.allowedRoles = random.choice(pr)
                log += f"Data operation on {d.name} in {d.parent.name} was changed from {prev} => {d.accessedMethods}.\n"
                log += f"Endpoint authorized roles for {d.parent.name} changed from {prev2} => {d.parent.allowedRoles}.\n"
        case "remoteCall":
            sample = random.sample(endpoints, numFaults)
            for fromEndpoint in sample:
                otherEndpoints = list(endpoints)
                if fromEndpoint in msSystem.systemConnections.connectionMap:
                    for e in msSystem.systemConnections.connectionMap[fromEndpoint]:
                        otherEndpoints.remove(e)
                for e in fromEndpoint.parent.endpoints:
                    otherEndpoints.remove(e)
                otherEndpoints = [e for e in otherEndpoints if fromEndpoint.allowedRoles & e.allowedRoles != fromEndpoint.allowedRoles]
                newConn = random.choice(otherEndpoints)
                msSystem.systemConnections.addSystemConnection(fromEndpoint, newConn)
                log += f"System connection from {fromEndpoint.name} => {newConn.name} was added.\n"

    return (msSystem, log)


def verifySystem(msSystem: MicroserviceSystem) -> str:
    # Keep log for readability
    log = ""

    # Perform formal methods
    s = AuthorizationConsistencySolver(msSystem)

    s.addAtLeastOnePermittedRoleConstraints()
    s.addEndpointPermittedRoleConstraints()
    s.addDataEntityOperationConsistencyConstraints()

    # Verifier
    log += "Is system satisfiable? "
    satisfiable = s.buildVerifier().check()
    log += str(satisfiable) + "\n"

    # Optimizer
    log += "Applying optimizer... "
    opt = s.buildOptimizer()
    log += str(opt.check()) + "\n"

    # Model Changes
    log += "\nSUGGESTIONS\n"
    if opt.check() == sat:
        model = opt.model()

        for r in model.decls():
            temp = r.name()
            temp = temp.replace("_permittedRoles", "")
            if (model[r].as_long() != msSystem.findEndpoint(temp).allowedRoles):
                log += f"{r.name()} = {model[r]}\n"
    
    return log


if __name__ == "__main__":
    msSystemFixed = modelFromJSON("data/system-models/train-ticket-auth-fixed.json")
    baseStoragePath = "data/auth_fault_injection/"

    # Test regimen
    # permittedRole, 1 fault => 3 instances
    # permittedRole, 2 fault => 3 instances
    # permittedRole, 3 fault => 3 instances
    # dataOperation, 1 fault => 3 instances
    # dataOperation, 2 fault => 3 instances
    # dataOperation, 3 fault => 3 instances
    # remoteCall, 1 fault => 3 instances
    # remoteCall, 2 fault => 3 instances
    # remoteCall, 3 fault => 3 instances
    # permittedRole + dataOperation + remoteCall, 1 fault of each => 3 instances
    # 30 instances total

    try:
        print("Generating tests...")
        faultTypes = ["permittedRole", "dataOperation", "remoteCall"]
        for i in range(1, 4):
            for j in range(3):
                for k in range(3):
                    faultSystem, log = generateFaultInjectedSystem(msSystemFixed, i, faultTypes[j])
                    modelToJSON(f"{baseStoragePath}/models/{i}_fault_{faultTypes[j]}_{k}.json", faultSystem)
                    with open(f"{baseStoragePath}/logs/{i}_fault_{faultTypes[j]}_{k}.txt", "w") as f:
                        f.write(log)
                    log2 = verifySystem(faultSystem)
                    with open(f"{baseStoragePath}/changes/{i}_fault_{faultTypes[j]}_{k}.txt", "w") as f:
                        f.write(log2)
                    print(f"{i}_fault_{faultTypes[j]}_{k} has been generated.")
                    
        for i in range(3):
            system = msSystemFixed
            log = ""
            for j in range(3):
                system1, log1 = generateFaultInjectedSystem(system, 1, faultTypes[j])
                system = system1
                log += log1
            modelToJSON(f"{baseStoragePath}/models/3_fault_multi_{i}.json", system)
            with open(f"{baseStoragePath}/logs/3_fault_multi_{i}.txt", "w") as f:
                f.write(log)
            log2 = verifySystem(system)
            with open(f"{baseStoragePath}/changes/3_fault_multi_{i}.txt", "w") as f:
                f.write(log2)
            print(f"3_fault_multi_{i} has been generated.")

        print("Test suite creation complete. Exiting...")
    except Exception as e:
        print(e)
