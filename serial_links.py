import numpy as np

class SL:
    
    def __init__(self, in_port, out_port):
        # Variables:
        # in_port: input deque
        # out_port: output deque
        self.in_port  = in_port
        self.out_port = out_port
        self.previous_values = [None, None]

    def read_port(self):
        content=[]
        if len(self.in_port) == 0:
            return None
        elif len(self.in_port) > 6:
            for i in range(6):
                content.append(self.in_port.popleft())
        else:
            for i in range(len(self.in_port)):
                content.append(self.in_port.popleft())
        return content
    
    def two_cycle_delay(self, input_value):
        self.previous_values.append(input_value)
        if len(self.previous_values) < 3:
            return None
        return self.previous_values.pop(0)
    
    def write_port(self, out):
        if out == None:
            return None
        else:
            for item in out:
                self.out_port.append(item)
            print(f"current output is {self.out_port}")
            return None


    def one_cycle(self):
        content = self.read_port()
        out = self.two_cycle_delay(content)
        self.write_port(out)