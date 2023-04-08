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
ep_idx_ranges = [0, 63]
num_vaults = 32
busy = []
buffer = []
count = []
        

fake_neighbour= []
for i in range(3):
    fake_neighbour.append(i)


#for i in range (60):
#    eq_i.append(event(i,i))

ep1=EP_h1(eq_i, eq_o, ep_0_i, ep_0_o, ep_1_i, ep_1_o, ep_idx_ranges, num_vaults,"sssp")
eq_i.append(event(0,0))
print("Cycle_1")
ep1.one_cycle(num_vaults)
ep1.vault_mem[0].request_port.popleft()
ep1.vault_mem[0].request_port.popleft()
request_1 = ep1.vault_mem[0].request_port.popleft()
request_2 = ep1.vault_mem[0].request_port.popleft()
print(request_1.cmd, request_1.addr, request_1.data, request_1.tag)
print(request_2.cmd, request_2.addr, request_2.data, request_2.tag)
Tag_1 = request_1.tag
Tag_2 = request_2.tag

print("\nCycle_2")
ep1.one_cycle(num_vaults)

print("\nCycle_3")
ep1.one_cycle(num_vaults)

print("\nCycle_4")
respone_1 = mem_response([0,3],Tag_2)
ep1.vault_mem[0].response_port.append(respone_1)
ep1.one_cycle(num_vaults)

print("\nCycle_5")
respone_2 = mem_response([float("inf")],Tag_1)
ep1.vault_mem[0].response_port.append(respone_2)
ep1.one_cycle(num_vaults)

print("\nCycle_6")
#ep1.vault_mem[0].request_port.popleft()
request_3  = ep1.vault_mem[0].request_port.popleft()
print(request_3.cmd, request_3.addr, request_3.data, request_3.tag)
ep1.one_cycle(num_vaults)
Tag_3 = request_3.tag

print("\nCycle_7")
ep1.one_cycle(num_vaults)

print("\nCycle_8")
respone_3 = mem_response(fake_neighbour,Tag_3)
ep1.vault_mem[0].response_port.append(respone_3)
ep1.one_cycle(num_vaults)

print("\nCycle_9")
ep1.one_cycle(num_vaults)

print("\nCycle_10")
ep1.one_cycle(num_vaults)

print("\nCycle_11")
ep1.one_cycle(num_vaults)

print("\nCycle_12")
ep1.one_cycle(num_vaults)

print("\nCycle_13")
ep1.one_cycle(num_vaults)


#print(ep1.buffer[2])



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
