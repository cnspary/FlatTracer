import os
import re
import json
import logging
import time

from EnvVariables import GAV2AVForm
from EnvVariables import fetchJsonData
from EnvVariables import timeout
from EnvVariables import UnifiedLog
from EnvVariables import GAV2CHACache

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
logging.basicConfig(filename=UnifiedLog, level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)

def convert_format2Paper1_function_signature(signature):
    signature = signature.replace("<", "").replace(">", "")
    segments = signature.split(" ")
    signature = segments[0] + segments[2]
    return signature
    
def convert_format2Paper2_function_signature(signature):
    #signature = signature.replace("<", "").replace(">", "")
    signature = signature[1:-1]
    segments = signature.split(" ") 
    signature = segments[0] + segments[2]
    signature = signature.replace("<", "%3C").replace(">", "%3E")
    signature = signature.split("(")[0] + "()"
    return signature

def matchMyReachableAndTargets(my_fun_sign_list, target_fun_sign_list):
    
    commonMethodNames = []
    for method in my_fun_sign_list:
        if method in target_fun_sign_list:
            commonMethodNames.append(method)
        elif convert_format2Paper1_function_signature(method) in target_fun_sign_list:
            commonMethodNames.append(method)
        elif convert_format2Paper2_function_signature(method) in target_fun_sign_list:
            commonMethodNames.append(method)
    return commonMethodNames

class JointSearch:

    def __init__(self):
        pass
    
    def writeCache(self):
        cache_file = GAV2CHACache(self.GAVChain[-1])
        with open(cache_file, 'w') as f:
            json.dump(self.cache, f, indent = 4)

    def getSelfHierJsonList(self, HierFileRoot, GAVChain, CHACacheRoot):
        self.GAVChain = GAVChain

        # load cache
        self.cache = {}
        if CHACacheRoot != "":
           with open(GAV2CHACache(GAVChain[-1]), 'r') as file:
                self.cache = json.loads(file.read())

        # read hier file
        self.HierDataList = []
        for pos in range(0,len(GAVChain)):
            try:
                self.HierDataList.append(fetchJsonData(self.getHierFile(HierFileRoot + GAV2AVForm(GAVChain[pos]))))
            except Exception as e:
                print(f"fail to find {GAVChain[pos]} {e}")
                self.HierDataList.append({})

    def getHierFile(self, filePathBase):
        return filePathBase + "-HierarchyInfo.json"

    # restore json file
    def getSelfJsonList(self, JsonFileRoot, GAVChain):
        self.JsonDataList = []
        for pos in range(0,len(GAVChain)):
            raw_json_data = fetchJsonData(self.getMatureOrNormalFile(JsonFileRoot + GAV2AVForm(GAVChain[pos])))
            new_json_data = {}
            # get GAV and basic info
            new_json_data['GAV'] = raw_json_data['GAV']
            new_json_data['PackageName'] = raw_json_data['PackageName']
            # map number to function
            map_number_2_function = {v: k for k, v in raw_json_data['AllFunctionDict'].items()}
            # restor number of EntranceAndReachableFunctions to signature
            new_EntranceAndReachableFunctions = {}
            for key, value in raw_json_data['EntranceAndReachableFunctions'].items():
                new_key = map_number_2_function[key]
                new_value = []
                for reachable in value:
                    new_value.append(map_number_2_function[reachable])
                new_EntranceAndReachableFunctions[new_key] = new_value
            new_json_data['EntranceAndReachableFunctions'] = new_EntranceAndReachableFunctions
            # get cross-pkg call & interface和virtual call
            new_CrossPackageFunctions = set()
            for number in raw_json_data['CrossPackageFunctions']:
                new_CrossPackageFunctions.add(map_number_2_function[number])
            new_InterfaceAndVirtualInvokeFunctions = set()
            for number in raw_json_data['InterfaceInvokeFunctions']:
                new_InterfaceAndVirtualInvokeFunctions.add(map_number_2_function[number])
            for number in raw_json_data['VirtualInvokeFunctions']:
                new_InterfaceAndVirtualInvokeFunctions.add(map_number_2_function[number])
            new_json_data['CrossPackageVirtualAndInterfaceInvokeFunctions'] = list(new_CrossPackageFunctions.intersection(new_InterfaceAndVirtualInvokeFunctions))
            # restore new structure
            self.JsonDataList.append(new_json_data)
        # new_json_data: GAV, PackageName, EntranceAndReachableFunctions, CrossPackageVirtualAndInterfaceInvokeFunctions
    
    def getMatureOrNormalFile(self, filePathBase):
        matureFile = filePathBase + "-PkgInfoMature.json"
        normalFile = filePathBase + "-PkgInfo.json"
        if os.path.exists(matureFile):
            return matureFile
        else:
            return normalFile

    # example: "<org.junit.rules.TemporaryFolder: org.junit.runners.model.Statement apply(org.junit.runners.model.Statement,org.junit.runner.Description)>"
    def parseClassAndMethod(self, methodSignature):
        pattern = r"<(.*?): (.*?) (.*?\(.*?\))>"
        matches = re.match(pattern, methodSignature)
        class_name = matches.group(1)
        return_type = matches.group(2)
        method = matches.group(3)
        return class_name, return_type, method

    def getSubClasses(self, hierData, sourceClass):
        if sourceClass in hierData:
            return hierData[sourceClass]['Subclasses'] + hierData[sourceClass]['Subinterfaces'] + hierData[sourceClass]['Implementers']
        else:
            return []
        
    # not include sourceMethod itself
    def getReachableWithinCG(self, jsonData, sourceMethod):

        if type(sourceMethod) is list:
            res = []
            for method in sourceMethod:
                if method in jsonData['EntranceAndReachableFunctions']:
                    #res.append(method)
                    res += jsonData['EntranceAndReachableFunctions'][method]
            return list(set(res))
        else:
            if sourceMethod in jsonData['EntranceAndReachableFunctions']:
                res = jsonData['EntranceAndReachableFunctions'][sourceMethod]
                #res.append(sourceMethod)
                return res
            else:
                return []
    
    # for cross-pkg virtual call and interface call, we use this to find all possible callee
    def findPossibleSubClassEntrance(self, hierData, jsonData, sourceMethodSignature):

        class_name, return_type, method_sig_part = self.parseClassAndMethod(sourceMethodSignature)
        subclasses = self.getSubClasses(hierData, class_name)

        sub_entrance_method_list = []
        for subclass in subclasses:
            new_method_sig = "<" + subclass + ": " + return_type + " " + method_sig_part + ">"
            if new_method_sig in jsonData['EntranceAndReachableFunctions']:
                sub_entrance_method_list.append(new_method_sig)

        return sub_entrance_method_list

    # get all entry functions in next pkg that are called by given entranceMethod in this pkg
    def findRelevantMethods(self, thisPos, nextPos, entranceMethod):
        
        thisJsonData = self.JsonDataList[thisPos]
        nextHierData = self.HierDataList[nextPos]
        nextJsonData = self.JsonDataList[nextPos]

        thisReachableList = self.getReachableWithinCG(thisJsonData, entranceMethod)

        if len(thisReachableList) == 0:
            return []

        nextEntranceList = list(nextJsonData["EntranceAndReachableFunctions"].keys())
    
        resultMethodList = []
        thisReachableSet = set(thisReachableList) 
        resultMethodList = [method for method in nextEntranceList if method in thisReachableSet]

        # deal with virtual calls and interface calls
        toFindSubList = list(set(resultMethodList) & set(thisJsonData['CrossPackageVirtualAndInterfaceInvokeFunctions']))
        newSubEntranceList = []
        for method in toFindSubList:
            newSubEntranceList += self.findPossibleSubClassEntrance(nextHierData, nextJsonData, method)
        resultMethodList += newSubEntranceList

        return resultMethodList
    
    # get precise flat path with DFS algorithm
    def getPrecisePathNew(self, sourceMethod, destinationMethod, JsonFileRoot, GAVChain, pos, path=[], resultPaths=[]):

        path.append(sourceMethod)
        
        if sourceMethod == destinationMethod: 
            if path not in resultPaths:
                resultPaths.append(list(path))  # use list() to copy
        
        if pos < len(GAVChain)-1: 
            reachableRelevantMethods = self.findRelevantMethods(pos, pos+1, sourceMethod)
            for reachableRelevantMethod in reachableRelevantMethods:
                # recursively call itself
                resultPaths = self.getPrecisePathNew(reachableRelevantMethod, destinationMethod, JsonFileRoot, GAVChain, pos+1, path, resultPaths)

        elif pos == len(GAVChain)-1:
            final_json = self.JsonDataList[pos]
            reachableRelevantMethods = self.getReachableWithinCG(final_json, sourceMethod)
            for reachableRelevantMethod in reachableRelevantMethods:
                resultPaths = self.getPrecisePathNew(reachableRelevantMethod, destinationMethod, JsonFileRoot, GAVChain, pos+1, path, resultPaths)

        # backtrack
        path.pop()
        return resultPaths

    # Assess if an entry function can reachable vulnerable functions
    # return True & target vuln funcs or False & [] 
    def isPossible2ReachTargets(self, GAVChian, JsonFileRoot, destinationMethods, givenEntranceMethod):

        entranceMethodList = [givenEntranceMethod]

        reachableMethodsInFinalGAV = []
        destinationMethodsReachablePathRecord = []

        is_possible = True

        if len(GAVChian) == 1: 
            reachableMethodsInFinalGAV = entranceMethodList
        else:
            this_round_method_list = []
            next_round_method_list = []

            # from downstream to upstream
            for pos in range(0, len(GAVChian)-1):

                if(pos == 0):
                    this_round_method_list = entranceMethodList
                else:
                    this_round_method_list = next_round_method_list.copy()
                next_round_method_list = []

                for method in this_round_method_list:
                    next_round_method_list += self.findRelevantMethods(pos, pos+1, method)

                if(len(next_round_method_list) == 0):
                    is_possible = False
                    break

            reachableMethodsInFinalGAV = list(set(next_round_method_list))

            if not (is_possible and reachableMethodsInFinalGAV):
                return False, []
        
        time2=time.time()
        
        final_reachable = []
        final_json = self.JsonDataList[-1]
        final_hier_json = self.HierDataList[-1]
        
        for src in reachableMethodsInFinalGAV:
            final_reachable.append(src)
            final_reachable += self.getReachableWithinCG(final_json, src)
        
        commonMethodNames = matchMyReachableAndTargets(final_reachable, destinationMethods)

        if len(commonMethodNames) == 0:
            return False, []
        else:
            return True, commonMethodNames

    # Find all flat paths
    @timeout(300)
    def run(self, GAVChian, JsonFileRoot, HierFileRoot, destinationMethods, givenEntranceMethods = [], enablePrecisePath = False, resultJsonFile = "", CHACacheRoot = ""):

        print("Search Start")

        self.getSelfJsonList(JsonFileRoot, GAVChian)
        self.getSelfHierJsonList(HierFileRoot, GAVChian, CHACacheRoot)

        time0 = time.time()

        # ------------------------------------------------------------
        # get entrances
        if givenEntranceMethods == []:
             entranceMethodList = list(self.JsonDataList[0]["EntranceAndReachableFunctions"].keys())
        else:
            entranceMethodList = givenEntranceMethods

        # ------------------------------------------------------------
        # get reachable in final pkg

        reachableMethodsInFinalGAV = []
        destinationMethodsReachableRecord = []
        destinationMethodsReachablePathRecord = []

        is_possible = True

        this_round_method_list = []
        next_round_method_list = []

        if len(GAVChian) == 1:
            reachableMethodsInFinalGAV = entranceMethodList
        else:

            for pos in range(0, len(GAVChian)-1):

                if(pos == 0):
                    this_round_method_list = entranceMethodList
                else:
                    this_round_method_list = next_round_method_list.copy()
                next_round_method_list = []

                for method in this_round_method_list:
                    next_round_method_list += self.findRelevantMethods(pos, pos+1, method)

                if(len(next_round_method_list) == 0):
                    is_possible = False
                    break
            
            reachableMethodsInFinalGAV = list(set(next_round_method_list))

        if not (is_possible and reachableMethodsInFinalGAV):
            
            #logging.info("[RESULT] Package not reachable for chain %s", GAVChian)
            return 0, [], [], [], time.time() - time0

        # ------------------------------------------------------------
        # get reachable vuln funcs

        final_reachable = []
        final_json = self.JsonDataList[-1]
        final_hier_json = self.HierDataList[-1]

        for src in reachableMethodsInFinalGAV:
            final_reachable.append(src)
            final_reachable += self.getReachableWithinCG(final_json, src)
        #print("src =", entranceMethod, "final reachable = ", final_reachable)
        #print(final_reachable)

        commonMethodNames = matchMyReachableAndTargets(final_reachable, destinationMethods)

        if len(commonMethodNames) == 0:
            #logging.info("[RESULT] There are %s methods reachable at the end of the chain %s", str(len(reachableMethodsInFinalGAV)), GAVChian)
            #logging.info("[RESULT] No target method reachable for chain %s", GAVChian)
            return 0, reachableMethodsInFinalGAV, [], [], time.time() - time0

        # ------------------------------------------------------------
        # get precise flat paths

        for i in range(0, len(entranceMethodList)):
            #print(i)
            entranceMethod = entranceMethodList[i]

            time1 = time.time()
            isPossiblePath, possibleTargets = self.isPossible2ReachTargets(GAVChian, JsonFileRoot, destinationMethods, entranceMethod)
            time2 = time.time()

            if isPossiblePath:

                destinationMethodsReachableRecord.append((entranceMethod, possibleTargets))
                #print(destinationMethodsReachableRecord)

                if enablePrecisePath:
                #print(entranceMethod)
                    for target in possibleTargets:
                        result = self.getPrecisePathNew(entranceMethod, target, JsonFileRoot, GAVChian, 0, path = [], resultPaths=[])
                        destinationMethodsReachablePathRecord += result     

                time3 = time.time()
                
            #if isPossiblePath:
            #    print(str(time2-time1), str(time3-time2))
            #else:
            #    print(str(time2-time1))

        #print("number of flat paths = "+str(len(destinationMethodsReachablePathRecord)))
        return  0, reachableMethodsInFinalGAV, destinationMethodsReachableRecord, destinationMethodsReachablePathRecord, time.time() - time0