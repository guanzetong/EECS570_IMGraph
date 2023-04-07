from collections import deque
from standard import mem_request, mem_response,TrackTableEntry,TrackTable
import numpy as np
from vault_mem import VM

# Create a deque to use as the request port and response port
request_port = deque()
response_port = deque()

# Create a memory bank for testing
memory_bank = np.zeros(2**32//4, dtype=np.uint32)
# Test a read request
addr1 =0#0 //105 cycles
size1 =128#
addr2=2**32//8-8
size2=16
addr3 =0#0 //105 cycles
size3 =40#8#
addr4=2**32//8-8
size4=16

for i in range(0,20):
    memory_bank[i]=1+i
for i in range(0,100):#size2//4
    memory_bank[(2**32//8//4-8//4)+i]=1+i
# print((2**32//8//4-8//4))
print("mem_bank:",memory_bank)
# Create a VM instance for testing
vm = VM(request_port, response_port, memory_bank)
tag1=vm.GetReqTag()
req1 = mem_request("read", addr1, None, size1,tag1)
tag2=vm.GetReqTag()
req2 = mem_request("read", addr2, None, size2,tag2)
req3=mem_request("write", addr3, [10,11,12,13,14,15,16,17,18,19], size3,0)
req4=mem_request("write", addr4, [1000,10001,10002,100003], size4,0)
request_port.append(req1)
request_port.append(req2)
request_port.append(req3)
request_port.append(req4)
count = 0
cycle=0
for i in range(450):
    print("//-----------------Cycle:", cycle, "-------------------//")
    vm.one_cycle()
    cycle = cycle + 1
print("vault_bank_mem[0][0:19]:",vm.vault_bank_mem[0][0:19])
print("vm.vault_bank_mem[1][0:1]:",vm.vault_bank_mem[1][0:2])

# while count < 2:
#     print("//-----------------Cycle:",cycle,"-------------------//")
#
#     vm.one_cycle()
#     cycle =cycle+1
#     if response_port:
#         for resp in response_port:
#             print(resp.data)
#         # Process the next response entry
#         response = response_port.popleft()
#         print("Response form VM:", response.data)
#         print("response.data[1]:", response.data[1])
#         # Do something with the response here
#         count += 1
#         print("Response count:", count)

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