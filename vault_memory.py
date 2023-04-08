from collections import deque
from standard import mem_request, mem_response

class VM:
    
    def __init__(self, request_port, response_port):
        # Variables:
        # request_port: input deque from logic base to transmit memory requests
        # response_port: output deque to logic base to response with data on read requests
        
        self.request_port = request_port
        self.response_port = response_port
    def GetReqTag(self):
        pass
        
    def one_cycle():
        pass