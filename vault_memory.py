from collections import deque
from standard import mem_request, mem_response
import math
import numpy as np
class VM:
    def print_deque(deque_to_print):
        for item in deque_to_print:
            print(item)

    def __init__(self, request_port, response_port,vault_memory):
        # Variables:
        # request_port: input deque from logic base to transmit memory requests
        # response_port: output deque to logic base to response with data on read requests
        
        self.request_port = request_port
        self.response_port = response_port
        
        # self.memory_bank= np.zeros(2**32//8, dtype=np.uint64) #byte addressable, 4GB memory size
        self.memory_bank = vault_memory
        self.mem_row_size = 1024 # bytes,8192 bits
        self.mem_bus_bandwidth =128 #bytes, 1024bits
        self.current_row = 0   
        self.nx_row = 0
        self.burst_num = 0
        # https://www.crucial.com/articles/about-memory/difference-between-speed-and-latency Clock Cycle Time=0.42ns   
        self.burst_delay = 0   #T_CAS=40 cycles=16.8ns=17 cycles if hits, T_RCD=39 cycles=16.38=17cycles, T_RP=39 cycles=17cycles
        self.burst_delay_deque = deque()
        self.burst_size_deque = deque()
        self.request_processing = False
        self.first_request = True
        self.cmd=0
        self.data=0
        self.addr=0
        self.size=0

    def one_cycle(self):
        
        print("If request in Processing:",self.request_processing)
        print("Left Burst Delay:",self.burst_delay)
        
        #continue reading or writing if not zero
        if self.burst_delay>1 :
            self.burst_delay= self.burst_delay-1
            return

        if (self.request_processing==True and self.burst_delay==1 and self.cmd=="read"):
            print("//-------------------Accessing Reading Request Finial cycle-----------------------//")
            Read_Data= np.zeros(16, dtype=np.uint64)
            if self.burst_size_deque:
                burst_size=self.burst_size_deque.popleft()
            for i in range (burst_size):
                Read_Data[i % 16] = self.memory_bank[(self.addr // 8 + i)]
            print("Read_Data Output:", Read_Data, "i:", i)
            self.response_port.append(mem_response(Read_Data))
            Read_Data = np.zeros(16, dtype=np.uint64)
            if self.burst_delay_deque:
                print("Dealing with next burst request")
                self.burst_delay = self.burst_delay_deque.popleft()
                return
            self.request_processing=False
            print("//--------------Finish Accessing Reading Request Finial cycle-------------------//")
            return
        if (self.request_processing == True and self.burst_delay == 1 and self.cmd == "write"):
            print("//-------------------Accessing Writing Request Finial cycle-----------------------//")
            for i in range(math.ceil(self.size/8)):
                self.memory_bank[self.addr//8+i]=self.data[i]
            self.request_processing = False
            self.burst_delay = 0
            self.cmd = 0
            self.data=0
            self.addr=0
            self.size=0
            self.burst_num = 0
            print("//--------------Finish Accessing Reading Request Finial cycle-------------------//")
            return



        # if there is request in request_port deque?
        if not self.request_port :
            return
        #pop oldest requests from deque
        req= self.request_port.popleft()
        print("//-----------------------------------Dealing with One Request---------------------------------//")

        print("Processing Request:","command:",self.cmd,"addr in bytes:",req.addr,"size in bytes:",req.size,"Data:",req.data)
        self.burst_delay = 0
        self.cmd = 0
        self.data = 0
        self.addr = 0
        self.size = 0
        self.burst_num = 0
        self.cmd=req.cmd
        self.addr=req.addr   #assume in bytes
        self.data=req.data
        self.size=req.size   #assume in bytes
        self.request_processing=True
        print("self.nx_row:",self.nx_row,"self.current_row:",self.current_row)
        

        #read request
        if self.cmd=="read":
            # calculate need how many Bursts, round up vaule, evey burst can deal with 128 bytes
            self.burst_num = math.ceil(self.size / self.mem_bus_bandwidth)
            print("How many Burst request needed:", self.burst_num)
            #calculating total delay
            print("//-------------------Calculating Reading Request Total Delay-------------------//")
            nx_size=self.size
            for i in range(1,self.burst_num+1):
                #first requesting, Open row and hit
                if(self.first_request ==True):
                    #if nx_size<128 can not calculate  self.nx_row = (addr + i*128) // self.mem_row_size
                    if(nx_size<128):
                        self.current_row = self.nx_row
                        self.nx_row = (self.addr + nx_size) // self.mem_row_size
                        if (self.current_row == self.nx_row):
                            self.burst_delay = self.burst_delay + 34 + 17
                        else:
                            # Within one burst request, but row changed
                            self.burst_delay = self.burst_delay + 34 * 2 + 17 * 2
                            # self.burst_delay_deque.append(self.burst_delay)
                        self.burst_size_deque.append(math.ceil(nx_size/8))
                        self.first_request = False
                    else:
                        print("Calculating Total Delay: accessing self.first_request ==True statement")
                        self.current_row = self.nx_row
                        print("current row:",self.current_row)
                        self.nx_row = (self.addr + i * 128) // self.mem_row_size
                        print("next row:", self.nx_row)
                        if(self.current_row==self.nx_row):
                            self.burst_delay = self.burst_delay + 34 + 17
                        else:
                            #Within one burst request, but row changed
                            self.burst_delay = self.burst_delay + 34*2 + 17*2
                        self.burst_size_deque.append(16)
                        nx_size = nx_size - 128
                        self.first_request = False
                    self.burst_delay_deque.append(self.burst_delay)
                    self.burst_delay = 0

                else:
                    print("Calculating Total Delay: accessing else statement")
                #calculating which row is read or wrote, for every burst
                    if(i==1):
                        print("nx_size is :", nx_size)
                        if (nx_size < 128):
                            self.current_row = self.nx_row
                            if (self.addr // self.mem_row_size != self.current_row):
                                self.burst_delay = self.burst_delay + 34
                            self.nx_row = (self.addr + nx_size) // self.mem_row_size
                            if (self.current_row == self.nx_row):
                                self.burst_delay = self.burst_delay + 17
                            else:
                                # Within one burst request, but row changed
                                self.burst_delay = self.burst_delay + 34 + 17 * 2
                                # self.burst_delay_deque.append(self.burst_delay)
                            self.burst_size_deque.append(math.ceil(nx_size / 8))
                            self.first_request = False
                        else:
                            self.current_row = self.nx_row
                            #reading from different row for starting addr
                            if (self.addr // self.mem_row_size != self.current_row):
                                self.burst_delay = self.burst_delay + 34

                            print("current row:", self.current_row)
                            self.nx_row = (self.addr + i * 128) // self.mem_row_size
                            print("next row:", self.nx_row)
                            if (self.current_row == self.nx_row):
                                self.burst_delay = self.burst_delay + 17
                            else:
                                # Within one burst request, but row changed
                                self.burst_delay = self.burst_delay + 34 + 17 * 2
                            self.first_request = False
                            self.burst_size_deque.append(16)
                            nx_size = nx_size - 128
                        self.burst_delay_deque.append(self.burst_delay)
                        self.burst_delay = 0
                        print("i is:", i, "ith burst delay is :", self.burst_delay)
                    else:
                        print("nx_size is :",nx_size )
                        if (nx_size < 128):
                            self.current_row = self.nx_row
                            print("Current Row: ", self.current_row)
                            self.nx_row = (self.addr+i*128 + nx_size) // self.mem_row_size
                            print("Next Row: ", self.nx_row)
                            # if burst do not hit row, add opening another row penalty
                            if (self.nx_row != self.current_row):
                                print("Current Row is not the same as Next Row, need to add latency")
                                self.burst_delay = self.burst_delay + 34 + 17
                            else:
                                print("Row hit delay")
                                self.burst_delay = self.burst_delay + 17
                            self.burst_size_deque.append(math.ceil(nx_size / 8))
                        else:
                            self.current_row=self.nx_row
                            print("Current Row: ",self.current_row)
                            self.nx_row=(self.addr+i*128)//self.mem_row_size
                            print("Next Row: ",self.nx_row)
                            #if burst do not hit row, add opening another row penalty
                            if(self.nx_row != self.current_row):
                                print("Current Row is not the same as Next Row, need to add latency")
                                self.burst_delay=self.burst_delay+34+17
                            else:
                                print("Row hit delay")
                                self.burst_delay = self.burst_delay + 17
                            self.burst_size_deque.append(16)
                            nx_size=nx_size-128
                        self.burst_delay_deque.append(self.burst_delay)
                        self.burst_delay=0
                        print("i is:", i, "total burst delay is :", self.burst_delay)
            print("Burst_delay is :",self.burst_delay )
            for item in self.burst_delay_deque:
                print("burst_delay_deque:",item)
            for i in self.burst_size_deque:
                print("burst_size_deque:",i)
            print("//----------------End of Calculating Total Delay-------------------//")
            self.burst_delay=self.burst_delay_deque.popleft()
            print("first burst request delay is :",self.burst_delay)
            # for item in self.burst_delay_deque:
            #     print("burst_delay_deque:",item)
            # for i in self.burst_size_deque:
            #     print("burst_size_deque:",i)
        #write request
        elif self.cmd=="write":

            print("//---------------Calculating Writing Request Total Delay-------------------//")
            nx_size=self.size
            # first requesting, Open row and hit
            if (self.first_request == True):
                print("Calculating Total Delay: accessing self.first_request ==True statement")
                self.current_row = self.nx_row
                print("current row:", self.current_row)
                self.nx_row = (self.addr + nx_size) // self.mem_row_size
                print("next row:", self.nx_row)
                if (self.current_row == self.nx_row):
                    self.burst_delay = self.burst_delay + 34 + 17
                else:
                    # Within one burst request, but row changed
                    self.burst_delay = self.burst_delay + 34 * 2 + 17 * 2
                self.first_request = False
            else:
                print("Calculating Total Delay: accessing else statement")
                # calculating which row is read or wrote, for every burst

                self.current_row = self.nx_row
                # reading from different row for start addr
                if (self.addr // self.mem_row_size != self.current_row):
                    self.burst_delay = self.burst_delay + 34

                print("current row:", self.current_row)
                self.nx_row = (self.addr + nx_size) // self.mem_row_size
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

