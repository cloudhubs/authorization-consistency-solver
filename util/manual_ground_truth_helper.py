# manual_ground_truth.py
# 24 March 2025

import sys
import json

with open("data/validation/ground_truth_system_connections.json", "r") as file:
    with open("data/validation/ground_truth_endpoint_roles.json", "w") as outputFile:
        data = json.load(file)["services"]

        outputFile.write("{\n")

        print("Data loaded.")
        i = 0
        for serv in data:
            i += 1
            print(f"{i}/{len(data)}")
            for endpoint in serv["endpoints"]:
                print(endpoint["method"] + " " + endpoint["name"])
                outputFile.write("\"" + endpoint["method"] + " " + endpoint["name"] + "\": ")
                roles = input("Type the permitted roles for this endpoint (i.e., [\"admin\", \"user\"]):")
                if roles == "QUIT":
                    sys.exit(0)
                outputFile.write(roles + ",\n")
                print("\n")

        outputFile.write("}\n")
