import numpy as np
from collections import deque
from vault_memory import VM
from standard import mem_request, mem_response, event

class Event:
    def __init__(self, src_vertex, dst_vertex, edge_weight, event_data):
        self.src_vertex = src_vertex
        self.dst_vertex = dst_vertex
        self.edge_weight = edge_weight
        self.event_data = event_data

class EQ:
    def __init__(self, ep_idx_ranges, num_vaults=32, ep_e_i=None, ep_e_o=None, ep_n_i=None, ep_n_o=None, ep_w_i=None, ep_w_o=None, ep_s_i=None, ep_s_o=None):
        self.num_vaults = num_vaults
        self.current_vault = 0

        self.ep_e_i = ep_e_i if ep_e_i else deque()
        self.ep_e_o = ep_e_o if ep_e_o else deque()
        self.ep_n_i = ep_n_i if ep_n_i else deque()
        self.ep_n_o = ep_n_o if ep_n_o else deque()
        self.ep_w_i = ep_w_i if ep_w_i else deque()
        self.ep_w_o = ep_w_o if ep_w_o else deque()
        self.ep_s_i = ep_s_i if ep_s_i else deque()
        self.ep_s_o = ep_s_o if ep_s_o else deque()

        self.ep_idx_ranges = ep_idx_ranges

        # Instantiate vault memories
        self.vault_mem = []
        for i in range(num_vaults):
            request_port = deque()
            response_port = deque()
            vault_mem = VM(request_port, response_port)
            self.vault_mem.append(vault_mem)

        # Instantiate serial links to PEs
        self.serial_links = []
        for i in range(num_vaults):
            serial_link = deque()
            self.serial_links.append(serial_link)

    # ... (other methods remain the same)

    def send_event(self, vault_idx):
        if self.serial_links[vault_idx]:
            event_to_send = self.serial_links[vault_idx].popleft()
            self.send_to_PE_HMC(event_to_send)

    def send_to_PE_HMC(self, event):
        # Replace this function with the actual logic for sending the event to the appropriate PE HMC
        pass
    
    def send_event_to_neighbor(self, event, direction, neighbor_eq):
        if direction == "east":
            neighbor_eq.ep_e_i.append(event)
        elif direction == "north":
            neighbor_eq.ep_n_i.append(event)
        elif direction == "west":
            neighbor_eq.ep_w_i.append(event)
        elif direction == "south":
            neighbor_eq.ep_s_i.append(event)
        else:
            raise ValueError("Invalid direction. Please use 'east', 'north', 'west', or 'south'.")

    def one_cycle(self):
            # Handle incoming events
        for i, ep_i in enumerate([self.ep_e_i, self.ep_n_i, self.ep_w_i, self.ep_s_i]):
            if ep_i:
                event = ep_i.popleft()
                self.handle_incoming_event(event)

        # Select a row of events in round-robin manner and send them to the serial link
        selected_vault = self.vault_mem[self.current_vault]
        row_events = self.get_events_from_row(selected_vault)
        self.serial_links[self.current_vault].extend(row_events)

        # Update the current vault for the next cycle
        self.current_vault = (self.current_vault + 1) % self.num_vaults

    #todo: get_vault_idx()
    #todo: get_event()
    #todo: update_event()
    #todo: insert_event()

    def handle_incoming_event(self, event):
        vault_idx = self.get_vault_idx(event.vertex_id)
        selected_vault = self.vault_mem[vault_idx]
        existing_event = self.get_event(selected_vault, event.vertex_id)

        if existing_event:
            combined_event = self.reduce(existing_event, event)
            self.update_event(selected_vault, combined_event)
        else:
            self.insert_event(selected_vault, event)

    # Dummy reduce function to combine events
    def reduce(self, event1, event2):
        return Event(event1.vertex_id, event1.propagation_value + event2.propagation_value)

if __name__ == "__main__":
    pass
