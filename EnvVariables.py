import os

WorkspaceRoot = os.getcwd() + "/"

# Java class path
SootMainName_FlattenCG_Release = "com.example.hello.BuildMyCGRelease"
SootMainName_FlattenCG_Release_SPARK = "com.example.hello.BuildMyCGReleaseSPARK"
SootMainName_AllCG_Release = "com.example.hello.BuildAllCGRelease"
SootMainName_AllCG_Release_SPARK = "com.example.hello.BuildAllCGReleaseSPARK"
HierSootMainName_Release = "com.example.hello.BuildHierRelease"

# Java dependencies
DependencyFiles = WorkspaceRoot + "Dependency/*"
DependencyRoot = WorkspaceRoot + "Dependency/"

UnifiedLog = WorkspaceRoot + "Logs.log"

DownloadRoot = WorkspaceRoot + "JarDownload/"
AllCGOutputDir = WorkspaceRoot + "AllCG/"
PartialAllCGOutputDir = WorkspaceRoot + "PartialAllCG/"
FlattenCGOutputDir = WorkspaceRoot + "FlattenCG/"
HierOutputDir =WorkspaceRoot + "HierInfo/"
try:
    os.mkdir(DownloadRoot) 
    os.mkdir(AllCGOutputDir)
    os.mkdir(PartialAllCGOutputDir) 
    os.mkdir(FlattenCGOutputDir) 
    os.mkdir(HierOutputDir) 
except FileExistsError:
    pass

path_additional_len = 0
enable_sprak = False

def GAV2AVForm(origin_name):
    org, name, version = origin_name.split(":")
    file_name = f"{name}-{version}"
    return file_name

import json
def fetchJsonData(json_file_path):
    print(f"read {json_file_path}")
    with open(json_file_path, 'r') as f:
        json_data  = json.load(f)
    return json_data

import functools
import signal
def timeout(sec):
    """
    timeout decorator
    :param sec: function raise TimeoutError after sec seconds
    ! windows system is not supported
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapped_func(*args, **kwargs):

            def _handle_timeout(signum, frame):
                err_msg = f'Function {func.__name__} timed out after {sec} seconds'
                raise TimeoutError(err_msg)

            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(sec)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapped_func
    return decorator

import re
def parseClassAndMethod(methodSignature):
        pattern = r"<(.*?): (.*?) (.*?\(.*?\))>"
        matches = re.match(pattern, methodSignature)
        class_name = matches.group(1)
        return_type = matches.group(2)
        method = matches.group(3)
        return class_name, return_type, method

#CHA Cache
def GAV2CHACache(GAV):
    AV = GAV2AVForm(GAV)
    name = WorkspaceRoot + "CHACahe/" + AV + "-CacheInfo.json"
    return name
