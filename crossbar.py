import numpy as np
import copy
from collections import deque

class round_robin_xbar:

    def __init__(self, in_port_list = [deque()], out_port_list = [deque()], idx_ranges = [], num_stages = 1):
        # Reconfigurable parameters
        assert out_port_list.size() == idx_ranges.size()
        self.num_input = in_port_list.size()
        self.num_output = out_port_list.size()
        if num_stages <= 0:
            self.num_stages = 1
        else:
            self.num_stages = num_stages

        self.in_port_list = in_port_list
        self.out_port_list = out_port_list
        self.idx_ranges = idx_ranges

        # Arbiter internal signals (combinational)
        self.arb_request = np.zeros(self.num_output, dtype=np.uint64)
        self.arb_mask = np.zeros(self.num_output, dtype=np.uint64)
        self.arb_mask_n = np.zeros(self.num_output, dtype=np.uint64)
        self.init_mask = np.uint64(2 ** self.num_input - 1)
        for output_idx in range(self.num_output):
            self.arb_mask[output_idx] = self.init_mask  # masks are initialized to all 1s
            self.arb_mask_n[output_idx] = self.init_mask  # masks are initialized to all 1s
        self.arb_grant = np.zeros(self.num_output, dtype=np.uint64)
        
        # Pipeline stages
        self.xbar_stages = []
        for i in range(self.num_output):
            self.xbar_stages.append(deque())

    def one_clock(self):

        # Input Switches

        # Clear requests in the previous cycle
        self.arb_request = np.zeros(self.num_output, dtype=np.uint64)

        # Iterate through the inputs and route the requests to output channels
        incoming_events = []
        for input_idx in range(self.num_input):
            if len(self.in_port_list[input_idx]) == 0:
                continue
            # event destination index decides output channel
            incoming_events.append(self.in_port_list[input_idx].pop())
            for output_idx in range(self.num_output):
                if self.idx_ranges[output_idx][0] < incoming_events[input_idx].idx and self.idx_ranges[output_idx][1] > incoming_events[input_idx].idx:
                    self.arb_request[output_idx] = self.arb_request[output_idx] | np.uint64(1 << input_idx)
                    break

        # Output Arbiters

        # Clear grants in the previous cycle
        self.arb_grant = np.zeros(self.num_output, dtype=np.uint64)

        # Iterate through the outputs and arbitrate
        for output_idx in range(self.num_output):

            # No request to send to the bin
            if self.arb_request[output_idx] == 0:
                continue

            masked = self.arb_mask[output_idx] & self.arb_request[output_idx]
            shifted = np.uint64(0)
            if masked == 0:
                shifted = self.arb_request[output_idx]
            else:
                shifted = masked

            for req_idx in range(self.num_input):
                if shifted & np.uint64(1) == 1:
                    self.arb_grant[output_idx] = np.uint64(1 << req_idx)
                    break
                else:
                    shifted = shifted >> 1

        for output_idx in range(self.num_output):
            if self.arb_grant[output_idx] == 0:
                self.xbar_stages[output_idx].append(None)
            else:
                for input_idx in range(self.num_input):
                    if self.arb_grant[output_idx] & np.uint64(1 << input_idx) != 0:
                        self.xbar_stages[output_idx].append(incoming_events[input_idx])
                        break

        # Update mask
        self.arb_mask_n = np.zeros(self.num_output, dtype=np.uint64)
        for output_idx in range(self.num_output):
            arb_grant_tmp = self.arb_grant[output_idx]
            if arb_grant_tmp == 0:
                self.arb_mask_n[output_idx] = copy.deepcopy(self.arb_mask[output_idx])
            else:
                self.arb_mask_n[output_idx] = self.init_mask
                while arb_grant_tmp != 0:
                    self.arb_mask_n[output_idx] = self.arb_mask_n[output_idx] << 1
                    arb_grant_tmp = arb_grant_tmp >> 1
        
        self.arb_mask = copy.deepcopy(self.arb_mask_n)

        # Pipelining
        if len(self.xbar_stages[0] > self.num_stages):
            for output_idx in range(self.num_output):
                outgoing_event = self.xbar_stages[output_idx].pop()
                if outgoing_event != None:
                    self.out_port_list[output_idx].append()
