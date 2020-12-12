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
from src.ZeldaStates import *
from search import *
import uuid

def zelda_agent():
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
    num_traces = 1
    for i in range(num_traces):
        Zelda_Env_Helper.start_server()
        print("Finished Tester")

def test_search(state1,state2):
    translator = Zelda_Translator()
    action_list,total_nodes_expanded = translator.plan_to_state(state1,state2,"astar")
    print(plot_state(state2))
    print("Plan:"+str(action_list))
    # for action in action_dict:
    #     print(action)
    #     print(plot_state(action_dict[action][1]))

def test_get_successor(state1,action):
    translator = Zelda_Translator()
    return translator.get_successor(state1,action)
    
def test_iaa_query(state,plan,stored_actions):
    '''
        state: abstract
        plan: hashed values corresponding to stored actions
    '''
    abstract_states = [state]
    for action in plan:
        '''
        can check plan possibility here itself
        '''
        abstract_states.append(stored_actions[plan][0])
        abstract_states.append(stored_actions[plan][1])

def save_action_dict():
    level_file = "/home/raoshashank/GVGAI-master/examples/gridphysics/zelda_lvl0.txt"
    game_file  = "/home/raoshashank/GVGAI-master/examples/gridphysics/zelda.txt"
    Zelda_Env_Helper = GVGAgent_Helper(90,level_file,game_file)
    sso_plan = []
    plan_file = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/plan.pkl" 
    sso_file = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/all_actions.pkl"

    with open(sso_file,"rb") as f:
        sso =  pickle.load(f)

    all_actions = sso.availableActions
    print(all_actions)

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
        high_level_traces.append(abs_trace)
    return high_level_actions,high_level_traces

def test_plan_run(high_level_trace,high_level_actions):
    actions = []
    state = high_level_trace[0][0]
    [actions.append(a) for s1,a,s2 in high_level_trace]
    translator = Zelda_Translator()
    translator.update_high_actions(high_level_actions)
    
    action_parameters, predTypeMapping, agent_model, abstract_model, objects, _ , init_state, name = translator.generate_ds()
    print("Hello")

    success,plan_length,final_state = translator.iaa_query(state,actions)
    return success,plan_length,final_state

def test_set_GVG_state(state):
    translator = Zelda_Translator()
    translator.set_GVG_state(state)

if __name__ == '__main__':
    #zelda_agent()
    test_trace = "test_trace"
    try:
        with open(test_trace,'rb') as f:
            test_trace = pickle.load(f)
    except IOError:
        pass
    
    high_level_actions,high_level_traces = save_action_dict()
    import IPython
    trace = high_level_traces[-1]
    
    success,plan_length,final_state = test_plan_run(trace,high_level_actions) #Next check for impossible plansd
    print(success)
    print(plan_length)
    print(len(trace))
    print(plot_state(final_state))
    IPython.embed()

    #test_set_GVG_state(trace[-1][0])
    state1 = test_trace[-1][0][0]
    state2 = test_trace[-1][1][0]
    all_actions = state1.availableActions
    zstate1 = Zelda_State(state1)
    zstate2 = Zelda_State(test_trace[-1][10][0])
    print(plot_state(zstate1))
    print(plot_state(zstate2))
    
    
    
    test_search(zstate1,zstate2)
    for i,sa in enumerate(test_trace[-1]):
         #zstate = test_get_successor(zstate,sa[1])
         print("from")
         print(plot_state(zstate1))
         print("to")
         test_search(zstate1,Zelda_State(test_trace[-1][i][0]))
         #print("Resulting State from action "+str(sa[1]))
         

