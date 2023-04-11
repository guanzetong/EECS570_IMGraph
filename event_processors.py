import numpy as np
import copy
from collections import deque
from vault_mem import VM
from standard import mem_request, mem_response, event
import random

class EP_h1:
    
    def __init__(self, eq_i, eq_o, ep_0_i, ep_0_o, ep_1_i, ep_1_o,
                 ep_idx_ranges, num_vaults, func, position):
        # Variables
        # eq_i/eq_o: input/output deque with event queues
        # ep_X_i/ep_X_o: input/output deque with adjacent event processors
        # ep_idx_ranges: a list of [min, max] to specify the range assigned to this EP and adjacent EPs
        # ep_idx_ranges[0..1] = [self, ep_0, ep_1]
        # busy: list of booleans
        # buffer: list of deque
        # n: initial for neighbor number
        
        self.eq_i   = eq_i
        self.eq_o   = eq_o
        self.ep_0_i = ep_0_i
        self.ep_0_o = ep_0_o
        self.ep_1_i = ep_1_i
        self.ep_1_o = ep_1_o
        self.ep_idx_ranges = ep_idx_ranges
        self.position = position
        self.func = func
        self.count = []
        self.busy = []
        self.buffer = []
        self.n = []
        self.delta = []
        self.Vp = []
        self.Vp_new = []
        self.Vid = []
        self.vp_ready = []
        self.st_ready = []
        self.neighbor_ready = []
        self.vp_tag = []
        self.st_tag = []
        self.neighbor_tag = []
        self.neighbor_deque = []
        self.vp_new_written = []
        
        for i in range(num_vaults):
            self.busy.append(False)
            self.buffer.append(deque())
            self.count.append(0)
            self.n.append(0)
            self.delta.append(0)
            self.Vp.append(0)
            self.Vp_new.append(0)
            self.Vid.append(None)
            self.vp_ready.append(False)
            self.st_ready.append(False)
            self.neighbor_ready.append(False)
            self.vp_tag.append(None)
            self.st_tag.append(None)
            self.neighbor_tag.append(None)
            self.neighbor_deque.append(deque())
            self.vp_new_written.append(False)

        
        # Instantiate vault memories
        self.vault_mem = []
        memory_bank_part = []
        if func.lower() == 'pagerank':
            memory_bank = np.zeros(2**21 // 4, dtype=np.uint32)
        elif func.lower() == 'sssp' or func.lower() == 'bfs':
            # for i in range(100):
            #     memory_bank_part.append(np.float32(np.inf))
            memory_part = [np.float32(np.inf), np.float32(np.inf), np.float32(np.inf), np.float32(np.inf), np.float32(np.inf), 44, 52, 56, 64, 68, 76, 1,2,3,1,3,4,2 ]
            memory_part2 = list(np.zeros(2**21 // 4 - 100 -18, dtype=np.uint32))  # read from file
            memory_bank = memory_part + memory_part2
        for i in range(num_vaults):
            request_port = deque()
            response_port = deque()
            vault_mem = VM(request_port, response_port, memory_bank)
            self.vault_mem.append(vault_mem)

        # Initialize vp of each vault based on algorithm
        vp_num = (self.ep_idx_ranges[1]-self.ep_idx_ranges[0]) // 32 + 1
        vp_addr = 0
        # if func.lower() == "pagerank":
        #     for i in range(32):
        #         for j in range(vp_num):
        #             req = mem_request("write", vp_addr+j*4, 0) # vp 32 bits = 4 bytes
        #             self.vault_mem[i].request_port.append(req)

        # elif func.lower() == 'sssp' or func.lower() == 'bfs':
        #     for i in range(32):
        #         for j in range(vp_num):
        #             req = mem_request("write", vp_addr+j*4, float('inf'),0)
        #             self.vault_mem[i].request_port.append(req)


    def alloc_vault(self, Vid):
        '''
        input:
        Vid: vertex id
        Return:
        vault_idx: idx of related vault (from 0 to 31)
        '''
        vault_capacity = (self.ep_idx_ranges[1]-self.ep_idx_ranges[0]) // 32 + 1
        vault_index = (Vid-self.ep_idx_ranges[0])// vault_capacity
        return int(vault_index)

    def vertex_property_addr(self, Vid):
        return int(Vid * 4)

    def vertex_st_addr(self, Vid):
        return int(Vid*4 + 20)  # 0 2 3 5 6 7

    def vertex_neighbor_addr(self, St1):
        #vault_num = self.alloc_vault(Vid)
        return int(St1 * 4 + 44)

    def allocate_event_vault_buffer(self, vault_idx):
      '''
      read event from buffer, do:
      1) get Vid and delta
      2) make read request for Vp
      3) make read request for St

      return:
        Vid, delta, vp_tag, st_tag
      '''
      if len(self.buffer[vault_idx]) == 0:
           return None
      else: #get an event from ep_i deque
        a = self.buffer[vault_idx].popleft()
        #   delta     = self.eq_i.popleft().val  #vault num is a result of the previous function
        vertex_id = a.idx
        delta = a.val
        vault_num = self.alloc_vault(Vid=vertex_id)
        # read vertex property request
        vp_addr = self.vertex_property_addr(Vid=vertex_id)
        vp_tag = self.vault_mem[vault_num].GetReqTag()
        req_vp = mem_request("read", vp_addr, None, 4, vp_tag)
        print(f"reading vp: vp_addr={vp_addr}")
        self.vault_mem[vault_num].request_port.append(req_vp)
        # read vertex start address request
        v_st_addr = self.vertex_st_addr(Vid=vertex_id)
        st_tag = self.vault_mem[vault_num].GetReqTag()
        req_v_st = mem_request(cmd="read", addr=v_st_addr, data=None, size=8, req_tag=st_tag)
        print(f"reading start addr: st_addr={v_st_addr}")
        self.vault_mem[vault_num].request_port.append(req_v_st)
        return vertex_id, delta, vp_tag, st_tag

    def reduce(self, old_value, delta, func): #delta = allocate_event_vault_port()[1]
        '''
        input:
        func: which algorithm
        old_value: stale vertex property in vm          # use read_vp function
        return:
        new_value of vertex property
        '''
        if old_value != None:
            if func.lower() == 'pagerank' or func.lower() == 'adsorption':
                new_value = old_value + delta
            elif func.lower() == 'sssp' or func.lower() == 'bfs':
                new_value = min(old_value, delta)
            elif func.lower() =='comp':
                new_value = max(old_value, delta)
            else:
                new_value = old_value + delta
        else:
            return None
        return new_value

    def read_VP(self, vault_num, vp_tag, vp_ready):
        '''
        return Vp vp_ready
        '''
        if len(self.vault_mem[vault_num].response_port) == 0:
           print("Tag isn't ready")
           return None, None
        else:
            length = len(self.vault_mem[vault_num].response_port)
            for i in range(length):
                response = self.vault_mem[vault_num].response_port[i]
                if response.req_tag == vp_tag:
                    Vp = response.data
                    vp_ready = True
                    self.vault_mem[vault_num].response_port.remove(self.vault_mem[vault_num].response_port[i])
                    print(f"Vp is returned, Vp={Vp}, response_vp_tag={response.req_tag}, req_vp_tag={vp_tag}")
                    return Vp, vp_ready
            print("No matched vp_tag, Vp is not ready")
            return None, None

    def Update_VP(self, Vid, Vp_new):
        '''
        write Vp_new to vault_mem
        return None
        '''
        
        #Vp_old = self.read_VP(Vid)
        #Vp_old =Vp
        #Vp_new = self.reduce(Vp, delta, func)
        print("Vp_new (after reduce): ",Vp_new)
        # write Vp_new to mem
        if Vp_new != None:
            Vp_addr = self.vertex_property_addr(Vid)
            vault_num = self.alloc_vault(Vid)
            #tag_w_vp = self.vault_mem[vault_num].GetReqTag()
            req_w_Vp = mem_request("write", Vp_addr, [Vp_new], 4, 0)
            print(f"writing Vp_new, Vp_new = {Vp_new}")
            self.vault_mem[vault_num].request_port.append(req_w_Vp)
            self.vp_new_written[vault_num] = True
        else:
            print('Vp_new is not ready')
        return None
        

    def get_edge_num(self, Vid, st_tag):
        '''
        read response port to get start address and create a request to read neighbor
        return number of neighbors, st_ready, neighbor_tag
        '''
        vault_num = self.alloc_vault(Vid)
        if len(self.vault_mem[vault_num].response_port) == 0:
           print("start addr is not ready")
           return None, None, None
        else:
            length = len(self.vault_mem[vault_num].response_port)
            for i in range(length):
                response = self.vault_mem[vault_num].response_port[i]
                if response.req_tag == st_tag:
                    St1 = response.data[0]
                    St2 = response.data[1]
                    n = St2 - St1  # bytes number for neighbors
                    st_ready = True
                    self.vault_mem[vault_num].response_port.remove(self.vault_mem[vault_num].response_port[i])
                    print(f"St1, St2 is returned, St1={St1}, St2={St2} response_st_tag={response.req_tag}, req_st_tag={st_tag}\n")
                    neighbor_tag = self.vault_mem[vault_num].GetReqTag()
                    neighbor_addr = St1
                    req_neighbor = mem_request("read", neighbor_addr, None, n, neighbor_tag)
                    self.vault_mem[vault_num].request_port.append(req_neighbor)
                    print(f"neigbor number is {n/4}, neighbor_tag is {neighbor_tag}, sending req_neighbor ")
                    return n, st_ready, neighbor_tag
            print("No matched st_tag, St is not ready")
            return None, None, None


    def Propagate(self, delta, number_neighbor, func='pagerank', beta=0.85):
        '''
        just algorithm
        delta = reduce(read_vp(), allocate_event_vault_port()[1])
        number_neighbor: number of neighbor
        '''
         
        if func.lower() == 'pagerank':
            new_value = beta*delta/number_neighbor
        elif func.lower() == 'adsorption':
            new_value = beta*delta
        elif func.lower() =='comp' or func.lower() =='sssp':
            new_value = delta + 1
        elif func.lower() == 'bfs':
            new_value = 0
        else:
            new_value = beta*delta/number_neighbor
        return new_value

#####
# pagerank: delta(from eq) < threshold, not do propagate
####
    def Propagate_condion(self,Vp_new, Vp, threshold):
        '''
        decide whether to do propagate
        return:
            boolean
        '''
        if Vp_new is None or Vp is None:
            return False
        elif np.abs(Vp_new-Vp) <= threshold:
            print(f'Vp_new({Vp_new}) - Vp({Vp}) <= threshold({threshold})')
            return False
        else:
            return True
        
    def read_neighbor(self, vault_num, neighbor_tag):
        '''
        read neighbor vertex id, if success set self.neighbor_ready[vault_num] to true
        return:
            neighbor_deque----deque that store all neighbor vid
        '''
        if self.st_ready[vault_num] and len(self.vault_mem[vault_num].response_port)!=0 :
            if not self.vp_ready[vault_num]:
                print("Bug: Vp is later than neighbor")
            else:
                length = len(self.vault_mem[vault_num].response_port)
                neighbor_deque = deque()
                for i in range(length):
                    response = self.vault_mem[vault_num].response_port[i]
                    if response.req_tag == neighbor_tag:
                        neighbors = self.vault_mem[vault_num].response_port[i].data
                        self.vault_mem[vault_num].response_port.remove(self.vault_mem[vault_num].response_port[i])
                        for item in neighbors:
                            neighbor_deque.append(item)
                        print("neighbors are ready, stored in neighbor_deque")
                        self.neighbor_ready[vault_num] = True
                        print(f'neighbor_deque is {neighbor_deque}')
                        return neighbor_deque
                print("neighbor tag isn't ready")
                print(f'response port number: {length}')
                self.neighbor_ready[vault_num] = False
        else: self.neighbor_ready[vault_num] = False
        return None


    def PropagateNewEvent(self, N_src, delta, vault_num, neighbor_deque, count=0, beta=0.85, func='pagerank'):
        '''
        use propagate function to create new event
        input:
        each cycle read a vid from neighbor_deque and do propagate
        Return:
            count: which neighbor is being processed
            busy: flag indicate not taking event in
            N_src: neighbor number
        '''
        #read vault_mem[x].respond_port.popleft()//64 bit neighbour vertex_id
        #propogate function => new_delta
        #self.eq_o.append(event(vertex_id, new_delta))
        if not self.neighbor_ready[vault_num]:
            return None
        else:
            if count < N_src/4-1:
                busy = True
                new_delta = self.Propagate(delta, N_src/4, func, beta) # function of alg
                new_Vid = neighbor_deque.popleft()
                print('new_Vid after propagate:', new_Vid)
                print('new_delta after propagate:', new_delta)
                self.eq_o.append(event(np.uint32(new_Vid),np.uint32(new_delta)))
                count +=1
                print('count: ',count)
            elif count == N_src/4-1:  #last propagate
                print('last count: ',count)
                busy = False
                new_Vid = neighbor_deque.popleft()
                print('new_Vid after propagate:', new_Vid)
                new_delta = self.Propagate(delta, N_src/4, func, beta) # function of alg
                print('new_delta after propagate:', new_delta)
                self.eq_o.append(event(np.uint32(new_Vid),np.uint32(new_delta)))
                print("finish last propagate")
                self.vp_ready[vault_num] = False
                self.st_ready[vault_num] = False
                self.neighbor_ready[vault_num] = False
                count = 0
            else:
                print('error')
            return count, busy, N_src
        
    def forward_PropagtedEvent(self):
        for event in self.ep_0_i:
            self.eq_i.append(event)
        for event in self.ep_1_i:
            self.eq_i.append(event)
        return None
    
    def forward_message(self,incoming_events):
        '''
               < ep0 >
            <          >
           ep1   eq   ep3
            >          <
               < ep2 >
        '''
        event_coming_this_ep = []
        for event in incoming_events:
            if (event.idx > self.ep_idx_ranges[1]):
                if (self.position == 0):
                    self.ep_0_o.append(event)  # n to ne
                elif (self.position == 1):
                    self.ep_1_o.append(event)  # w to sw
                elif (self.position == 2):
                    self.ep_0_o.append(event)  # s to se
                elif (self.position == 3):
                    self.ep_0_o.append(event)  # e to ne
            elif(event.idx < self.ep_idx_ranges[0]):
                if (self.position == 0):
                    self.ep_1_o.append(event)  # n to nw
                elif (self.position == 1):
                    self.ep_0_o.append(event)  # w to nw
                elif (self.position == 2):
                    self.ep_1_o.append(event)  # s to sw
                elif (self.position == 3):
                    self.ep_1_o.append(event)  # e to se
            else:
                event_coming_this_ep.append(event)
        return event_coming_this_ep

    def buffer_event(self, buffer_idx, incoming_events):
        '''
        allocate all incoming_events into each buffer based on Vid
        return None
        '''
        for i in range(len(incoming_events)):
            if self.alloc_vault(incoming_events[i].idx) == buffer_idx:
                self.buffer[buffer_idx].append(incoming_events[i])
        return None

    def one_cycle(self, num_vaults):
        incoming_events = []
        for j in range(len(self.eq_i)):
            incoming_events.append(self.eq_i.popleft())
        event_coming_this_ep = self.forward_message(incoming_events)
        print(f"incoming events number for all: {len(incoming_events)}\n")
        print(f"incoming events number for current ep: {len(event_coming_this_ep)}") # check the number of events feed into ep this cycle
        for i in range(num_vaults):
            # forward events propagate by adjacent eps
            self.forward_PropagtedEvent()
            # read events into buffer
            self.vault_mem[i].one_cycle()
            self.buffer_event(i, event_coming_this_ep)
            print(f'buffer_{i} number:{len(self.buffer[i])}')
            if not self.busy[i]: # when not busy, try to take a new event if any
                print('not busy, try to get a new event')
                # read new events
                if (len(self.buffer[i]) != 0):
                    (self.Vid[i], self.delta[i], self.vp_tag[i], self.st_tag[i]) = self.allocate_event_vault_buffer(i)
                    self.busy[i] = True
                    self.Vp[i] = None
                    self.Vp_new[i] = None
                    self.n[i] = None
                    print(f"vault[{i}] is reading event from buffer{i}")  # check working buffer
                else:
                    pass
            else:# when busy not accept new event, reading Vp,St or propagating
                print('busy, try to read needed data')
                if not self.vp_ready[i] and self.vp_tag[i] !=None:
                    self.Vp[i], self.vp_ready[i] = self.read_VP(i, self.vp_tag[i], self.vp_ready[i])
                elif not self.vp_new_written[i]:
                    Vp_new = self.reduce(self.Vp[i], self.delta[i],self.func)
                    self.Update_VP(self.Vid[i], Vp_new)
                if not self.st_ready[i] and self.st_tag[i] != None:
                    self.n[i], self.st_ready[i], self.neighbor_tag[i],  = self.get_edge_num(self.Vid[i], self.st_tag[i])
                    print(f'now neighbor n:{self.n[i]}')
                else:
                    pass
                if not self.neighbor_ready[i] and self.neighbor_tag[i] != None:
                    self.neighbor_deque[i] = self.read_neighbor(i, self.neighbor_tag[i])
                    print(f'neighbor ready or not :{self.neighbor_ready[i]}')
                elif self.vp_ready[i] and self.st_ready[i] and self.neighbor_ready[i] and self.n[i] != None:
                    print('busy, data is ready, propagating')
                    print(f"number of neighbor(n[i]): {self.n[i]}")
                    self.count[i], self.busy[i], self.n[i] = self.PropagateNewEvent(N_src=self.n[i], delta=self.delta[i], vault_num=i, neighbor_deque=self.neighbor_deque[i], count=self.count[i], beta=0.85, func=self.func)
                else:
                    print("fetching data")
                return None


class EP_h2:
    def __init__(self, ep_0_i, ep_0_o, ep_1_i, ep_1_o,
                 ep_idx_ranges, num_vaults, func):
        # Variables
        # ep_X_i/ep_X_o: input/output deque with adjacent event processors
        # ep_idx_ranges: a list of [min, max] to specify the range assigned to this EP and adjacent EPs
        # ep_idx_ranges[0..0] = [self]

        self.ep_0_i = ep_0_i
        self.ep_0_o = ep_0_o
        self.ep_1_i = ep_1_i
        self.ep_1_o = ep_1_o
        self.ep_idx_ranges = ep_idx_ranges
        self.func = func
        self.count = []
        self.busy = []
        self.buffer = []
        self.n = []
        self.delta = []
        self.Vp = []
        self.Vp_new = []
        self.Vid = []
        self.vp_ready = []
        self.st_ready = []
        self.neighbor_ready = []
        self.vp_tag = []
        self.st_tag = []
        self.neighbor_tag = []
        self.neighbor_deque = []
        self.vp_new_written = []

        for i in range(num_vaults):
            self.busy.append(False)
            self.buffer.append(deque())
            self.count.append(0)
            self.n.append(0)
            self.delta.append(0)
            self.Vp.append(0)
            self.Vp_new.append(0)
            self.Vid.append(None)
            self.vp_ready.append(False)
            self.st_ready.append(False)
            self.neighbor_ready.append(False)
            self.vp_tag.append(None)
            self.st_tag.append(None)
            self.neighbor_tag.append(None)
            self.neighbor_deque.append(deque())
            self.vp_new_written.append(False)


        # Instantiate vault memories
        self.vault_mem = []
        memory_bank_part = []
        if func.lower() == 'pagerank':
            memory_bank = np.zeros(2**21 // 4, dtype=np.uint32)
        elif func.lower() == 'sssp' or func.lower() == 'bfs':
            # for i in range(100):
            #     memory_bank_part.append(np.float32(np.inf))
            memory_part = [np.float32(np.inf), np.float32(np.inf), np.float32(np.inf), np.float32(np.inf), np.float32(np.inf), 44, 52, 56, 64, 68, 76, 1,2,3,1,3,4,2 ]
            memory_part2 = list(np.zeros(2**21 // 4 - 100 -18, dtype=np.uint32))  # read from file
            memory_bank = memory_part + memory_part2
        for i in range(num_vaults):
            request_port = deque()
            response_port = deque()
            vault_mem = VM(request_port, response_port, memory_bank)
            self.vault_mem.append(vault_mem)

        # Initialize vp of each vault based on algorithm
        vp_num = (self.ep_idx_ranges[1]-self.ep_idx_ranges[0]) // 32 + 1
        vp_addr = 0
        # Instantiate vault memories
        self.vault_mem = []
        for i in range(num_vaults):
            request_port = deque()
            response_port = deque()
            vault_mem = VM(request_port, response_port)
            self.vault_mem.append(vault_mem)

    def alloc_vault(self, Vid):
        '''
        input:
        Vid: vertex id
        Return:
        vault_idx: idx of related vault (from 0 to 31)
        '''
        vault_capacity = (self.ep_idx_ranges[1]-self.ep_idx_ranges[0]) // 32 + 1
        vault_index = (Vid-self.ep_idx_ranges[0])// vault_capacity
        return int(vault_index)

    def vertex_property_addr(self, Vid):
        return int(Vid * 4)

    def vertex_st_addr(self, Vid):
        return int(Vid*4 + 20)  # 0 2 3 5 6 7

    def vertex_neighbor_addr(self, St1):
        #vault_num = self.alloc_vault(Vid)
        return int(St1 * 4 + 44)

    def allocate_event_vault_buffer(self, vault_idx):
      '''
      read event from buffer, do:
      1) get Vid and delta
      2) make read request for Vp
      3) make read request for St

      return:
        Vid, delta, vp_tag, st_tag
      '''
      if len(self.buffer[vault_idx]) == 0:
           return None
      else: #get an event from ep_i deque
        a = self.buffer[vault_idx].popleft()
        #   delta     = self.eq_i.popleft().val  #vault num is a result of the previous function
        vertex_id = a.idx
        delta = a.val
        vault_num = self.alloc_vault(Vid=vertex_id)
        # read vertex property request
        vp_addr = self.vertex_property_addr(Vid=vertex_id)
        vp_tag = self.vault_mem[vault_num].GetReqTag()
        req_vp = mem_request("read", vp_addr, None, 4, vp_tag)
        print(f"reading vp: vp_addr={vp_addr}")
        self.vault_mem[vault_num].request_port.append(req_vp)
        # read vertex start address request
        v_st_addr = self.vertex_st_addr(Vid=vertex_id)
        st_tag = self.vault_mem[vault_num].GetReqTag()
        req_v_st = mem_request(cmd="read", addr=v_st_addr, data=None, size=8, req_tag=st_tag)
        print(f"reading start addr: st_addr={v_st_addr}")
        self.vault_mem[vault_num].request_port.append(req_v_st)
        return vertex_id, delta, vp_tag, st_tag

    def reduce(self, old_value, delta, func): #delta = allocate_event_vault_port()[1]
        '''
        input:
        func: which algorithm
        old_value: stale vertex property in vm          # use read_vp function
        return:
        new_value of vertex property
        '''
        if old_value != None:
            if func.lower() == 'pagerank' or func.lower() == 'adsorption':
                new_value = old_value + delta
            elif func.lower() == 'sssp' or func.lower() == 'bfs':
                new_value = min(old_value, delta)
            elif func.lower() =='comp':
                new_value = max(old_value, delta)
            else:
                new_value = old_value + delta
        else:
            return None
        return new_value

    def read_VP(self, vault_num, vp_tag, vp_ready):
        '''
        return Vp vp_ready
        '''
        if len(self.vault_mem[vault_num].response_port) == 0:
           print("Tag isn't ready")
           return None, None
        else:
            length = len(self.vault_mem[vault_num].response_port)
            for i in range(length):
                response = self.vault_mem[vault_num].response_port[i]
                if response.req_tag == vp_tag:
                    Vp = response.data
                    vp_ready = True
                    self.vault_mem[vault_num].response_port.remove(self.vault_mem[vault_num].response_port[i])
                    print(f"Vp is returned, Vp={Vp}, response_vp_tag={response.req_tag}, req_vp_tag={vp_tag}")
                    return Vp, vp_ready
            print("No matched vp_tag, Vp is not ready")
            return None, None

    def Update_VP(self, Vid, Vp_new):
        '''
        write Vp_new to vault_mem
        return None
        '''
        #Vp_old = self.read_VP(Vid)
        #Vp_old =Vp
        #Vp_new = self.reduce(Vp, delta, func)
        print("Vp_new (after reduce): ",Vp_new)
        # write Vp_new to mem
        if Vp_new != None:
            Vp_addr = self.vertex_property_addr(Vid)
            vault_num = self.alloc_vault(Vid)
            #tag_w_vp = self.vault_mem[vault_num].GetReqTag()
            req_w_Vp = mem_request("write", Vp_addr, [Vp_new], 4, 0)
            print(f"writing Vp_new, Vp_new = {Vp_new}")
            self.vault_mem[vault_num].request_port.append(req_w_Vp)
            self.vp_new_written[vault_num] = True
        else:
            print('Vp_new is not ready')
        return None

    def get_edge_num(self, Vid, st_tag):
        '''
        read response port to get start address and create a request to read neighbor
        return number of neighbors, st_ready, neighbor_tag
        '''
        vault_num = self.alloc_vault(Vid)
        if len(self.vault_mem[vault_num].response_port) == 0:
           print("start addr is not ready")
           return None, None, None
        else:
            length = len(self.vault_mem[vault_num].response_port)
            for i in range(length):
                response = self.vault_mem[vault_num].response_port[i]
                if response.req_tag == st_tag:
                    St1 = response.data[0]
                    St2 = response.data[1]
                    n = St2 - St1
                    st_ready = True
                    self.vault_mem[vault_num].response_port.remove(self.vault_mem[vault_num].response_port[i])
                    print(f"St1, St2 is returned, St1={St1}, St2={St2} response_st_tag={response.req_tag}, req_st_tag={st_tag}\n")
                    neighbor_tag = self.vault_mem[vault_num].GetReqTag()
                    neighbor_addr = St1
                    req_neighbor = mem_request("read", neighbor_addr, None, n, neighbor_tag)
                    self.vault_mem[vault_num].request_port.append(req_neighbor)
                    print(f"neigbor number is {n/4}, neighbor_tag is {neighbor_tag}, sending req_neighbor ")
                    return n, st_ready, neighbor_tag
            print("No matched st_tag, St is not ready")
            return None, None, None


    def Propagate(self, delta, N_src, func='pagerank', beta=0.85):
        '''
        just algorithm
        delta = reduce(read_vp(), allocate_event_vault_port()[1])
        N_src = get_edge_num(Vid)
        '''
        if func.lower() == 'pagerank':
            new_value = beta*delta/N_src
        elif func.lower() == 'adsorption':
            new_value = beta*delta
        elif func.lower() =='comp' or func.lower() =='sssp':
            new_value = delta + 1
        elif func.lower() == 'bfs':
            new_value = 0
        else:
            new_value = beta*delta/N_src
        return new_value

#####
# pagerank: delta(from eq) < threshold, not do propagate
####
    def Propagate_condion(self,Vp_new, Vp, threshold):
        '''
        decide whether to do propagate
        return:
            boolean
        '''
        if Vp_new is None or Vp is None:
            return False
        elif np.abs(Vp_new-Vp) <= threshold:
            print(f'Vp_new({Vp_new}) - Vp({Vp}) <= threshold({threshold})')
            return False
        else:
            return True

    def read_neighbor(self, vault_num, neighbor_tag):
        '''
        read neighbor vertex id, if success set self.neighbor_ready[vault_num] to true
        return:
            neighbor_deque----deque that store all neighbor vid
        '''
        if self.st_ready[vault_num] and len(self.vault_mem[vault_num].response_port)!=0 :
            if not self.vp_ready[vault_num]:
                print("Bug: Vp is later than neighbor")
            else:
                length = len(self.vault_mem[vault_num].response_port)
                neighbor_deque = deque()
                for i in range(length):
                    response = self.vault_mem[vault_num].response_port[i]
                    if response.req_tag == neighbor_tag:
                        neighbors = self.vault_mem[vault_num].response_port[i].data
                        self.vault_mem[vault_num].response_port.remove(self.vault_mem[vault_num].response_port[i])
                        for item in neighbors:
                            neighbor_deque.append(item)
                        print("neighbors are ready, stored in neighbor_deque")
                        self.neighbor_ready[vault_num] = True
                        print(f'neighbor_deque is {neighbor_deque}')
                        return neighbor_deque
                print("neighbor tag isn't ready")
                print(f'response port number: {length}')
                self.neighbor_ready[vault_num] = False
        else: self.neighbor_ready[vault_num] = False
        return None


    def PropagateNewEvent(self, N_src, delta, vault_num, neighbor_deque, count=0, beta=0.85, func='pagerank'):
        '''
        use propagate function to create new event
        input:
        each cycle read a vid from neighbor_deque and do propagate
        Return:
            count: which neighbor is being processed
            busy: flag indicate not taking event in
            N_src: neighbor number
        '''
        #read vault_mem[x].respond_port.popleft()//64 bit neighbour vertex_id
        #propogate function => new_delta
        #self.eq_o.append(event(vertex_id, new_delta))
        if not self.neighbor_ready[vault_num]:
            return None
        else:
            if count < N_src/4-1:
                busy = True
                new_delta = self.Propagate(delta, N_src, func, beta) # function of alg
                new_Vid = neighbor_deque.popleft()
                print('new_Vid after propagate:', new_Vid)
                print('new_delta after propagate:', new_delta)
                random_number = random.randint(0, 1)
                if random_number == 0:
                    self.ep_0_o.append(event(np.uint32(new_Vid),np.uint32(new_delta)))
                else:
                    self.ep_1_o.append(event(np.uint32(new_Vid),np.uint32(new_delta)))
                count +=1
                print('count: ',count)
            elif count == N_src/4-1:  #last propagate
                print('last count: ',count)
                busy = False
                new_Vid = neighbor_deque.popleft()
                print('new_Vid after propagate:', new_Vid)
                new_delta = self.Propagate(delta, N_src, func, beta) # function of alg
                print('new_delta after propagate:', new_delta)
                random_number = random.randint(0, 1)
                if random_number == 0:
                    self.ep_0_o.append(event(np.uint32(new_Vid),np.uint32(new_delta)))
                else:
                    self.ep_1_o.append(event(np.uint32(new_Vid),np.uint32(new_delta)))
                print("finish last propagate")
                self.vp_ready[vault_num] = False
                self.st_ready[vault_num] = False
                self.neighbor_ready[vault_num] = False
                count = 0
            else:
                print('error')
            return count, busy, N_src

    def buffer_event(self, buffer_idx, incoming_events):
        '''
        allocate all incoming_events into each buffer based on Vid
        return None
        '''
        for i in range(len(incoming_events)):
            if self.alloc_vault(incoming_events[i].idx) == buffer_idx:
                self.buffer[buffer_idx].append(incoming_events[i])
        return None

    def one_cycle(self, num_vaults):
        incoming_events = []#allocate all the events from adjacent ep
        event_coming_this_ep = []
        for j in range(len(self.ep_0_i)):
            incoming_events.append(self.ep_0_i.popleft())
        for j in range(len(self.ep_1_i)):
            incoming_events.append(self.ep_1_i.popleft())

        event_coming_this_ep = incoming_events
        print(f"incoming events number for all: {len(incoming_events)}\n")
        print(f"incoming events number for current ep: {len(event_coming_this_ep)}") # check the number of events feed into ep this cycle
        for i in range(num_vaults):
            # read events into buffer
            self.vault_mem[i].one_cycle()
            self.buffer_event(i, event_coming_this_ep)
            print(f'buffer_{i} number:{len(self.buffer[i])}')
            if not self.busy[i]: # when not busy, try to take a new event if any
                print('not busy, try to get a new event')
                # read new events
                if (len(self.buffer[i]) != 0):
                    (self.Vid[i], self.delta[i], self.vp_tag[i], self.st_tag[i]) = self.allocate_event_vault_buffer(i)
                    self.busy[i] = True
                    self.Vp[i] = None
                    self.Vp_new[i] = None
                    self.n[i] = None
                    print(f"vault[{i}] is reading event from buffer{i}")  # check working buffer
                else:
                    pass
            else:# when busy not accept new event, reading Vp,St or propagating
                print('busy, try to read needed data')
                if not self.vp_ready[i] and self.vp_tag[i] !=None:
                    self.Vp[i], self.vp_ready[i] = self.read_VP(i, self.vp_tag[i], self.vp_ready[i])
                elif not self.vp_new_written[i]:
                    Vp_new = self.reduce(self.Vp[i], self.delta[i],self.func)
                    self.Update_VP(self.Vid[i], Vp_new)
                if not self.st_ready[i] and self.st_tag[i] != None:
                    self.n[i], self.st_ready[i], self.neighbor_tag[i],  = self.get_edge_num(self.Vid[i], self.st_tag[i])
                    print(f'now neighbor n:{self.n[i]}')
                else:
                    pass
                if not self.neighbor_ready[i] and self.neighbor_tag[i] != None:
                    self.neighbor_deque[i] = self.read_neighbor(i, self.neighbor_tag[i])
                    print(f'neighbor ready or not :{self.neighbor_ready[i]}')
                elif self.vp_ready[i] and self.st_ready[i] and self.neighbor_ready[i] and self.n[i] != None:
                    print('busy, data is ready, propagating')
                    print(f"number of neighbor(n[i]): {self.n[i]}")
                    self.count[i], self.busy[i], self.n[i] = self.PropagateNewEvent(N_src=self.n[i], delta=self.delta[i], vault_num=i, neighbor_deque=self.neighbor_deque[i], count=self.count[i], beta=0.85, func=self.func)
                else:
                    print("fetching data")
                return None

