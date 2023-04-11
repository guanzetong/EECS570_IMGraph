import numpy as np
import math
import copy
from collections import deque
from vault_memory import VM
from standard import mem_request, mem_response, event
from serial_links import SL

#define constant
VERTEX_NUM = 32
VAULT_SIZE = 2 * 1024 * 1024 # byte addressable
VAULT_NUM = 32
EVENT_SIZE = 4# 8 bytes
ROW_EVENT_NUM = 32

ROW_SIZE = int(ROW_EVENT_NUM * EVENT_SIZE)
ROW_NUM = int(VAULT_SIZE / ROW_SIZE)
VERTEX_PER_VAULT = int(VERTEX_NUM // VAULT_NUM)


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
        
        self.current_vault_idx = 0
        self.current_row_idx = 0

        self.eq_o_list = [self.eq_n_o_list, self.eq_e_o_list, self.eq_s_o_list, self.eq_w_o_list]
        self.eq_e_o_list = []
        self.eq_n_o_list = []
        self.eq_w_o_list = []
        self.eq_s_o_list = []
        
        # initial as all 1's
        self.row_valid_list = np.ones((num_vaults, ROW_NUM), dtype=bool)
        self.vault_valid_list = np.ones(VERTEX_NUM, dtype=bool)

        # self.max_vertex_per_vault = VAULT_SIZE // EVENT_SIZE
        vault_mem_size = np.zeros(VAULT_SIZE // 4, dtype=np.uint32)
        self.max_events_per_port = 8
        self.fun = "pagerank"
        # Instantiate vault memories
        self.vault_mem = []
        for i in range(num_vaults):
            request_port = deque()
            response_port = deque()
            vault_mem = VM(request_port, response_port, vault_mem_size)
            self.vault_mem.append(vault_mem)
    
  
    # todo: remove row index and valid, vertex id
    
    def get_val_addr(self, vertex_idx):
        return vertex_idx * 4 % VERTEX_PER_VAULT

    def get_vault_index(self, vertex_idx):
        return vertex_idx // VERTEX_PER_VAULT

    def get_row_index(self, vertex_idx):
        return vertex_idx % VERTEX_PER_VAULT // ROW_EVENT_NUM

    def get_row_valid_bit(self, vertex_idx):
        row_valid_bit = self.row_valid_list[self.get_vault_index(vertex_idx), self.get_row_index(vertex_idx)]
        return row_valid_bit

    def write_row_valid_bit(self, vertex_idx ,write_valid_tag):
        self.row_valid_list[self.get_vault_index(vertex_idx), self.get_row_index(vertex_idx)] = write_valid_tag

    def get_vault_valid_bit(self, vertex_idx):
        vault_valid_bit = self.vault_valid_list[vertex_idx]
        return vault_valid_bit
    
    # def get_val_addr_from_row(self, row_idx):
    #     ROW_EVENT_NUM * 4 
    #     return row_idx * 4 % VERTEX_PER_VAULT

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
    
    def coalesce_event(self, delta, vault_idx, func):
        # Calculate the addresses for the existing event and new event
        old_event_val_addr = self.get_val_addr(delta.idx)
        delta_value = self.get_vidx_addr(delta.val)
        
        # invalidate the row valid bit
        self.write_row_valid_bit(delta.idx, False)

        # Read the existing event's value from the vault memory
        old_value_tag = self.vault_mem[vault_idx].GetReqTag()
        req_old_val = mem_request(cmd="read", addr=old_event_val_addr, data=None, size=4, req_tag=old_value_tag)
        print(f"reading old value start addr: st_addr={old_event_val_addr}")
        self.vault_mem[vault_idx].request_port.append(req_old_val)
        # Search for the response tag
        length = len(self.vault_mem[vault_idx].response_port)
        for i in range(length):
            resp_old_val = self.vault_mem[vault_idx].response_port[i]
            if resp_old_val.req_tag == old_value_tag:
                old_val = self.vault_mem[vault_idx].response_port[i].data
                self.vault_mem[vault_idx].response_port.remove(self.vault_mem[vault_idx].response_port[i])
                print(f"Find old value: old_val={old_val}")
                break

        # Combine the existing event's value and the new event's value using the reduce function
        coalesced_val = self.reduce(old_val, delta_value, func)

        # Write the coalesced event's value back to the vault memory at the existing event's value address
        write_value_tag = self.vault_mem[vault_idx].GetReqTag()
        req_wirte_new = mem_request(cmd="write", addr=old_event_val_addr, data=coalesced_val, size=4, req_tag=write_value_tag)
        print(f"write coalescing value: new_val={coalesced_val}")

        # make this row valid
        self.write_row_valid_bit(delta.idx, True)
        
    def insert_event(self, new_event, func):
        vault_idx = self.get_vault_index(new_event.idx)
        if self.get_row_valid_bit(new_event.idx):
            # If the row event located in is valid, coalesce the new event with the existing event
            self.coalesce_event(new_event, vault_idx, func)
        else:
            None
    
    def get_events_from_ep(self, max_events_per_port, func):
        ep_input_list = [self.ep_e_i, self.ep_n_i, self.ep_w_i, self.ep_s_i]
        # add a logic to distinguish the longest queue
        longest_queue = max(ep_input_list ,key=len)
        # select the max queue and process the events from the max queue
        if len(longest_queue) > max_events_per_port:
            for _ in range(max_events_per_port):
                if self.ep_n_i:
                    event = self.ep_n_i.popleft()
                    self.insert_event(event, func)
            ep_input_list.remove(longest_queue)
        else :
            for _ in range(len(longest_queue)):
                if self.ep_n_i:
                    event = self.ep_n_i.popleft()
                    self.insert_event(event, func)
            ep_input_list.remove(longest_queue)
        # also process rest of the events in the other queues
        for ep_input in ep_input_list:
            if ep_input:
                for _ in range(len(ep_input)):
                    event = ep_input.popleft()
                    self.insert_event(event, func)

    def find_next_valid_vault(self, current_vault_idx):
        # Base case: If the current vault is valid, return its index
        if self.vault_valid_list[current_vault_idx]:
            return current_vault_idx

        # Recursive case: Increment the index and wrap around if necessary, then call the function recursively
        next_vault_idx = (self.current_vault_idx + 1) % VAULT_NUM
        return self.find_next_valid_vault(next_vault_idx)

    def find_next_valid_row(self, current_vault_idx, current_row_idx):
        if self.row_valid_list[current_vault_idx][current_row_idx]:
            return current_row_idx
        
        next_row_idx = (self.current_row_idx + 1) % ROW_NUM
        return self.find_next_valid_row(current_vault_idx, next_row_idx)

    def find_vid_range_ep(self, value, ep_idx_ranges):
        for i, (min_val, max_val) in enumerate(ep_idx_ranges):
            if min_val <= value <= max_val:
                return i
        return -1  # Indicates that the value was not found in any range
    
    def ep_alloc(self, routing_algo, ep_idx):
        if routing_algo == "neareast routing":
            if ep_idx == 0 or 1:
                return self.ep_n_o
            if ep_idx == 2 or 4:
                return self.ep_e_o
            if ep_idx == 3 or 5:
                return self.ep_w_o
            if ep_idx == 6 or 7:
                return self.ep_s_o
        
    def send_event_to_ep(self):
        # find valid row in round robin fashion
        current_valid_vault_idx = self.find_next_valid_vault(self.current_vault_idx)
        current_valid_row_idx = self.find_next_valid_row(current_valid_vault_idx, self.current_row_idx)
        # get the start address from vault idx and row idx
        vertex_id = current_valid_vault_idx * VERTEX_PER_VAULT + (current_valid_row_idx - 1) * ROW_EVENT_NUM
        row_start_addr = self.get_val_addr(vertex_id)
        
        # Read the existing event's value from the vault memory
        send_row_tag = self.vault_mem[current_valid_vault_idx].GetReqTag()
        req_row = mem_request(cmd="read", addr=row_start_addr, data=None, size=ROW_SIZE, req_tag=send_row_tag)
        print(f"reading old value start addr: st_addr={row_start_addr}")
        self.vault_mem[current_valid_vault_idx].request_port.append(req_row)
        # Search for the response tag
        length = len(self.vault_mem[current_valid_vault_idx].response_port)
        for i in range(length):
            resp_old_val = self.vault_mem[current_valid_vault_idx].response_port[i]
            if resp_old_val.req_tag == send_row_tag:
                row_data = self.vault_mem[current_valid_vault_idx].response_port[i].data
                self.vault_mem[current_valid_vault_idx].response_port.remove(self.vault_mem[current_valid_vault_idx].response_port[i])
                print(f"Find old value: old_val={row_data}")
                break
        
        # send the row data to the EP
        find_ep_idx = self.find_vid_range_ep(vertex_id, self.ep_idx_ranges)
        if find_ep_idx == -1:
            print("Error: Cannot find the EP index")
        else:
            # determine which EP to send the data
            ep_output = self.ep_alloc("neareast routing", find_ep_idx)
            ep_output.append(row_data)
            print(f"send row data to EP: ep_idx={find_ep_idx}, row_data={row_data}")
            # todo : send the row data through serial link


    def one_cycle(self):
        # Get the events from the input ports
        self.get_events_from_ep(self.max_events_per_port, self.func)
        # Send the events to the output ports
        self.send_event_to_ep()
        # Update the current vault and row indices
        self.current_vault_idx = (self.current_vault_idx + 1) % VAULT_NUM
        self.current_row_idx = (self.current_row_idx + 1) % ROW_NUM