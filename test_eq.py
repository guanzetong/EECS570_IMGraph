from event_queues import EQ
from collections import deque


ep_e_i = deque()
ep_e_o = deque()
ep_n_i = deque()
ep_n_o  = deque()
ep_w_i = deque()
ep_w_o = deque()
ep_s_i = deque()
ep_s_o = deque()
ep_idx_ranges = [0, 1000]
num_vaults=32

eq = EQ(ep_e_i, ep_e_o, ep_n_i, ep_n_o, ep_w_i, ep_w_o, ep_s_i, ep_s_o, ep_idx_ranges, num_vaults)