import numpy as np
import copy
from collections import deque
from vault_memory import VM
from standard import mem_request, mem_response, event

class EP_h1:
    
    def __init__(self, eq_i, eq_o, ep_0_i, ep_0_o, ep_1_i, ep_1_o,
                 ep_idx_ranges, num_vaults, func, busy, buffer, count):
        # Variables
        # eq_i/eq_o: input/output deque with event queues
        # ep_X_i/ep_X_o: input/output deque with adjacent event processors
        # ep_idx_ranges: a list of [min, max] to specify the range assigned to this EP and adjacent EPs
        #   ep_idx_ranges[0..1] = [self, ep_0, ep_1]
        # busy: list of booleans
        # buffer: list of deque
        
        self.eq_i   = eq_i
        self.eq_o   = eq_o
        self.ep_0_i = ep_0_i
        self.ep_0_o = ep_0_o
        self.ep_1_i = ep_1_i
        self.ep_1_o = ep_1_o
        self.ep_idx_ranges = ep_idx_ranges
        self.func = func
        self.count = []
        self.busy = []
        self.buffer = []
        for i in range(num_vaults):
            self.busy.append(False)
            self.buffer.append(deque())
            self.count.append(0)
        
        # Instantiate vault memories
        self.vault_mem = []
        for i in range(num_vaults):
            request_port = deque()
            response_port = deque()
            vault_mem = VM(request_port, response_port)
            self.vault_mem.append(vault_mem)

        # Initialize vp of each vault based on algorithm
        vp_num = (self.ep_idx_ranges[1]-self.ep_idx_ranges[0]) // 32 + 1
        vp_addr = 0
        if func.lower() == "pagerank":
            for i in range(32):
                for j in range(vp_num):
                    req = mem_request("write", vp_addr+j, 0)
                    self.vault_mem[i].request_port.append(req)

        elif func.lower() == 'sssp' or func.lower() == 'bfs':
            for i in range(32):
                for j in range(vp_num):
                    req = mem_request("write", vp_addr+j, float('inf'))
                    self.vault_mem[i].request_port.append(req)

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
    ## deque().append(vid)
    ## reduce,propagate from deque (32)
    ## foreach

    def vertex_property_addr(self, Vid):
        return Vid

    def vertex_st_addr(self, Vid):
        return int(Vid + 10000)

    def vertex_neighbor_addr(self, Vid):
        vault_num = self.alloc_vault(Vid)
        return int(Vid + 20000)

    def allocate_event_vault_port(self):
      if len(self.eq_i) == 0:
           return None
      else: #get an event from ep_i deque
        a = self.eq_i.popleft()
        #   delta     = self.eq_i.popleft().val  #vault num is a result of the previous function
        vertex_id = a.idx
        delta = a.val
        vault_num = self.alloc_vault(Vid=vertex_id)
        # read vertex property request
        vp_addr = self.vertex_property_addr(Vid=vertex_id)
        req_vp = mem_request("read", vp_addr, 1)
        self.vault_mem[vault_num].request_port.append(req_vp)
        # read vertex start address request
        v_st_addr = self.vertex_st_addr(Vid=vertex_id)
        req_v_st = mem_request("read", v_st_addr, 2)
        self.vault_mem[vault_num].request_port.append(req_v_st)
        return vertex_id, delta
    
    def allocate_event_vault_buffer(self, vault_idx):
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
        req_vp = mem_request("read", vp_addr, 1)
        self.vault_mem[vault_num].request_port.append(req_vp)
        # read vertex start address request
        v_st_addr = self.vertex_st_addr(Vid=vertex_id)
        req_v_st = mem_request("read", v_st_addr, 2)
        self.vault_mem[vault_num].request_port.append(req_v_st)
        return vertex_id, delta

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

    def read_VP(self, Vid):
        vault_num = self.alloc_vault(Vid)
        if len(self.vault_mem[vault_num].response_port) == 0:
           print("No Vp")
           return None
        else:
            Vp = self.vault_mem[vault_num].response_port.popleft()
            print("Vp read from response_port:", Vp)
            return Vp       #vp is a class

    def Update_VP(self, Vid, Vp_new):
        '''
        read mem.repsone() to get vertex property, use reduce function to update
        delta = allocate_event_vault_port()[1]
        '''
        
        #Vp_old = self.read_VP(Vid)
        #Vp_old =Vp
        #Vp_new = self.reduce(Vp, delta, func)
        print("Vp_new (after reduce): ",Vp_new)
        # write Vp_new to mem
        if Vp_new != None:
            Vp_addr = self.vertex_property_addr(Vid)
            vault_num = self.alloc_vault(Vid)
            req_w_Vp = mem_request("write", Vp_addr, Vp_new)
            self.vault_mem[vault_num].request_port.append(req_w_Vp)
        else:
            pass
        return None

    def get_edge_num(self, Vid):
        '''
        read response port to get start address and create a request to read neighbor
        return the number of edge of this vertex
        '''
        vault_num = self.alloc_vault(Vid)
        if len(self.vault_mem[vault_num].response_port) == 0:
           return None
        else:
            St_1 = self.vault_mem[vault_num].response_port.popleft()
            St_2 = self.vault_mem[vault_num].response_port.popleft()
            n = St_2 - St_1    # byte sized
            print("neighbor num: ",n)
            neighbor_addr = self.vertex_neighbor_addr(Vid)
            req_neighbor = mem_request("read", neighbor_addr, n)
            self.vault_mem[vault_num].request_port.append(req_neighbor)
            return n

    def Propagate(self, delta, N_src, func='pagerank', beta=0.85):
        '''
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
        if Vp_new is None or Vp is None:
            return False
        elif abs(Vp_new-Vp) <= threshold:
            return False
        else:
            return True
    def PropagateNewEvent(self, N_src, delta, Vp_new, Vp, vault_num, count=0, beta=0.85, func='pagerank', threshold=0):
        '''
        use propagate function to create new event
        input:
        beta: dumping factor
        N_src: number of neighbors of VI, N_src = get_edge_num(self, Vid)
        VI_neighor: list of VI's neighbor
        delta: delta of VI from EQ
        Return:
        New_event: list of event: new events sent to EQ
        '''
        #read vault_mem[x].respond_port.popleft()//64 bit neighbour vertex_id
        #propogate function => new_delta
        #self.eq_o.append(event(vertex_id, new_delta))
        if count < N_src:
            self.busy = True
            new_delta = self.Propagate(delta, N_src, func, beta) # function of alg
            print('new_delta after propagate:', new_delta)
            new_Vid = self.vault_mem[vault_num].response_port.popleft()
            print('new_Vid after propagate:', new_Vid)
            self.eq_o.append(event(new_Vid,new_delta))
            count +=1
            print('count: ',count)
        elif count == N_src:
            self.busy = False
            new_delta = self.Propagate(delta, N_src, func, beta) # function of alg
            self.eq_o.append(event(new_Vid,new_delta))
            count = 0
        return count, self.busy, N_src

    def forward_message():
        pass

    def buffer_event(self, buffer_idx, incoming_events):
        '''
        buffer events that aren't able to feed in EP
        '''
        for i in range(len(incoming_events)):
            if self.alloc_vault(incoming_events[i].idx) == buffer_idx:
                self.buffer[buffer_idx].append(incoming_events[i])
        return None

        

    def one_cycle(self, num_vaults):
        # # feed an event from port and make read req for Vp and St_addr
        # # now the # of event is 1, depend on crossbar
        # if (len(self.eq_i) != 0) and not self.busy:
        #     (Vid, delta) = self.allocate_event_vault_port()# !read vid, and read two start address(size = 2)
        # ####
        #     count = 0
        # # read data from response port of vm in order
        # ###
        # # use Vp
        #     Vp = self.read_VP(Vid)
        #     print("Vp read in one cycle: ",Vp)
        #     print("delta read in one cycle: ",delta)
        #     print('func in one cycle', self.func)
        #     # use St_addr and make read req for neighbors
        #     n = self.get_edge_num(Vid)# !already send request to get all its neighboor!!!!!!!!!!!!!!!!
        #     # update Vp(making a write req for Vp)
        #     Vp_new = self.reduce(Vp, delta, self.func)
        #     self.Update_VP(Vid,Vp_new)#! and update vp
        # else:
        #     pass
        # # propagate new event
        # for i in range(32):
        #     if len(self.vault_mem[i].response_port) == 0:
        #         count = 0
        #     else:
        #         count, self.busy = self.PropagateNewEvent(N_src=n, delta=delta, Vp_new=Vp_new, Vp=Vp, vault_num=i, count=count, beta=0.85, func=self.func, threshold=0)
        #         print('count in propagate: ',count)
        # return None
        incoming_events = []
        for j in range(len(self.eq_i)):
            incoming_events.append(self.eq_i.popleft())
        for i in range(num_vaults):
            # read events into buffer
            self.buffer_event(i, list(self.eq_i))
            if not self.busy[i]:
                if (len(self.buffer[i]) != 0):
                    (Vid, delta) = self.allocate_event_vault_buffer(i)
                    self.busy[i] = True
                else:
                    pass
                Vp = self.read_VP(Vid) # pop vp at once, return None if no response
                Vp_new = self.reduce(Vp, delta, self.func) # return None if Vp is None
                n = self.get_edge_num(Vid) # pop st1 st2 at once and read neighbors, return None if st1 st2 not ready
                count = 0
                self.Update_VP(Vid,Vp_new) # write Vp_new
                # try use neighbor vp
                if self.Propagate_condion(Vp_new, Vp, threshold=0): #make sure all data is ready
                    if (len(self.vault_mem[i].response_port) != 0) and n != None:
                        count[i], self.busy[i], n = self.PropagateNewEvent(N_src=n, delta=delta, Vp_new=Vp_new, Vp=Vp, vault_num=i, count=count[i], beta=0.85, func=self.func, threshold=0)
                    else:
                        pass

            else:
                count[i], self.busy[i], n = self.PropagateNewEvent(N_src=n, delta=delta, Vp_new=Vp_new, Vp=Vp, vault_num=i, count=count, beta=0.85, func=self.func, threshold=0)
                print(f"vault[{i}] is busy on propagate, count={count[i]} , n={n} ")
            return None



# worst: different vault


class EP_h2:
    
    def __init__(self, ep_0_i, ep_0_o, ep_1_i, ep_1_o,
                 ep_idx_ranges, num_vaults):
        # Variables
        # eq_i/eq_o: input/output deque with event queues
        # ep_X_i/ep_X_o: input/output deque with adjacent event processors
        # ep_idx_ranges: a list of [min, max] to specify the range assigned to this EP and adjacent EPs
        #   ep_idx_ranges[0..0] = [self]
        self.ep_0_i = ep_0_i
        self.ep_0_o = ep_0_o
        self.ep_1_i = ep_1_i
        self.ep_1_o = ep_1_o
        self.ep_idx_ranges = ep_idx_ranges
        
        # Instantiate vault memories
        self.vault_mem = []
        for i in range(num_vaults):
            request_port = deque()
            response_port = deque()
            vault_mem = VM(request_port, response_port)
            self.vault_mem.append(vault_mem)
        
    def one_cycle():
        pass