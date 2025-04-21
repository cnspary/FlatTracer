import time
import networkx as nx
import time

from EnvVariables import timeout
from EnvVariables import path_additional_len


# Recover traditional paths
def find_exact_path_with_flatten_path(args):
    call_graphs, flatten_path = args
    print(f"\n[To recover flatten_path] = {flatten_path}")

    if len(flatten_path) < 2:
        return [], -1, -1, -1, -1, -1, -1
    
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