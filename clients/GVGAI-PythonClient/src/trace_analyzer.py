import logging
import os
import subprocess
import sys
import traceback
import argparse
import pickle
sys.path.append("./src")
sys.path.append("src/utils")
sys.path.append("./utils")
from IAA_GVG_helper import GVGAgent_Helper
from zelda_translator import *
#import IPython

level_file = "/home/raoshashank/GVGAI-master/examples/gridphysics/zelda_lvl0.txt"
game_file  = "/home/raoshashank/GVGAI-master/examples/gridphysics/zelda.txt"
Zelda_Env_Helper = GVGAgent_Helper(90,level_file,game_file)
plan = [2,2,2,2,3,3,3,0,3,0,3,3,3,0,3,1,0]
sso_plan = []
plan_file = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/plan.pkl" 
sso_file = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/all_actions.pkl"
with open(sso_file,"rb") as f:
    sso =  pickle.load(f)
all_actions = sso.availableActions
print(all_actions)
with open(plan_file,"wb") as f:
    for i in range(len(plan)):
        sso_plan.append(all_actions[plan[i]])
    pickle.dump(sso_plan,f)
try:
    with open("test_trace",'rb') as f:
        test_trace = pickle.load(f)
except IOError:
    pass
new_test_traces = []
for run in test_trace:
    sas_trace = []
    for sa1,sa2 in zip(run,run[1:]):
        if sa1[1]!='ACTION_ESCAPE':
            sas_trace.append([sa1[0],sa1[1],sa2[0]])
    new_test_traces.append(sas_trace)
#IPython.embed()


# modded_traces = []
# previous_zstate = None
# for pair in test_trace:
#     zstate = Zelda_State(pair[0])
#     modded_traces.append((zstate,pair[1]))
#     if previous_zstate!=None:
#         #compare_states(zstate,previous_zstate)
#         for k in previous_zstate.state.keys():
#             if previous_zstate.state[k]!=zstate.state[k]:
#                 if k!='clear':
#                     print("Key: "+k)
#                     print("value1:"+str(previous_zstate.state[k]))
#                     print("value2:"+str(zstate.state[k]))
#                     print("transition action:"+str(pair[1]))
#                 else:
#                     print("Key: "+k)
#                     print("Diff:"+str(set(previous_zstate.state[k]).difference(zstate.state[k])))
#                     print("transition action:"+str(pair[1]))
#     print("===============")
#     previous_zstate = zstate
