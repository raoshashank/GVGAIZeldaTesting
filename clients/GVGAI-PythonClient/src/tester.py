import logging
import os
import subprocess
import sys
import traceback
import argparse
import pickle
#sys.path.append("./src")
#sys.path.append("src/utils")
sys.path.append("./utils")
from IAA_GVG_helper import GVGAgent_Helper
from zelda_translator import *
from ZeldaStates import *
from search import *
import uuid
from GVGAgent import GVGAgent

def zelda_agent():
    level_file = "/home/raoshashank/GVGAI-master/examples/gridphysics/zelda_lvl0.txt"
    game_file  = "/home/raoshashank/GVGAI-master/examples/gridphysics/zelda.txt"
    Zelda_Env_Helper = GVGAgent_Helper(90,level_file,game_file)
    # plan = [2,2,2,2,3,3,3,0,3,0,3,3,3,0,3,1,0]
    # sso_plan = []
    # plan_file = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/plan.pkl" 
    # sso_file = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/all_actions.pkl"
    # with open(sso_file,"rb") as f:
    #     sso =  pickle.load(f)
    # all_actions = sso.availableActions
    # print(all_actions)
    # with open(plan_file,"wb") as f:
    #     for i in range(len(plan)):
    #         sso_plan.append(all_actions[plan[i]])
    #     pickle.dump(sso_plan,f)
    # try:
    #     with open("test_trace",'rb') as f:
    #         test_trace = pickle.load(f)
    # except IOError:
    #     pass
    num_traces = 1
    for i in range(num_traces):
        Zelda_Env_Helper.start_server()
        print("Finished Tester")

def test_search(trace,agent):
    translator = Zelda_Translator()
    p = 0
    for i,sa in enumerate(trace):
        #zstate = test_get_successor(zstate,sa[1])
        if i < 2:
            p = 2
        else:
            p = i
        s1 = translator.refine_abstract_state(sa[0])
        s2 = translator.refine_abstract_state(sa[2])
        print("FROM:")
        print(plot_state(s1))
        print("TO:")
        print(plot_state(s2))
        action_list,total_nodes_expanded = translator.plan_to_state(s1,s2,"astar")
        print("Plan:"+str(action_list))

def test_get_successor(state1):
    translator = Zelda_Translator()
    return translator.get_successor(state1)
    
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

    with open(sso_file,"rb") as f:
        sso =  pickle.load(f)

    all_actions = sso.availableActions
    print(all_actions)

    try:
        with open("files/test_trace",'rb') as f:
            test_trace = pickle.load(f)
    except IOError:
        pass

    new_test_traces = []
    for i,run in enumerate(test_trace):
        sas_trace = []
        #first_state = Zelda_State(run[0][0],trace_id=0)
        #monster_mapping = first_state.monster_mapping
        for sa1,sa2 in zip(run,run[1:]):
            zsa1 = self.translator.from_sso(sa1[0])
            zsa2 = self.translator.from_sso(sa2[0])
            sas_trace.append([zsa1,sa1[1],zsa2])
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

def test_plan_run(trace,agent):
    actions = []
    state = trace[0][0]
    [actions.append(a) for s1,a,s2 in trace]
    query = {
        'state':state,
        'plan':actions
    }
   
    #action_parameters, predTypeMapping, agent_model, abstract_model, objects, _ , init_state, name = translator.generate_ds()
    #print("Hello")
    return agent.run_query(query)

def test_set_GVG_state(state):
    translator = Zelda_Translator()
    translator.set_GVG_state(state)

def test_random_generator(n=5):
    translator = Zelda_Translator()
    random_states = []
    for i in range(n):
        random_states.append(translator.generate_random_state())

if __name__ == '__main__':
    '''    
        #success,plan_length,final_state = test_plan_run(trace,high_level_actions) #Next check for impossible plans
        #print(success)
        #print(plan_length)
        #print(len(trace))
        #print(plot_state(final_state))
        #IPython.embed()
        #test_set_GVG_state(trace[-1][0])
        state1 = test_trace[-1][8][0]
        state2 = test_trace[-1][10][0]
        all_actions = state1.availableActions
        zstate1 = Zelda_State(state1)
        zstate2 = Zelda_State(state2)
        #print(plot_state(zstate1))
        #print(plot_state(zstate2))
        test_search(zstate1,zstate2)
        p = 0
        for i,sa in enumerate(test_trace[-1]):
            #zstate = test_get_successor(zstate,sa[1])
            if i < 2:
                p = 2
            else:
                p = i
            s1 = Zelda_State(test_trace[-1][p-2][0])
            s2 = Zelda_State(test_trace[-1][i][0])
            test_search(s1,s2)
            #print("Resulting State from action "+str(sa[1]))
    '''        
    #zelda_agent()
    agent = GVGAgent()
    #generate random states
    random_states = agent.generate_random_states(5,save=True,abstract = True)
    #validate random states
    for state in random_states:
        if not agent.validate_state(state):
            print(False)
            agent.validate_state(state)

    #save actions in dict using traces and abstraction
    agent.load_actions()
    #select a trace and run the plan from initial state as a query
    with open("files/high_traces",'rb') as f:
        test_traces = pickle.load(f)
    # for s1,a,s2 in test_traces[0]:
    #     print(plot_state(s1))
    #     print(a)
    #     print(plot_state(s2))
    #     print(s1.state['has_key'])
    #     print(s2.state['has_key'])
    #     input()
    
    for test_trace in test_traces:
        success,plan_length,final_state = test_plan_run(test_trace,agent)
        print(success)
        print(len(test_trace))
        print(plan_length)
        print(final_state)
    
    #further test low level search
    for tr in test_traces:
        test_search(tr,agent)
