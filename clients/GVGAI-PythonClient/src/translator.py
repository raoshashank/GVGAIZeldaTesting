#!/usr/bin/env python

import socket
import IPython



'''
    Define predicates for Zelda:
'''
class Translator:
    def __init__(self,games_path,game_name,level_num = 0):
        '''
            create a translator that interacts with the JavaServer to:
                set initial states and 
                run plans (low level)
        '''
        self.games_path = games_path
        self.game_name = game_name
        self.game_file = games_path+'/'+game_name+'".txt'
        self.level_file = games_path+'/'+game_name+"_lvl"+str(level_num)+'.txt'
        self.predicates = []
        self.HOST = "localhost"
        self.PORT = 8080
            
    def set_initial_state(self,state):
        return NotImplementedError
    
    def run_plan(self,state):
        return NotImplementedError