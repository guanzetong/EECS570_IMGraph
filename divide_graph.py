import os

# Create the output directory if it does not exist
output_dir="output_files"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

#read input file
input_file="soc-LiveJournal1.adj"
with open(input_file,"r") as file:
    lines=file.readlines()

# Fetch the total number of nodes and edges from the file
total_nodes=int(lines[1])
total_lines=int(lines[2])

#read nodes' pointer to edge list
node_pointers=[int(line) for line in lines[3:total_nodes+3]]
edge_list = lines[total_nodes+3:]
# Calculate the number of nodes in each file
nodes_per_file = total_nodes // 256 +1
# print("nodes_per_file",nodes_per_file)
# remainder_nodes = total_nodes % 256
remainder_nodes = total_nodes-(nodes_per_file)*255
# print("remainder_nodes",remainder_nodes)
start_node=0

for i in range(256):
    # if(i<remainder_nodes):
    #     end_node = start_node + nodes_per_file+1
    #     num_nodes = nodes_per_file + 1
    # else:
    #     end_node = start_node + nodes_per_file
    #     num_nodes = nodes_per_file
    if (i < 255):
        end_node = start_node + nodes_per_file-1
        num_nodes = nodes_per_file

        start_pointer = node_pointers[start_node]
        end_pointer = node_pointers[end_node]
        num_edges = end_pointer - start_pointer

        edge_data = node_pointers[start_node:end_node]
        # create output file
        output_filename = f"{output_dir}/vault_mem_{i + 1}.txt"
        with open(output_filename, "w") as output_file:
            output_file.write(f"{num_nodes}\n{num_edges}\n")
            for i in range(num_nodes + 1):
                edge_start = start_pointer
                output_file.write(f"{node_pointers[start_node + i] - node_pointers[start_node]+ 4* num_nodes*2}\n")  # -node_pointers[start_node]
            # for i in range(num_nodes + 1):
            #     output_file.write(f"{edge_list[node_pointers[start_node+i]:node_pointers[start_node+i+1]]}")
            for i in range(num_nodes + 1):
                edge_slice = edge_list[node_pointers[start_node + i]:node_pointers[start_node + i + 1]]
                for edge in edge_slice:
                    output_file.write(f"{edge}")
            # for j in range(num_nodes):
    else:
        # print("accessing last vault")
        end_node = start_node + remainder_nodes-1
        # print("start_node:", start_node)
        # print("remaining nodes:",remainder_nodes)
        # print("end_node",end_node)
        num_nodes = remainder_nodes

        start_pointer = node_pointers[start_node]
        end_pointer = node_pointers[end_node]
        num_edges = end_pointer - start_pointer

        edge_data = node_pointers[start_node:end_node]
        # create output file
        output_filename = f"{output_dir}/vault_mem_{i + 1}.txt"
        with open(output_filename, "w") as output_file:
            output_file.write(f"{num_nodes}\n{num_edges}\n")
            for i in range(num_nodes):
                edge_start = start_pointer
                output_file.write(f"{node_pointers[start_node + i] - node_pointers[start_node] + 4 * num_nodes*2 }\n")  # -node_pointers[start_node]
                # output_file.write(f"{edge_list[start_pointer:]}")
            # for i in range(num_nodes-1):
            #     output_file.write(f"{edge_list[node_pointers[start_node+i]:node_pointers[start_node+i+1]]}")
            for i in range(num_nodes-1 ):
                edge_slice = edge_list[node_pointers[start_node + i]:node_pointers[start_node + i + 1]]
                for edge in edge_slice:
                    output_file.write(f"{edge}")
            # for j in range(num_nodes):
    #
    # start_pointer=node_pointers[start_node]
    # end_pointer=node_pointers[end_node]
    # num_edges=end_pointer-start_pointer
    #
    # edge_data=node_pointers[start_node:end_node]
    # #create output file
    # output_filename=f"{output_dir}/vault_mem_{i+1}.txt"
    # with open (output_filename,"w") as output_file:
    #     output_file.write(f"{num_nodes}\n{num_edges}\n")
    #     for i in range(num_nodes+1):
    #         edge_start=start_pointer
    #         output_file.write(f"{node_pointers[start_node+i]}\n")#-node_pointers[start_node]
    #         #output_file.write(f"{edge_list[start_pointer:]}")
    #     # for j in range(num_nodes):
    # print("start_node",start_node)
    # print("end_node", end_node)
    start_node = end_node+1
# for i in range(256):
#     for i in range(num_nodes):
#         edge_list[]
#         output_file.write(f"{node_pointers[start_node + i] - node_pointers[start_node]}\n")