import numpy as np

class event:
    
    def __init__(self, idx, val):
        self.idx = np.uint64(idx)
        self.val = np.float64(val)
        

class mem_request:
    
    def __init__(self, cmd, addr, data):
        self.cmd  = cmd
        self.addr = addr
        self.data = data
        
        
class mem_response:
    
    def __init__(self, data):
        self.data = data