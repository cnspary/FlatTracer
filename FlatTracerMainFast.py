import json
import os
import networkx as nx
import datetime
import sys
import concurrent.futures

from EnvVariables import GAV2AVForm
from EnvVariables import fetchJsonData


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


from JointSearch import JointSearch

from GenerateCGDummy import chose_to_generate
from RecoverPath import find_exact_path_with_flatten_path
 
 
if __name__ == '__main__':

    DownloadJarInstance = DownloadJar()
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

            ############# STEP1 generate flat cg 
            
            print("\n----generate flat cg, hierarchy info, partial traditional cg----")

            args_list = []
            for gav in entry['chain']:
                args_list.append(['flatcg', DownloadRoot, [gav], SootMainName_FlattenCG_Release, DependencyFiles, FlattenCGOutputDir, False, True, False])
                args_list.append(['hier', DownloadRoot, [gav], HierSootMainName_Release, DependencyFiles, HierOutputDir, True, False])
                args_list.append(['traditional_partial',gav, os.path.join(DownloadRoot, GAV2AVForm(gav) + ".jar"), PartialAllCGOutputDir, SootMainName_AllCG_Release, DependencyFiles, False])
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(chose_to_generate, args_list)
            
            ############# STEP2 search for flat paths
            print("\n----search for flat paths----")
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


            ############ STEP3 recover traditional paths
            print("\n----recover traditional paths----")


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

            args_list = []
            for path in destinationMethodsReachablePathRecord:
                args_list.append([call_graphs, path])
            with concurrent.futures.ProcessPoolExecutor() as executor:
                results = executor.map(find_exact_path_with_flatten_path, args_list) # In case of exception, it will return []
            
            my_detail_paths = []
            except_paths_my2detail = 0
            for result in results:
                detail_paths, time_consumption, this_time_out_paths_my2detail, path_count, ave_len, this_except_paths_my2detail, this_time_stitch_path = result
                my_detail_paths.append(detail_paths)
                if this_except_paths_my2detail > 0:
                    except_paths_my2detail += 1

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