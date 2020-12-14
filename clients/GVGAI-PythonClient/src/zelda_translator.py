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
        '''
            Given zelda state, create GVG level
        '''
        level_text = ""
        for i in range(zelda_state.grid_height): 
            for j in range(zelda_state.grid_width):
                cell = 'cell_'+str(j)+'_'+str(i)
                if cell in zelda_state.state['monster']:
                    level_text+=self.sprites["monsterSlow"]
                if cell in zelda_state.state['wall']:
                    level_text+=self.sprites['wall']
                if cell in zelda_state.state['player']:
                    if zelda_state['has_key'][0]==True:
                        level_text+=self.sprites["withkey"]
                    else:
                        level_text+=self.sprites["nokey"]
                if cell in zelda_state.state['door']:
                    level_text+=self.sprites["door"]
                if cell in  zelda_state.state['key']:
                    level_text+=self.sprites["key"]
                else:
                    level_text+="."
            level_text+="\n"         
        with open(level_file,"w") as f:
            f.writelines(level_text)

    def generate_random_state(self,r=4,c=4):
        random_state = Zelda_State()
        player_location = 'cell_'+str(np.random.randint(1,c-1))+'_'+str(np.random.randint(1,r-1))
        for i in range(c):
            for j in range(r):
                cell_name = 'cell_'+str(i)+'_'+str(j)
                cell_up = 'cell_'+str(i)+'_'+str(j-1)
                cell_down = 'cell_'+str(i)+'_'+str(j+1)
                cell_right = 'cell_'+str(i+1)+'_'+str(j)
                cell_left = 'cell_'+str(i-1)+'_'+str(j)
                random_state.objects[cell_name] = 'location'
                if i+1<c:
                    random_state.state['leftOf'].append([cell_name,cell_right])
                    random_state.state['rightOf'].append([cell_right,cell_name])
                if j+1<r:
                    random_state.state['above'].append([cell_name,cell_down])
                    random_state.state['below'].append([cell_down,cell_name])
                if i!=0:
                    random_state.state['leftOf'].append([cell_left,cell_name])
                    random_state.state['rightOf'].append([cell_name,cell_right])
                if j!=0:
                    random_state.state['above'].append([[cell_up,cell_name]])
                    random_state.state['below'].append([[cell_name,cell_up]])        
        
        num_monsters = np.random.randint(2,5)
        num_blocked_cells = np.random.choice(range(int(5 * c * r / 10)))
        all_cells = list(random_state.objects.keys())

        #walls
        blocked_cells = np.random.choice(all_cells, num_blocked_cells)
        all_cells = list(set(tuple(all_cells)).difference(set(tuple(blocked_cells))))
        #monster
        monster_positions = np.random.choice(all_cells, num_monsters)
        all_cells = list(set(tuple(all_cells)).difference(set(tuple(monster_positions))))
        monster_mapping = {}
        for i in range(len(monster_positions)):
            monster_mapping[monster_positions[i].replace('cell','monster')] = monster_positions[i]
        #door
        door_position = np.random.choice(all_cells)
        all_cells.remove(door_position)
        #key
        key_position = np.random.choice(all_cells)
        all_cells.remove(key_position)
        #player
        player_position = np.random.choice(all_cells)
        all_cells.remove(player_position)
        random_state.monster_mapping = monster_mapping 
        random_state.state['player_orientation'] =['EAST']
        [random_state.state['monster'].append([k,v]) for k,v in monster_mapping.items()]
        [random_state.state['wall'].append(blocked_cells[i]) for i in range(len(blocked_cells))]
        #[random_state.state['clear'].append(blocked_cells[i]) for i in range(len(clear_cells))]
        random_state.state['player'].append(player_position)
        random_state.state['key'].append(key_position)
        random_state.state['door'].append(door_position)
        random_state.state['has_key'] = [False]
        random_state.state['escaped'] = [False]
        
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
            keys = state.state['key']
            doors = state.state['door']
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
        
        if current_position in keys:
            next_state.state['key'].remove(current_position)
            next_state.state['has_key'] = [True]

        if current_position in doors and len(state.state['monster'])==0 and state.state['has_key'][0]==True:
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
            Given ABSTRACT STATE, validate it
            assuming cell positioning is correct already, those are not to be learnt anyway
        '''
        x_axis_size = zstate.grid_height
        y_axis_size = zstate.grid_width
        grid = np.chararray([y_axis_size,x_axis_size],unicode=True)
        cells_assigned = []
        sprites = []
        alive_monsters  = zstate.state['monster_alive']
        monsters = zstate.state['is_monster']           
        doors = zstate.state['is_door'] #There can be multiple doors
        keys = zstate.state['is_key']    #There can be multiple keys
        if len(zstate.state['is_player'])>1:
            return False    
        player = zstate.state['is_player'][0]
        '''
            1 cell assigned to only 1 sprite + wall -(player+door)
        '''
        cell_assigned = []
        doors = []        
        [cell_assigned.append(pair[1]) for pair in zstate.state['at']]
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
        if len(set(tuple(zstate.state['monster_alive'])).difference(set(tuple(zstate.state['is_monster']))))>0:
            return False
        for pair in zstate.state['at']:
            if pair[0] in monsters:
                if pair[0] not in zstate.state['monster_alive']:
                    return False

        #Add check if key is missing, has_key should be true
        
        if True in zstate.state['escaped']:
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
    
    def abstract_state(self,low_state):
        abs_state = AbstractZeldaState()
        for obj in low_state.objects:
            if low_state.objects[obj] in ['location']:
                abs_state.objects[obj]=low_state.objects[obj]
        abs_state.state['leftOf'] = low_state.state['leftOf']
        abs_state.state['rightOf'] = low_state.state['rightOf']
        abs_state.state['above'] = low_state.state['above']
        abs_state.state['below'] = low_state.state['below']
        abs_state.state['wall'] = low_state.state['wall']
        abs_state.state['escaped'] = low_state.state['escaped']
        try:
            abs_state.state['at'].append(('player',low_state.state['player']))
            abs_state.objects['player']='sprite'
            abs_state.state['is_player'].append('player')
        except IndexError:
            # if len(low_state.state['sword'])==1: #REMOVE DEPENDENCY ON SWORD!
            #     #print("No player in low level state, but sword is there")
            #     abs_state.state['at'].append(('player',low_state.state['sword'][0]))
            # else:
            print("No player, no sword. this is foul play")
            pass
        try:
            #abs_state.state['at'].append(('key',low_state.state['key']))#assuming there's just one
            #abs_state.state['is_key'].append('key')
            for i,val in enumerate(low_state.state['key']):
                abs_state.objects['key'+str(i)]='sprite'
                abs_state.state['is_key'].append('key'+str(i))
                abs_state.state['at'].append(('key'+str(i),val))
        except IndexError:
            print("No key in low level state")
            pass
        for pair in low_state.state['monster']:
            abs_state.state['at'].append((pair[0],pair[1]))
            abs_state.state['monster_alive'].append(pair[0])
            abs_state.state['is_monster'].append(pair[0])
            abs_state.objects[pair[0]]='sprite'
        try:
            for i,val in enumerate(low_state.state['door']):
                abs_state.objects['door'+str(i)]='sprite'
                abs_state.state['is_door'].append('door'+str(i))
                abs_state.state['at'].append(('door'+str(i),val))
        except IndexError:
            print("No door in low level state WHAT?!")
            pass
        try:
            abs_state.state['has_key'].append(low_state.state['has_key'][0])
        except IndexError:
            print("No has_key in low level state")
            pass
        abs_state.grid_height = low_state.grid_height 
        abs_state.grid_width = low_state.grid_width
        return abs_state

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
            state = AbstractZeldaState(self.from_sso(sso_state))
            for key,val in state.objects.items():
                objects[val].append(key)
        except IOError:
            pass
        
        predTypeMapping = {
            'at' : ['sprite','location'],
	        'monster_alive' : ['sprite'],
            'has_key' : [],
            'escaped' : [],
            'wall' : ['location'],
	        'is_player' : ['sprite'],
            'is_key': ['sprite'],
            'is_door':['sprite'],
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

    def refine_abstract_state(abstract_state):
        '''
            This will only be used for setting initial state for a query
            TODO:
                add to 'key' and 'door' predicates -- DONE -- 
                
        '''
        for obj in abstract_state.objects:
            if abstract_state.objects[obj] in ['location']:
                self.objects[obj]=abstract_state.objects[obj]
        refined_state = Zelda_State()        
        refined_state.state['has_key'].append(abstract_state.state['has_key'][0])
        refined_state.state['wall'] = abstract_state.state['wall']
        refined_state.state['leftOf'] = abstract_state.state['leftOf']
        refined_state.state['rightOf'] = abstract_state.state['rightOf']
        refined_state.state['above'] = abstract_state.state['above']
        refined_state.state['below'] = abstract_state.state['below']
        refined_state.state['player_orientation'].append('EAST')
        refined_state.state['escaped'] = abstract_state.state['escaped']
        for pair in abstract_state.state['at']:
            if pair[0] in abstract_state.state['is_player']:
                refined_state.state['player'].append(pair[1])
                #refined_state.objects[pair[0]]='sprite'
            if pair[0] in abstract_state.state['is_key']:
                refined_state.state['key'].append(pair[1])
                #refined_state.objects[pair[0]]='sprite'
            if pair[0] in abstract_state.state['is_door']:
                refined_state.state['door'].append(pair[1])
                #refined_state.objects[pair[0]]='sprite'
            if pair[0] in abstract_state.state['is_monster']:
                refined_state.state["monster"].append([pair[0],pair[1]])
                #refined_state.objects[pair[0]]='sprite'
        refined_state.grid_height = abstract_state.grid_height
        refined_state.grid_width = abstract_state.grid_width
        return refined_state

    def from_sso(self,sso):
        '''
            Convert Serialized state observation into relational interpretable state
            predicates:
                wall(?cell)
                player(?cell)
                player_orientation(?direction)
                monster(?cell)
                key(?cell)
                door(?cell)
                has_key()
                leftOf(?cell1,?cell2) #cell1 is left of cell2 
                rightOf(?cell1,?cell2) #cell1 is right of cell2
                above(?cell1,?cell2) #cell1 is above cell2
                below(?cell1,?cell2)   #cell1 is below cell2
                monster_alive()                    
        '''
        state = ZeldaStates()
        state.grid_width = len(sso.observationGrid)
        state.grid_height = len(sso.observationGrid[0]) ##(i,j) is column i, row jprint_grid = np.zeros([len(sso.observationGrid),len(sso.observationGrid[0])])
        sword_at = None
        monster_id = 0
        player_won = 0
        player = 0
        if sso.gameWinner == 'PLAYER_WINS':
            player_won = 1
        for i in range(state.grid_width):
            for j in range(state.grid_height):
                cell_name = 'cell_'+str(i)+'_'+str(j)
                cell_up = 'cell_'+str(i)+'_'+str(j-1)
                cell_down = 'cell_'+str(i)+'_'+str(j+1)
                cell_right = 'cell_'+str(i+1)+'_'+str(j)
                cell_left = 'cell_'+str(i-1)+'_'+str(j)
                state.objects[cell_name]='location' 
                if i+1<state.grid_width:
                    state.state['leftOf'].append([cell_name,cell_right])
                    state.state['rightOf'].append([cell_right,cell_name])
                if j+1<state.grid_height:
                    state.state['above'].append([cell_name,cell_down])
                    state.state['below'].append([cell_down,cell_name])
                if i!=0:
                    state.state['leftOf'].append([cell_left,cell_name])
                    state.state['rightOf'].append([cell_name,cell_right])
                if j!=0:
                    state.state['above'].append([[cell_up,cell_name]])
                    state.state['below'].append([[cell_name,cell_up]])
                if sso.observationGrid[i][j][0]!=None:
                    if sso.observationGrid[i][j][0].itype not in IDs.keys():
                        print("Problem in zelda_translator")
                        pass
                    else:
                        if IDs[sso.observationGrid[i][j][0].itype] == 'MONSTER':  
                            if state.trace_id==0:
                                #assign monster numbers here itself
                                state.state['monster'].append(['monster'+str(monster_id),cell_name])
                                state.monster_mapping[cell_name] = 'monster'+str(monster_id)
                                monster_id+=1
                                #state.objects['monster'+str(monster_id)]='sprite'
                            else:
                                try:
                                    state.state['monster'].append([state.monster_mapping[cell_name],cell_name])
                                except KeyError:
                                    print("Monster not present in mapping!")
                        if IDs[sso.observationGrid[i][j][0].itype] == 'WALL':
                            state.state['wall'].append(cell_name)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'PLAYER':
                            state.state['player'].append(cell_name)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'DOOR':
                            state.state['door'].append(cell_name)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'KEY':
                            state.state['key'].append(cell_name)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'PLAYER_WITH_KEY':
                            state.state['player'].append(cell_name)
                            state.state['has_key'].append(True)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'SWORD':
                             #state.state['sword'].append(cell_name)
                             sword_at = cell_name
                # else:
                #     state.state['clear'].append(cell_name)
        if len(state.state['has_key']) == 0:
            state.state['has_key'].append(False)
        if sso.avatarOrientation == [-1,0]:
            state.state['player_orientation'].append('WEST')
        if sso.avatarOrientation == [1,0]:
            state.state['player_orientation'].append('EAST')
        if sso.avatarOrientation == [0,-1]:
            state.state['player_orientation'].append('NORTH')
        if sso.avatarOrientation == [0,1]:
            state.state['player_orientation'].append('SOUTH')
        if len(state.state['player'])==0:
            state.state['player'].append(sword_at)    
        if player_won:
            #move player to door location and make escaped true
            state.state['player']=state.state['door']
            state.state['escaped'] = [True]        
        
        return state
    
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