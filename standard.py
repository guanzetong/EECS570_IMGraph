import numpy as np

class event:
    
    def __init__(self, idx, val):
        self.idx = np.uint64(idx)
        self.val = np.float64(val)
        

class mem_request:
    
    def __init__(self, cmd, addr, data, tag):
        self.cmd  = cmd
        self.addr = addr
        self.data = data
        self.tag = tag
        
        
class mem_response:
    
    def __init__(self, data, tag):
        self.data = data #list
        self.tag = tag