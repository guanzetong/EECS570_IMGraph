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
        
    def one_cycle():
        pass

    

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