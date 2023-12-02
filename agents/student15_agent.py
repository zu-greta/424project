# win rate: ? against random_agent with 100 games and ? time 
# changes: same as 16 + A* search?

# testing commands:
# source venv/bin/activate
# cd 424_project
# python3 simulator.py --player_1 random_agent --player_2 student15_agent --display
# python3 simulator.py --player_1 random_agent --player_2 student15_agent --autoplay --autoplay_runs 100

# helpful website for a*: https://gist.github.com/ryancollingwood/32446307e976a11a1185a5394d6657bc


# Student agent: Add your own agent here
from agents.agent import Agent
from store import register_agent
import sys
import numpy as np
from copy import deepcopy
import time

import json
import ctypes 

@register_agent("student15_agent")
class Student15Agent(Agent):
    """
    A dummy class for your implementation. Feel free to use this class to
    add any helper functionalities needed for your agent.
    """

    def __init__(self):
        super(Student15Agent, self).__init__()
        self.name = "Student15Agent"
        self.dir_map = {
            "u": 0,
            "r": 1,
            "d": 2,
            "l": 3,
        }
        self.max_time = 1.9 # max time for each step
        self.max_sims = 5 # max simulations for each step
        self.moves = ((-1, 0), (0, 1), (1, 0), (0, -1)) # up, right, down, left

    # check if time out
    def timeout(self, start_time):
        return time.time() - start_time > self.max_time
    
    # get all legal moves in order of priority based on heuristic function
    def all_moves(self, chess_board, my_pos, adv_pos, max_step, start_time):
        # return a list of legal moves using BFS
        # for every possible num of steps until max_step, travel 4 directions + put wall. append to legal, sort and return the top #
        legal = [] # list of [p, s, n, (x, y), dir]
        state_queue = [(my_pos, 0)]
        visited = [my_pos, adv_pos]
        # BFS
        while state_queue and not self.timeout(start_time):
            cur_pos, cur_step = state_queue.pop()
            x, y = cur_pos
            dis = self.calculate_distance(cur_pos, adv_pos) #get the distance between my current position and adv
            for dir, move in enumerate(self.moves): # 4 directions
                if chess_board[x, y, dir]: # if there is a wall, skip the move
                    continue
                #check if gameover, me winner = 1, adv winner = -1, tie = 0
                self.set_barrier(x, y, dir, chess_board, True)
                over, w = self.is_gameover((x, y), adv_pos, chess_board)
                self.set_barrier(x, y, dir, chess_board, False)
                if over and w: # gameover, get winner and set p as the returned winner
                    p = w 
                    if p == 1:
                        return [[1, 1, 1, (x, y), dir]] #immediate win, just play that move
                else:
                    # Defense heuristic
                    if sum([chess_board[x, y, i] for i in range(4)]) >= 2: # if there are 2 walls, p = 0.1 
                        walls = 0.1
                    else: 
                        walls = 1
                    # Heuristic function: offense distance * defense walls * offense direction
                    p = (1 - dis/20) * walls * self.calculate_direction((x,y), adv_pos, dir)
                legal.append([p, 0, 1, (x, y), dir]) # append to legal
                # get the next step
                new_x, new_y = x + move[0], y + move[1] 
                new_pos = (new_x, new_y)
                if new_pos not in visited and cur_step + 1 <= max_step: # if not visited and not exceed max_step, append to queue
                    visited.append(new_pos)
                    state_queue.append((new_pos, cur_step + 1))
        return sorted(legal, key=lambda x: x[0], reverse=True)
    
    # A* search to find the shortest path from my_pos to adv_pos
    def a_star(self, chess_board, my_pos, adv_pos, max_step):
        # find the shortest path from my_pos to adv_pos
        def path_find(chess_board, my_pos, adv_pos, max_step):
            start = [my_pos[0], my_pos[1], 0, 0, 0, 0, 0, None] # [x, y, d, g, h, f, step, parent]
            end = [adv_pos[0], adv_pos[1], 0, 0, 0, 0, 0, None] # [x, y, d, g, h, f, step, parent]
            step = 0
            open_list = [start]
            closed_list = []
            visited = []
            while len(open_list) > 0:
                open_list.sort(key=lambda x: x[5], reverse=True) # sort on f value
                cur = open_list.pop() # node with least f value sorted on the rightmost
                closed_list.append((cur[0], cur[1], cur[2], cur[6]))
                visited.append((cur[0], cur[1], cur[2]))
                #print("cur:", cur)
                if (cur[0], cur[1]) == (end[0], end[1]):
                    #backtrack to get the path
                    path = []
                    c = cur
                    while c is not None:
                        print("c:", c)
                        if c[6] <= max_step:
                            path.append(((c[0], c[1]), c[2], c[6]))
                        print("addr:", c[7])
                        c = ctypes.cast(c[7], ctypes.py_object).value # parent
                        print("c parent:", c)
                    return path, closed_list # return the path and closed_list
                # all children of cur
                for dir, move in enumerate(self.moves):
                    if chess_board[cur[0], cur[1], dir]:
                        continue
                    new_x, new_y = cur[0] + move[0], cur[1] + move[1]
                    new_node = [new_x, new_y, dir, 0, 0, 0, step + 1, id(cur)]
                    # check if child is in closed_list
                    if (new_x, new_y, dir) in visited:
                        continue
                    # assign f, g, h values
                    new_node[3] = cur[3] + 1
                    new_node[4] = self.calculate_distance((new_x, new_y), adv_pos)
                    new_node[5] = new_node[3] + new_node[4]
                    # check if child is in open_list
                    if len([open_node for open_node in open_list if (new_x, new_y, dir) == (open_node[0], open_node[1], open_node[2]) and new_node[3] > open_node[3]]) > 0:
                        continue
                    open_list.append(new_node)
        # find the max position reachable from my_pos (using max_step)
        path = path_find(chess_board, my_pos, adv_pos, max_step)
        
        # set priorities
        # only keep top # of moves legal and closest to the max position
        # return the list
        print(path)
    
    # calculate the manhattan distance between two positions
    def calculate_distance(self, my_pos, adv_pos):
        r0, c0 = my_pos
        r1, c1 = adv_pos
        return abs(r0 - r1) + abs(c0 - c1)
    
    # calculate the direction of the adversary (for offensive heuristic)
    def calculate_direction(self, my_pos, adv_pos, dir):
        r0, c0 = my_pos
        r1, c1 = adv_pos
        if (r0 < r1 and dir == 2) or (r0 > r1 and dir == 0) or (c0 < c1 and dir == 1) or (c0 > c1 and dir == 3):
            return 1
        elif (r0 == r1 and dir == 2) or (r0 == r1 and dir == 0) or (c0 == c1 and dir == 1) or (c0 == c1 and dir == 3):
            return 0.5
        else:
            return 0
    
    # build or remove barrier
    def set_barrier(self, r, c, dir, step_board, is_set):
        opposites = {0: 2, 1: 3, 2: 0, 3: 1}
        # Set the barrier to True/False
        step_board[r, c, dir] = is_set
        # Set the opposite barrier to True/False
        move = self.moves[dir]
        step_board[r + move[0], c + move[1], opposites[dir]] = is_set
    
    # randomly select from the best moves simulation
    def simulation(self, my_pos, dir, adv_pos, max_step, step_board, start_time):
        # take the current step
        self.set_barrier(my_pos[0], my_pos[1], dir, step_board, True)
        player_switch = -1 # -1 is adv, 1 is me. every time switch player do player_switch *= -1
        score = 0 # score = 1 if win, score = -1 if lose, score = 0 if tie
        depth = 0 # depth of simulations
        gameover = False
        while (not gameover and not self.timeout(start_time) and depth <= max_step) :
            depth += 0.5
            # is_gamover is true if one of the player is enclosed, return the winner
            if (player_switch == -1) :
                # adversary's turn
                a_children = self.all_moves(step_board, adv_pos, my_pos, max_step, start_time)[:self.max_sims]
                if len(a_children) == 0:
                    gameover, score = self.is_gameover(my_pos, adv_pos, step_board)
                    break
                else:
                    n = np.random.randint(0, len(a_children))
                    adv_pos, dir = a_children[n][3], a_children[n][4]
                    self.set_barrier(adv_pos[0], adv_pos[1], dir, step_board, True)
            else :
                # my turn
                m_children = self.all_moves(step_board, my_pos, adv_pos, max_step, start_time)[:self.max_sims]
                if len(m_children) == 0:
                    gameover, score = self.is_gameover(my_pos, adv_pos, step_board)
                    break
                else:
                    n = np.random.randint(0, len(m_children))
                    my_pos, dir = m_children[n][3], m_children[n][4]
                    self.set_barrier(my_pos[0], my_pos[1], dir, step_board, True)
            gameover, score = self.is_gameover(my_pos, adv_pos, step_board) # check if gameover
            player_switch *= -1 # switch player
        # run random simulation on x, y, d node. if win, s+=1, lose, s-=1. tie s+=0
        return score * (2 - depth/max_step)
    
    # check if gameover
    def is_gameover(self, my_pos, adv_pos, step_board):
        # return list of spaces reachable from pos
        def find(pos):
            visited = [pos]
            path_queue = [pos]
            while path_queue:
                cur_pos = path_queue.pop()
                x, y = cur_pos
                for dir, move in enumerate(self.moves):
                    if not step_board[x, y, dir]:
                        new_x, new_y = x + move[0], y + move[1]
                        new_pos = (new_x, new_y)
                        if new_pos not in visited:
                            visited.append(new_pos)
                            path_queue.append(new_pos)
            return visited
        find_my_pos = find(my_pos) # list of spaces reachable from my_pos
        if adv_pos in find_my_pos: # if adv_pos is in find_my_pos the game is not over
            return False, 0
        # game is over, check if I win or lose
        find_adv_pos = find(adv_pos) # list of spaces reachable from adv_pos
        if len(find_adv_pos) == len(find_my_pos): # if the two lists are the same, it's a tie
            return True, 0
        elif len(find_adv_pos) > len(find_my_pos): # if find_adv_pos is larger, I lose
            return True, -1
        else: # if find_my_pos is larger, I win
            return True, 1
        
    # Heuristic: check number of moves left after placing a wall
    def check_moves_left(self, chess_board, my_pos, adv_pos, max_step, children):
        def find_moves(my_pos, adv_pos, chess_board, max_step):
            # return a list of legal moves using BFS
            # for every possible num of steps until max_step, travel 4 directions + put wall. append to legal, sort and return the top #
            legal = [] # list of [(x, y), dir]
            state_queue = [(my_pos, 0)]
            visited = [my_pos, adv_pos]
            # BFS
            while state_queue:
                cur_pos, cur_step = state_queue.pop()
                x, y = cur_pos
                for dir, move in enumerate(self.moves): # 4 directions
                    if chess_board[x, y, dir]: # if there is a wall, skip the move
                        continue
                    legal.append([(x, y), dir]) # append to legal
                    # get the next step
                    new_x, new_y = x + move[0], y + move[1] 
                    new_pos = (new_x, new_y)
                    if new_pos not in visited and cur_step + 1 <= max_step: # if not visited and not exceed max_step, append to queue
                        visited.append(new_pos)
                        state_queue.append((new_pos, cur_step + 1))
            return len(legal)
        # [(p, s, n, (x, y), dir), ...] -> [0: p, 1: s, 2: n, 3: (x, y), 4: dir]
        for i in range(len(children)):
            # get numbe rof moves left before placing wall
            new_pos, new_dir = children[i][3], children[i][4]
            adv_moves_bef = find_moves(adv_pos, my_pos, chess_board, max_step)
            my_moves_bef = find_moves(my_pos, adv_pos, chess_board, max_step)
            # get number of moves left after placing wall
            self.set_barrier(new_pos[0], new_pos[1], new_dir, chess_board, True)
            adv_moves_aft = find_moves(adv_pos, my_pos, chess_board, max_step)
            my_moves_aft = find_moves(my_pos, adv_pos, chess_board, max_step)
            self.set_barrier(new_pos[0], new_pos[1], new_dir, chess_board, False)
            # update p based on heuristic, 
            # offensive: increase p if adv_moves_aft < adv_moves_bef, increase p if my_moves_aft > my_moves_bef
            # defensive: decrease p if adv_moves_aft > adv_moves_bef, decrease p if my_moves_aft < my_moves_bef
            if (adv_moves_aft < adv_moves_bef) :
                children[i][0] += 0.1
            if (my_moves_aft > my_moves_bef) :
                children[i][0] += 0.1
            if (adv_moves_aft > adv_moves_bef) :
                children[i][0] -= 0.1
            if (my_moves_aft < my_moves_bef) :
                children[i][0] -= 0.1
        return sorted(children, key=lambda x: x[0], reverse=True)

    # get the best next move
    def best_move(self, children):
        # return a tuple of ((x, y), dir),
        # where (x, y) is the next position of your agent and dir is the direction of the wall you want to put on.
        # [(p, s, n, (x, y), dir), ...]
        best_next_move = sorted(children, key=lambda x: ((x[1]/x[2], x[0])), reverse=True)[0]
        return best_next_move[3], best_next_move[4]
    
    def step(self, chess_board, my_pos, adv_pos, max_step):
        """
        Implement the step function of your agent here.
        You can use the following variables to access the chess board:
        - chess_board: a numpy array of shape (x_max, y_max, 4)
        - my_pos: a tuple of (x, y)
        - adv_pos: a tuple of (x, y)
        - max_step: an integer

        You should return a tuple of ((x, y), dir),
        where (x, y) is the next position of your agent and dir is the direction of the wall
        you want to put on.

        Please check the sample implementation in agents/random_agent.py or agents/human_agent.py for more details.
        """
        self.a_star(chess_board, my_pos, adv_pos, max_step)
        print("done a*")
        return my_pos, 0
        chess_board_list = chess_board.tolist() # convert chess_board to list -> json format
        # Some simple code to help you with timing. Consider checking 
        # time_taken during your search and breaking with the best answer
        # so far when it nears 2 seconds.
        start_time = time.time()
        # get all legal moves in order of priority based on heuristic function
        # [(p, s, n, (x, y), dir), ...] -> [0: p, 1: s, 2: n, 3: (x, y), 4: dir]
        children = self.all_moves(chess_board, my_pos, adv_pos, max_step, start_time)[:10] # get top legal moves
        children = self.check_moves_left(chess_board, my_pos, adv_pos, max_step, children) # heuristic: check moves left after placing wall
        #print("time:", time.time() - start_time)
        if (len(children) == 1): 
            # only one move (usually immediate win)
            my_pos, dir = children[0][3], children[0][4]
        elif (len(children) != 0): # more than one move, run simulations to find the best move
            for i in range(len(children)): # run simulations on each child
                while (children[i][2] < self.max_sims and not self.timeout(start_time)): # run until max_sims or timeout
                    #step_board = deepcopy(chess_board) # copy the chess_board
                    step_board = np.array(json.loads(json.dumps(chess_board_list))) # copy the chess_board
                    score = self.simulation(children[i][3], children[i][4], adv_pos, max_step, step_board, start_time) # run simulation
                    children[i][1] += score # update score
                    children[i][2] += 1 # update num of simulations
                #print("num:", children[i])
                if (self.timeout(start_time)): # if timeout, break
                    break
            my_pos, dir = self.best_move(children) # get the best move based on score/num_sims

        time_taken = time.time() - start_time     
        print("My AI's turn took ", time_taken, "seconds.")
        return my_pos, dir 
