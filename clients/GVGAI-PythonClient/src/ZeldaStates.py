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
    If you cannot ensure that all the states that are abstracted to a single state are fully connected, this approach won't work.
'''
IDs = {
    11:'MONSTER',
    0:'WALL',
    7:'PLAYER',
    3:'DOOR',
    4:'KEY',
    8:'PLAYER_WITH_KEY',
    5:'SWORD',
    1:'CLEAR'
    }

class AbstractZeldaState:
    def __init__(self,low_state):
        self.grid_height = 4 #assign dynamically later
        self.grid_width = 4 #assign dynamically later
        self.state = {
            'at' : [],
	        'monster_alive' : [],
            'has_key' : [],
            'escaped' : [],
            'wall' : [],
	        'is_player' : [],
	        'is_monster': [],
            'is_key' : [],
            'is_door':[],
            'leftOf': [],
            'rightOf': [],
            'above': [],
            'below': []
        }
        self.objects = {}#locations(cells),sprites(monster,player),things(door,key)
        self.abstract_state(low_state)
    
    def abstract_state(self,low_state):
        for obj in low_state.objects:
            if low_state.objects[obj] in ['location','sprite']:
                self.objects[obj]=low_state.objects[obj]
        self.state['leftOf'] = low_state.state['leftOf']
        self.state['rightOf'] = low_state.state['rightOf']
        self.state['above'] = low_state.state['above']
        self.state['below'] = low_state.state['below']
        self.state['wall'] = low_state.state['wall']
        self.state['escaped'] = low_state.state['escaped']
        try:
            self.state['at'].append(('player',low_state.state['player']))
            self.objects['player']='sprite'
            self.state['is_player'].append('player')
        except IndexError:
            # if len(low_state.state['sword'])==1: #REMOVE DEPENDENCY ON SWORD!
            #     #print("No player in low level state, but sword is there")
            #     self.state['at'].append(('player',low_state.state['sword'][0]))
            # else:
            print("No player, no sword. this is foul play")
            pass
        try:
            #self.state['at'].append(('key',low_state.state['key']))#assuming there's just one
            #self.state['is_key'].append('key')
            self.objects['key']='thing'
        except IndexError:
            print("No key in low level state")
            pass
        for pair in low_state.state['monster']:
            self.state['at'].append((pair[0],pair[1]))
            self.state['monster_alive'].append(pair[0])
            self.state['is_monster'].append(pair[0])
        try:
            self.state['at'].append(('door',low_state.state['door'][0]))
            self.state['is_door'].append('door')
            self.objects['door']='thing'
        except IndexError:
            print("No door in low level state WHAT?!")
            pass
        try:
            self.state['has_key'].append(low_state.state['has_key'][0])
        except IndexError:
            print("No has_key in low level state")
            pass
        self.grid_height = low_state.grid_height 
        self.grid_width = low_state.grid_width

    def __eq__(self,abstract2):
        for pred in self.state:
            if abstract2.state[pred]!=self.state[pred]:
                return False
        if self.objects!=abstract2.objects:
            return False

        return True

    def __str__(self):
        s = ""
        for k,v in self.state.items():
            if k not in ['leftOf','rightOf','above','below']:
                s+=k+": "+str(v)+"\n"
        return s
    
    #def within(self,state):
    #    dstate = copy.deepcopy(state)

class Zelda_State:
    def __eq__(self,state2):
        try:
            # for pred in self.state:
            #     if state2.state[pred]!=self.state[pred]:
            #         return False
            if self.state!=state2.state:
                return False
            if self.objects!=state2.objects:
                return False
            return True
        except AttributeError:
            return False
    def __str__(self):
        s = ""
        for k,v in self.state.items():
            if k not in ['leftOf','rightOf','above','below']:
                s+=k+": "+str(v)+"\n"
        return s      
    
    def __hash__(self):
        return hash(str(self))
    
    def __init__(self,sso=None,monster_mapping={},trace_id=0):
        self.monster_id = 11
        self.wall_id = 0
        self.player_id = 7
        self.door_id = 3
        self.key_id = 4
        self.player_with_key_id = 8
        self.grid_height = 4 #assign dynamically later
        self.grid_width = 4 #assign dynamically later
        self.objects = {}#types: location(cells),sprite(monsters)
        self.monster_mapping=monster_mapping #key:monster name, value: original monster-location
        self.trace_id=trace_id
        self.state = {
            'wall':[],
            'player':[],
            'monster':[],
            'key':[],
            'door':[],
            'player_orientation':[],
            'has_key':[],
            #'clear':[],
            'leftOf': [],
            'rightOf': [],
            'above': [],
            'below': [],
            #'sword':[],
            'escaped':[]
        }
        self.g_score = 0 #for search
        self.best_path = None #for search
        if sso!=None:
            self.from_sso(sso)  
    
    def print_grid(self,sso):
        grid = np.zeros([len(sso.observationGrid),len(sso.observationGrid[0])])
        for i in range(len(sso.observationGrid)):
             for j in range(len(sso.observationGrid[i])):
                 if sso.observationGrid[i][j][0]==None:
                     grid[i,j]=1
                 else:
                     grid[i,j] = sso.observationGrid[i][j][0].itype
        print(grid.T)

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
        self.grid_width = len(sso.observationGrid)
        self.grid_height = len(sso.observationGrid[0]) ##(i,j) is column i, row jprint_grid = np.zeros([len(sso.observationGrid),len(sso.observationGrid[0])])
        sword_at = None
        monster_id = 0
        player_won = 0
        if sso.gameWinner == 'PLAYER_WINS':
            player_won = 1
        for i in range(self.grid_width):
            for j in range(self.grid_height):
                cell_name = 'cell_'+str(i)+'_'+str(j)
                cell_up = 'cell_'+str(i)+'_'+str(j-1)
                cell_down = 'cell_'+str(i)+'_'+str(j+1)
                cell_right = 'cell_'+str(i+1)+'_'+str(j)
                cell_left = 'cell_'+str(i-1)+'_'+str(j)
                self.objects[cell_name]='location' 
                if i+1<self.grid_width:
                    self.state['leftOf'].append([cell_name,cell_right])
                    self.state['rightOf'].append([cell_right,cell_name])
                if j+1<self.grid_height:
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
                            if self.trace_id==0:
                                #assign monster numbers here itself
                                self.state['monster'].append(['monster'+str(monster_id),cell_name])
                                self.monster_mapping[cell_name] = 'monster'+str(monster_id)
                                monster_id+=1
                                self.objects['monster'+str(monster_id)]='sprite'
                            else:
                                try:
                                    self.state['monster'].append([self.monster_mapping[cell_name],cell_name])
                                except KeyError:
                                    print("Monster not present in mapping!")
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
                             #self.state['sword'].append(cell_name)
                             sword_at = cell_name
                # else:
                #     self.state['clear'].append(cell_name)
        if len(self.state['has_key']) == 0:
            self.state['has_key'].append(False)
        if sso.avatarOrientation == [-1,0]:
            self.state['player_orientation'].append('WEST')
        if sso.avatarOrientation == [1,0]:
            self.state['player_orientation'].append('EAST')
        if sso.avatarOrientation == [0,-1]:
            self.state['player_orientation'].append('NORTH')
        if sso.avatarOrientation == [0,1]:
            self.state['player_orientation'].append('SOUTH')
        if len(self.state['player'])==0:
            self.state['player'].append(sword_at)    
        if player_won:
            #move player to door location and make escaped true
            self.state['player']=self.state['door']
            self.state['escaped'] = [True]
    def refine_abstract_state(self,abstract_state):
        '''
            This will only be used for setting initial state for a query
            TODO:
                add to 'key' and 'door' predicates
        '''
        for obj in abstract_state.objects:
            if abstract_state.objects[obj] in ['location']:
                self.objects[obj]=abstract_state.objects[obj]
        refined_state = Zelda_State()        
        refined_state.state['has_key'].append(abstract_state.state['has_key'][0])
        #refined_state.state['clear'] = abstract_state.state['clear']
        refined_state.state['wall'] = abstract_state.state['wall']
        refined_state.state['leftOf'] = abstract_state.state['leftOf']
        refined_state.state['rightOf'] = abstract_state.state['rightOf']
        refined_state.state['above'] = abstract_state.state['above']
        refined_state.state['below'] = abstract_state.state['below']
        #refined_state.state['monster_alive'] = abstract_state.state['monster_alive']
        refined_state.state['player_orientation'].append('EAST')
        refined_state.state['escaped'] = abstract_state.state['escaped']
        for pair in abstract_state.state['at']:
            # if 'player' in pair[0]:
            #     refined_state.state['player'].append(pair[1])
            # if 'monster' in pair[0]:
            #     refined_state.state['monster'].append(pair[1])
            # if 'key' in pair[0]:
            #     refined_state.state[]
            # if 'door' in pair[0]:
            if 'monster' in pair[0]:
                refined_state.state["monster"].append([pair[0],pair[1]])
                refined_state.objects[pair[0]]='sprite'
            else:
                try:
                    refined_state.state[pair[0]].append(pair[1])
                except KeyError:
                    print("Key " + str(pair[0]))
        refined_state.grid_height = abstract_state.grid_height
        refined_state.grid_width = abstract_state.grid_width
        return refined_state