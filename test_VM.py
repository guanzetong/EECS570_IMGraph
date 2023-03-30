from collections import deque
from standard import mem_request, mem_response
import numpy as np
from vault_memory import VM

# Create a deque to use as the request port and response port
request_port = deque()
response_port = deque()

# Create a memory bank for testing
memory_bank = np.zeros(2**32 // 8, dtype=np.uint64)
# Test a read request
addr1 =0#0
size1 =136#
addr2=1000
size2=136

for i in range(0,20):
    memory_bank[i]=1+i
for i in range(0,size2//8):
    memory_bank[1000//8+i]=1+i
print("mem_bank:",memory_bank)
# Create a VM instance for testing
vm = VM(request_port, response_port, memory_bank)


req1 = mem_request("read", addr1, None, size1)
req2 = mem_request("read", addr2, None, size2)
request_port.append(req1)
request_port.append(req2)
count = 0
# for i in range(60):
#     vm.one_cycle()
while count < 4:
    vm.one_cycle()
    if response_port:
        for resp in response_port:
            print(resp.data)
        # Process the next response entry
        response = response_port.popleft()
        print("Response form VM:", response.data)
        # Do something with the response here
        count += 1
        print("Response count:", count)

# data=[3,4]
# req1 = mem_request("write", addr1,data, size1)
# request_port.append(req1)
# for req in request_port:
#             print(req.data)
# count = 0
# while count < 53:
#     # Do something here, such as calling a method or performing a computation
#     vm.one_cycle()
#     count += 1
# print("mem_bank:",memory_bank)


print("//-------------------Response port---------------------//")

print("//----------------End Response port---------------------//")
# response = response_port.popleft()



# # Test a write request
# addr = 0x2000
# size = 64
# data = np.array([0x123456789abcdef0], dtype=np.uint64)
# req = mem_request("write", addr, data, size)
# request_port.append(req)
# vm.one_cycle()
# assert memory_bank[addr // 8: (addr + size) // 8].tolist() == data.tolist()

print("All tests passed!")