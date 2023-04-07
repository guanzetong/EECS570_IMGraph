import numpy as np

class event:
    
    def __init__(self, idx, val):
        self.idx = np.uint64(idx)
        self.val = np.float64(val)
        

class mem_request:
    
    def __init__(self, cmd, addr, data,size,req_tag):
        self.cmd  = cmd
        self.addr = addr
        self.data = data
        self.size =size
        self.req_tag= req_tag


class bank_request:
    def __init__(self, cmd, addr, data, size,req_tag):
        self.cmd = cmd
        self.addr = addr
        self.data = data
        self.size = size
        self.req_tag = req_tag

class bank_response:

    def __init__(self, data,tag):
        self.data = data
        self.tag = tag
        
class mem_response:
    
    def __init__(self, data, req_tag):
        self.data = data
        self.req_tag = req_tag

class TrackTableEntry:
    def __init__(self, tags,req_tag,ready=0):
        self.tags = tags
        # self.data = []
        self.data_dict = {}
        self.data= []
        self.ready = ready
        self.req_tag=req_tag

class TrackTable:
    def __init__(self):
        self.entries = []
    def add_entry(self, tags,req_tag):
        entry = TrackTableEntry(tags,req_tag)
        self.entries.append(entry)
    def update_entry(self, tag, data):
        for entry in self.entries:
            if tag in entry.tags:
                entry.data_dict[tag] = data  # Add data to the dictionary with the tag as the key
                entry.tags.remove(tag)
                if not entry.tags:
                    entry.ready = 1
                    # When all tags are received, sort the dictionary by key and update the data[] list
                    entry.data = np.concatenate([val for _, val in sorted(entry.data_dict.items())])
                    del entry.data_dict  # Delete the data_dict attribute as it's no longer needed
                break


    def transfer_to_resp_port(self, response_port):
        ready_entries = [entry for entry in self.entries if entry.ready]
        for entry in ready_entries:
            resp=mem_response(entry.data,entry.req_tag)
            response_port.append(resp)
            self.entries.remove(entry)
            break
    # def check_all_entries_ready(self):
    #     return all(entry.ready for entry in self.entries)
    # def clear(self):
    #     self.entries.clear()
    # def __str__(self):
    #     return '\n'.join([f'Req_Tag: {entry.req_tag}, Tags: {entry.tags}, Data: {entry.data}, Ready: {entry.ready}' for entry in self.entries])
    def __str__(self):
        return '\n'.join(
            [f'Req_Tag: {entry.req_tag}, Tags: {entry.tags}, Data: {entry.data}, Ready: {entry.ready}' for entry in
             self.entries])