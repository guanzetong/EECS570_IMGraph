from event_queues import EQ
from collections import deque
from standard import mem_response
import numpy as np
from standard import mem_request, mem_response, event

offset = 140000

ep_e_i = deque(event(idx = i, val = 0.15+i) for i in range(10))
ep_e_o = deque()
ep_n_i = deque(event(idx = i+offset, val = 0.2+i) for i in range(10))
ep_n_o  = deque()
ep_w_i = deque(event(idx = i+offset*2, val = 0.25+i) for i in range(10))
ep_w_o = deque()
ep_s_i = deque(event(idx = i+offset*3, val = 0.3+i) for i in range(10))
ep_s_o = deque()
# create a list of lists to store the index ranges for each vault, each vault contains 100 elements
ep_idx_ranges = [[i*100, (i+1)*100] for i in range(8)]
num_vaults=32

eq = EQ(ep_e_i, ep_e_o, ep_n_i, ep_n_o, ep_w_i, ep_w_o, ep_s_i, ep_s_o, ep_idx_ranges, num_vaults, func = "pagerank")

for i in range(2000):
    print(f"----------------------------- cycle: {i} -----------------------------")
    # if i == 10:
        #  eq.vault_mem[0].response_port.append(mem_response([0.15 for i in range(256)],1))
    eq.one_clock_try()
    