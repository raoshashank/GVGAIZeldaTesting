import random
import sys
from AbstractPlayer import AbstractPlayer
from Types import *
from ClientComm import ClientComm
from utils.Types import LEARNING_SSO_TYPE
#import IPython
import pprint
import pickle
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
        self.step = 0
        self.max_steps = 10
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
                print("Running plan")
            except IndexError:
                print("Whoops")
            print(action)
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
        return random.randint(0, 2)
