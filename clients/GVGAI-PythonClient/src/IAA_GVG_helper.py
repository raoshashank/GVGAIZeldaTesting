import logging
import os
import subprocess
import sys
import traceback
import argparse
sys.path.append("src/utils")
sys.path.append("./utils")
sys.path.append("./Agents")
from CompetitionParameters import CompetitionParameters

from ClientComm import ClientComm

'''
    Java File which runs in server: /home/raoshashank/GVGAI-master/src/tracks/singleLearning/utils/JavaServer_test.java
    Server Call: LearningMachine.runOneGame(game, level_files[0], true,cmd, null,0);
    Agent creation: LearningPlayer player = LearningMachine.createPlayer(cmd);
        where: String cmd[] = new String[]{null, null, port, clientType};
    Agent Improted: module = importlib.import_module(self.agentName, __name__) (ClientComm.py)
    Agent Initialization: commSend("START"); (Comm.java)
    Playing the game: double[] finalScore = playOnce(player, actionFile, game_file, level_file, visuals, randomSeed);
'''
class GVGAgent_Helper:
    def __init__(self,game_id,level_file,game_file,serverDir= '../../..'):
        self.gameId = game_id
        self.serverDir = serverDir
        self.agentName = "sampleRandom.ZeldaAgent"
        self.shDir = ""
        self.visuals = False
        self.gamesDir = serverDir
        self.gameFile = game_file
        self.levelFile = level_file
        self.serverJar = ""
        self.server_scriptFile = os.path.join("/home/raoshashank/GVGAI-master/clients/GVGAI-PythonClient/src/utils/runServer_nocompile_python.sh " + str(self.gameId) + " " + str(self.serverDir) +
                                      " " + str(self.visuals))
    def start_server(self):
        print("Starting Server...")
        subprocess.Popen(self.server_scriptFile, shell=True)
        self.ccomm = ClientComm(self.agentName)
        self.ccomm.startComm()
        print("Finished start server")