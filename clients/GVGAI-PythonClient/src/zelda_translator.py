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

'''
    Required behavior:
        Create a level file from a relational state
        Run a plan with the given initial state
        Store the actions that cause change in abstract states (from traces)
        plans will contain these actions and will have to be applied on low-level states
        Q: How do I apply a high-level action to a low-level state since info is lost in abstraction?
'''

IDs = {
    11:'MONSTER',
    0:'WALL',
    7:'PLAYER',
    3:'DOOR',
    4:'KEY',
    8:'PLAYER_WITH_KEY',
    0:'NONE',
    5:'SWORD'
    }

class AbstractZeldaState:
    def __init__(self,low_state):
        self.grid_height = 4 #assign dynamically later
        self.grid_width = 4 #assign dynamically later
        self.state = {
            'at' : [],
	        'monster_alive' : [],
            'has_key ' : [],
            'escaped ' : [],
            'clear ' : [],
	        'is_player ' : [],
	        'is_key' : [],
	        'is_door' : [],
            'is_monster': [],
            'leftOf': [],
            'rightOf': [],
            'above': [],
            'below': []
        }
        self.objects = {}
        self.abstract_state(low_state)
    
    def abstract_state(self,low_state):
        self.objects = low_state.objects
        self.state['leftOf'] = low_state.state['leftOf']
        self.state['rightOf'] = low_state.state['rightOf']
        self.state['above'] = low_state.state['above']
        self.state['below'] = low_state.state['below']
        self.state['clear'] = low_state.state['clear']
        try:
            self.state['at'].append(('player',low_state.state['player'][0]))
            self.state['is_player'].append('player')
        except IndexError:
            print("No player in low level state")
            pass
        try:
            self.state['at'].append(('key',low_state.state['key'][0]))
            self.state['is_key'].append('key')
        except IndexError:
            print("No key in low level state")
            pass
        for i in range(len(low_state.state['monster'])):
            self.state['at'].append(('monster'+str(i),low_state.state['monster'][i]))
            self.state['monster_alive'].append('monster'+str(i))
            self.state['is_monster'].append('monster'+str(i))
        try:
            self.state['at'].append(('door',low_state.state['door'][0]))
            self.state['is_door'].append('door')
        except IndexError:
            print("No door in low level state WHAT?!")
            pass
        try:
            self.state['has_key'].append(('has_key',low_state.state['has_key'][0]))
        except IndexError:
            print("No has_key in low level state")
            pass
        self.grid_height = low_state.grid_height 
        self.grid_width = low_state.grid_width
        
class Zelda_State:
    def __init__(self):
        self.monster_id = 11
        self.wall_id = 0
        self.player_id = 7
        self.door_id = 3
        self.key_id = 4
        self.player_with_key_id = 8
        self.objects = []
        self.grid_height = 4 #assign dynamically later
        self.grid_width = 4 #assign dynamically later
        self.state = {
            'wall':[],
            'player':[],
            'monster':[],
            'key':[],
            'door':[],
            'player_orientation':[],
            'has_key':[],
            'clear':[],
            'leftOf':[],
            'rightOf':[],
            'above':[],
            'below':[],
            'monster_alive':[]
        }
    def __init__(self,sso):
        self.monster_id = 11
        self.wall_id = 0
        self.player_id = 7
        self.door_id = 3
        self.key_id = 4
        self.player_with_key_id = 8
        self.grid_height = 4 #assign dynamically later
        self.grid_width = 4 #assign dynamically later
        self.objects = []
        self.state = {
            'wall':[],
            'player':[],
            'monster':[],
            'key':[],
            'door':[],
            'player_orientation':[],
            'has_key':[],
            'clear':[],
            'leftOf': [],
            'rightOf': [],
            'above': [],
            'below': [],
            'monster_alive':[],
            'sword':[]
        }
        self.from_sso(sso)  
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
        print_grid = np.zeros([len(sso.observationGrid),len(sso.observationGrid[0])])
        self.num_cols = len(sso.observationGrid)
        self.num_rows = len(sso.observationGrid[0]) ##(i,j) is column i, row jprint_grid = np.zeros([len(sso.observationGrid),len(sso.observationGrid[0])])
        for i in range(len(sso.observationGrid)):
            for j in range(len(sso.observationGrid[i])):
                if sso.observationGrid[i][j][0]==None:
                    print_grid[i,j]=1
                else:
                    print_grid[i,j] = sso.observationGrid[i][j][0].itype
        print(print_grid.T)

        for i in range(self.num_cols):
            for j in range(self.num_rows):
                cell_name = 'cell_ '+str(i)+'_'+str(j)
                cell_up = 'cell_ '+str(i)+'_'+str(j-1)
                cell_down = 'cell_ '+str(i)+'_'+str(j+1)
                cell_right = 'cell_ '+str(i+1)+'_'+str(j)
                cell_left = 'cell_ '+str(i-1)+'_'+str(j)
                self.objects.append(cell_name)
                if i+1<self.num_cols:
                    self.state['leftOf'].append([cell_name,cell_right])
                    self.state['rightOf'].append([cell_right,cell_name])
                if j+1<self.num_rows:
                    self.state['above'].append([cell_name,cell_down])
                    self.state['below'].append([cell_down,cell_name])
                if i!=0:
                    self.state['leftOf'].append([cell_left,cell_name])
                    self.state['rightOf'].append([cell_name,cell_right])
                if j!=0:
                    self.state['above'].append([[cell_up,cell_name]])
                    self.state['below'].append([[cell_name,cell_up]])
                if sso.observationGrid[i][j][0]!=None:
                    if sso.observationGrid[i][j][0].itype not in IDs.keys():
                        print("Problem in zelda_translator")
                        pass
                    else:
                        if IDs[sso.observationGrid[i][j][0].itype] == 'MONSTER':  
                            self.state['monster'].append(cell_name)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'WALL':
                            self.state['wall'].append(cell_name)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'PLAYER':
                            self.state['player'].append(cell_name)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'DOOR':
                            self.state['door'].append(cell_name)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'KEY':
                            self.state['key'].append(cell_name)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'PLAYER_WITH_KEY':
                            self.state['player'].append(cell_name)
                            self.state['has_key'].append(True)
                        if IDs[sso.observationGrid[i][j][0].itype] == 'SWORD':
                            self.state['sword'].append(cell_name)
                        
                else:
                    self.state['clear'].append(cell_name)
        if sso.avatarOrientation == [-1,0]:
            self.state['player_orientation'].append('EAST')
        if sso.avatarOrientation == [1,0]:
            self.state['player_orientation'].append('WEST')
        if sso.avatarOrientation == [0,-1]:
            self.state['player_orientation'].append('SOUTH')
        if sso.avatarOrientation == [0,1]:
            self.state['player_orientation'].append('NORTH')

class Zelda_Translator(Translator):
    def __init__(self,level_num = 0):
        super.__init__('/home/raoshashank/GVGAI-master/examples/gridphysics','zelda',level_num)   
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

    def get_relational_state(self,sso):
        return Zelda_State(sso)

    def refine_abstract_state(self,abstract_state):
        '''
            This will only be used for setting initial state for a query
            TODO:
                refinement to any corresponding Zelda State
        '''
        refined_state = Zelda_State()        
        refined_state.state['has_key'].append(abstract_state.state['has_key'])
        refined_state.state['clear'] = abstract_state.state['clear']
        refined_state.state['leftOf'] = abstract_state.state['leftOf']
        refined_state.state['rightOf'] = abstract_state.state['rightOf']
        refined_state.state['above'] = abstract_state.state['above']
        refined_state.state['below'] = abstract_state.state['below']
        refined_state.state['monster_alive'] = abstract_state.state['monster_alive']
        refined_state.state['player_orientation'].append('EAST')
        for pair in abstract_state.state['at']:
            # if 'player' in pair[0]:
            #     refined_state.state['player'].append(pair[1])
            # if 'monster' in pair[0]:
            #     refined_state.state['monster'].append(pair[1])
            # if 'key' in pair[0]:
            #     refined_state.state[]
            # if 'door' in pair[0]:
            try:
                refined_state.state[pair[0]].append(pair[1])
            except KeyError:
                print("Key " + str(pair[0]))
        refined_state.grid_height = abstract_state.grid_height
        refined_state.grid_width = abstract_state.grid_width
        return refined_state

    
    def create_level_from_state(self,zelda_state,level_file):
        level_text = ""
        for i in range(zelda_state.num_rows): 
            for j in range(zelda_state.num_cols):
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

    # def collect_traces(self,number_of_traces):
    #     '''
    #       Also store the actions that cause the action transition
    #     '''
    #     #state = self.random_state_generator(np.random.randint(5,10),np.random.randint(5,10))
    #     max_trace_length = 30 
    #     for i in range(number_of_traces):
            

