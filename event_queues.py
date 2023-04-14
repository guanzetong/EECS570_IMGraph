import numpy as np
import math
import copy
from collections import deque
from vault_mem import VM
from standard import mem_request, mem_response, event
from serial_links import SL
import copy

#define constant
EVENT_SIZE = 4  # bytes
EVENTS_PER_ROW = 256
ROW_SIZE = EVENT_SIZE * EVENTS_PER_ROW  # 1024 bytes
ROWS_PER_BANK = 256
BANK_SIZE = ROW_SIZE * ROWS_PER_BANK  # 256 KB
BANKS_PER_VAULT = 8


VERTEX_NUM = 6301 * 4
VAULT_NUM = 32
VAULT_GROUP_NUM = 4
VAULT_NUM_PER_GROUP = 8
VERTEX_PER_VAULT = int(np.ceil(float(VERTEX_NUM) / VAULT_NUM))
VERTEX_PER_BANK = int(np.ceil(float(VERTEX_PER_VAULT) / BANKS_PER_VAULT))
VERTEX_PER_ROW =int(np.ceil(float(VERTEX_PER_BANK) / ROWS_PER_BANK))

ROW_VALID_NUM = int(np.ceil(float(VERTEX_PER_BANK) / EVENTS_PER_ROW) * BANKS_PER_VAULT)

VAULT_SIZE = BANK_SIZE * BANKS_PER_VAULT  # 2 MB


ALPHA = 0.85
BETA = 0.5


# a vault has 8 banks, 2M byte
# 1 bank 256k byte
# 256 event 1024 byte a row
# a bank has 256 row
#  a row has 256 event
# each event is 4 byte
# 1 event is 1 vertex


class EQ:
    
    def __init__(self, ep_e_i, ep_e_o, ep_n_i, ep_n_o, ep_w_i, ep_w_o, ep_s_i, ep_s_o,
                 ep_idx_ranges, num_vaults=32, func = None):
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
        self.num_vaults = num_vaults
        self.ep_idx_ranges = ep_idx_ranges
        self.func = func
        
        self.max_events_per_port = 6
        
        self.current_vault_idx = 0
        self.current_row_idx = 0
        self.eq_e_o_list = []
        self.eq_n_o_list = []
        self.eq_w_o_list = []
        self.eq_s_o_list = []
        self.eq_o_list = [self.eq_n_o_list, self.eq_e_o_list, self.eq_s_o_list, self.eq_w_o_list]
        
        #initial row data
        self.row_data_list = [[] for i in range(self.num_vaults)]
        self.row_address_list = [None for i in range(self.num_vaults)]
        self.priority_counter = [0, 0, 0, 0]
        
        self.grant_vault_idx = [None for i in range(4)]
        self.grant_vault_onehot = []
        
        self.grant_row_idx = [None for i in range(self.num_vaults)]
        self.grant_row_onehot = []
        # initial as all 1's
        self.row_valid_list = np.ones((VAULT_NUM, ROWS_PER_BANK * BANKS_PER_VAULT), dtype=bool)

        # self.bank_valid_list = np.ones((num_vaults, BANKS_PER_VAULT), dtype=bool)
        # self.vault_valid_list = np.ones(VAULT_NUM, dtype=bool)
    
    
        #coalesce
        self.old_value_addr = []
        self.old_val = []
        self.new_val = []
        self.delta = []
        self.coalesced_val = []
        self.old_value_tag = []
        
        # priority list
        # self.vault_priority_list = [[i for i in range(VAULT_NUM_PER_GROUP)] for j in range(VAULT_GROUP_NUM)]
        self.vault_valid_list = np.ones((VAULT_GROUP_NUM, VAULT_NUM_PER_GROUP), dtype=bool)
        # self.row_priority_list = [[i for i in range(ROWS_PER_BANK)] for j in range(BANKS_PER_VAULT)]
        self.event_list = [[] for i in range(32)]
        #flag
        self.coalesce_read_data_flag = []
        self.coalesce_write_flag = []
        self.coalesce_done_flag = []
        self.coalesce_read_ing_flag = []
        self.send_row_tag_list = []
        # new adding 4.13
        self.vault_coalescing_flag = [False for _ in range(self.num_vaults)]
        
        self.write_identity_flag = []
        # self.send_data_flag = []
        self.event_list_ready_flag = []
        self.read_row_data_flag = []
        
        self.busy_flag = []
        self.row_vid_list = []
        
        #group level flag
        self.get_row_data_flag = []
        self.arbit_busy_flag = []
        # new adding 4.13
        self.group_busy_flag = [False for _ in range(4)]
        
        if func.lower() == 'pagerank':
           #vault_mem_size = np.full(VAULT_SIZE// 4, 1 - ALPHA, dtype=np.uint32)
           vault_mem_size = [np.float32(1 - ALPHA) for _ in range(VAULT_SIZE// 4)]
            #vault_mem_size = list(np.full(VAULT_SIZE // 4, 1 - ALPHA, dtype=np.uint32))
        elif func.lower() == 'sssp' or 'bfs':
            vault_mem_size = list(np.full(VAULT_SIZE // 4, np.inf, dtype=np.uint32))
        
        self.max_events_per_port = 8
        self.func = func
        self.buffer = []
        # Instantiate vault memories
        self.vault_mem = []
        for i in range(num_vaults):
            self.buffer.append(deque())
            
            self.coalesce_done_flag.append(False)
            self.coalesce_read_ing_flag.append(False)
            self.coalesce_write_flag.append(False)
            self.coalesce_read_data_flag.append(False)
            self.busy_flag.append(False)
            
            self.old_value_addr.append([])
            self.old_val.append([])
            self.new_val.append([])
            self.delta.append([])
            self.coalesced_val.append([])
            self.old_value_tag.append(None)
            
            request_port = deque()
            response_port = deque()
            vault_mem = VM(request_port, response_port, vault_mem_size)
            self.vault_mem.append(vault_mem)
            
            self.row_vid_list.append(None)
            self.grant_row_onehot.append([])
            self.send_row_tag_list.append([])
            self.read_row_data_flag.append(False)
            
            self.row_valid_list[i][ROW_VALID_NUM:] = False
            # print('row_valid_list[i][ROW_VALID_NUM:]',self.row_valid_list[i])
            # print('ROW_VALID_NUM',ROW_VALID_NUM)
            

        for i in range(int(num_vaults // 8)):
            self.arbit_busy_flag.append(False)
            self.get_row_data_flag.append(False)
            self.write_identity_flag.append(False)
            self.event_list_ready_flag.append(False)
            
            self.grant_vault_onehot.append([])
    # basic index
    

    
    def get_vault_idx(self, vertex_id):
        if vertex_id > VERTEX_NUM:
            #print("Error: vertex_id is out of range")
            return -1
        return int(vertex_id // VERTEX_PER_VAULT)
    
    def get_bank_idx(self, vertex_id):
        if vertex_id > VERTEX_NUM:
            #print("Error: vertex_id is out of range")
            return -1
        vault_idx = self.get_vault_idx(vertex_id)
        position_in_vault = (vertex_id - vault_idx * VERTEX_PER_VAULT) * EVENT_SIZE
        return position_in_vault // BANK_SIZE
    
    def get_row_idx(self, vertex_id):
        if vertex_id > VERTEX_NUM:
            #print("Error: vertex_id is out of range")
            return -1
        vault_idx = self.get_vault_idx(vertex_id)
        bank_idx = self.get_bank_idx(vertex_id)
        position_in_bank = (vertex_id * EVENT_SIZE) % BANK_SIZE
        position_in_bank = (vertex_id - vault_idx * VERTEX_PER_VAULT - bank_idx * VERTEX_PER_BANK) * EVENT_SIZE
        return position_in_bank // ROW_SIZE

    def get_event_idx(self,vertex_id):
        if vertex_id > VERTEX_NUM:
            #print("Error: vertex_id is out of range")
            return -1
        # return the index of the event in the row
        position_in_row = (vertex_id * EVENT_SIZE) % ROW_SIZE
        return position_in_row // EVENT_SIZE

    def get_row_valid_bit(self, vertex_idx):
        row_valid_bit = self.row_valid_list[self.get_row_index(vertex_idx), self.get_vault_index(vertex_idx)]
        return row_valid_bit

    def write_row_valid_bit(self, vertex_idx ,write_valid_tag):
        self.row_valid_list[self.get_vault_index(vertex_idx), self.get_row_index(vertex_idx)] = write_valid_tag

    def get_vault_valid_bit(self, vertex_idx):
        vault_valid_bit = self.vault_valid_list[vertex_idx]
        return vault_valid_bit
    
    # def get_starting_address(self, vertex_id):
    #     vault_idx = self.get_vault_idx(vertex_id)
    #     bank_idx = self.get_bank_idx(vertex_id)
    #     row_idx = self.get_row_idx(vertex_id)
    #     event_idx = self.get_event_idx(vertex_id)

    #     address = (vault_idx * BANKS_PER_VAULT * BANK_SIZE +
    #             bank_idx * BANK_SIZE +
    #             row_idx * ROW_SIZE +
    #             event_idx * EVENT_SIZE)
        
    #     return address
    
    def get_starting_address(self, vertex_id):
        bank_idx = self.get_bank_idx(vertex_id)
        row_idx = self.get_row_idx(vertex_id)
        event_idx = self.get_event_idx(vertex_id)

        address = (bank_idx * BANK_SIZE +
                row_idx * ROW_SIZE +
                event_idx * EVENT_SIZE)
        return address
    # send out index


    def reduce(self,vault_idx, func): #delta = allocate_event_vault_port()[1]
        '''
        input:
        func: which algorithm
        old_value: stale vertex property in vm          # use read_vp function
        return:
        new_val of vertex property
        '''
        if self.old_val[vault_idx] != None:
            if func.lower() == 'pagerank' or func.lower() == 'adsorption':
                self.coalesced_val[vault_idx] = self.old_val[vault_idx] + self.delta[vault_idx].val
            elif func.lower() == 'sssp' or func.lower() == 'bfs':
                self.coalesced_val[vault_idx] = min(self.old_val[vault_idx], self.delta[vault_idx].val)
            elif func.lower() =='comp':
                self.coalesced_val[vault_idx] = max(self.old_val[vault_idx], self.delta[vault_idx].val)
            else:
                self.coalesced_val[vault_idx] = self.old_val[vault_idx] + self.delta[vault_idx].val
        else:
            return None
        # return self.new_val[vault_idx]  # actully no need to return
    
    def coalesce_read_req(self, vault_idx):
        #print("EQ: send coalsece read request")
        incoming_event_val_addr = self.get_starting_address(int(self.delta[vault_idx].idx))
        self.old_value_addr[vault_idx] = incoming_event_val_addr
        # Read the existing event's value from the vault memory
        self.old_value_tag[vault_idx] = self.vault_mem[vault_idx].GetReqTag()
        req_old_val = mem_request(cmd="read", addr=incoming_event_val_addr, data=None, size=4, req_tag=self.old_value_tag[vault_idx])
        #print(f"reading old value start addr: st_addr={incoming_event_val_addr}")
        self.vault_mem[vault_idx].request_port.append(req_old_val)
        # self.coalesce_read_ing_flag[vault_idx] = True
    
    def coalesce_check_response(self, vault_idx):
        # Search for the response tag and return value(matched) in self.old_val[vault_idx]
        length = len(self.vault_mem[vault_idx].response_port)
        for i in range(length):
            resp_old_val = self.vault_mem[vault_idx].response_port[i]
            if resp_old_val.req_tag == self.old_value_tag[vault_idx]:
                self.old_val[vault_idx] = self.vault_mem[vault_idx].response_port[i].data
                self.vault_mem[vault_idx].response_port.remove(self.vault_mem[vault_idx].response_port[i])
                # #print(f"Find old value: old_val={self.old_val[vault_idx]}")
                # self.coalesce_read_data_flag[vault_idx] = True
            # else:
            #     #print(f"error: old value not found")
            #     self.coalesce_read_data_flag[vault_idx] = False
            #     return -1
    
    def coalesce_write(self, vault_idx):
        # Write the coalesced event's value back to the vault memory at the existing event's value address
        # print(f"EQ: self.coalesced_val[{vault_idx}]",self.coalesced_val[vault_idx])
        req_wirte_new = mem_request(cmd="write", addr=self.old_value_addr[vault_idx], data=self.coalesced_val[vault_idx], size=4, req_tag=0)
        #print(f"write coalescing value: new_val={self.coalesced_val[vault_idx]}")
        self.vault_mem[vault_idx].request_port.append(req_wirte_new)
        self.old_val[vault_idx] = None
        self.coalesced_val[vault_idx] = None
        self.old_value_addr[vault_idx] = None
        # self.coalesce_write_flag[vault_idx] = True




    def get_events_from_ep(self):
        
        ep_input_list = [self.ep_e_i, self.ep_n_i, self.ep_w_i, self.ep_s_i]
        # add a logic to distinguish the longest queue
        event_list = []
        for ep_input in ep_input_list:
            if ep_input:
                ep_len = len(ep_input)
                for _ in range(ep_len):
                    event = ep_input.popleft()
                    event_list.append(event)
        for event in event_list:
            event_vault_idx = self.get_vault_idx(event.idx)
            self.buffer[event_vault_idx].append(event)
            print(f"EQ: get event from EP: idx={event.idx}, val={event.val}, vault_idx={event_vault_idx}")
        # return event_list
    

    
    
    def round_robin_arbiter(self, group_idx):
        #print("round robin arbiter")
        grant_onehot = [False] * int(VAULT_NUM / 4)
        # #print(f"grant_onehot={grant_onehot}")
        grant_idx = None

        for i in range(int(VAULT_NUM / 4)):
            idx = int((self.priority_counter[group_idx] + i) % int(VAULT_NUM / 4))
            # #print(f"idx={idx}")
            # #print(f"req={req}")
            # #print(f"req[idx]={req[idx]}")
            if self.vault_valid_list[group_idx][idx]:
                grant_onehot[idx] = True
                grant_idx = idx
                break
        if grant_idx != None:
            self.priority_counter[group_idx] = (self.priority_counter[group_idx] + 1) % (VAULT_NUM / 4)
        #print(f"grant_onehot={grant_onehot}")

        self.grant_vault_idx[group_idx] = grant_idx
        self.grant_vault_onehot[group_idx] = grant_onehot


    def priority_arbiter(self, vault_idx):
        #print("priority arbiter")
        grant_onehot = [False] * (BANKS_PER_VAULT * ROWS_PER_BANK)
        num_inputs = BANKS_PER_VAULT * ROWS_PER_BANK  # 8*256 = 1024
        grant_idx = None

        for i in range(num_inputs):
            idx = i
            # #print(f"req={req}")
            if self.row_valid_list[vault_idx][idx]:
                grant_onehot[idx] = True
                grant_idx = idx
                break
        self.grant_row_idx[vault_idx] = grant_idx
        self.grant_row_onehot[vault_idx] = grant_onehot


    def get_starting_address_for_row(self, bank_idx, row_idx):
        address = (bank_idx * BANK_SIZE +
                    row_idx * ROW_SIZE)
        return address
    
    def get_vertex_id_from_address(self, address):
        vault_idx = address // (BANKS_PER_VAULT * BANK_SIZE)
        address %= BANKS_PER_VAULT * BANK_SIZE

        bank_idx = address // BANK_SIZE
        address %= BANK_SIZE

        row_idx = address // ROW_SIZE
        address %= ROW_SIZE

        event_idx = address // EVENT_SIZE

        # base_vertex_id = vault_idx * VERTEX_PER_VAULT
        vertex_id = (bank_idx * BANK_SIZE + row_idx * ROW_SIZE + event_idx * EVENT_SIZE) // EVENT_SIZE

        return vertex_id

    def write_mem_to_identity(self, vault_idx):
        # #print("write mem to identity")
        row_addr = self.row_address_list[vault_idx]
        # #print("row_addr_list = ", self.row_address_list)
        # #print("row_addr = ", row_addr)
        req_wirte_identity = mem_request(cmd="write", addr=row_addr, data=[np.float32(0) for i in range(256)], size=ROW_SIZE, req_tag=0)
        self.vault_mem[vault_idx].request_port.append(req_wirte_identity)
        # #print(f"write identity value to addr : {row_addr}")
        self.row_address_list[int(vault_idx)] = None
        # self.write_identity_flag[int(vault_idx // 8)] = True


    # def arbit_row_data(self, vault_group_idx):
    #     # get addr of selected row
    #     # for vault_group in self.vault_valid_list:
    #     #print("D ", self.row_address_list)
    #     self.grant_vault_idx, grant_vault_onehot = self.round_robin_arbiter(self.vault_valid_list[vault_group_idx], vault_group_idx)
    #     #print(f"grant_vault_idx={self.grant_vault_idx}")
    #     vault_idx = copy.deepcopy(self.grant_vault_idx + vault_group_idx * 8)
    #     #print(f"vault_group_idx={vault_group_idx}")
    #     if vault_idx is not None:
    #         vault_idx
    #         #print(f"vault_idx={vault_idx}")
    #         # self.slc_vault_list.append(vault_idx)
    #         grant_row_idx, grant_row_onehot = self.priority_arbiter(self.row_valid_list[vault_idx])
    #         # #print(f"grant_row_idx={grant_row_idx}")
    #         bank_idx = grant_row_idx % BANKS_PER_VAULT
    #         row_idx = grant_row_idx // BANKS_PER_VAULT
    #         self.vault_valid_list[vault_idx // 8][vault_idx % 8] = False
    #         # #print(f"write vault {vault_idx} to invalid")
    #         self.row_valid_list[vault_idx][grant_row_idx] = False
    #         # #print(f"write row {vault_idx} {grant_row_idx} to invalid")
    #         #print("E",self.row_address_list)
    #         #print(self.grant_vault_idx)
    #         self.row_address_list[int(vault_idx)//8].append(self.get_starting_address_for_row(bank_idx, row_idx))  # new:self.row_address_list for each vault
    #         #print("F", self.row_address_list)
    #     #print("partial row_address_list = ", self.row_address_list)
    #         # self.finish_arbit_flag[int(vault_idx // 8)] = True
    #     return self.row_address_list


    def read_row_data_req(self, vault_idx):
        # Read the existing event's value from the vault memory
        # for vault_idx in vault_list:
        bank_idx = self.grant_row_idx[vault_idx] % BANKS_PER_VAULT
        row_idx = self.grant_row_idx[vault_idx] // BANKS_PER_VAULT
        self.row_address_list[vault_idx] = (self.get_starting_address_for_row(bank_idx, row_idx))
        self.row_vid_list[vault_idx] = bank_idx * VERTEX_PER_BANK + row_idx * VERTEX_PER_ROW + vault_idx * VERTEX_PER_VAULT
        # #print("row_address_list = ", self.row_address_list)
        # #print("bank_idx = ", bank_idx)
        # #print("row_idx = ", row_idx)
        self.send_row_tag_list[vault_idx] = (self.vault_mem[vault_idx].GetReqTag())
        req_row = mem_request(cmd="read", addr=self.row_address_list[vault_idx], data=None, size=ROW_SIZE, req_tag=self.send_row_tag_list[vault_idx])
        #print(f"read row data from addr : {self.row_address_list[vault_idx]}")
        self.vault_mem[vault_idx].request_port.append(req_row)
        # for i in range(len(self.vault_mem[vault_idx].request_port)):
        #     #print("Request tag: ", self.vault_mem[vault_idx].request_port[i].req_tag)
        #     #print("Request addr: ", self.vault_mem[vault_idx].request_port[i].addr)
        #     #print("Request size: ", self.vault_mem[vault_idx].request_port[i].size)
        #     #print("Request data: ", self.vault_mem[vault_idx].request_port[i].data)
        #     #print("Request cmd: ", self.vault_mem[vault_idx].request_port[i].cmd)



    def read_row_data_resp(self, vault_idx):
        # Search for the response tag
        # for vault_idx in vault_list:
        resp_port_len = len(self.vault_mem[vault_idx].response_port)
        for i in range(resp_port_len):
            resp_val = self.vault_mem[vault_idx].response_port[i]
            # #print("Response: ", resp_val.req_tag, "Send row tag: ", self.send_row_tag_list[vault_idx])
            if resp_val.req_tag == self.send_row_tag_list[vault_idx]:
                #print("EQ: accessing tag matched")
                self.send_row_tag_list[vault_idx] = None
                self.row_data_list[vault_idx] = resp_val.data
                #print("vault_idx",vault_idx)
                self.vault_mem[vault_idx].response_port.remove(self.vault_mem[vault_idx].response_port[i])
                # self.read_row_data_flag[vault_idx] = False


    def row_data_2_event_list(self, vault_idx):
        # #print(f"row_data_list [{vault_idx}] = ", self.row_data_list[vault_idx])
        # #print(f"len of row_data_list [{vault_idx}] = ", len(self.row_data_list[vault_idx]))
        # #print(f"row_address_list [{vault_idx}] = ", self.row_address_list[vault_idx])
        # #print(f"type of row data list [{vault_idx}] = ", type(self.row_data_list[vault_idx]))
        value_list = self.row_data_list[int(vault_idx)].tolist()
        #print("value_list", value_list)
        for i in range(len(self.row_data_list[int(vault_idx)])):
            # #print("i", i)
            # for j in len(self.row_data_list[int(vault_idx)][i]):
            self.event_list[vault_idx].append(event(idx = self.row_vid_list[vault_idx] + i
                                                    , val = value_list[i]))
            # self.row_address_list[int(vault_idx)][i] = 
            # #print("clear row_address_list", [int(vault_idx)][i])
            # self.row_data_list[int(vault_idx)][i][j] = []
            # #print("clear row_data_list", [int(vault_idx)][i][j])
        
        self.row_data_list[int(vault_idx)] = []
        # return self.event_list[vault_idx]

    def send_data_to_ep(self, vault_idx):
        # append one row data in row_data_list to each EP, the append data should be removed from row_data_list
        # for vault_idx in vault_list
        # #print("vault_idx = ", vault_idx)
        # #print("event_list = ", self.event_list[vault_idx])
        if self.event_list[int(vault_idx)] != []:
            if int(vault_idx) // 8 == 0:
                for event in self.event_list[vault_idx]:
                    self.ep_n_o.append(event)
            elif int(vault_idx) // 8 == 1:
                for event in self.event_list[vault_idx]:
                    self.ep_w_o.append(event)
            elif int(vault_idx) // 8 == 2:
                for event in self.event_list[vault_idx]:
                    self.ep_s_o.append(event)
            elif int(vault_idx) // 8 == 3:
                for event in self.event_list[vault_idx]:
                    self.ep_e_o.append(event)
        self.event_list[vault_idx] = []


    # def one_cycle(self):
    #     self.get_events_from_ep()
    #     for i in range(self.num_vaults):
    #         self.vault_mem[i].one_cycle()
    #         #print(f"vault {i} buffer: {self.buffer[i]}")
    #         if len(self.buffer[i]) == 0:
    #             #print(f"buffer{i} is empty")
    #             pass
    #         else:
    #             # coalescing
    #             #print("start coalescing")
    #             if self.busy_flag[i] == True:
    #                 #print(f"vault {i} is busy")
    #                  # coalescing, not send read req(already sent) waiting response, deal response to write request
    #                 self.coalesce_get_read_data(i, event)
    #                 if self.coalesce_read_data_flag[i] == False:
    #                     #print("not read data")
    #                     pass
    #                 else:
    #                     old_event = self.coalesce_event(event, i, fun = "pagerank")
    #                     if self.coalesce_done_flag[i] == False:
    #                         #print("coalesce not done")
    #                         pass
    #                     else:
    #                         self.coalesce_write(i)
    #                         if self.coalesce_write_flag[i] == False:
    #                             #print("coalesce write no done")
    #                             pass
    #                         else:
    #                             self.busy_flag[i] = False
    #             else:
    #                 event = self.buffer[i].popleft()
    #                 self.busy_flag[i] = True
    #                 self.coalesce_read_req(i, event)
    #                 #print("reading coalesce data")



    #     #print("start arbit row data")
        
    #     for i in range(int(self.num_vaults//8)):
    #         #print("response_port",len((self.vault_mem[i].response_port)))
    #         #print("request_port",len((self.vault_mem[i].request_port)))
    #         #print(" self.arbit_busy_flag=",self.arbit_busy_flag[i])
    #         if self.arbit_busy_flag[i] == True:
    #             # depending on what state is now
    #             if self.read_row_data_flag[i] == True:
    #                     self.read_row_data_resp(i)
    #                     #print("read row data response")
    #                     pass
    #             elif self.write_identity_flag[i] == False:
    #                 self.write_mem_to_identity(i)
    #                 #print("write mem to identity")
    #                 pass
    #             elif self.write_identity_flag == True:
    #                 self.send_data_to_ep(i)
    #                 self.arbit_busy_flag[i] = False
    #         else:
    #             #print("A ", self.row_address_list)
    #             self.row_address_list = self.arbit_row_data(i)
    #             #print("B ", self.row_address_list)
    #             #print("read_row_data_flag = ", self.read_row_data_flag[i])
    #             if self.read_row_data_flag[i] == False and len(self.row_address_list) != 0:
    #                 self.arbit_busy_flag[i] = True
    #                 self.read_row_data_req(i)
    #                 #print(f"read row data req flag {i}", self.read_row_data_flag[i])
    #                 #print("read row data req")
    #                 pass


        # Get the events from the input ports

    def one_clock_try(self):

    # allocte all incoming events to related buffer (use append), each vault has a buffer deque

        self.get_events_from_ep()

        for i in range(self.num_vaults):
            self.vault_mem[i].one_cycle()
            #print(f"EQ: vault {i} buffer len: {len(self.buffer[i])}")
            if len(self.buffer[i]) == 0:
                ##print(f"buffer{i} is empty")
                pass
        
        for i in range(int(self.num_vaults // 8)):
            
            if self.group_busy_flag[i] == False:
                self.round_robin_arbiter(i)
                #print(f'EQ: vault[{self.grant_vault_idx[i]}] is selected')
                if self.grant_vault_idx[i] != None:
                    #print(f'group[{i}] is choosing a new vault')
                    self.group_busy_flag[i] = True
                    #print(f"group {i} busy", self.group_busy_flag[i])
        
        
        #for group in vault_groups:
            # if this group not busy #vault selected is not valid/empty:
            #     round robin choose vault
            #     if valid grant:
            #         set group busy flag
        for i in range(self.num_vaults):
            
            if self.grant_vault_onehot[i // 8][i % 8] == True:
                
                #print(f'vault[{i}] is selected')
                if self.vault_coalescing_flag[i] == True:
                    #print(f'selected vault[{i}] is coalescing')
                    if self.old_val[i] == None:
                        #print('fetching old_val')
                        self.coalesce_check_response(i) # get resp tag and old val
                    elif self.old_val[i] != None:
                        #print('old_val is ready')
                        self.reduce(i, "pagerank")
                        self.coalesce_write(i)
                        self.vault_coalescing_flag[i] = False
                        self.old_val[i] = None
                        self.vault_valid_list[i // 8][i % 8] = True # 有东西
                        row_idx = int(self.get_bank_idx(self.delta[i].idx)*BANKS_PER_VAULT + self.get_row_idx(self.delta[i].idx) * ROWS_PER_BANK)
                        print(f'row_idx_type: {type(row_idx)}')
                        self.row_valid_list[i][row_idx] = True
                        
                elif self.read_row_data_flag[i] == True:  # 32 sized flag indicating whether is reading a row data
                    #print('selected vault is fetching row data')
                    self.read_row_data_resp(i)  # todo : modify read_row_data_resp to vault-level behavior
                    #print("i",i)
                    if self.row_data_list[i] != []:
                        # print('self.row_data_list is not empty')
                        #print(f'EQ: self.row_data_list[{i}] = {self.row_data_list[i]}')
                        #print(f'EQ: self.row_address_list[{i}] = {self.row_address_list[i]}')
                        self.row_data_2_event_list(i)
                        #if i < 8:
                            #print(f'EQ: self.event_list[{i}].val = {self.event_list[i][0].val}' ,f"len = {len(self.event_list[i])}")
                            #print(f'EQ: self.event_list[{i}].idx = {self.event_list[i][0].idx}')
                        self.send_data_to_ep(i)
                        self.row_vid_list[i] = None
                        self.write_mem_to_identity(i)
                        self.read_row_data_flag[i] = False
                        
                        # bank_idx = self.grant_row_idx[i] % BANKS_PER_VAULT
                        # row_idx = self.grant_row_idx[i] // BANKS_PER_VAULT
                        # row_index = # todo: calculate row index from arbit
                        self.row_valid_list[i][self.grant_row_idx[i]] = False
                
                else: 
                    print(f'grant row idx {i} {self.grant_row_idx[i]}')
                    self.priority_arbiter(i) #grant_row_idx = num_bank* row_pre_bank
                    print(f'grant row idx {i} {self.grant_row_idx[i]}')
                    if i == 2:
                        print(self.row_valid_list[i][256])
                    #print("arbited row i:", i)
                    if self.grant_row_idx[i] == None: # to do add self.grant_row_idx
                        self.group_busy_flag[i//8] = False
                        #print(f"group {i // 8} not busy", self.group_busy_flag[i//8])
                        self.vault_valid_list[i//8][i%8] = False
                        #print(f'vault[{i}] is empty, set to not valid')
                        #print(f'group[{i//8}] is not busy now')
                    else:
                        self.read_row_data_req(i) # which row to read
                        self.read_row_data_flag[i] = True
            
            
            elif self.grant_vault_onehot[i // 8][i % 8] == False:
                #print(f'EQ: vault[{i}] is not selected')
                #print(f'EQ: vault_coalescing_flag[{i} is {self.vault_coalescing_flag[i]}]')
                if self.vault_coalescing_flag[i] == True:
                    #print(f'EQ: vault[{i}] is coalescing')
                    if self.old_val[i] == None and self.old_value_tag[i] != None:
                        #print('EQ: fetching old_val')
                        self.coalesce_check_response(i) # get resp tag and old val
                    elif self.old_val[i] != None:
                        #print('EQ: old_val is ready')
                        #print("EQ: self.old_val[i]", self.old_val[i])
                        #print("EQ: self.delta[i] idx", self.delta[i].idx , "EQ: self.delta[i] val:", self.delta[i].val)
                        self.reduce(i, "pagerank")
                        #print("EQ: self.coalesced_val[i]", self.coalesced_val[i])
                        self.coalesce_write(i)
                        #print(f'EQ: self.vault_mem[{i}].request data = {self.vault_mem[i].request_port[0].data}')
                        self.vault_coalescing_flag[i] = False
                        self.old_val[i] = None
                        self.vault_valid_list[i // 8][i % 8] = True # 有东西
                        bank_idx = int(self.get_bank_idx(self.delta[i].idx))
                        row_idx_offset = int(self.get_row_idx(self.delta[i].idx))
                        row_idx = bank_idx * ROWS_PER_BANK + row_idx_offset
                        #print(f'EQ: bank_idx={bank_idx}, row_idx_offset ={row_idx_offset}')
                        #print("EQ: row_idx", row_idx)
                        self.row_valid_list[i][row_idx] = True
                

                elif self.vault_coalescing_flag[i] == False:
                    if (len(self.buffer[i])==0):
                        pass
                        #print(f'no incoming event for vault[{i}]')
                    else:
                        #print(f'vault[{i}] is taking a new event this cylce')
                        incoming_event = self.buffer[i].popleft()
                        self.delta[i] = incoming_event
                        # how to store incoming_event.idx (Vid)?
                        # -----------------
                        # calculate address send read req(at the same time renew self.old_value_tag[i])
                        self.coalesce_read_req(i)
                        # reset flags and values
                        self.vault_coalescing_flag[i] = True
                        self.old_val[i] = None




                
        
        # for vault in all the vaults:
            
        #     if selected: # check the round robin grant onehot [vault_idx//8][vault_idx%8]

        #         if vault is coalescing: # waiting for the read data (coalesing flag)
        #             monitor response
        #             if response tag matches:
        #                 coalesce with reduce function
        #                 send write request
        #                 set not coalescing flag
        #                 set row valid flag
        #                 set vault valid flag
                
        #         elif vault is reading a row: #reading flag
        #             monitor response
        #             if response tag matches:
        #                 send events to serial link
        #                 write identity value to the row in DRAM
        #                 set not reading flag
        #                 set row not valid flag
                
        #         else: #vault is not reading a row
        #             priority arbiter choose a row
        #             if no valid grant: #vault is empty
        #                 set group not busy # 通知arbiter
        #                 set vault not valid # 不参与
        #             else: #vault is not empty yet, a new row is selected
        #                 send request to read the new row
        #                 set reading flag
                
        #     else: #not selected
                
        #         if vault is coalescing: # waiting for the read data (coalesing flag)
        #             monitor response
        #             if response tag matches:
        #                 coalesce with reduce function
        #                 send write request
        #                 set not coalescing flag
        #                 set row valid flag
        #                 set vault valid flag
                        
        #         else: # no ongoing colescing, can take in a new event
        #             pop a event from vault input buffer
        #             if the event is not NONE:
        #                 send read request
        #                 set coalesing flag
