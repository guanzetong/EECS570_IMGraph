from event_queues import EQ
from collections import deque


ep_e_i = deque()
ep_e_o = deque()
ep_n_i = deque()
ep_n_o  = deque()
ep_w_i = deque()
ep_w_o = deque()
ep_s_i = deque()
ep_s_o = deque()
# create a list of lists to store the index ranges for each vault, each vault contains 100 elements
ep_idx_ranges = [[i*100, (i+1)*100] for i in range(8)]
num_vaults=32

eq = EQ(ep_e_i, ep_e_o, ep_n_i, ep_n_o, ep_w_i, ep_w_o, ep_s_i, ep_s_o, ep_idx_ranges, num_vaults, func = "pagerank")

for i in range(500):
    print(f"------------------ cycle: {i} -----------------")
    # if i == 10:
    #     eq.vault_mem[0].response_port.append([1 for i in range(256)])
    eq.one_cycle()
