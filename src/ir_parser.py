# ir_parser.py
# 7 March 2025

from src.ms_system import *

import json
import collections
from pathlib import Path
from itertools import chain
import re


def rolesAlreadySet(endpoint):
    return endpoint.allowedRoles != 0 or endpoint._allowAllRoles is True


def addRoleToSystemRoles(systemRoles, roleName, ret=True):
    if roleName not in systemRoles.values():
        idx = 0
        while True:
            a = int(math.pow(2, idx))
            idx += 1
            if a in systemRoles:
                continue
            systemRoles[a] = roleName
            return a
    elif ret is True:
        for key, value in systemRoles.items():
            if value == roleName:
                return key


def findEndpointFromURL(fullIR, url):
    endpoint = None
    endpointMSIR = None
    for ms in fullIR["microservices"]:
        for controller in ms["controllers"]:
            for method in controller["methods"]:
                if method["type"] == "Endpoint":
                    for annotation in method["annotations"]:
                        for attribute in annotation["attributes"]:
                            if attribute == "path":
                                if attribute["path"] == url:
                                    endpoint = method
                                    endpointMSIR = ms
                                    break
    return endpoint, endpointMSIR


def findClassInMicroservice(msIR, className, classLocation=None):
    if classLocation is None:
        ret = findClassInMicroservice(msIR, className, "controllers")
        if ret is None:
            ret = findClassInMicroservice(msIR, className, "services")
            if ret is None:
                ret = findClassInMicroservice(msIR, className, "repositories")
                if ret is None:
                    ret = findClassInMicroservice(msIR, className, "entities")
                    if ret is None:
                        ret = findClassInMicroservice(msIR, className, "feignClients")
        return ret
    else:
        theClass = None
        for cls in msIR[classLocation]:
            # Note that some services have interface implementations, so look for those using .contains()
            if className == cls["name"] or className + "Impl" == cls["name"]:
                if classLocation == "services" and cls["fileType"] != "JCLASS":
                    continue
                theClass = cls
                break
        return theClass


def findMethodInClass(classIR, methodName):
    met = None
    for method in classIR["methods"]:
        if method["name"] == methodName:
            met = method
            break
    return met


def findMethodCallsFromMethod(classIR, methodName, requireEndpoint=False):
    mcs = []
    for methodCall in classIR["methodCalls"]:
        if methodCall["calledFrom"] == methodName:
            if requireEndpoint and methodCall["type"] != "Endpoint":
                continue
            mcs.append(methodCall)
    return mcs


def scanRestCalls(msIR, methodIR, scg, microserviceSystem):
    toScan = collections.deque()
    toScan.append(methodIR)
    visited = []

    theURL = methodIR["url"]
    theRequestMethod = methodIR["httpMethod"]
    if theURL is None or theRequestMethod is None:
        return

    while len(toScan) != 0:
        method = toScan.pop()

        if method in visited:
            continue
        else:
            visited.append(method)

        className = method["className"]
        theClass = findClassInMicroservice(msIR, className)
        if theClass is not None:
            methodCalls = findMethodCallsFromMethod(theClass, method["name"])
            for methodCall in methodCalls:
                if methodCall["calledFrom"] != method["name"]:
                    continue
                if methodCall["type"] == "RestCall":
                    endpointFrom = microserviceSystem.findEndpoint(f"{theRequestMethod} {theURL}")
                    if endpointFrom is None:
                        print(f"Invalid from endpoint: {theRequestMethod} {theURL}")
                        continue
                    endpointTo = microserviceSystem.findEndpoint(f"{methodCall["httpMethod"]} {methodCall["url"]}")
                    if endpointTo is None:
                        if "{?}" in methodCall["url"]:
                            firstParameter = methodCall["parameterContents"].split(",")[0]
                            for fie in theClass["fields"]:
                                if fie["name"] in firstParameter:
                                    constPieces = re.findall(r"\"(.+)\"", firstParameter)
                                    sub = ""
                                    candidatePart = fie["initializer"].replace("\"", "")
                                    candidatePart = re.sub(r'http[s]?://[^/]+', "", candidatePart)
                                    candidateURL = ""
                                    for c in firstParameter:
                                        sub += c
                                        if sub.find(fie["name"]) != -1:
                                            candidateURL += candidatePart
                                            sub = sub.replace(fie["name"], "")
                                        for piece in constPieces:
                                            if sub.find(piece) != -1:
                                                candidateURL += piece
                                                sub = sub.replace(piece, "")
                                    if len(sub) != 0:
                                        candidateURL += "{?}"

                                    endpointTo = microserviceSystem.findEndpoint(
                                        f"{methodCall["httpMethod"]} {candidateURL}")
                                    if endpointTo is None:
                                        print(f"Invalid to endpoint: {methodCall["httpMethod"]} {methodCall["url"]}")
                                        print(theClass)
                                        break
                                    else:
                                        break
                    if endpointFrom is None or endpointTo is None:
                        continue
                    if endpointFrom in scg.connectionMap and endpointTo in scg.connectionMap[endpointFrom]:
                        continue
                    scg.addSystemConnection(endpointFrom, endpointTo)
                    continue

                nextMethodName = methodCall["name"]
                className = methodCall["objectType"]
                if className != "":
                    nextClass = findClassInMicroservice(msIR, className)
                else:
                    nextClass = theClass
                if nextClass is not None:
                    nextMethod = findMethodInClass(nextClass, nextMethodName)
                    if nextMethod is not None:
                        toScan.append(nextMethod)


def parseRepositoryHelper(repositories, repo, bits):
    for r in repositories:
        if r.name == repo["name"]:
            r.accessedMethods |= bits
            return
    repositories.append(Repository(bits, repo["name"]))
    return


def parseRepository(mcIR, repositories, originalMethod, repo):
    createUpdateWords = ["create", "add", "insert", "save", "update"]
    readWords = ["read", "find", "get", "query"]
    deleteWords = ["delete", "remove"]

    if any(keyword in mcIR["name"] for keyword in createUpdateWords):
        if originalMethod == "POST":
            parseRepositoryHelper(repositories, repo, 0b1000)
        else:
            parseRepositoryHelper(repositories, repo, 0b0010)
    elif any(keyword in mcIR["name"] for keyword in readWords):
        parseRepositoryHelper(repositories, repo, 0b0100)
    elif any(keyword in mcIR["name"] for keyword in deleteWords):
        parseRepositoryHelper(repositories, repo, 0b0001)


def parseServiceRecursively(msIR, parentMC, serv, repositories, originalMethod):
    if parentMC["objectName"] != "":
        repo = findClassInMicroservice(msIR, parentMC["objectType"], "repositories")
        if repo is not None:
            parseRepository(parentMC, repositories, originalMethod, repo)
        return
    for mc in serv["methodCalls"]:
        if mc["calledFrom"] == parentMC["name"] and mc["name"] != parentMC["name"]:
            repo = findClassInMicroservice(msIR, mc["objectType"], "repositories")
            if repo is not None:
                parseRepository(mc, repositories, originalMethod, repo)
            parseServiceRecursively(msIR, mc, serv, repositories, originalMethod)


def parseService(msIR, mcIR, originalMethod):
    serv = findClassInMicroservice(msIR, mcIR["objectType"], "services")
    if serv is None:
        return []

    met = findMethodInClass(serv, mcIR["name"])
    if met is None:
        return []

    repositories = []
    for methodCall in serv["methodCalls"]:
        if methodCall["calledFrom"] == met["name"]:
            parseServiceRecursively(msIR, methodCall, serv, repositories, originalMethod)

    return repositories


def parseEndpoint(msIR, controllerIR, endpointIR):
    endpoint = Endpoint([], 0, f"{endpointIR["httpMethod"]} {endpointIR["url"]}",
                        funcName=endpointIR["packageName"] + "." + endpointIR["className"] + "#" + endpointIR["name"])

    repoTracker = {}

    for methodCall in controllerIR["methodCalls"]:
        if methodCall["calledFrom"] == endpoint.funcName[endpoint.funcName.rfind("#") + 1:]:
            repositories = parseService(msIR, methodCall, endpointIR["httpMethod"])
            for repository in repositories:
                if repository.name in repoTracker:
                    repoTracker[repository.name].accessedMethods |= repository.accessedMethods
                else:
                    repoTracker[repository.name] = repository
                    endpoint.repositories.append(repository)

    return endpoint


def parseMicroservice(msIR):
    microservice = Microservice([], msIR["name"])

    for controller in msIR["controllers"]:
        for method in controller["methods"]:
            if method["type"] == "Endpoint":
                microservice.endpoints.append(parseEndpoint(msIR, controller, method))

    return microservice


def parseConnections(msIR, scg, microserviceSystem):
    for controller in msIR["controllers"]:
        for method in controller["methods"]:
            if method["type"] == "Endpoint":
                scanRestCalls(msIR, method, scg, microserviceSystem)


def getSecurityRoles(systemRoles, msIR, msSystem, codePath):
    msPath = codePath + msIR["path"]
    for path in chain(Path(msPath).rglob("SecurityConfig.java"), Path(msPath).rglob("WebSecurityConfig.java")):
        if path.is_file() and "config" in str(path):
            with open(path, 'r', encoding="utf-8") as f:
                securityConfig = f.read()
                pattern = r"""\.antMatchers\((.*?)\)\.hasRole\(\"(.*?)\"\)|\.antMatchers\((.*?)\)\.hasAnyRole\((.*?)\)|\.antMatchers\((.*?)\)\.permitAll\(\)|\.(.*?)\.authenticated\(\)"""
                matches = re.findall(pattern, securityConfig)

                authenticated = False
                for match in matches:
                    # hasRole
                    if match[0] and match[1]:
                        roleName = match[1].lower().replace("\"", "").replace(" ", "")
                        roleBitVec = addRoleToSystemRoles(systemRoles, roleName)
                        addRoleToSystemRoles(systemRoles, roleName)
                        if "HttpMethod." in match[0]:
                            methodBased = re.findall("HttpMethod.(.*), (.*)", match[0])
                            for metRule in methodBased:
                                url = metRule[1].replace("\"", "")
                                httpMethod = metRule[0]
                                if "**" in url[-2]:
                                    url = url.replace("*", "")
                                    endpoints = msSystem.findAllEndpointsWithGenericPath(httpMethod + ' ' + url)
                                else:
                                    url = url.replace("*", "{?}")
                                    endpoints = msSystem.findEndpoint(httpMethod + ' ' + url)
                                    if endpoints is not None:
                                        endpoints = [endpoints]
                                    else:
                                        endpoints = []
                                for endpoint in endpoints:
                                    if not rolesAlreadySet(endpoint):
                                        endpoint.allowedRoles |= roleBitVec
                        else:
                            urls = match[0].replace("\"", "").split(",")
                            for url in urls:
                                endpoints = msSystem.findAllEndpointsWithGenericPath(url)
                                for endpoint in endpoints:
                                    if not rolesAlreadySet(endpoint):
                                        endpoint.allowedRoles |= roleBitVec
                    # hasAnyRole
                    elif match[2] and match[3]:
                        roles = match[3].lower().replace("\"", "").replace(" ", "").split(",")
                        if "HttpMethod." in match[2]:
                            methodBased = re.findall("HttpMethod.(.*), (.*)", match[2])
                            for metRule in methodBased:
                                url = metRule[1].replace("\"", "")
                                httpMethod = metRule[0]
                                if "**" in url[-2]:
                                    url = url.replace("*", "")
                                    endpoints = msSystem.findAllEndpointsWithGenericPath(httpMethod + ' ' + url)
                                else:
                                    url = url.replace("*", "{?}")
                                    endpoints = msSystem.findEndpoint(httpMethod + ' ' + url)
                                    if endpoints is not None:
                                        endpoints = [endpoints]
                                    else:
                                        endpoints = []
                                for endpoint in endpoints:
                                    if not rolesAlreadySet(endpoint):
                                        for roleName in roles:
                                            roleBitVec = addRoleToSystemRoles(systemRoles, roleName)
                                            endpoint.allowedRoles |= roleBitVec
                        else:
                            urls = match[2].replace("\"", "").split(",")
                            for url in urls:
                                endpoints = msSystem.findAllEndpointsWithGenericPath(url)
                                for endpoint in endpoints:
                                    if not rolesAlreadySet(endpoint):
                                        for roleName in roles:
                                            roleBitVec = addRoleToSystemRoles(systemRoles, roleName)
                                            endpoint.allowedRoles |= roleBitVec
                    # permitAll
                    elif match[4]:
                        rule = match[4]
                        if "HttpMethod." in rule:
                            methodBased = re.findall("HttpMethod.(.*), (.*)", rule)
                            for metRule in methodBased:
                                url = metRule[1].replace("\"", "")
                                httpMethod = metRule[0]
                                if "**" in url[-2]:
                                    url = url.replace("*", "")
                                    endpoints = msSystem.findAllEndpointsWithGenericPath(httpMethod + ' ' + url)
                                else:
                                    url = url.replace("*", "{?}")
                                    endpoints = msSystem.findEndpoint(httpMethod + ' ' + url)
                                    if endpoints is not None:
                                        endpoints = [endpoints]
                                    else:
                                        endpoints = []
                                for endpoint in endpoints:
                                    if not rolesAlreadySet(endpoint):
                                        endpoint._allowAllRoles = True
                                        for role in msSystem.systemRoles:
                                            endpoint.allowedRoles |= role
                        else:
                            urls = rule.replace("\"", "").split(",")
                            for url in urls:
                                endpoints = msSystem.findAllEndpointsWithGenericPath(url, msName=msIR["name"])
                                for endpoint in endpoints:
                                    if not rolesAlreadySet(endpoint):
                                        endpoint._allowAllRoles = True
                                        for role in msSystem.systemRoles:
                                            endpoint.allowedRoles |= role
                            pass
                    # authenticated
                    elif match[5]:
                        authenticated = True

                if authenticated is False:
                    for ms in msSystem.microservices:
                        if ms.name == msIR["name"]:
                            for endpoint in ms.endpoints:
                                if not rolesAlreadySet:
                                    for role in msSystem.systemRoles:
                                        endpoint.allowedRoles |= role
                            break
                else:
                    for ms in msSystem.microservices:
                        if ms.name == msIR["name"]:
                            for endpoint in ms.endpoints:
                                if not rolesAlreadySet(endpoint):
                                    for roleVec, roleName in systemRoles.items():
                                        if roleName == "UnauthenticatedRole":
                                            continue
                                        endpoint.allowedRoles |= roleVec
                            break


def preScanRoles(systemRoles, msIR, codePath):
    msPath = codePath + msIR["path"]
    for path in chain(Path(msPath).rglob("SecurityConfig.java"), Path(msPath).rglob("WebSecurityConfig.java")):
        if path.is_file() and "config" in str(path):
            with open(path, 'r', encoding="utf-8") as f:
                securityConfig = f.read()
                pattern = r"""\.antMatchers\((.*?)\)\.hasRole\(\"(.*?)\"\)|\.antMatchers\((.*?)\)\.hasAnyRole\((.*?)\)|\.antMatchers\((.*?)\)\.permitAll\(\)|\.(.*?)\.authenticated\(\)"""
                matches = re.findall(pattern, securityConfig)

                for match in matches:
                    # hasRole
                    if match[0] and match[1]:
                        roleName = match[1].lower().replace("\"", "").replace(" ", "")
                        addRoleToSystemRoles(systemRoles, roleName, False)
                    # hasAnyRole
                    elif match[2] and match[3]:
                        roles = match[3].lower().replace("\"", "").replace(" ", "").split(",")
                        for roleName in roles:
                            addRoleToSystemRoles(systemRoles, roleName, False)


def getModelFromIRAndCode(pathToIR, pathToCode):
    # Prepare system connection graph
    scg = SystemConnectionGraph()

    # Prepare system roles
    sysRoles = {}
    addRoleToSystemRoles(sysRoles, "UnauthenticatedRole")

    # Prepare microservice system
    msSystem = MicroserviceSystem([], scg, "", sysRoles)

    with (open(pathToIR, 'r') as fileIR):
        ir = json.load(fileIR)
        msSystem.name = ir["name"]

        for ms in ir["microservices"]:
            msSystem.microservices.append(parseMicroservice(ms))
        for ms in ir["microservices"]:
            parseConnections(ms, scg, msSystem)
        for ms in ir["microservices"]:
            preScanRoles(sysRoles, ms, pathToCode)

        # Not required, but easier on our eyes for case study: flip around which bits represent admin and user
        # user: is 0b100 right now, want to be 0b010
        # admin is 0b010 right now, want to be 0b100
        # Thus bits go from most privilege to least: admin => user => UnauthenticatedRole. Not necessary for methodology, but personal preference for manual analysis
        if 2 in sysRoles and 4 in sysRoles and sysRoles[4] == "user" and sysRoles[2] == "admin":
            sysRoles[2] = "user"
            sysRoles[4] = "admin"

        for ms in ir["microservices"]:
            getSecurityRoles(sysRoles, ms, msSystem, pathToCode)

        msSystem.populateBackReferences()

    return msSystem
