import numpy as np
from collections import deque

def init():
    # I/O of ep_nw
    global ep_nw_e_o, ep_nw_e_i
    global ep_nw_s_o, ep_nw_s_i
    ep_nw_e_o = deque()
    ep_nw_e_i = deque()
    ep_nw_s_o = deque()
    ep_nw_s_i = deque()
    
    # I/O of ep_n
    global ep_n_e_o, ep_n_e_i
    global ep_n_w_o, ep_n_w_i
    global ep_n_s_o, ep_n_s_i
    ep_n_e_o = deque()
    ep_n_e_i = deque()
    ep_n_w_o = deque()
    ep_n_w_i = deque()
    ep_n_s_o = deque()
    ep_n_s_i = deque()
    
    # I/O of ep_ne
    global ep_ne_w_o, ep_ne_w_i
    global ep_ne_s_o, ep_ne_s_i
    ep_ne_w_o = deque()
    ep_ne_w_i = deque()
    ep_ne_s_o = deque()
    ep_ne_s_i = deque()
    
    # I/O of ep_w
    global ep_w_e_o, ep_w_e_i
    global ep_w_n_o, ep_w_n_i
    global ep_w_s_o, ep_w_s_i
    ep_w_e_o = deque()
    ep_w_e_i = deque()
    ep_w_n_o = deque()
    ep_w_n_i = deque()
    ep_w_s_o = deque()
    ep_w_s_i = deque()
    
    # I/O of eq_c
    global eq_c_e_o, eq_c_e_i
    global eq_c_n_o, eq_c_n_i
    global eq_c_w_o, eq_c_w_i
    global eq_c_s_o, eq_c_s_i
    eq_c_e_o = deque()
    eq_c_e_i = deque()
    eq_c_n_o = deque()
    eq_c_n_i = deque()
    eq_c_w_o = deque()
    eq_c_w_i = deque()
    eq_c_s_o = deque()
    eq_c_s_i = deque()
    
    # I/O of ep_e
    global ep_e_w_o, ep_e_w_i
    global ep_e_n_o, ep_e_n_i
    global ep_e_s_o, ep_e_s_i
    ep_e_w_o = deque()
    ep_e_w_i = deque()
    ep_e_n_o = deque()
    ep_e_n_i = deque()
    ep_e_s_o = deque()
    ep_e_s_i = deque()
    
    # I/O of ep_sw
    global ep_sw_n_o, ep_sw_n_i
    global ep_sw_e_o, ep_sw_e_i
    ep_sw_n_o = deque()
    ep_sw_n_i = deque()
    ep_sw_e_o = deque()
    ep_sw_e_i = deque()
    
    # I/O of ep_s
    global ep_s_w_o, ep_s_w_i
    global ep_s_n_o, ep_s_n_i
    global ep_s_e_o, ep_s_e_i
    ep_s_w_o = deque()
    ep_s_w_i = deque()
    ep_s_n_o = deque()
    ep_s_n_i = deque()
    ep_s_e_o = deque()
    ep_s_e_i = deque()
    
    # I/O of ep_se
    global ep_se_n_o, ep_se_n_i
    global ep_se_w_o, ep_se_w_i
    ep_se_n_o = deque()
    ep_se_n_i = deque()
    ep_se_w_o = deque()
    ep_se_w_i = deque()