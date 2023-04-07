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
ep_idx_ranges = [0, 100]
num_vaults = 32
busy = []
buffer = []
count = []

for i in range(num_vaults):
    busy.append(False)
    buffer.append(deque())
    count.append(0)
        

ep1=EP_h1(eq_i, eq_o, ep_0_i, ep_0_o, ep_1_i, ep_1_o, ep_idx_ranges, num_vaults,"sssp", busy=False, buffer = buffer, count = count)


ep1.buffer[0].append(event(0,0))
ep1.one_cycle(num_vaults)
request_1 = ep1.vault_mem[0].request_port.popleft()
print(request_1.cmd, request_1.addr, request_1.data)
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
ep_idx_ranges = [0, 100]
num_vaults = 32
busy = []
buffer = []
count = []

for i in range(num_vaults):
    busy.append(False)
    buffer.append(deque())
    count.append(0)
        

ep1=EP_h1(eq_i, eq_o, ep_0_i, ep_0_o, ep_1_i, ep_1_o, ep_idx_ranges, num_vaults,"sssp", busy=False, buffer = buffer, count = count)


ep1.buffer[0].append(event(0,0))
ep1.one_cycle(num_vaults)
request_1 = ep1.vault_mem[0].request_port.popleft()
print(request_1.cmd, request_1.addr, request_1.data)