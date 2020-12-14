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
    def __init__(self):
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
        self.objects = {}#locations(cells),sprites(monster,player,door,key)   

    def __eq__(self,abstract2):
        '''
            TODO: 
                Check for equivalency, not equality
                But is that required?
        '''
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
    
    def __init__(self,monster_mapping={},trace_id=0):
        self.monster_id = 11
        self.wall_id = 0
        self.player_id = 7
        self.door_id = 3
        self.key_id = 4
        self.player_with_key_id = 8
        self.grid_height = 4 #assign dynamically later
        self.grid_width = 4 #assign dynamically later
        self.objects = {}#types: location(cells) ONLY
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
            'leftOf': [],
            'rightOf': [],
            'above': [],
            'below': [],
            'escaped':[]
        }
        self.g_score = 0 #for search
        self.best_path = None #for search 
    
    def print_grid(self,sso):
        grid = np.zeros([len(sso.observationGrid),len(sso.observationGrid[0])])
        for i in range(len(sso.observationGrid)):
             for j in range(len(sso.observationGrid[i])):
                 if sso.observationGrid[i][j][0]==None:
                     grid[i,j]=1
                 else:
                     grid[i,j] = sso.observationGrid[i][j][0].itype
        print(grid.T)

    
    