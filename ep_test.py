from event_processors import EP_h1
from collections import deque
from standard import mem_request, mem_response, event
import math
import numpy as np
import io_port
#initial ep

eq_i    = deque()
eq_o    = deque()
ep_0_i  = deque()
ep_0_o  = deque()
ep_1_i  = deque()
ep_1_o  = deque()
ep_idx_ranges = [0, 31]
num_vaults = 32
busy = []
buffer = []
count = []
        

ep1=EP_h1(eq_i, eq_o, ep_0_i, ep_0_o, ep_1_i, ep_1_o, ep_idx_ranges, num_vaults,"sssp")

for i in range (60):
    eq_i.appned(event(i,i))
print("Cycle")
ep1.one_cycle(num_vaults)



# ep1.buffer[0].append(event(0,0))
# print("Cycle_1")
# ep1.one_cycle(num_vaults)
# #request_1 = ep1.vault_mem[0].request_port.popleft()
# #rint(request_1.cmd, request_1.addr, request_1.data)
# respone_1 = mem_response(float("inf"))
# ep1.vault_mem[0].response_port.append(respone_1)
# print("Cycle_2")
# ep1.one_cycle(num_vaults)
# print("Cycle_3")
# ep1.one_cycle(num_vaults)
# print("Cycle_4")
# ep1.one_cycle(num_vaults)
# print("Cycle_5")
# respone_2 = mem_response(0)
# respone_3 = mem_response(2)
# ep1.vault_mem[0].response_port.append(respone_2)
# ep1.vault_mem[0].response_port.append(respone_3)
# ep1.one_cycle(num_vaults)
# print("Cycle_6")
# ep1.one_cycle(num_vaults)
# print("Cycle_7")
# ep1.one_cycle(num_vaults)
# print("Cycle_8")
# response_4 = mem_response(1)
# response_5 = mem_response(2)
# ep1.vault_mem[0].response_port.append(response_4)
# ep1.vault_mem[0].response_port.append(response_5)
# ep1.one_cycle(num_vaults)
# print("Cycle_9")
# ep1.one_cycle(num_vaults)
# print("Cycle_10")
# ep1.one_cycle(num_vaults)
