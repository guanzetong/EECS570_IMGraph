import numpy as np
import copy
from collections import deque
from vault_memory import VM
from standard import mem_request, mem_response, event

class EQ:
    
    def __init__(self, ep_e_i, ep_e_o, ep_n_i, ep_n_o, ep_w_i, ep_w_o, ep_s_i, ep_s_o,
                 ep_idx_ranges, num_vaults=32):
        # Variables:
        # ep_X_i/ep_X_o: input/output deque on the X direction
        # ep_idx_ranges: a list of [min, max] to specify the range assigned to each EP
        #   ep_idx_ranges[0..7] = [nw, n, ne, w, e, sw, s, e]
        
        self.ep_e_i = ep_e_i
        self.ep_e_o = ep_e_o
        self.ep_n_i = ep_n_i
        self.ep_n_o = ep_n_o
        self.ep_w_i = ep_w_i
        self.ep_w_o = ep_w_o
        self.ep_s_i = ep_s_i
        self.ep_s_o = ep_s_o
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