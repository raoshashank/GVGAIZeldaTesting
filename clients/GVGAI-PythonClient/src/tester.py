import logging
import os
import subprocess
import sys
import traceback
import argparse
import pickle
sys.path.append("src/utils")
sys.path.append("./utils")
from src.IAA_GVG_helper import GVGAgent_Helper
level_file = "/home/raoshashank/GVGAI-master/examples/gridphysics/zelda_lvl0.txt"
game_file  = "/home/raoshashank/GVGAI-master/examples/gridphysics/zelda.txt"
Zelda_Env_Helper = GVGAgent_Helper(90,level_file,game_file)
plan = [2,2,3,2,2,0,3,0,1,2,2,2,2,2,2,0,0,1,3,3,4,4,4,2,2,1,1,0,0]
sso_plan = []
plan_file = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/plan.pkl" 
sso_file = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/all_actions.pkl"
with open(sso_file) as f:
    sso =  pickle.load(f)
all_actions = sso.availableActions
with open(plan_file,"wb") as f:
    for i in range(len(plan)):
        sso_plan.append(all_actions[plan[i]])
    pickle.dump(sso_plan,f)
Zelda_Env_Helper.start_server()