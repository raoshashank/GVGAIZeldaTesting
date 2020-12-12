import random
import sys
from AbstractPlayer import AbstractPlayer
from Types import *
from ClientComm import ClientComm
from utils.Types import LEARNING_SSO_TYPE
#import IPython
import pprint
import pickle
from src.zelda_translator import Zelda_State,AbstractZeldaState
pp = pprint.PrettyPrinter(indent=4)

class Agent(AbstractPlayer):
    def __init__(self):
        AbstractPlayer.__init__(self)
        self.lastSsoType = LEARNING_SSO_TYPE.JSON
        self.plan_file = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/plan.pkl" #Add file to read plan from
        self.comm = ClientComm(None)
        self.count = 0
        self.has_key = False
        self.sso_traces = []
        self.plan = []
        self.current_trace = []
        self.step = 0
        self.max_steps = 30
        self.max_score = 0
        self.trace_recorder_file = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/test_trace" 
        self.actionFile = "/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/actionFile" #this is used to read the winner state after game terminates
        try:
            with open(self.trace_recorder_file,"rb") as f:
                self.old_traces = pickle.load(f)
        except IOError:
            self.old_traces = []
            pass

        try:
            with open(self.plan_file,"rb") as f:
                self.plan = pickle.load(f)
        except IOError:
            pass

    """
    * Public method to be called at the start of every level of a game.
    * Perform any level-entry initialization here.
    * @param sso Phase Observation of the current game.
    * @param elapsedTimer Timer (1s)
    """
    def set_plan(self,new_plan):
        self.plan = new_plan
        self.step = 0

    def init(self, sso, elapsedTimer):
        pass

    """
     * Method used to determine the next move to be performed by the agent.
     * This method can be used to identify the current state of the game and all
     * relevant details, then to choose the desired course of action.
     *
     * @param sso Observation of the current state of the game to be used in deciding
     *            the next action to be taken by the agent.
     * @param elapsedTimer Timer (40ms)
     * @return The action to be performed by the agent.
     """

    def act(self, sso, elapsedTimer):
        if sso.avatarOrientation == [-1,0]:
            print('WEST')
        if sso.avatarOrientation == [1,0]:
            print('EAST')
        if sso.avatarOrientation == [0,-1]:
            print('NORTH')
        if sso.avatarOrientation == [0,1]:
            print('SOUTH')
        if (len(self.plan)==0 and self.step<self.max_steps) or self.step>=len(self.plan):
            index = random.randint(0, len(sso.availableActions) - 1)
            action = sso.availableActions[index]
            print("Selecting random action")
            self.step+=1
        else:    
            # if self.step>=len(self.plan):
            #     print("Something is wrong here in agent action")
            #     action =  unicode("ACTION_ESCAPE")
            # else:
            #     
            try:
                action = self.plan[self.step-1]
                self.step+=1
                #print("Running plan")
            except IndexError:
                print("Whoops")
            #print(action)
        #modded_traces.append((zstate,pair[1]))
        # for k in previous_zstate.state.keys():
        #     if previous_zstate.state[k]!=current_zstate.state[k]:
        #         print("Key: "+k)
        #         print("value1:"+str(previous_zstate.state[k]))
        #         print("value2:"+str(zstate.state[k]))
        #         print("transition action:"+str(previous_action))
        # #print(sso.availableActions)
        dirs = {
            'w':-1,
            'a':1,
            's':3,
            'd':2,
            'e':0,
        }
        input_action = str.lower(input())
        if input_action!='q' and input_action!='x':
            while True:
                try:
                    action = sso.availableActions[dirs[input_action]]
                    break
                except KeyError as e:
                    pass   
        elif input_action=='q':
            action = 'ABORT'
        else:
            action = 'ACTION_NIL'
        # if self.step>self.max_steps:
        #     action = 'ACTION_ESCAPE'
        print(action)
        self.current_trace.append((sso,action))
        current_zstate = Zelda_State(sso)
        previous_zstate = Zelda_State(self.current_trace[-1][0])
        previous_action = self.current_trace[-1][1]
        return action
    
    """
    * Method used to perform actions in case of a game end.
    * This is the last thing called when a level is played (the game is already in a terminal state).
    * Use this for actions such as teardown or process data.
    *
    * @param sso The current state observation of the game.
    * @param elapsedTimer Timer (up to CompetitionParameters.TOTAL_LEARNING_TIME
    * or CompetitionParameters.EXTRA_LEARNING_TIME if current global time is beyond TOTAL_LEARNING_TIME)
    * @return The next level of the current game to be played.
    * The level is bound in the range of [0,2]. If the input is any different, then the level
    * chosen will be ignored, and the game will play a random one instead.
    """
    def result(self, sso, elapsedTimer):
        print("Stored New Trace")
        #if self.current_trace[-1][0].
        with open(self.actionFile,"r") as f:
            lines = f.readlines()
        winner = int(lines[0].split(" ")[1])
        if winner == 1:
            dummy_sso = self.current_trace[-1][0]
            dummy_sso.gameWinner = 'PLAYER_WINS'
            self.current_trace.append((dummy_sso,'ACTION_ESCAPE'))
        self.old_traces.append(self.current_trace)
        with open(self.trace_recorder_file,'wb') as f:
            pickle.dump(self.old_traces,f)
        return random.randint(0, 2)
#0 1 2.0 23 :seed,winner,score,tick
#0 0 0.0 5 : seed,winner(1 for player wins, 0 for terminate),score,tick  