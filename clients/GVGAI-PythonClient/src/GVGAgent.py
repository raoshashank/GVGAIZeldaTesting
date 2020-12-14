from src.zelda_translator import *
from src.ZeldaStates import *
import pickle
import uuid
class GVGAgent():
    def __init__(self):
        self.translator = Zelda_Translator()

    def run_query(self,query):
        if len(self.translator.high_actions)!=0:
            return self.translator.iaa_query(query['state'],query['plan'])
        else:
            print("Actions not stored yet!")
            return False,-1,query['state']

    def validate_state(self,state):
        return self.translator.validate_state(state)

    def generate_random_states(self,n=5,save=False,abstract = False):
        random_states = []
        [random_states.append(self.translator.generate_random_state()) for i in range(n)]
        abs_random_states = []
        if abstract:
            for s in random_states:
                abs_random_states.append(self.translator.abstract_state(s))
            random_states = abs_random_states
        if save:
            with open("random_states","wb") as f:
                pickle.dump(random_states,f)
        return random_states
    
    def get_random_states(self,n=5):
        if n>self.translator.random_states:
            self.get_random_states(n-len(self.translator.random_states)+1)
            return self.translator.random_states
        else:
            return self.translator.random_states[0:n]

    def generate_ds(self):
        if len(self.translator.high_actions)!=0:
            return self.translator.generate_ds()
        else:
            #not created actions yet!
            print("Actions not stored yet")
            return False

    def load_actions(self,file="test_trace"):
        try:
            with open(file,'rb') as f:
                test_trace = pickle.load(f)
        except IOError:
            pass

        new_test_traces = []
        for i,run in enumerate(test_trace):
            sas_trace = []
            #first_state = self.translator.from_sso(run[0][0],Zelda_State(trace_id=0))
            #monster_mapping = first_state.monster_mapping
            for j,(sa1,sa2) in enumerate(zip(run,run[1:])):
                zsa1 = self.translator.from_sso(sa1[0])
                zsa2 = self.translator.from_sso(sa2[0])
                if zsa1.state['has_key'][0] != zsa2.state['has_key'][0]:
                    print("Here")
                sas_trace.append([zsa1,sa1[1],zsa2])
                if sa2[1]=='ACTION_ESCAPE':
                    break
                #if i == 7 and j>20:
                #    print(plot_state(zsa1))
                #    print("----"+str(i)+"--"+str(j))
                #    print(plot_state(zsa2))
            new_test_traces.append(sas_trace)

        high_level_traces = []
        high_level_actions = {} #key: action_id, value: (abs_s1,abs_s2)
        #translator = Zelda_Translator()
        for trace in new_test_traces:
            abs_trace = []
            for s1,a,s2 in trace:
                abs_s1 = self.translator.abstract_state(s1) 
                abs_s2 = self.translator.abstract_state(s2)
                '''
                print("Abstract State1:"+str(abs_s1))
                print("Concretized_state1:"+str(self.translator.refine_abstract_state(abs_s1))) 
                print("-------------") 
                print("Abstract State2:"+str(abs_s2))
                print("Concretized_state2:"+str(self.translator.refine_abstract_state(abs_s2))) 
                print("===============")
                '''
                if abs_s1 != abs_s2:
                    #create a new action
                    action_id = uuid.uuid1()
                    high_level_actions[action_id] = [abs_s1,abs_s2,]
                    abs_trace.append((abs_s1,action_id,abs_s2))
            high_level_traces.append(abs_trace)
        with open("high_actions_dict","wb") as f:
            pickle.dump(high_level_actions,f)
        with open("high_traces","wb") as f:
            pickle.dump(high_level_traces,f)
        self.translator.update_high_actions(high_level_actions)
        print("Saved High-level actions as traces")
        #return high_level_actions,high_level_traces 