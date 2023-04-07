from collections import deque
from standard import mem_request, mem_response, TrackTable, TrackTableEntry
import math
import numpy as np
import vault_bank as vb

class VM:
    def print_deque(deque_to_print):
        for item in deque_to_print:
            print(item)

    def __init__(self, request_port, response_port,vault_memory):
        # Variables:
        # request_port: input deque from logic base to transmit memory requests
        # response_port: output deque to logic base to response with data on read requests
        self.vault_bank_req_port = [deque() for _ in range(8)]
        # print("self.vault_bank_req_port:", self.vault_bank_req_port, type(self.vault_bank_req_port))
        self.vault_bank_resp_port = [deque() for _ in range(8)]
        self.vault_bank_size = 2**32 // 8
        self.vault_bank_mem = [vault_memory[i * self.vault_bank_size//4: (i + 1) * self.vault_bank_size//4] for i in range(8)]
        self.vault_bank = [None] * 8
        for i in range(8):
            self.vault_bank[i] = vb.vault_bank(self.vault_bank_req_port[i], self.vault_bank_resp_port[i], self.vault_bank_mem[i],i)


        self.track_table = TrackTable()
        # print("self.track_table:", self.track_table, type(self.track_table))

        self.request_port = request_port
        self.response_port = response_port
        #to track what tags need
        # self.track_table = deque()
        # self.req_tags = deque()
        #if getting all tags back
        # self.track_table_ready_bit = deque()
        # self.memory_bank= np.zeros(2**32//8, dtype=np.uint64) #byte addressable, 4GB memory size
        # self.memory_bank = vault_memory
        self.mem_row_size = 1024  # bytes,8192 bits
        self.data_signal_width = 32  # bytes, 256bits
        # self.current_row = 0
        # self.nx_row = 0
        self.burst_num = 0
        # https://www.crucial.com/articles/about-memory/difference-between-speed-and-latency Clock Cycle Time=0.42ns
        # self.burst_delay = 0  # T_CAS=40 cycles=16.8ns=17 cycles if hits, T_RCD=39 cycles=16.38=17cycles, T_RP=39 cycles=17cycles
        # self.burst_delay_deque = deque()
        # self.burst_size_deque = deque()
        # self.request_processing = False
        # self.first_request = True
        self.cmd = 0
        self.data = 0
        self.addr = 0
        self.size = 0
        self.req_tag = 0
        self.req_bank_tag=0

        # print("self.track_table:", self.track_table, type(self.track_table))
    #getting tag for req,range[1,999]
    def GetReqTag(self):
        if (self.req_tag==1000):
            self.req_tag=1
        else:
            self.req_tag=self.req_tag+1
        return self.req_tag
    #getting 2nd level tag to store in Track table
    def GetBankTag(self):
        if (self.req_bank_tag==2000):
            self.req_bank_tag=1
        else:
            self.req_bank_tag=self.req_bank_tag+1
        return self.req_bank_tag

    def one_cycle(self):
        # print("self.track_table:", self.track_table, type(self.track_table))
        # print("self.vault_bank_mem[1]", self.vault_bank_mem[1])
        #output from each vault_bank mem_ctrl
        if self.request_port:
            req = self.request_port.popleft()
            req_addr_size=0
            Tags = []
            num_burst = math.ceil(req.size / self.data_signal_width)
            if req.cmd == "read":
                # print("self.track_table:", self.track_table, type(self.track_table))
                next_size = req.size
                for i in range(1, num_burst + 1):
                    if (next_size > self.data_signal_width):
                        req_addr_size=req_addr_size+self.data_signal_width
                        start_addr = req.addr + (i - 1) * self.data_signal_width
                        end_addr = start_addr + self.data_signal_width
                        if ((start_addr // self.vault_bank_size) == (end_addr // self.vault_bank_size)):
                            bank_idx = start_addr // self.vault_bank_size
                            bank_tag = self.GetBankTag()
                            req_bank=mem_request(req.cmd, start_addr, req.data,self.data_signal_width, bank_tag)
                            self.vault_bank[bank_idx].request_port.append(req_bank)
                            next_size = next_size - self.data_signal_width
                            Tags.append(bank_tag)
                        else:
                            bank_idx1 = start_addr // self.vault_bank_size
                            bank_tag1 = self.GetBankTag()
                            Tags.append(bank_tag1)
                            size1 = self.vault_bank_size * (bank_idx1 + 1) - start_addr
                            req1_bank=mem_request(req.cmd, start_addr, req.data,size1, bank_tag1)
                            self.vault_bank[bank_idx1].request_port.append(req1_bank)

                            bank_idx2 = end_addr // self.vault_bank_size
                            new_start_addr = (bank_idx2) * self.vault_bank_size
                            bank_tag2 = self.GetBankTag()
                            size2 = self.data_signal_width - size1
                            Tags.append(bank_tag2)
                            req2_bank = mem_request(req.cmd, start_addr, req.data, size1, bank_tag2)
                            self.vault_bank[bank_idx2].request_port.append(req2_bank)
                            next_size = next_size - self.data_signal_width
                    else:
                        start_addr = req.addr + req_addr_size #+ (i - 1) * (self.data_signal_width//4) +

                        end_addr = start_addr + next_size
                        if ((start_addr // self.vault_bank_size) == (end_addr // self.vault_bank_size)):
                            bank_idx = start_addr // self.vault_bank_size
                            bank_tag = self.GetBankTag()
                            req_bank = mem_request(req.cmd, start_addr, req.data, next_size, bank_tag)
                            self.vault_bank[bank_idx].request_port.append(req_bank)
                            Tags.append(bank_tag)
                        else:
                            bank_idx1 = start_addr // self.vault_bank_size
                            bank_tag1 = self.GetBankTag()
                            Tags.append(bank_tag1)
                            size1 = self.vault_bank_size * (bank_idx1 + 1) - start_addr
                            req1_bank = mem_request(req.cmd, start_addr, req.data,size1, bank_tag1)
                            self.vault_bank[bank_idx1].request_port.append(req1_bank)

                            bank_idx2 = end_addr // self.vault_bank_size
                            new_start_addr = (bank_idx2) * self.vault_bank_size
                            bank_tag2 = self.GetBankTag()
                            size2 = next_size - size1
                            Tags.append(bank_tag2)
                            req2_bank =mem_request (req.cmd, new_start_addr, req.data, size2, bank_tag2)
                            self.vault_bank[bank_idx2].request_port.append(req2_bank)
                self.track_table.add_entry(Tags,req.req_tag)
            elif req.cmd == "write":
                next_size = req.size
                for i in range(1, num_burst + 1):
                    if (next_size > self.data_signal_width):
                        req_addr_size = req_addr_size + self.data_signal_width
                        start_addr = req.addr + (i - 1) * self.data_signal_width
                        end_addr = start_addr + self.data_signal_width
                        if ((start_addr // self.vault_bank_size) == (end_addr // self.vault_bank_size)):
                            bank_idx = start_addr // self.vault_bank_size
                            bank_tag = self.GetBankTag()
                            req_bank = mem_request(req.cmd, start_addr, req.data, self.data_signal_width, bank_tag)
                            self.vault_bank[bank_idx].request_port.append(req_bank)
                            next_size = next_size - self.data_signal_width
                            Tags.append(bank_tag)
                        else:
                            bank_idx1 = start_addr // self.vault_bank_size
                            bank_tag1 = self.GetBankTag()
                            Tags.append(bank_tag1)
                            size1 = self.vault_bank_size * (bank_idx1 + 1) - start_addr
                            req1_bank = mem_request(req.cmd, start_addr, req.data, size1, bank_tag1)
                            self.vault_bank[bank_idx1].request_port.append(req1_bank)

                            bank_idx2 = end_addr // self.vault_bank_size
                            new_start_addr = (bank_idx2) * self.vault_bank_size
                            bank_tag2 = self.GetBankTag()
                            size2 = self.data_signal_width - size1
                            Tags.append(bank_tag2)
                            req2_bank = mem_request(req.cmd, start_addr, req.data, size1, bank_tag2)
                            self.vault_bank[bank_idx2].request_port.append(req2_bank)
                            next_size = next_size - self.data_signal_width
                    else:
                        start_addr = req.addr + req_addr_size  # + (i - 1) * (self.data_signal_width//4) +
                        # start_addr=self.start_addr
                        end_addr = start_addr + next_size
                        if ((start_addr // self.vault_bank_size) == (end_addr // self.vault_bank_size)):
                            bank_idx = start_addr // self.vault_bank_size
                            bank_tag = self.GetBankTag()
                            req_bank = mem_request(req.cmd, start_addr, req.data, next_size, bank_tag)
                            self.vault_bank[bank_idx].request_port.append(req_bank)
                            Tags.append(bank_tag)
                        else:
                            bank_idx1 = start_addr // self.vault_bank_size
                            bank_tag1 = self.GetBankTag()
                            Tags.append(bank_tag1)
                            size1 = self.vault_bank_size * (bank_idx1 + 1) - start_addr
                            req1_bank = mem_request(req.cmd, start_addr, req.data, size1, bank_tag1)
                            self.vault_bank[bank_idx1].request_port.append(req1_bank)

                            bank_idx2 = end_addr // self.vault_bank_size
                            new_start_addr = (bank_idx2) * self.vault_bank_size
                            bank_tag2 = self.GetBankTag()
                            size2 = next_size - size1
                            Tags.append(bank_tag2)
                            req2_bank = mem_request(req.cmd, new_start_addr, req.data, size2, bank_tag2)





        for i in range(8):  # iterate over each vault_bank object
            print(f"Request Port in vault_bank i is:", i)
            for req in self.vault_bank[i].request_port:  # iterate over each request in the request port
                print("req.cmd:",req.cmd,"req.addr:",req.addr,"req.data:",req.data,"req.size:",req.size,"req.tag:",req.req_tag)
        for i in range(8):
            print("accessing vault_bank idx is:",i)
            self.vault_bank[i].one_cycle()
        print("return from each bank, accessing response")
        #response
        for i in range(8):
            # self.vault_bank[i].one_cycle()
            if self.vault_bank[i].response_port:
                resp=self.vault_bank[i].response_port.popleft()
                self.track_table.update_entry(resp.tag,resp.data)
        #if ready bit it set, send data to response port
        self.track_table.transfer_to_resp_port(self.response_port)
        print(self.track_table)
        print("finish this cycle")











