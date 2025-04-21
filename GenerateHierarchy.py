import os
import logging
import subprocess
import json
import time

from EnvVariables import UnifiedLog as UnifiedLog
from EnvVariables import GAV2AVForm
from EnvVariables import timeout


LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
logging.basicConfig(filename=UnifiedLog, level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)

class GenerateHierarchy:

    @timeout(300)                   
    def run(self, DownloadRoot, AnalysisList, SootMainName, DependencyFiles, OutputRoot, mode = "list", return_time = False, reGen = False):

        jar_file_address_list = []
        for item in AnalysisList:
            add = os.path.join(DownloadRoot, GAV2AVForm(item) + ".jar")
            jar_file_address_list.append(add)

        for i in range(0, len(jar_file_address_list)):

            possibleFilePos = OutputRoot + GAV2AVForm(AnalysisList[i]) + "-HierarchyInfo.json" 
            if os.path.isfile(possibleFilePos) and not reGen:
                print("GAV = " + AnalysisList[i] + " Generate Already Hierarchy" +" at " + possibleFilePos)
            
            else:
                print("\n[now generate Hier for ] " + jar_file_address_list[i])

                command = ['java', '-cp', f'{DependencyFiles}:.', SootMainName, jar_file_address_list[i], possibleFilePos]
                
                time0 = time.time()
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                time1 = time.time()

                #print(result.stdout)
                print(result.stderr)

                if result.returncode != 0:
                    print("GAV = " + AnalysisList[i] + f" Generate Exception code = {result.returncode}")
                    return 1

                # Reorganize outputs
                classes = {}
                with open(possibleFilePos, 'r') as file:
                    for line in file:
                        line = line.strip()
                        if line.startswith("Class:"):
                            current_class = line.split(":")[1].strip()
                            classes[current_class] = {"Subclasses": [], "Superclasses": [], "Implements": [], "Superinterfaces": [], "Subinterfaces": [], "Implementers": []}
                        elif line.startswith("Subclasses:"):
                            subclass = line.split(":")[1].strip()
                            classes[current_class]["Subclasses"].append(subclass)
                        elif line.startswith("Superclasses:"):
                            superclass = line.split(":")[1].strip()
                            classes[current_class]["Superclasses"].append(superclass)
                        elif line.startswith("Implements:"):
                            superclass = line.split(":")[1].strip()
                            classes[current_class]["Implements"].append(superclass)
                        elif line.startswith("Superinterfaces:"):
                            superclass = line.split(":")[1].strip()
                            classes[current_class]["Superinterfaces"].append(superclass)
                        elif line.startswith("Subinterfaces:"):
                            superclass = line.split(":")[1].strip()
                            classes[current_class]["Subinterfaces"].append(superclass)
                        elif line.startswith("Implementers:"):
                            superclass = line.split(":")[1].strip()
                            classes[current_class]["Implementers"].append(superclass)

                for key,value in classes.items():
                    if len(value["Superclasses"]) > 0:
                        for item in value["Superclasses"]:
                            if item in classes:
                                classes[key]["Implements"] += classes[item]["Implements"]
                    classes[key]["Implements"] = list(set(classes[key]["Implements"]))

                json_output = json.dumps(classes, indent=4)
                with open(possibleFilePos, 'w') as output_file:
                    output_file.write(json_output)

        if return_time:
            return time1-time0

        return 0