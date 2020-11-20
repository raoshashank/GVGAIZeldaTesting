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
        self.comm = ClientComm(None)
        self.count = 0
        self.has_key = False
        self.sso_traces = []
    """
    * Public method to be called at the start of every level of a game.
    * Perform any level-entry initialization here.
    * @param sso Phase Observation of the current game.
    * @param elapsedTimer Timer (1s)
    """

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
        if sso.gameTick == 1000:
            #print("Acting")
            return "ACTION_ESCAPE"
        else:
            #index = random.randint(0, len(sso.availableActions) - 1)
            #IPython.embed()
            #self.comm.processLine(sso)
            #print(sso.avatarPosition)
            #print(sso.availableActions)
            actions = [1,1,1,1,1,3,3,3,3,2,2,2,-1,-1,2,2,0]
            pp.pprint("Avatar Position:"+str(sso.avatarPosition))
            grid_string = ""
            pp.pprint("Immovable positions:"+str(sso.immovablePositions))
            if sso.gameTick == 1000:
                action = "ACTION_ESCAPE"
            else:
                index = random.randint(0, len(sso.availableActions) - 1)
                action =  sso.availableActions[index]
            return action
            # for i in range(len(sso.observationGrid)):
            #     for j in range(len(sso.observationGrid[i])):
            #         if not sso.observationGrid[i][j][0]==None:
            #             grid_string+=str(sso.observationGrid[i][j][0].itype)
            #         else:
            #             grid_string+='. '
            #     grid_string+="\n"
            
            # print("Observation Grid: \n"+str(grid_string))
            # self.sso_traces.append(sso)
            # if not self.has_key:
            #     if sso.avatarPosition[0]<110:
            #         #print("Going Right")
            #         action = sso.availableActions[2]
            #         return action
            #     elif sso.avatarPosition[1]<30:
            #         #print("Going Down")
            #         action = sso.availableActions[3]
            #         return action
            #     else:
            #         self.has_key = True
            # else:
            #     self.count+=1
            # return sso.availableActions[actions[self.count-1]]
            # # if sso.gameTick == 1000:
            #     action = "ACTION_ESCAPE"
            # else:
            #     index = random.randint(0, len(sso.availableActions) - 1)
            #     action =  sso.availableActions[index]
            
            #self.sso_traces.append([sso,action])
            # if self.count-1 == len(actions):
            #     with open("sso_traces.pkl","wb") as f:
            #         pickle.dump(self.sso_traces,f)
            #return action
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
