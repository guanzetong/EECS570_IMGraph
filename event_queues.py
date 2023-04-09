import numpy as np
import copy
from collections import deque
from vault_memory import VM
from standard import mem_request, mem_response, event
<<<<<<< HEAD
=======
from serial_links import SL
>>>>>>> f073179 (coalesce unit)

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
<<<<<<< HEAD
        self.ep_idx_ranges = ep_idx_ranges
        
=======
        #todo: add the logic to send events to the corresponding EPs
        
        #todo: a row of 8192 bit is 1024 bytes, an event is 8 bytes, so 128 events per row, and send event is atomic operation
        self.ep_idx_ranges = ep_idx_ranges

        self.current_vault_idx = 0


>>>>>>> f073179 (coalesce unit)
        # Instantiate vault memories
        self.vault_mem = []
        for i in range(num_vaults):
            request_port = deque()
            response_port = deque()
            vault_mem = VM(request_port, response_port)
            self.vault_mem.append(vault_mem)
<<<<<<< HEAD
        
    def one_cycle():
        pass
=======

    def get_vault_index(self, vertex_idx):
        # Implement logic to get the vault index based on the vertex index
        vault_capacity = (self.ep_idx_ranges[1]-self.ep_idx_ranges[0]) // 32 + 1
        vault_index = [vertex_idx-self.ep_idx_ranges[0]]// vault_capacity
        return vault_index

    def get_ep_output_port(self, vertex_idx):
        # Implement logic to get the output port of the corresponding EP based on the vertex index
        pass
    
    def redunce_func(self, old_val, delta):
        # Implement logic to reduce two values
        new_val = old_val + delta
        return new_val
    
    def coalesce_unit(self, old_event, vault_idx, delta):
        coalesced_event = event(old_event.idx, self.redunce_func(old_event.val, delta))
        self.vault_mem[vault_idx].request_port.append(coalesced_event)
    
    def insert_event(self, new_event):
        vault_idx = self.get_vault_index(new_event.idx)
        response_port_len = len(self.vault_mem[vault_idx].response_port)
        if response_port_len == 0:
            self.vault_mem[vault_idx].request_port.append(new_event.idx, new_event)
        else:
            self.coalesce_unit(existing_event, new_event, vault_idx)


    def one_cycle(self):
        for ep_i in [self.ep_e_i, self.ep_n_i, self.ep_w_i, self.ep_s_i]:
            if ep_i:
                incoming_event = ep_i.popleft()
                self.insert_event(incoming_event)

        # Send events to corresponding EPs
        vault_idx = self.select_next_vault()
        if vault_idx is not None:
            row_of_events = self.vault_mem[vault_idx].read_row()
            self.send_event_to_ep(row_of_events)
>>>>>>> f073179 (coalesce unit)
