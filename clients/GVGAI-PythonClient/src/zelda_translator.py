import logging
import os
import subprocess
import sys
import traceback
import argparse
sys.path.append("src/utils")
sys.path.append("./utils")
from ClientComm import ClientComm
from pprint import pprint
from translator import Translator
import numpy as np
from ZeldaStates import *
from search import *
import pickle
import copy
from config import Literal
'''
    Required behavior:
        Create a level file from a relational state
        Run a plan with the given initial state
        Store the actions that cause change in abstract states (from traces)
        plans will contain these actions and will have to be applied on low-level states
        Q: How do I apply a high-level action to a low-level state since info is lost in abstraction?
'''
def plot_state(zstate):
    sprites = {
            "goal": 'g', 
            "key": '+',         
            "nokey": 'A', 
            "monsterQuick": '1', 
            "monsterNormal": '2', 
            "monsterSlow": '3', 
            "wall":"w",
            "floor":".",
            "withkey":"Q"
        }

    x_axis_size = zstate.grid_height
    y_axis_size = zstate.grid_width
    
    data = np.chararray([y_axis_size,x_axis_size],unicode=True)
    try:
        for i in range(y_axis_size):
            for j in range(x_axis_size):
                cell = 'cell_'+str(i)+'_'+str(j)
                if cell in zstate.state['wall']:
                    data[i,j] = sprites["wall"]
                elif cell in zstate.state["door"]:
                    data[i,j] = sprites["goal"]
                elif cell in zstate.state["key"]:
                    data[i,j]= sprites["key"]
                elif cell in zstate.state["player"]:
                    if zstate.state["has_key"][0]==True:
                        data[i,j] = zstate.state["player_orientation"][0]#+sprites["withkey"]
                    else:
                        data[i,j] = zstate.state["player_orientation"][0]#+sprites["nokey"]
                else:
                    data[i,j]='.'
        for pair in zstate.state["monster"]:
            x = int(pair[1].replace("cell_","").split('_')[0])
            y = int(pair[1].replace("cell_","").split('_')[1])
            data[x,y] = sprites["monsterQuick"]
        return data.T
    except KeyError:
        pass
class Zelda_Translator(Translator):
    def __init__(self,level_num = 0):
        super().__init__('/home/raoshashank/GVGAI-master/examples/gridphysics','zelda',level_num)   
        self.level_file_root  = "/home/raoshashank/GVGAI-master/examples/gridphysics/"
        self.sprites = {
            "goal": 'g', 
            "key": '+',         
            "nokey": 'A', 
            "monsterQuick": '1', 
            "monsterNormal": '2', 
            "monsterSlow": '3', 
            "wall":"w",
            "floor":".",
            "withkey":"Q"
        }
        self.high_actions = {}
        self.random_states = []
      
    def update_high_actions(self,actions):
        #just to make sure this is called atleast once
        self.high_actions.update(actions)
    
    def create_level_from_state(self,zelda_state,level_file):
        level_text = ""
        for i in range(zelda_state.grid_height): 
            for j in range(zelda_state.grid_width):
                cell = 'cell_'+str(j)+'_'+str(i)
                if cell in zelda_state.predicates['monster']:
                    level_text+=self.sprites["monsterSlow"]
                if cell in zelda_state.predicates['wall']:
                    level_text+=self.sprites['wall']
                if cell in zelda_state.predicates['player']:
                    if zelda_state['has_key'][0]==True:
                        level_text+=self.sprites["withkey"]
                    else:
                        level_text+=self.sprites["nokey"]
                if cell in zelda_state.predicates['door']:
                    level_text+=self.sprites["door"]
                if cell in  zelda_state.predicates['key']:
                    level_text+=self.sprites["key"]
                else:
                    level_text+="."
            level_text+="\n"         
        with open(level_file,"w") as f:
            f.writelines(level_text)

    def random_state_generator(self,r,c):
        random_state = Zelda_State()
        player_location = 'cell_'+str(np.random.randint(1,c-1))+'_'+str(np.random.randint(1,r-1))
        for i in range(c):
            for j in range(r):
                cell_name = 'cell_ '+str(i)+'_'+str(j)
                cell_up = 'cell_ '+str(i)+'_'+str(j-1)
                cell_down = 'cell_ '+str(i)+'_'+str(j+1)
                cell_right = 'cell_ '+str(i+1)+'_'+str(j)
                cell_left = 'cell_ '+str(i-1)+'_'+str(j)
                random_state.objects.append(cell_name)
                if i+1<c:
                    random_state.predicates['leftOf'].append([cell_name,cell_right])
                    random_state.predicates['rightOf'].append([cell_right,cell_name])
                if j+1<r:
                    random_state.predicates['above'].append([cell_name,cell_down])
                    random_state.predicates['below'].append([cell_down,cell_name])
                if i!=0:
                    random_state.predicates['leftOf'].append([cell_left,cell_name])
                    random_state.predicates['rightOf'].append([cell_name,cell_right])
                if j!=0:
                    random_state.predicates['above'].append([[cell_up,cell_name]])
                    random_state.predicates['below'].append([[cell_name,cell_up]])        
        
        num_monsters = np.random.randint(2,5)
        num_blocked_cells = np.random.choice(range(int(3 * c * r / 10)))
        all_cells = list(random_state.objects)
        blocked_cells = np.random.sample(all_cells, num_blocked_cells)
        unblocked_cells = list(set(all_cells).difference(set(blocked_cells)))
        monster_positions = np.random.sample(unblocked_cells, num_monsters)
        sprite_positions = np.random.sample(set(unblocked_cells).difference(monster_positions), 3)
        
        player_position = sprite_positions[0]
        key_position = sprite_positions[1]
        door_position = sprite_positions[2] 
        
        clear_cells = list(set(unblocked_cells).difference(set(monster_positions).union(set(sprite_positions))))
        random_state.predicates['player_orientation'].append(['EAST'])
        [random_state.predicates['monster'].append(monster_positions[i]) for i in range(len(monster_positions))]
        [random_state.predicates['wall'].append(blocked_cells[i]) for i in range(len(blocked_cells))]
        [random_state.predicates['clear'].append(blocked_cells[i]) for i in range(len(clear_cells))]
        random_state.predicates['player'].append(player_position)
        random_state.predicates['key'].append(key_position)
        random_state.predicates['door'].append(door_position)
        
        return random_state

    def get_next_state(self,state,action):
        '''
            given state and action, apply action virtually and get resulting state
            actions: up,down,right,left,use
            input: ZeldaState, Action name
            assume only legal actions applied, including no effect
        '''
        try:
            current_position = state.state['player'][0]
            x = int(current_position.replace('cell_','').split('_')[0])
            y = int(current_position.replace('cell_','').split('_')[-1])
            current_orientation = state.state['player_orientation'][0]
            #assume cell naming convention to avoid searching
            cell_up = 'cell_'+str(x)+'_'+str(y-1)
            cell_down = 'cell_'+str(x)+'_'+str(y+1)
            cell_right = 'cell_'+str(x+1)+'_'+str(y)
            cell_left = 'cell_'+str(x-1)+'_'+str(y)
            monster_locs = []
            for pair in state.state['monster']:
                monster_locs.append(pair[1])
            if cell_up not in state.objects.keys() or cell_up in state.state['wall']:
                cell_up = None
            if cell_down not in state.objects.keys() or cell_down in state.state['wall']:
                cell_down = None    
            if cell_right not in state.objects.keys() or cell_right in state.state['wall']:
                cell_right = None    
            if cell_left not in state.objects.keys() or cell_left in state.state['wall']:
                cell_left = None    
            d = {
                'EAST': cell_right,
                'WEST': cell_left,
                'NORTH': cell_up,
                'SOUTH': cell_down
            }
            facing_cell = d[current_orientation] #cell the player is facing
            if len(state.state['key'])!=0: ##CHECK
                key_cell = state.state['key'][0]
            else:
                key_cell = None
            door_cell = state.state['door'][0]
        except KeyError:
            print("Something wrong with state!")
        '''
            arrow effects: if facing in same direction, move else change orientation of player
            upon moving, if all monsters  killed and next cell is door, then escape
            upon moving, if next cell is key, then obtain key
            use effects: if monster present in facing cell, then kill monster. otherwise no effect
        '''
        next_state = copy.deepcopy(state)
        if action == 'ACTION_UP':
            if cell_up !=None and facing_cell == cell_up and cell_up not in monster_locs:
                next_state.state['player'] = [cell_up]
                current_position = cell_up
            else:
                next_state.state['player_orientation'] = ['NORTH']
                return next_state                
        if action == 'ACTION_DOWN':
            if cell_down !=None and facing_cell == cell_down and cell_down not in monster_locs:
                next_state.state['player'] = [cell_down]
                current_position = cell_down
            else:
                next_state.state['player_orientation'] = ['SOUTH']
                return next_state
        if action == 'ACTION_RIGHT':
            if cell_right!=None and facing_cell == cell_right and cell_right not in monster_locs:
                next_state.state['player'] = [cell_right]
                current_position = cell_right
            else:
                next_state.state['player_orientation'] = ['EAST']
                return next_state
        if action == 'ACTION_LEFT':
            if cell_left!=None and facing_cell == cell_left and cell_left not in monster_locs:
                next_state.state['player'] = [cell_left]
                current_position = cell_left
            else:
                next_state.state['player_orientation'] = ['WEST']
                return next_state
        if action == 'ACTION_USE':
            if facing_cell in monster_locs:
                for i,pair in enumerate(state.state['monster']):
                    if pair[1] == facing_cell:
                        del next_state.state['monster'][i]
                        break
            else:
                return state
        
        if current_position == key_cell:
            next_state.state['key'] = [] ##CHECK
            next_state.state['has_key'] = [True]

        if current_position == door_cell and len(state.state['monster'])==0 and state.state['has_key'][0]==True:
            next_state.state['escaped'] = [True]

        return next_state
            
    def get_successor(self,state):
        action_dict = {
        'ACTION_UP':[],
        'ACTION_DOWN':[],
        'ACTION_RIGHT':[],
        'ACTION_LEFT':[],
        'ACTION_USE':[],
        }
        for action in action_dict:
            next_state = self.get_next_state(state,action)
            if next_state == state:
                action_dict[action] = [0,state]
            else:
                action_dict[action] = [1,next_state]
        return action_dict
    
    def is_goal_state(self,current_state,goal_state):
        #all orientations should be corrent goal state
        dcurrent_state = copy.deepcopy(current_state)
        dcurrent_state.state['player_orientation'] = None
        dgoal_state = copy.deepcopy(goal_state)
        dgoal_state.state['player_orientation'] = None
        if dcurrent_state==dgoal_state:
            return True
        else:
            return False

    def plan_to_state(self,state1,state2,algo):
        '''
        orientation is not considered for goal check, this is done since
        we need to plan only to abstract states which do not differ by orientation
        '''
        action_dict = self.get_successor(state1)
        action_list,total_nodes_expanded = search(state1,state2,self,algo)
        return action_list,total_nodes_expanded
        #print(plot_state(state2))
        #print("Plan:"+str(action_list))

    def execute_from_ID(self,abs_state,abs_action):
        try:
            abs_before,abs_after = self.high_actions[abs_action]
            if abs_before!=abs_state: #Might have to change this to a more sophisticated comparison
                return False,abs_state
            else:
                return True,abs_after
        except KeyError:
            print("Unknown Action ID!")

    def validate_state(self,zstate):
        '''
            assuming cell positioning is correct already, those are not to be learnt anyway
        '''
        x_axis_size = zstate.grid_height
        y_axis_size = zstate.grid_width
        grid = np.chararray([y_axis_size,x_axis_size],unicode=True)
        cells_assigned = []
        sprites = []
        alive_monsters  = zstate.state['monster_alive']
        monsters = zstate.state['is_monster']           
        #doors = zstate.state['is_door'] #There can be multiple doors
        #keys = zstate.state['is_key']    #There can be multiple keys
        if len(zstate.state['is_player'])>1:
            return False    
        player = zstate.state['is_player'][0]
        '''
            1 cell assigned to only 1 sprite + wall -(player+door)
        '''
        cell_assigned = []
        doors = []
        for key,val in zstate.state['at']:
            [cell_assigned.append(cell) for cell in val]
        [cell_assigned.append(cell) for cell in zstate.state['wall']]
        player_and_door = False
        for cell in cell_assigned:
            if cell_assigned.count(cell)>1:
                if [player,cell] in zstate.state['at'] and cell_assigned.count(cell)==2:
                    for door in doors:
                        if [door,cell] in zstate.state['at']:
                            player_and_door = True
                            continue
                if not player_and_door:
                    return False
                else:
                    return False
        '''
            match monster_alive, is_monster and at(monster,_)
        '''            
        for monster,location in zstate.state['at']['monster']:
            if monster not in monsters or monster not in zstate.state['monster_alive']:
                return False
        
        if True in zstate.state['escaped'][0]:
            if alive_monsters>0:
                return False
            if True not in zstate.state['has_key']:
                return False

        return True   
      
    def set_GVG_state(self,zstate):
        sprites = {
            "goal": 'g', 
            "key": '+',         
            "nokey": 'A', 
            "monsterQuick": '1', 
            "monsterNormal": '2', 
            "monsterSlow": '3', 
            "wall":"w",
            "floor":".",
            "withkey":"Q"
        }
        x_axis_size = zstate.grid_height
        y_axis_size = zstate.grid_width
        data = np.chararray([y_axis_size,x_axis_size],unicode=True)        

        for i in range(y_axis_size):
            for j in range(x_axis_size):
                cell = 'cell_'+str(i)+'_'+str(j)
                try:
                    if cell in zstate.state['wall']:
                        data[i,j] = sprites["wall"]
                        
                    elif cell in zstate.state["door"]:
                        data[i,j] = sprites["goal"]
                    elif cell in zstate.state["key"]:
                        data[i,j]= sprites["key"]
                    elif cell in zstate.state["player"]:
                        if zstate.state["has_key"][0]==True:
                            data[i,j] = sprites['withkey']
                        else:
                            data[i,j] = sprites['nokey']
                    else:
                        data[i,j]='.'
                except KeyError as e:
                    print(e)    
                    data[i,j] = '.'
                    pass
        try:
            for pair in zstate.state["monster"]:
                x = int(pair[1].replace("cell_","").split('_')[0])
                y = int(pair[1].replace("cell_","").split('_')[1])
                data[x,y] = sprites["monsterNormal"]        
        except KeyError as e:
            print(e)
            pass
        s = ''
        for row in data.T:
            s+=row.astype('|S1').tostring().decode('utf-8')
            s+='\n'
        return data.T
    
    def generate_ds(self):
        '''
            assume the actions are assigned
        '''
        
        abstract_model = {}
        action_parameters = {}
        abstract_predicates = {}
        objects = {
            'location' : [],
            'sprite': []
        }
        agent_model ={}
        init_state = None
        try:
            with open("test_trace","rb") as f:
                temp_traces = pickle.load(f)
            sso_state = temp_traces[-1][0][0]
            zstate = Zelda_State(sso_state)
            for key,val in zstate.objects.items():
                objects[val].append(key)
            init_state = copy.deepcopy(zstate)
        except IOError:
            pass
        
        predTypeMapping = {
            'at' : ['sprite','location'],
	        'monster_alive' : ['sprite'],
            'has_key' : [],
            'escaped' : [],
            'wall' : ['location'],
	        'is_player' : ['sprite'],
	        'is_monster': ['sprite'],
            'leftOf': ['location','location'],
            'rightOf': ['location','location'],
            'above': ['location','location'],
            'below': ['location','location']
        }
        types = {
            'object':['location','sprite']
        }
            
        for action in self.high_actions:
            abstract_model[action] = {}
            action_parameters[action] = []
            agent_model[action]= {}
            for pred in predTypeMapping:
                agent_model[action][pred] = [Literal.ABS,Literal.ABS]

        
        return action_parameters, predTypeMapping, agent_model, abstract_model, objects, None , None, "zelda_GVG"

    def iaa_query(self,abs_state,plan):
        '''
        state: abstract
        plan: hashed values corresponding to stored actions
        '''
        if self.validate_state(abs_state):            
            state  = copy.deepcopy(abs_state)
            for i,action in enumerate(plan):
                '''
                    can check plan possibility here itself
                    if subsequent states are not equal, can't execute
                '''
                can_execute,abs_after = self.execute_from_ID(state,action)
                if can_execute:
                    state = abs_after
                else:
                    return False,i,abs_after #check from sokoban code
            return True,len(plan),abs_after #check from sokoban code
        else:
            return False,0,abs_state