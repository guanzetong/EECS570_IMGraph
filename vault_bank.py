from collections import deque
from standard import mem_request, mem_response, bank_request, bank_response
import math
import numpy as np


class vault_bank:
    def print_deque(deque_to_print):
        for item in deque_to_print:
            print(item)

    def __init__(self, request_port, response_port, vault_bank,idx):
        # Variables:
        # request_port: input deque from logic base to transmit memory requests
        # response_port: output deque to logic base to response with data on read requests

        self.request_port = request_port
        self.response_port = response_port

        # self.memory_bank= np.zeros(2**32//8, dtype=np.uint64) #byte addressable, 4GB memory size
        self.memory_bank = vault_bank
        self.mem_row_size = 1024  # bytes,8192 bits
        self.data_signal_width = 32  # bytes, 256bits
        self.current_row = idx*2**29//self.mem_row_size

        self.nx_row = idx*2**29//self.mem_row_size
        # self.burst_num = 0
        # https://www.crucial.com/articles/about-memory/difference-between-speed-and-latency Clock Cycle Time=0.42ns
        self.burst_delay = 0  # T_CAS=40 cycles=16.8ns=17 cycles if hits, T_RCD=39 cycles=16.38=17cycles, T_RP=39 cycles=17cycles
        # self.burst_delay_deque = deque()
        # self.burst_size_deque = deque()
        self.request_processing = False
        self.first_request = True
        self.cmd = 0
        self.data = 0
        self.addr = 0
        self.size = 0
        self.tag = 0
        self.data_size = 4 #4bytes, 32 bits
        self.idx=idx
        # print("self.cmd:", self.cmd, type(self.cmd))

    def one_cycle(self):
        # print("self.cmd:", self.cmd, type(self.cmd))

        print("If request in Processing:", self.request_processing)
        print("Left Burst Delay:", self.burst_delay)

        # continue reading or writing if not zero
        if self.burst_delay > 1:
            # print("accessing:self.burst_delay-1")
            self.burst_delay = self.burst_delay - 1
            # print("self.burst_delay:",self.burst_delay)
            return

        if (self.request_processing == True and self.burst_delay == 1 and self.cmd == "read"):
            print("//-------------------Accessing Reading Request Finial cycle-----------------------//")
            num_data=self.size//self.data_size
            Read_Data = np.zeros(num_data, dtype=np.uint32)
            # print("self.memory_bank:",self.memory_bank)
            for i in range(num_data):
                Read_Data[i] = self.memory_bank[((self.addr-self.idx*2**29)//self.data_size + i)]
                # print("((self.addr-self.idx*2**29)//self.data_size + i)",((self.addr-self.idx*2**29)//self.data_size + i))
            # print("Read_Data",Read_Data)
            response=bank_response(Read_Data,self.tag)
            self.response_port.append(response)
            Read_Data = np.zeros(num_data, dtype=np.uint32)
            self.request_processing = False
            self.burst_delay = 0
            self.cmd = 0
            self.data = 0
            self.addr = 0
            self.size = 0
            self.tag = 0
            print("//--------------Finish Accessing Reading Request Finial cycle-------------------//")
            return
        if (self.request_processing == True and self.burst_delay == 1 and self.cmd == "write"):
            print("//-------------------Accessing Writing Request Finial cycle-----------------------//")
            num_data = self.size // self.data_size
            for i in range(num_data):
                self.memory_bank[((self.addr-self.idx*2**29)//self.data_size + i)] = self.data[i]
            self.request_processing = False
            self.burst_delay = 0
            self.cmd = 0
            self.data = 0
            self.addr = 0
            self.size = 0
            self.tag = 0

            print("//--------------Finish Accessing Reading Request Finial cycle-------------------//")
            return

        # if there is request in request_port deque?
        if not self.request_port:
            return
        # pop oldest requests from deque
        req = self.request_port.popleft()
        # print("self.request_port:", self.request_port, type(self.request_port))
        # print("req:", req, type(req))
        print("//-----------------------------------Dealing with One Request---------------------------------//")

        # print("Processing Request:", "command:", req.cmd, "addr in bytes:", req.addr, "size in bytes:", req.size,
        #       "Data:", req.data, "tag", req.tag)
        # self.burst_delay = 0
        # self.cmd = 0
        # self.data = 0
        # self.addr = 0
        # self.size = 0

        self.cmd = req.cmd
        # print("self.cmd:", self.cmd, type(self.cmd))
        # print("req:", req, type(req))
        self.addr = req.addr  # assume in bytes
        self.data = req.data
        self.size = req.size  # assume in bytes
        self.tag = req.req_tag
        self.request_processing = True
        print("self.nx_row:", self.nx_row, "self.current_row:", self.current_row)
        # print("len(vault_bank):", len(self.memory_bank))
        # read request
        if self.cmd == "read":
            # calculate need how many Bursts, round up vaule, evey burst can deal with 128 bytes
            # self.burst_num = math.ceil(self.size / self.data_signal_width)
            # print("How many Burst request needed:", self.burst_num)
            # calculating total delay
            print("//-------------------Calculating Reading Request Total Delay-------------------//")
            # print("self.first_request:",self.first_request)
            # nx_size = self.size
            # for i in range(1, self.burst_num + 1):
                # first requesting, Open row and hit
            if (self.first_request == True):
                # if nx_size<128 can not calculate  self.nx_row = (addr + i*128) // self.mem_row_size
                if (self.size < self.data_signal_width):
                    self.current_row = self.nx_row
                    print("current row:", self.current_row)
                    self.nx_row = (self.addr + self.size) // self.mem_row_size
                    print("next row:", self.nx_row)
                    if (self.current_row == self.nx_row):
                        self.burst_delay = self.burst_delay + 34 + 17
                    else:
                        # Within one burst request, but row changed
                        self.burst_delay = self.burst_delay + 34 * 2 + 17 * 2
                    self.first_request = False
                    print("self.burst_delay:",self.burst_delay)
                else:
                    print("Calculating Total Delay: accessing self.first_request == Ture statement,size>=36")
                    self.current_row = self.nx_row
                    print("current row:", self.current_row)
                    self.nx_row = (self.addr + self.data_signal_width) // self.mem_row_size
                    print("next row:", self.nx_row)
                    if (self.current_row == self.nx_row):
                        self.burst_delay = self.burst_delay + 34 + 17
                    else:
                        # Within one burst request, but row changed
                        self.burst_delay = self.burst_delay + 34 * 2 + 17 * 2
                    self.first_request = False
                    print("self.burst_delay:", self.burst_delay)
                # self.burst_delay_deque.append(self.burst_delay)
            else:
                print("Calculating Total Delay: accessing else statement")
                # calculating which row is read or wrote, for every burst
                print("nx_size is :", self.size)
                if (self.size < self.data_signal_width):
                    self.current_row = self.nx_row
                    if (self.addr // self.mem_row_size != self.current_row):
                        self.burst_delay = self.burst_delay + 34
                    self.nx_row = (self.addr + self.size) // self.mem_row_size
                    if (self.current_row == self.nx_row):
                        self.burst_delay = self.burst_delay + 17
                    else:
                        # Within one burst request, but row changed
                        self.burst_delay = self.burst_delay + 34 + 17 * 2
                    self.first_request = False
                else:
                    self.current_row = self.nx_row
                    # reading from different row for starting addr
                    if (self.addr // self.mem_row_size != self.current_row):
                        self.burst_delay = self.burst_delay + 34

                    print("current row:", self.current_row)
                    self.nx_row = (self.addr + self.data_signal_width) // self.mem_row_size
                    print("next row:", self.nx_row)
                    if (self.current_row == self.nx_row):
                        self.burst_delay = self.burst_delay + 17
                    else:
                        # Within one burst request, but row changed
                        self.burst_delay = self.burst_delay + 34 + 17 * 2
                    self.first_request = False

        # write request
        elif self.cmd == "write":
            print("//---------------Calculating Writing Request Total Delay-------------------//")
            # first requesting, Open row and hit
            if (self.first_request == True):
                # if nx_size<128 can not calculate  self.nx_row = (addr + i*128) // self.mem_row_size
                if (self.size < self.data_signal_width):
                    self.current_row = self.nx_row
                    print("current row:", self.current_row)
                    self.nx_row = (self.addr + self.size) // self.mem_row_size
                    print("next row:", self.nx_row)
                    if (self.current_row == self.nx_row):
                        self.burst_delay = self.burst_delay + 34 + 17
                    else:
                        # Within one burst request, but row changed
                        self.burst_delay = self.burst_delay + 34 * 2 + 17 * 2
                    self.first_request = False
                    print("self.burst_delay:", self.burst_delay)
                else:
                    print("Calculating Total Delay: accessing self.first_request == Ture statement,size>=36")
                    self.current_row = self.nx_row
                    print("current row:", self.current_row)
                    self.nx_row = (self.addr + self.data_signal_width) // self.mem_row_size
                    print("next row:", self.nx_row)
                    if (self.current_row == self.nx_row):
                        self.burst_delay = self.burst_delay + 34 + 17
                    else:
                        # Within one burst request, but row changed
                        self.burst_delay = self.burst_delay + 34 * 2 + 17 * 2
                    self.first_request = False
                    print("self.burst_delay:", self.burst_delay)
                # self.burst_delay_deque.append(self.burst_delay)
            else:
                print("Calculating Total Delay: accessing else statement")
                # calculating which row is read or wrote, for every burst
                print("nx_size is :", self.size)
                if (self.size < self.data_signal_width):
                    self.current_row = self.nx_row
                    if (self.addr // self.mem_row_size != self.current_row):
                        self.burst_delay = self.burst_delay + 34
                    self.nx_row = (self.addr + self.size) // self.mem_row_size
                    if (self.current_row == self.nx_row):
                        self.burst_delay = self.burst_delay + 17
                    else:
                        # Within one burst request, but row changed
                        self.burst_delay = self.burst_delay + 34 + 17 * 2
                    self.first_request = False
                else:
                    self.current_row = self.nx_row
                    # reading from different row for starting addr
                    if (self.addr // self.mem_row_size != self.current_row):
                        self.burst_delay = self.burst_delay + 34

                    print("current row:", self.current_row)
                    self.nx_row = (self.addr + self.data_signal_width) // self.mem_row_size
                    print("next row:", self.nx_row)
                    if (self.current_row == self.nx_row):
                        self.burst_delay = self.burst_delay + 17
                    else:
                        # Within one burst request, but row changed
                        self.burst_delay = self.burst_delay + 34 + 17 * 2
                    self.first_request = False

                print("Burst_delay is :", self.burst_delay)
                # print_deque()
                print("//----------------End of Calculating Total Delay-------------------//")
        print("//-----------------------------------End of Dealing One Request-----------------------------------//")

