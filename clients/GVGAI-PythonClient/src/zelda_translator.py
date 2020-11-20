import logging
import os
import subprocess
import sys
import traceback
import argparse
sys.path.append("src/utils")
sys.path.append("./utils")
from ClientComm import ClientComm
import IPython
from pprint import pprint
from translator import Translator
import numpy as np

'''
    Required behavior:
        Create a level file from a relational state
        Run a plan with the given initial state
'''

class Zelda_State:
    def __init__(self):
        self.monster_id = 11
        self.wall_id = 0
        self.player_id = 7
        self.door_id = 3
        self.key_id = 4
        self.player_with_key_id = 8
        self.objects = []
        self.predicates = {
            'wall':[],
            'player':[],
            'monster':[],
            'key':[],
            'door':[],
            'player_orientation':[],
            'player_has_key':[],
            'clear':[],
            'leftOF': [],
            'rightOF': [],
            'above': [],
            'below': [],
            'monster_dead':[]
        }
    
    def from_sso(self,sso):
        '''
            Convert Serialized state observation into relational interpretable state
            predicates:
                wall(?cell)
                player_at(?cell)
                player_orientation(?direction)
                monster(?cell)
                key(?cell)
                door(?cell)
                player_has_key()
                leftOF(?cell1,?cell2) #cell1 is left of cell2 
                rightOF(?cell1,?cell2) #cell1 is right of cell2
                above(?cell1,?cell2) #cell1 is above cell2
                below(?cell1,?cell2)   #cell1 is below cell2
                monster_dead()                    
        '''
        self.num_cols = len(sso.observationGrid)
        self.num_rows = len(sso.observationGrid[0]) ##(i,j) is column i, row j
        for i in range(self.num_cols):
            for j in range(self.num_rows):
                cell_name = 'cell_ '+str(i)+'_'+str(j)
                cell_up = 'cell_ '+str(i)+'_'+str(j-1)
                cell_down = 'cell_ '+str(i)+'_'+str(j+1)
                cell_right = 'cell_ '+str(i+1)+'_'+str(j)
                cell_left = 'cell_ '+str(i-1)+'_'+str(j)
                self.objects.append(cell_name)
                if i+1<self.num_cols:
                    self.predicates['leftOf'].append([cell_name,cell_right])
                    self.predicates['rightOf'].append([cell_right,cell_name])
                if j+1<self.num_rows:
                    self.predicates['above'].append([cell_name,cell_down])
                    self.predicates['below'].append([cell_down,cell_name])
                if i!=0:
                    self.predicates['leftOf'].append([cell_left,cell_name])
                    self.predicates['rightOf'].append([cell_name,cell_right])
                if j!=0:
                    self.predicates['above'].append([[cell_up,cell_name]])
                    self.predicates['below'].append([[cell_name,cell_up]])
                if sso.observationGrid[i][j][0]!=None:
                    if IDs[sso.observationGrid[i][j][0].itype] == 'MONSTER':  
                        self.predicates['monster'].append(cell_name)
                    if IDs[sso.observationGrid[i][j][0].itype] == 'WALL':
                        self.predicates['wall'].append(cell_name)
                    if IDs[sso.observationGrid[i][j][0].itype] == 'PLAYER':
                        self.predicates['player_at'].append(cell_name)
                    if IDs[sso.observationGrid[i][j][0].itype] == 'DOOR':
                        self.predicates['door'].append(cell_name)
                    if IDs[sso.observationGrid[i][j][0].itype] == 'KEY':
                        self.predicates['key'].append(cell_name)
                    if IDs[sso.observationGrid[i][j][0].itype] == 'PLAYER_WITH_KEY':
                        self.predicates['player_has_key'].append(True)
                    if sso.avatarOrientation == [-1,0]:
                        self.predicates['player_orientation'].append(['EAST'])
                    if sso.avatarOrientation == [1,0]:
                        self.predicates['player_orientation'].append(['WEST'])
                    if sso.avatarOrientation == [0,-1]:
                        self.predicates['player_orientation'].append(['SOUTH'])
                    if sso.avatarOrientation == [0,1]:
                        self.predicates['player_orientation'].append(['NORTH'])
                else:
                    self.predicates['clear'].append(cell_name)
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
                    if zelda_state['player_has_key'][0]==True:
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

    def collect_traces(self,number_of_traces):
        state = self.random_state_generator(np.random.randint(5,10),np.random.randint(5,10))
        max_trace_length = 30 
        for i in range(number_of_traces):

