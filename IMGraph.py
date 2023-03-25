#############################################
###     IMGraph Architecture Simulator    ###
#############################################
#                                           #
#           ep_nw = ep_n = ep_ne            #
#             ||     ||      ||             #
#           eq_w  = eq_c =  ep_e            #
#             ||     ||      ||             #
#           ep_sw = ep_s = ep_se            #
#                                           #
#############################################

import copy
import io_port
import numpy as np
from event_processors import EP_h1, EP_h2
from event_queues import EQ
from serial_links import SL


if __name__ == "__main__":
    
    # Instantiate HMCs
    
    ep_nw = EP_h2(ep_0_i=io_port.ep_nw_e_i, 
                  ep_0_o=io_port.ep_nw_e_o, 
                  ep_1_i=io_port.ep_nw_s_i, 
                  ep_1_o=io_port.ep_nw_s_o)
    
    ep_n  = EP_h1(eq_i  =io_port.ep_n_s_i , 
                  eq_o  =io_port.ep_n_s_o , 
                  ep_0_i=io_port.ep_n_e_i , 
                  ep_0_o=io_port.ep_n_e_o , 
                  ep_1_i=io_port.ep_n_w_i , 
                  ep_1_o=io_port.ep_n_w_o )
    
    ep_ne = EP_h2(ep_0_i=io_port.ep_ne_w_i, 
                  ep_0_o=io_port.ep_ne_w_o, 
                  ep_1_i=io_port.ep_ne_s_i, 
                  ep_1_o=io_port.ep_ne_s_o)
    
    eq_w  = EP_h1(eq_i  =io_port.ep_w_e_i , 
                  eq_o  =io_port.ep_w_e_o , 
                  ep_0_i=io_port.ep_w_n_i , 
                  ep_0_o=io_port.ep_w_n_o , 
                  ep_1_i=io_port.ep_w_s_i , 
                  ep_1_o=io_port.ep_w_s_o )
    
    eq_c  = EQ   (ep_e_i=io_port.eq_c_e_i ,
                  ep_e_o=io_port.eq_c_e_o ,
                  ep_n_i=io_port.eq_c_n_i ,
                  ep_n_o=io_port.eq_c_n_o ,
                  ep_w_i=io_port.eq_c_w_i ,
                  ep_w_o=io_port.eq_c_w_o ,
                  ep_s_i=io_port.eq_c_s_i ,
                  ep_s_o=io_port.eq_c_s_o )
    
    ep_e  = EP_h1(eq_i  =io_port.ep_e_w_i ,
                  eq_o  =io_port.ep_e_w_o ,
                  ep_0_i=io_port.ep_e_n_i ,
                  ep_0_o=io_port.ep_e_n_o ,
                  ep_1_i=io_port.ep_e_s_i ,
                  ep_1_o=io_port.ep_e_s_o )
    
    ep_sw = EP_h2(ep_0_i=io_port.ep_sw_e_i,
                  ep_0_o=io_port.ep_sw_e_o,
                  ep_1_i=io_port.ep_sw_n_i,
                  ep_1_o=io_port.ep_sw_n_o)
    
    ep_s  = EP_h1(eq_i  =io_port.ep_s_n_i ,
                  eq_o  =io_port.ep_s_n_o ,
                  ep_0_i=io_port.ep_s_e_i ,
                  ep_0_o=io_port.ep_s_e_o ,
                  ep_1_i=io_port.ep_s_w_i ,
                  ep_1_o=io_port.ep_s_w_o )
    
    ep_se = EP_h2(ep_0_i=io_port.ep_se_w_i,
                  ep_0_o=io_port.ep_se_w_o,
                  ep_1_i=io_port.ep_se_n_i,
                  ep_1_o=io_port.ep_se_n_o)
    
    # Instantiate serial links
    
    ep_nw2ep_n = SL(in_port=io_port.ep_nw_e_o, out_port=io_port.ep_n_w_i)
    ep_n2ep_nw = SL(in_port=io_port.ep_n_w_o, out_port=io_port.ep_nw_e_i)
    
    ep_n2ep_ne = SL(in_port=io_port.ep_n_e_o, out_port=io_port.ep_ne_w_i)
    ep_ne2ep_n = SL(in_port=io_port.ep_ne_w_o, out_port=io_port.ep_n_e_i)
    
    ep_w2eq_c  = SL(in_port=io_port.ep_w_e_o, out_port=io_port.eq_c_w_i)
    eq_c2ep_w  = SL(in_port=io_port.eq_c_w_o, out_port=io_port.ep_w_e_i)
    
    eq_c2ep_e  = SL(in_port=io_port.eq_c_e_o, out_port=io_port.ep_e_w_i)
    eq_e2ep_c  = SL(in_port=io_port.ep_e_w_o, out_port=io_port.eq_c_e_i)
    
    ep_sw2ep_s = SL(in_port=io_port.ep_sw_e_o, out_port=io_port.ep_s_w_i)
    ep_s2ep_sw = SL(in_port=io_port.ep_s_w_o, out_port=io_port.ep_sw_e_i)
    
    ep_s2ep_se = SL(in_port=io_port.ep_s_e_o, out_port=io_port.ep_se_w_i)
    ep_se2ep_s = SL(in_port=io_port.ep_se_w_o, out_port=io_port.ep_s_e_i)
    
    ep_nw2ep_w = SL(in_port=io_port.ep_nw_s_o, out_port=io_port.ep_w_n_i)
    ep_w2ep_nw = SL(in_port=io_port.ep_w_n_o, out_port=io_port.ep_nw_s_i)
    
    ep_w2ep_sw = SL(in_port=io_port.ep_w_s_o, out_port=io_port.ep_sw_n_i)
    ep_sw2ep_w = SL(in_port=io_port.ep_sw_n_o, out_port=io_port.ep_w_s_i)
    
    ep_n2eq_c  = SL(in_port=io_port.ep_n_s_o, out_port=io_port.eq_c_n_i)
    eq_c2ep_n  = SL(in_port=io_port.eq_c_n_o, out_port=io_port.ep_n_s_i)
    
    eq_c2ep_s  = SL(in_port=io_port.eq_c_s_o, out_port=io_port.ep_s_n_i)
    ep_s2eq_c  = SL(in_port=io_port.ep_s_n_o, out_port=io_port.eq_c_s_i)
    
    ep_ne2ep_e = SL(in_port=io_port.ep_ne_s_o, out_port=io_port.ep_e_n_i)
    ep_e2ep_ne = SL(in_port=io_port.ep_e_n_o, out_port=io_port.ep_ne_s_i)
    
    ep_e2ep_se = SL(in_port=io_port.ep_e_s_o, out_port=io_port.ep_se_n_i)
    ep_se2ep_e = SL(in_port=io_port.ep_se_n_o, out_port=io_port.ep_e_s_i)
    