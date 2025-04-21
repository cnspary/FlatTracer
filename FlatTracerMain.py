import json
import subprocess
import os
import time
import networkx as nx
import datetime
import sys

from EnvVariables import GAV2AVForm
from EnvVariables import fetchJsonData
from EnvVariables import timeout
from EnvVariables import path_additional_len

# Build partial traditional call graph
def build_cg_without_dep(startGAV, inputFilePath, outputDirPath, SootMainName, DependencyFiles, toMerge = False, reGen = False):

    possibleFilePos = outputDirPath + GAV2AVForm(startGAV) + "-PkgInfo-sootcg-partial.txt"
    #print(f"possibleFilePos = {possibleFilePos}")
    
    if os.path.isfile(possibleFilePos) and not reGen:
        print(f"alreay generated cg {possibleFilePos}")
        return 0
    
    else:
        output_file_name = GAV2AVForm(startGAV) + "-PkgInfo-sootcg-partial.txt"

        command = ['java', '-cp', f'{DependencyFiles}:.', SootMainName, inputFilePath, outputDirPath, output_file_name, "direct_use_given_name"]
        time0 = time.time()
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time1 = time.time()

        print(result.stdout)
        print(result.stderr)
        
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

# Recover traditional paths
def find_exact_path_with_flatten_path(call_graphs, flatten_path):

    if len(flatten_path) < 2:
        return [], -1
    
    res = []
    time0 = time.time()
    time_out_paths_my2detail = 0
    except_paths_my2detail = 0
    path_count = -1
    ave_len = 0

    for i in range(0, len(flatten_path)-1): 

        call_graph = call_graphs[i]
        start_method = flatten_path[i]
        end_method = flatten_path[i+1]
        
        try:
            path = nx.shortest_path(call_graph, source=start_method, target=end_method)
            try:
                path_count, this_ave_len, paths = findAllPaths600WithRes(call_graph, start_method, end_method, len(path))
                res.append(paths)
                ave_len += this_ave_len
            except:
                time_out_paths_my2detail += 1
                res.append([[start_method, end_method]])
                ave_len += 1
        except:
            except_paths_my2detail += 1
            res.append([[start_method, end_method]])
            ave_len += 1

    time_consumption = time.time() - time0
    
    # stitch traditional path with flat path. The "stitch" here is different to cg stitch
    time_stitch = time.time()
    prev_paths = [[flatten_path[0]]]
    for i in range(0, len(flatten_path)-1):
        next_paths = res[i]
        for prev_path in prev_paths: 
            new_prev_paths = []
            for next_path in next_paths:
                if prev_path[-1] == next_path[0]:
                    new_prev_paths.append(prev_path + next_path[1:])
        prev_paths = new_prev_paths            
    time_stitch = time.time() - time_stitch
    
    path_count = len(prev_paths)
    recovered_paths = prev_paths

    for path in recovered_paths:
        print(f'\n[Recovered Traditional Path] = {" -> ".join(path)}')

    return recovered_paths, time_consumption, time_out_paths_my2detail, path_count, ave_len, except_paths_my2detail, time_stitch

# Search within traditional call graph
@timeout(600)
def findAllPaths600WithRes(call_graph, start_method, dest_method, cut_off):
    path_count = 0
    ave_len = 0
    paths = nx.all_simple_paths(call_graph, source=start_method, target=dest_method, cutoff=cut_off+path_additional_len)
    res = []
    for path in paths:
        res.append(path)
        path_count += 1
        ave_len += len(path)
    ave_len = ave_len/max(1, path_count)
    return path_count, ave_len, res


from EnvVariables import HierSootMainName_Release
from EnvVariables import enable_sprak
if enable_sprak:
    from EnvVariables import SootMainName_AllCG_Release_SPARK as SootMainName_AllCG_Release
    from EnvVariables import SootMainName_FlattenCG_Release_SPARK as SootMainName_FlattenCG_Release
else:
    from EnvVariables import SootMainName_AllCG_Release
    from EnvVariables import SootMainName_FlattenCG_Release

from EnvVariables import DependencyFiles
from EnvVariables import PartialAllCGOutputDir
from EnvVariables import FlattenCGOutputDir
from EnvVariables import HierOutputDir  
from EnvVariables import DownloadRoot

from DownloadJar import DownloadJar
from GenerateCG import GenerateCG
from GenerateHierarchy import GenerateHierarchy
from JointSearch import JointSearch
 
if __name__ == '__main__':

    DownloadJarInstance = DownloadJar() 
    GenerateJsonInstance = GenerateCG()
    GenerateHierarchyInstance = GenerateHierarchy()
    JointSearchInstance = JointSearch()

    inputfile = sys.argv[1]
    inputdata = fetchJsonData(inputfile)

    result_file = f"Output-{datetime.datetime.now().strftime('%m-%d-%H-%M')}.json" # generate output file path
    print(f"target result file = {result_file}")

    for i in range(0, len(inputdata)): 
        print(f"index = {i}")
        entry = inputdata[i]

        try:
            print(f"dependency chain = {entry['chain']}")
            startGAV = entry['chain'][0]
            ori_dest_methods = entry['dest_methods']

            # download jar file on dep chain only
            for gav in entry['chain']:
                return_value = DownloadJarInstance.run([gav], DownloadRoot)
                if return_value != 0:
                    print(f"Error Download Jar for {gav}")
            print("download complete")

            # generate flat cg
            print("\n----generate flat cg and search for flat paths----")

            time_cg_my = 0
            time_cg_my2detail = 0
            for gav in entry['chain']:
                try:                                          
                    return_time_0 = GenerateJsonInstance.run(DownloadRoot, [gav], SootMainName_FlattenCG_Release, DependencyFiles, FlattenCGOutputDir, enable_merge = False, return_time=True, reGen = False) 
                    return_time_1 = GenerateHierarchyInstance.run(DownloadRoot, [gav], HierSootMainName_Release, DependencyFiles, HierOutputDir, reGen = False)
                    if return_time_0 == 1 or return_time_1 == 1:
                        print("generate flatcg error")
                    else:
                        time_cg_my = max(time_cg_my, return_time_0+return_time_1)
                except TimeoutError:
                    print("timeout")

            # search for flat paths
            status, reachableMethodsInFinalGAV, destinationMethodsReachableRecord, destinationMethodsReachablePathRecord, time_path_my = JointSearchInstance.run(entry['chain'], FlattenCGOutputDir, HierOutputDir, ori_dest_methods, [], True)
            destinationMethodsReachableRecord = [list(item) for item in destinationMethodsReachableRecord]
            for flat_path in destinationMethodsReachablePathRecord:
                print(f'\n[Find Flat Path] = {" -> ".join(flat_path)}')

            # a path pair is (entry_function, destination_function)
            path_pair_count_my = 0
            for record in destinationMethodsReachableRecord:
                path_pair_count_my += len(record[1])
            print(f"path pair found with flatcg = {path_pair_count_my}") 

            # the format of dest_methods in input file may change as it comes from multiple sources, but the format in destinationMethodsReachableRecord is the one provide by soot

            # generate partial cg for traditional path recovery
            for gav in entry['chain']:
                time_cg_my2detail_this = build_cg_without_dep(gav, os.path.join(DownloadRoot, GAV2AVForm(gav) + ".jar"), PartialAllCGOutputDir, SootMainName_AllCG_Release, DependencyFiles, False, False)
                time_cg_my2detail += time_cg_my2detail_this

            # recover traditional paths
            print("\n----recover traditional paths----")

            time_path_my2detail = 0
            count_my2detail = 0

            target_cg_files = []
            for gav in entry['chain']:
                target_cg_files.append(PartialAllCGOutputDir + GAV2AVForm(gav) + "-PkgInfo-sootcg-partial.txt")

            call_graphs = []
            for cg_file in target_cg_files:
                call_graph = nx.DiGraph()
                with open(cg_file, 'r') as file:
                    for line in file:
                        # format: '<caller> ==> <callee>'
                        caller, callee = line.strip().split(' ==> ')
                        call_graph.add_edge(caller, callee)
                call_graphs.append(call_graph)

            count_path_dealed_my2detail = 0
            early_termination_my2detail = False
            time_out_paths_my2detail = 0
            except_paths_my2detail = 0
            time_stitch_path = 0 
            act_my2detail_out = False
            my_detail_paths = []
            for path in destinationMethodsReachablePathRecord:
                
                if count_path_dealed_my2detail > 10:
                    act_my2detail_out = True
                    break

                # maximum running time 1800s 
                if early_termination_my2detail:
                    break

                detail_paths, time_consumption, this_time_out_paths_my2detail, path_count, ave_len, this_except_paths_my2detail, this_time_stitch_path = find_exact_path_with_flatten_path(call_graphs, path)
                my_detail_paths.append(detail_paths)
                if this_time_out_paths_my2detail > 0:
                    time_out_paths_my2detail += 1
                if this_except_paths_my2detail > 0:
                    except_paths_my2detail += 1
                time_path_my2detail += time_consumption
                count_my2detail += 1
                count_path_dealed_my2detail += 1
                if time_path_my2detail > 1800:
                    early_termination_my2detail = True

            # output result
            dict = {
                    "chain": entry['chain'],
                    "CVE": entry['CVE'],
                    "dest_methods": entry['dest_methods'],
                    "destinationMethodsReachableRecord": destinationMethodsReachableRecord, # pair of entry function and destination function
                    "destinationMethodsReachablePathRecord": destinationMethodsReachablePathRecord, # flat path
                    "recoveredTraditionalPaths": my_detail_paths,
                    "status": "ok"
                }
            if os.path.exists(result_file) and os.stat(result_file).st_size != 0:
                with open(result_file, 'r') as file:
                    data = json.load(file)
            else:
                data = []
            data.append(dict)
            with open(result_file, 'w') as file:
                json.dump(data, file, indent = 4)

        except Exception as e:
            print(e)
            dict = {
                "chain": entry['chain'],
                "status": str(e)
            }
            if os.path.exists(result_file) and os.stat(result_file).st_size != 0:
                with open(result_file, 'r') as file:
                    data = json.load(file)
            else:
                data = []
            data.append(dict)
            with open(result_file, 'w') as file:
                json.dump(data, file, indent = 4)

    print(f"\noutput result to {result_file}")