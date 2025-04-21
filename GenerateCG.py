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

class GenerateCG:

    @timeout(500)                   
    def run(self, DownloadRoot, AnalysisList, SootMainName, DependencyFiles, OutputRoot, mode = "list", reGen = False, wholeCG = False, enable_merge = True, return_time = False):

        jar_file_address_list = []
        for item in AnalysisList:
            add = os.path.join(DownloadRoot, GAV2AVForm(item) + ".jar")
            jar_file_address_list.append(add)

        for i in range(0, len(jar_file_address_list)):

            possibleFilePos = OutputRoot + GAV2AVForm(AnalysisList[i]) + "-PkgInfo.json" 
            if wholeCG:
                possibleFilePos = OutputRoot + GAV2AVForm(AnalysisList[i]) + "-PkgInfo-WholeCG.txt" 

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
                    return 1