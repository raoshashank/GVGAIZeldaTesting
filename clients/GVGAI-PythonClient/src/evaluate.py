def compute_g(algorithm, node, goal_state):
    """
        Evaluates the g() value.
        
        Parameters
        ===========
            algorithm: str
                The algorithm type based on which the g-value will be computed.
            node: Node
                The node whose g-value is to be computed.
            goal_state: State
                The goal state for the problem.
                
        Returns
        ========
            int
                The g-value for the node.
    """
    
    if algorithm == "bfs":
    
        return node.get_depth()
    
    if algorithm == "astar":
    
        return node.get_total_action_cost()

    elif algorithm == "gbfs":
        
        return 0

    elif algorithm == "ucs":
        
        return node.get_total_action_cost()

    elif algorithm == "custom-astar":
    
        return node.get_total_action_cost()
        
    # Should never reach here.
    assert False
    return float("inf")
    
def compute_h(algorithm, node, goal_state):
    """
        Evaluates the h() value.
        
        Parameters
        ===========
            algorithm: str
                The algorithm type based on which the h-value will be computed.
            node: Node
                The node whose h-value is to be computed.
            goal_state: State
                The goal state for the problem.

        Returns
        ========
            int
                The h-value for the node.
    """
    
    if algorithm == "bfs":
    
        return 0

    if algorithm == "astar":
        
        return get_manhattan_distance(node.get_state(), goal_state)

    elif algorithm == "gbfs":
    
        return get_manhattan_distance(node.get_state(), goal_state) 

    elif algorithm == "ucs":

        return 0
    elif algorithm == "custom-astar":
    
        return get_custom_heuristic(node.get_state(), goal_state)
        
    # Should never reach here.
    assert False
    return float("inf")

def get_manhattan_distance(from_state, to_state):
    '''
    Returns the manhattan distance between 2 states
    '''
    from_player = from_state.state['player'][0]
    to_player = to_state.state['player'][0]
    from_x = int(from_player.replace('cell_','').split('_')[0])
    from_y = int(from_player.replace('cell_','').split('_')[1])
    to_x = int(to_player.replace('cell_','').split('_')[0])
    to_y = int(to_player.replace('cell_','').split('_')[1])
    #print(abs(from_x - to_x) + abs(from_y - to_y))
    return abs(from_x - to_x) + abs(from_y - to_y)


def get_custom_heuristic(from_state, to_state):
    '''
    Custom heuristic function. Assumes that given we need to reach the top right corner of the grid, if the bot is facing south or west 
    then it would have to do extra work in turning to move towards the goal.
    if the orientation is west or south then extra cost is added for turns.
    returns penalty of orientation + euclidean distance 
    '''
    cost = 0
    if(from_state.orientation == "NORTH"):
        cost = 1
    elif(from_state.orientation == "EAST"):
        cost = 1
    elif(from_state.orientation == "WEST"):
        cost = 2
    elif(from_state.orientation == "SOUTH"):
        cost = 2
    return cost + ((from_state.x - to_state.x)**2 + (from_state.y - to_state.y)**2)**0.5
