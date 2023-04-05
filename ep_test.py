from event_processors import EP_h1
from collections import deque
from standard import mem_request, mem_response, event
import math
import numpy as np
#initial ep

eq_i    = deque()
eq_o    = deque()
ep_0_i  = deque()
ep_0_o  = deque()
ep_1_i  = deque()
ep_1_o  = deque()
ep_idx_ranges = [0, 100]
num_vaults = 32

ep1=EP_h1(eq_i, eq_o, ep_0_i, ep_0_o, ep_1_i, ep_1_o, ep_idx_ranges, num_vaults,"sssp")

# EQ send event
event_1 = event(0, 0)
eq_i.append(event_1)
#ep1.allocate_event_vault()
#for i in range(num_vaults):
# #   for j in range(12):
 #       if len(ep1.vault_mem[i].request_port) >0:
# a = ep1.vault_mem[0].request_port.popleft()
# print(a.cmd, a.addr,a.data)
b = deque([float('inf'), 0,2,1,2 ])
ep1.vault_mem[0].response_port=b
ep1.one_cycle()



