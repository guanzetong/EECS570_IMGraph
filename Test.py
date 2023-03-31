from crossbar import round_robin_xbar
from standard import event
import numpy as np
import copy
from collections import deque
event1_1=event(idx=1,val=0)
event1_2=event(idx=2,val=1)
event2_1=event(idx=3,val=2)
event2_2=event(idx=4,val=3)
event3_1=event(idx=5,val=4)
event3_2=event(idx=5,val=5)
event4_1=event(idx=7,val=6)
event4_2=event(idx=8,val=7)

event1_deque=deque()
event1_deque.append(event1_1)
event1_deque.append(event1_2)

event2_deque=deque()
event2_deque.append(event2_1)
event2_deque.append(event2_2)

event3_deque=deque()
event3_deque.append(event3_1)
event3_deque.append(event3_2)

event4_deque=deque()
event4_deque.append(event4_1)
event4_deque.append(event4_2)
in_port_list= [deque() for i in range(4)]
in_port_list[0]=event1_deque
in_port_list[1]=event2_deque
in_port_list[2]=event3_deque
in_port_list[3]=event4_deque
out_port_list = [deque() for i in range(4)]
idx_ranges = [[1,2],[3,4],[5,6],[7,8]]
rr_xbar=round_robin_xbar(in_port_list,out_port_list,idx_ranges,1);
# for idx,in_idex in enumerate(in_port_list):
#     print("in_idex is :", idx, "in_port_list:")
#     for element in in_idex:
#         print("element.idx is:", element.idx, "element.val is:", element.val)
cnt_cycle=0
while len(in_port_list[0]) or len(in_port_list[1]) or len(in_port_list[2]) or len(in_port_list[3]) >0:
    print("//--------------------Input_port before cycle :",cnt_cycle,"-------------------------------//")

    for idx, in_idex in enumerate(in_port_list):
        print("in_idex is :", idx, "in_port_list:")
        for element in in_idex:
            print("element.idx is:", element.idx, "element.val is:", element.val)
    print("//-----------------------Output_port before cycle:",cnt_cycle,"-------------------------------//")
    for idx, out_idex in enumerate(out_port_list):
        print("out_idex is :", idx, "in_port_list:")
        for element in out_idex:
            print("element.idx is:", element.idx, "element.val is:", element.val)
    rr_xbar.one_clock()
    print("//---------------------------Cycle:",cnt_cycle,"-------------------------------//")
    print("//------------------------Input_port After cycle-------------------------------//")

    for idx, in_idex in enumerate(in_port_list):
        print("in_idex is :", idx, "in_port_list:")
        for element in in_idex:
            print("element.idx is:", element.idx, "element.val is:", element.val)
    print("//-----------------------Output_port After cycle-------------------------------//")
    for idx, out_idex in enumerate(out_port_list):
        print("out_idex is :", idx, "in_port_list:")
        for element in out_idex:
            print("element.idx is:", element.idx, "element.val is:", element.val)
    print("//-----------------------Finish Cycle:",cnt_cycle,"-------------------------------//")
    cnt_cycle=cnt_cycle+1




