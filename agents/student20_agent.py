# 2nd best

# Student agent: Add your own agent here
from agents.agent import Agent
from store import register_agent
import sys
import numpy as np
from copy import deepcopy
import time

import json #standard python library - no need to install (used instead of deepcopy)

@register_agent("student20_agent")
class Student20Agent(Agent):
    """
    A dummy class for your implementation. Feel free to use this class to
    add any helper functionalities needed for your agent.
    """

    def __init__(self):
        super(Student20Agent, self).__init__()
        self.name = "Student20Agent"
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
    
    # get all legal moves in order of priority based on heuristic function using BFS
    def BFS_search(self, chess_board, my_pos, adv_pos, max_step, start_time):
        # return a list of legal moves using BFS
        # for every possible num of steps until max_step, travel 4 directions + put wall. append to legal, sort and return the top #
        legal = [] # list of [p, s, n, (x, y), dir]
        state_queue = [(my_pos, 0)] # queue of next states
        visited = [my_pos, adv_pos] # list of visited states
        # BFS
        while state_queue and not self.timeout(start_time): # if timeout or state_queue is empty, break
            cur_pos, cur_step = state_queue.pop() # get the current position and current step
            x, y = cur_pos # get the current x, y
            dis_p = 1 - self.calculate_distance(cur_pos, adv_pos) / 20 #get the distance between my current position and adv
            for dir, move in enumerate(self.moves): # 4 directions
                if chess_board[x, y, dir]: # if there is a wall, skip the move
                    continue
                #check if gameover, me winner = 1, adv winner = -1, tie = 0
                self.set_barrier(x, y, dir, chess_board, True)
                over, w = self.is_gameover((x, y), adv_pos, chess_board)
                self.set_barrier(x, y, dir, chess_board, False)
                if over and w: # gameover, get winner and set p as the returned winner
                    p = w # p = 1 if I win, p = -1 if I lose, p = 0 if tie
                    if p == 1:
                        return [[1, 1, 1, (x, y), dir]] #immediate win, just play that move
                else:
                    # Defense heuristic (counts the number of walls around me)
                    if sum([chess_board[x, y, i] for i in range(4)]) >= 2: # if there are 2 walls, p = 0.1 
                        walls = 0.1
                    else: 
                        walls = 1 # if there is 1 wall or no wall, p = 1
                    # Heuristic function: offense distance * defense walls * offense direction
                    p = dis_p * walls * self.calculate_direction((x,y), adv_pos, dir)
                legal.append([p, 0, 1, (x, y), dir]) # append to legal
                # get the next step
                new_x, new_y = x + move[0], y + move[1] 
                new_pos = (new_x, new_y)
                if new_pos not in visited and cur_step + 1 <= max_step: # if not visited and not exceed max_step, append to queue
                    visited.append(new_pos)
                    state_queue.append((new_pos, cur_step + 1))
        return sorted(legal, key=lambda x: x[0], reverse=True) # sort legal moves based on p, higher p first
    
    # calculate the manhattan distance between two positions
    def calculate_distance(self, my_pos, adv_pos):
        r0, c0 = my_pos
        r1, c1 = adv_pos
        return abs(r0 - r1) + abs(c0 - c1)
    
    # Offensive heuristic: calculate the direction of the adversary 
    def calculate_direction(self, my_pos, adv_pos, dir):
        r0, c0 = my_pos
        r1, c1 = adv_pos
        if (r0 < r1 and dir == 2) or (r0 > r1 and dir == 0) or (c0 < c1 and dir == 1) or (c0 > c1 and dir == 3):
            return 1 # if the direction is towards the adversary, p = 1
        elif (r0 == r1 and dir == 2) or (r0 == r1 and dir == 0) or (c0 == c1 and dir == 1) or (c0 == c1 and dir == 3):
            return 0.5 # if the direction is perpendicular to the adversary, p = 0.5
        else:
            return 0 # if the direction is away from the adversary, p = 0
    
    # build or remove barrier
    def set_barrier(self, r, c, dir, step_board, is_set):
        opposites = {0: 2, 1: 3, 2: 0, 3: 1}
        # Set the barrier to True/False
        step_board[r, c, dir] = is_set
        # Set the opposite barrier to True/False
        move = self.moves[dir]
        step_board[r + move[0], c + move[1], opposites[dir]] = is_set
    
    # randomly select from the best moves (using BFS search) simulation step
    def simulation(self, my_pos, dir, adv_pos, max_step, step_board, start_time):
        # take the current step
        self.set_barrier(my_pos[0], my_pos[1], dir, step_board, True)
        player_switch = -1 # -1 is adv, 1 is me. every time switch player do player_switch *= -1
        score = 0 # score = 1 if win, score = -1 if lose, score = 0 if tie
        depth = 0 # depth of simulations
        gameover = False
        while (not gameover and not self.timeout(start_time) and depth <= max_step) : # if timeout or gameover or depth > max_step, break
            depth += 0.5 # increase depth by 0.5, break if depth > max_step (stop simulations if too deep - no use)
            # is_gamover is true if one of the player is enclosed, return the winner
            if (player_switch == -1) :
                # adversary's turn
                a_children = self.BFS_search(step_board, adv_pos, my_pos, max_step, start_time)[:self.max_sims] # get top legal moves
                if len(a_children) == 0: # if no legal moves, gameover
                    gameover, score = self.is_gameover(my_pos, adv_pos, step_board)
                    break
                else:
                    n = np.random.randint(0, len(a_children)) # randomly select a move out of top legal moves and play it
                    adv_pos, dir = a_children[n][3], a_children[n][4]
                    self.set_barrier(adv_pos[0], adv_pos[1], dir, step_board, True)
            else :
                # my turn
                m_children = self.BFS_search(step_board, my_pos, adv_pos, max_step, start_time)[:self.max_sims] # get top legal moves
                if len(m_children) == 0: # if no legal moves, gameover
                    gameover, score = self.is_gameover(my_pos, adv_pos, step_board)
                    break
                else:
                    n = np.random.randint(0, len(m_children)) # randomly select a move out of top legal moves and play it
                    my_pos, dir = m_children[n][3], m_children[n][4]
                    self.set_barrier(my_pos[0], my_pos[1], dir, step_board, True)
            gameover, score = self.is_gameover(my_pos, adv_pos, step_board) # check if gameover and get score
            player_switch *= -1 # switch player
        # run random simulations. if win, s+=1, lose, s-=1. tie or unfinished simulations s+=0
        return score * (2 - depth/max_step) # return score * (2 - depth/max_step) to give more weight to win/lose in early simulations
    
    # check if gameover
    def is_gameover(self, my_pos, adv_pos, step_board):
        # return list of spaces reachable from pos using BFS
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

    # get the best next move
    def best_move(self, children):
        # return a tuple of ((x, y), dir),
        # where (x, y) is the next position of your agent and dir is the direction of the wall you want to put on.
        # [(p, s, n, (x, y), dir), ...]
        best_next_move = sorted(children, key=lambda x: ((x[1]/x[2], x[0])), reverse=True)[0]
        return best_next_move[3], best_next_move[4] # return (x, y), dir

    # A* search to find the shortest path from my_pos to adv_pos (apply BFS if close, else apply A*)
    def all_moves(self, chess_board, my_pos, adv_pos, max_step, start_time):
        # find all possible moves using a BFS search
        def find_moves(my_pos, adv_pos, chess_board, max_step):
            # return a list of legal moves using BFS
            # for every possible num of steps until max_step, travel 4 directions + put wall. append to legal, sort and return the top #
            legal = []  # list of [(x, y), dir]
            state_queue = [(my_pos, 0)]
            visited = [my_pos, adv_pos]
            # BFS
            while state_queue:
                cur_pos, cur_step = state_queue.pop()
                x, y = cur_pos
                for dir, move in enumerate(self.moves):  # 4 directions
                    if chess_board[x, y, dir]:  # if there is a wall, skip the move
                        continue
                    legal.append([(x, y), dir])  # append to legal
                    # get the next step
                    new_x, new_y = x + move[0], y + move[1]
                    new_pos = (new_x, new_y)
                    if new_pos not in visited and cur_step + 1 <= max_step:  # if not visited and not exceed max_step, append to queue
                        visited.append(new_pos)
                        state_queue.append((new_pos, cur_step + 1))
            return len(legal)

        # find the shortest path from my_pos to adv_pos using A* search
        def aStar_Search(chess_board, my_pos, adv_pos, max_step):
            [nX, nY, nG, nH, nParent] = [i for i in range(5)] # init index
            open_list = [[my_pos[0], my_pos[1], 0, 0, None]]  # [0: x, 1: y, 2: g, 3: h, 4: parent]
            visited_list = [] # list of visited nodes (only position)
            visited_node = [] # list of visited nodes, positions and their steps
            visited = [] # list of all visited nodes with all their parameters
            while open_list:
                open_list.sort(key=lambda x: x[nG] + x[nH], reverse=True)  # sort on f value
                cur = open_list.pop()  # node with least f value sorted on the rightmost
                if (cur[nX], cur[nY]) == adv_pos: # if reach adv_pos, return the path
                    # backtrack to get the path
                    c = cur # current node
                    path = [] # list of positions in the path
                    while c[nParent] is not None:  # from end point, until the start point
                        c = visited[c[nParent]]  # go to parent
                        if c[nG] <= max_step: # if the step is less than max_step, append to path
                            path.append((c[nX], c[nY]))
                    return path, cur[nG], visited_node  # return the furthest position reachable from my_pos and closed_list
                visited_list.append((cur[nX], cur[nY])) # append cur position to visited_list
                visited_node.append(((cur[nX], cur[nY]), cur[nG])) # append cur position and step to visited_node
                visited.append(cur) # append cur node to visited
                # all children of cur
                for dir, move in enumerate(self.moves):
                    if chess_board[cur[nX], cur[nY], dir]: # if there is a wall, skip
                        continue
                    x, y = cur[nX] + move[0], cur[nY] + move[1] # get the next position
                    # skip if child is in closed_list
                    if (x, y) in visited_list:
                        continue
                    # assign f, g, h values
                    new_node = [x, y, cur[nG] + 1, self.calculate_distance((x, y), adv_pos), visited.index(cur)]
                    # check if child is in open_list with higher steps
                    if sum([1 for oN in open_list if ((x, y) == (oN[nX], oN[nY]) and new_node[nG] > oN[nG])]):
                        continue
                    open_list.append(new_node) # append new node to open_list
            return [], 0 , [] # Nothing found - should not happen but here for safety reasons

        # find the max position reachable from my_pos (using max_step)
        path, m_step, visited = aStar_Search(chess_board, my_pos, adv_pos, max_step) # [(x, y, step), ...]
        children = []
        if m_step <= max_step:
            # close enough to run BFS
            children = self.BFS_search(chess_board, my_pos, adv_pos, max_step, start_time)[:10]
        elif m_step <= max_step * 1.5: # not that close, run BFS on visited nodes
            for p_pos, p_step in visited: # go through visited
                if p_step > max_step: continue # get rid of nodes with step > max_step
                (x,y) = p_pos
                dis_p = 1 - self.calculate_distance(p_pos, adv_pos) / 20  # Heursitic: get the distance between my current position and adv
                for dir in range(4): # 4 directions
                    if chess_board[x, y, dir]:
                        continue
                    #check if gameover, me winner = 1, adv winner = -1, tie = 0
                    self.set_barrier(x, y, dir, chess_board, True)
                    over, w = self.is_gameover(p_pos, adv_pos, chess_board)
                    self.set_barrier(x, y, dir, chess_board, False)
                    if over: # gameover and im the winner or game is tied, just play that move
                        if w != -1: return [[1, 1, 1, p_pos, dir]]
                    else:
                        # Defense heuristic: walls
                        if sum([chess_board[x, y, i] for i in range(4)]) >= 2:  # if there are 2 walls, p = 0.1
                            walls = 0.1
                        else:
                            walls = 1
                        # Heuristic function: offense distance * defense walls * offense direction
                        p = dis_p * walls * self.calculate_direction((x, y), adv_pos, dir)
                        children.append([p, 0, 1, p_pos, dir])  # append to children
            children = sorted(children, key=lambda x: x[0], reverse=True)[:10]  # sort on priority
        else: # far, first check if there is a winner
            for p_pos in path: 
                (x, y) = p_pos
                for dir in range(4):
                    if not chess_board[x, y, dir]:
                        #check if gameover, me winner = 1, adv winner = -1, tie = 0
                        self.set_barrier(x, y, dir, chess_board, True)
                        over, w = self.is_gameover(p_pos, adv_pos, chess_board)
                        self.set_barrier(x, y, dir, chess_board, False)
                        if over and w != -1: return [[1, 1, 1, p_pos, dir]] # gameover and im the winner or game is tied, just play that move
        # reached here, children is empty so take the furthest point on the A* path
        if not children: # take the first path position
            x, y = path[0]
            for d in range(4):
                if not chess_board[x, y, d]:
                    children.append([self.calculate_direction(path[0], adv_pos, d), 0, 1, path[0], d]) # append all possible wall directions for furthest point
        
        # Heuristic: check for number of moves left before and after placing wall
        if len(children) > self.max_sims:
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
                if (adv_moves_aft < adv_moves_bef):
                    children[i][0] += 0.1
                if (my_moves_aft > my_moves_bef):
                    children[i][0] += 0.1
                if (adv_moves_aft > adv_moves_bef):
                    children[i][0] -= 0.1
                if (my_moves_aft < my_moves_bef):
                    children[i][0] -= 0.1
        return sorted(children, key=lambda x: x[0], reverse=True) # sort legal moves based on p, higher p first

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
        chess_board_list = chess_board.tolist() # convert chess_board to list -> json format
        # Some simple code to help you with timing. Consider checking 
        # time_taken during your search and breaking with the best answer
        # so far when it nears 2 seconds.
        start_time = time.time()
        # get all legal moves in order of priority based on heuristic function
        # [(p, s, n, (x, y), dir), ...] -> [0: p, 1: s, 2: n, 3: (x, y), 4: dir]
        children = self.all_moves(chess_board, my_pos, adv_pos, max_step, start_time)[:10] # get top legal moves
        if (len(children) == 1):
            # only one move (usually immediate win)
            my_pos, dir = children[0][3], children[0][4]
        elif (len(children) != 0): # more than one move, run simulations to find the best move
            for i in range(len(children)): # run simulations on each child
                while (children[i][2] < self.max_sims and not self.timeout(start_time)): # run until max_sims or timeout
                    #step_board = deepcopy(chess_board) # copy the chess_board but deepcopy version is slower - enable if cannot use json
                    step_board = np.array(json.loads(json.dumps(chess_board_list))) # copy the chess_board using json
                    score = self.simulation(children[i][3], children[i][4], adv_pos, max_step, step_board, start_time) # run simulation
                    children[i][1] += score # update score
                    children[i][2] += 1 # update num of simulations
                if (self.timeout(start_time)): # if timeout, break
                    break
            my_pos, dir = self.best_move(children) # get the best move based on score/num_sims

        time_taken = time.time() - start_time     
        print("My AI's turn took ", time_taken, "seconds.")
        return my_pos, dir 