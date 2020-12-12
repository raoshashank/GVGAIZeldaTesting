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
import uuid

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
for i,run in enumerate(test_trace):
    sas_trace = []
    first_state = Zelda_State(run[0][0],trace_id=0)
    monster_mapping = first_state.monster_mapping
    for sa1,sa2 in zip(run,run[1:]):
        sas_trace.append([Zelda_State(sa1[0],monster_mapping,trace_id = i),sa1[1],Zelda_State(sa2[0],monster_mapping,trace_id = i+1)])
        if sa2[1]=='ACTION_ESCAPE':
            break
    new_test_traces.append(sas_trace)

high_level_traces = []
high_level_actions = {} #key: action_id, value: (abs_s1,abs_s2)
#translator = Zelda_Translator()
for trace in new_test_traces:
    abs_trace = []
    for s1,a,s2 in trace:
        abs_s1 = AbstractZeldaState(s1) 
        abs_s2 = AbstractZeldaState(s2)
        print("Abstract State1:"+str(abs_s1))
        print("Concretized_state1:"+str(Zelda_State().refine_abstract_state(abs_s1))) 
        print("-------------") 
        print("Abstract State2:"+str(abs_s2))
        print("Concretized_state2:"+str(Zelda_State().refine_abstract_state(abs_s2))) 
        print("===============")
        if abs_s1 != abs_s2:
            #create a new action
            action_id = uuid.uuid1()
            high_level_actions[action_id] = [abs_s1,abs_s2,]
            abs_trace.append((abs_s1,action_id,abs_s2))

import IPython
IPython.embed()