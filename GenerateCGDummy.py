import os
import subprocess
import json
import time

from EnvVariables import UnifiedLog as UnifiedLog
from EnvVariables import GAV2AVForm

    
def generateCG(args):
    DownloadRoot, AnalysisList, SootMainName, DependencyFiles, OutputRoot, enable_merge, return_time, reGen = args

    jar_file_address_list = []
    for item in AnalysisList:
        add = os.path.join(DownloadRoot, GAV2AVForm(item) + ".jar")
        jar_file_address_list.append(add)

    for i in range(0, len(jar_file_address_list)):

        possibleFilePos = OutputRoot + GAV2AVForm(AnalysisList[i]) + "-PkgInfo.json"

        if os.path.isfile(possibleFilePos) and (reGen == False):
            print("GAV = " + AnalysisList[i] + " Generate Already " +" at " + possibleFilePos)
            return 0
        
        else:
            print("\n[now generate CG for ] " + jar_file_address_list[i])

            command = ['java', '-cp', f'{DependencyFiles}:.', SootMainName, jar_file_address_list[i], OutputRoot, AnalysisList[i]]
            
            time0 = time.time()
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time1 = time.time()
            print("generate json done, begin output")

            # print(result.stdout)
            print(result.stderr)

            # if we have multiple output file, we merge it into one file
            if enable_merge:
                if (result.returncode == 0 and (not os.path.exists(possibleFilePos))) or ((reGen == True)):
                    part_files = []
                    for file_index in range(0, 100):
                        guess_path = possibleFilePos.replace("PkgInfo.json", "PkgInfo-" + str(file_index) + ".json")
                        if os.path.exists(guess_path):
                            part_files.append(guess_path)
                        else:
                            print("get ", str(file_index), "files")
                            break
                    
                    entrance_list_merge = []
                    data = None
                    for file in part_files:
                        with open(file, 'r') as f:
                            data = json.load(f)
                            entrance_list = data['EntranceList']
                            entrance_list_merge.extend(entrance_list)
                        print("done parse " + file)
                    data['EntranceList'] = entrance_list_merge
                    
                    with open(possibleFilePos, 'w') as f:
                        json.dump(data, f, indent=4)
                    print("done output merge " + possibleFilePos)

                    for file in part_files:
                        os.remove(file)
                        print("remove "+file)

            if result.returncode == 0:
                print("GAV = " + AnalysisList[i] + " Generate Success" +" at " + possibleFilePos)
                if return_time:
                    return time1-time0
                return 0
            else:
                print("GAV = " + AnalysisList[i] + f" Generate Exception code = {result.returncode}")
                return -1
              
        
def generateHier(args):
    
    DownloadRoot, AnalysisList, SootMainName, DependencyFiles, OutputRoot, return_time, reGen = args

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
                return -1

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
  
  
def build_cg_without_dep(args):
  
    startGAV, inputFilePath, outputDirPath, SootMainName, DependencyFiles, reGen = args

    possibleFilePos = outputDirPath + GAV2AVForm(startGAV) + "-PkgInfo-sootcg-partial.txt"
    #print(f"possibleFilePos = {possibleFilePos}")
    
    if os.path.isfile(possibleFilePos) and not reGen:
        print(f"alreay generated cg {possibleFilePos}")
        return 0
    
    else:
        print("\n[now generate Partial All CG for ] " + inputFilePath)
        output_file_name = GAV2AVForm(startGAV) + "-PkgInfo-sootcg-partial.txt"

        command = ['java', '-cp', f'{DependencyFiles}:.', SootMainName, inputFilePath, outputDirPath, output_file_name, "direct_use_given_name"]
        time0 = time.time()
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time1 = time.time()

        print(result.stdout)
        print(result.stderr)
        
        if result.returncode != 0:
            print("GAV = " + inputFilePath + f" Generate Exception code = {result.returncode}")
            return -1
        
    # clean format
    with open(possibleFilePos, 'r') as file:
        lines = file.readlines()
    new_lines = []
    for line in lines:
        if ' in ' in line:
            index = line.index(' in ')
            new_line = line[index+4:]
        else:
            new_line = line
        new_lines.append(new_line)

    with open(possibleFilePos, 'w') as file:
        for line in new_lines:
            file.write(line)
    print(f"generate partial cg at {possibleFilePos}")

    return time1-time0

# chose to generate flatcg, hierinfo, traditionalcg
def chose_to_generate(args):
  if args[0] == 'flatcg':
    generateCG(args[1:])
  elif args[0] == 'hier':
    generateHier(args[1:])
  elif args[0] == 'traditional_partial':
    build_cg_without_dep(args[1:])