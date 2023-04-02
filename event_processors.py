import numpy as np
import copy
from collections import deque
from vault_memory import VM
from standard import mem_request, mem_response, event

class EP_h1:
    
    def __init__(self, eq_i, eq_o, ep_0_i, ep_0_o, ep_1_i, ep_1_o,
                 ep_idx_ranges, num_vaults):
        # Variables
        # eq_i/eq_o: input/output deque with event queues
        # ep_X_i/ep_X_o: input/output deque with adjacent event processors
        # ep_idx_ranges: a list of [min, max] to specify the range assigned to this EP and adjacent EPs
        #   ep_idx_ranges[0..1] = [self, ep_0, ep_1]
        
        self.eq_i   = eq_i
        self.eq_o   = eq_o
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

        # todo initial

    def alloc_vault(self, Vid):
        '''
        input:
        Vid: vertex id
        Return:
        vault_idx: idx of related vault (from 0 to 31)
        '''
        vault_capacity = (self.ep_idx_ranges[1]-self.ep_idx_ranges[0]) // 32 + 1
        vault_index = [Vid-self.ep_idx_ranges[0]]// vault_capacity
        return vault_index
    ## deque().append(vid)
    ## reduce,propagate from deque (32)
    ## foreach

    def vertex_property_addr(self, Vid):
        return Vid
        pass

    def vertex_st_addr(self, Vid):
        return Vid + 10000
        pass

    def vertex_neighbor_addr(self, Vid):
        vault_num = self.alloc_vault(Vid)
        return self.vault_mem[vault_num].response_port.popleft()
        pass

    def allocate_event_vault(self):
      if len(self.ep_i) == 0:
           return None
      else: #get an event from ep_i deque
          vertex_id = self.ep_i.popleft().idx
          delta     = self.ep_i.popleft().val  #vault num is a result of the previous function
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

    def reduce(old_value, delta=0.85, func='pagerank'): #delta = allocate_event_vault()[1]
        '''
        input:
        func: which algorithm
        old_value: stale vertex property in vm          # use read_vp function
        return:
        new_value of vertex property
        '''
        if func.lower() == 'pagerank' or func.lower() == 'adsorption':
            new_value = old_value + delta
        elif func.lower() == 'sssp' or func.lower() == 'bfs':
            new_value = min(old_value, delta)
        elif func.lower() =='comp':
            new_value = max(old_value, delta)
        else:
            new_value = old_value + delta
        return new_value

    def read_VP(self, Vid):
        vault_num = self.alloc_vault(Vid)
        if len(self.vault_mem[vault_num].response_port) == 0:
           return None
        else:
            Vp = self.vault_mem[vault_num].response_port.popleft()
            return Vp       #vp is a class

    def Update_VP(self, Vid, delta, func='pagerank'):
        '''
        read mem.repsone() to get vertex property, use reduce function to update
        delta = allocate_event_vault()[1]
        '''
        
        Vp_old = self.read_VP(Vid)
        Vp_new = self.reduce(Vp_old, delta, func)
        # write Vp_new to mem
        Vp_addr = self.vertex_property_addr(Vid)
        vault_num = self.alloc_vault(Vid)
        req_w_Vp = mem_request("write", Vp_addr, Vp_new)
        self.vault_mem[vault_num].request_port.append(req_w_Vp)
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
            n = St_2 - St_1
            neighbor_addr = self.vertex_neighbor_addr(Vid)
            req_neighbor = mem_request("read", neighbor_addr, n)
            self.vault_mem[vault_num].request_port.append(req_neighbor)
            return n

    def Propagate(delta, N_src, func='pagerank', beta=0.85):
        '''
        delta = reduce(read_vp(), allocate_event_vault()[1])
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
    def PropagateNewEvent(self, N_src, delta, Vid, vault_num, count=0, beta=0.85, func='pagerank', threshold=0):
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
        #self.eq_o.respond_port.append(event(vertex_id, new_delta))
        if N_src == 0 or abs(delta) <= threshold or count >= N_src:
            #count = 0
            return count + 1
        else:
            if count < N_src:
                new_delta = self.Propagate(delta, N_src, func, beta) # function of alg
                new_Vid = self.vault_mem[vault_num].response_port.popleft()
                self.eq_o.respond_port.append(event(new_Vid,new_delta))
                count +=1
            elif count == N_src:
                new_delta = self.Propagate(delta, N_src, func, beta) # function of alg
                self.eq_o.respond_port.append(event(new_Vid,new_delta))
                count = 0
            return count
    
    #to do
    def initial(self, offset_vp, offset_vault, func='pagerank', beta=0.85):
        '''
        offset_vault = 
        offset_vp = 
        '''
        if func.lower() == "pagerank":
            for i in range(32):
                self.vault_mem[offset_vault*i:offset_vault*i+offset_vp] = 0
            delta_i = 1-beta
        elif func.lower() == 'sssp' or func.lower() == 'bfs':
            for i in range(32):
                self.vault_mem[offset_vault*i:offset_vault*i+offset_vp] = float('inf')
            delta_i = 0
        return self.vault_mem, delta_i

    def forward_message():
        pass

    def one_cycle():
        pass

    #def allocate_event_vault(self):
    #   if len(self.ep_i) == 0:
    #        return
    #   else
    #       vertex_id = self.ep_i.popleft().idx
    #       delta     = self.ep_i.popleft().val//vault num is a result of the previous function
    #       vault_mem = function()
    #       v_addr = function(vertix_id)
    #       req = mem_request("read", v_addr, 1)
    #       vault_mem[vault_num].request_port.append(req)
    #       

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