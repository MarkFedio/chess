import copy
import multiprocessing
import math
import time
import random

from chess_piece import Piece
from constants import *

class Engine_Process():
    def __init__(self, moves_file):
        
        self.in_queue = multiprocessing.Queue()
        self.out_queue = multiprocessing.Queue()
        self.process = self.init_engine_process()
        if moves_file:
            # tracks whether this engine has a moves_file or not
            self.moves_file_bool = True
            self.read_moves_file(moves_file)
        else:
            self.moves_file_bool = False


    def init_engine_process(self):
        engine_process = multiprocessing.Process(target = Engine_Process.get_best_move, 
                                                 args=(self.in_queue, self.out_queue), 
                                                 daemon=True)
        engine_process.start()
        print(f"process started")
        return engine_process

    def read_moves_file(self, moves_file):
        """reads moves_file and adds each move to self.out_queue.
        moves_file is in format of ((row, col), (row, col, 'move_type')) \n repeated"""
        with open(moves_file, "r") as file:
            for line in file:
                first_comma_idx = line.find(",", 0)
                second_comma_idx = line.find(",", first_comma_idx + 1)
                # ((row, col)  
                move_1 = line[:second_comma_idx]
                # (row, col)  
                move_1 = move_1[1:]
                
                # (row, col, 'move_type'))
                move_2 = line[second_comma_idx + 2:]
                first_apostrophe_idx = move_2.find("'", 0)
                second_apostrophe_idx = move_2.find("'", first_apostrophe_idx + 1)
                move_type = move_2[first_apostrophe_idx + 1:second_apostrophe_idx]

                # gets the job done...
                move = ((int(move_1[1]), int(move_1[4])), (int(move_2[1]), int(move_2[4]), move_type))
                #print(f"line: {line}")
                #print(f"move: {move}")
                self.out_queue.put(move)

    @staticmethod
    def get_best_move(in_queue, out_queue):
        # TODO: convert move1/2 in here to do_moves format (bruh)
        """in_queue is a hashable_board"""
        while True:
            curr_board = in_queue.get()
            if curr_board is None:
                break
            engine = Engine(curr_board)
            engine.board.legal_moves = engine.get_legal_moves()

            move_1 = ()
            move_2 = ()
            # player wants a more negative number so initialize their score to positive inf and vice versa
            if engine.board.turn == PLAYER_COLOR:
                best_score = math.inf
            else:
                best_score = -math.inf
            for possible_move_1, list in engine.board.legal_moves.items():
                if len(list) > 0:
                    for possible_move_2 in list:
                        # it's an Engine, but we're only using it for the board really
                        sim_board = copy.deepcopy(engine)
                        result = sim_board.evaluate_board(possible_move_1, possible_move_2)
                        if engine.board.turn == PLAYER_COLOR and result < best_score:
                            best_score = result
                            move_1 = possible_move_1
                            move_2 = possible_move_2
                        if engine.board.turn == OPPOSING_COLOR and result > best_score:
                            best_score = result
                            move_1 = possible_move_1
                            move_2 = possible_move_2

            # random_piece_and_moves = random.choice(list(engine.board.legal_moves.items()))
            # while len(random_piece_and_moves[1]) < 1:
            #     random_piece_and_moves = random.choice(list(engine.board.legal_moves.items()))
            # random_piece = random_piece_and_moves[0]
            # random_move = random.choice(random_piece_and_moves[1])


            print(f"selected move 1, move 2: {move_1}, {move_2}")
            # ((row, col), (row, col, move_type))
            out_queue.put((move_1, move_2))

class Engine():
    def __init__(self, board):
        import hashable_chess_board
        self.board: hashable_chess_board.Hashable_Board = board

    def evaluate_board(self, move_1, move_2):
        # TODO possible criteria:
        # - the more moves a piece can make, the better
        # - a piece guarding another piece is good
        # - having more attackers on an opposing piece than it has defenders (and vice versa).
        #       - But points of material must be considered too
        #       - Probabily similar recursion logic to trades 
        # - trades
        """Evalutes a board. Returns an int where a more negative number
        is better for the player and a more positive number is better for the opponent.
        Something like: player wins with checkmate -------- 0 -------- opponent wins with checkmate
        Current criteria:
        -Difference in points of material
        """
        self.move_piece(move_1, (move_2[0], move_2[1]), move_2[2])
        material_diff = self.board.opponent_material - self.board.player_material
        
        return material_diff

    def move_piece(self, sq1, sq2, move_type):
        """given move is of type (row, col, move_type)... does a move_type from (row, col)
        to (sq2[0], sq2[1]). Move validation must come prior to this function. Function
        is largely copied from chess_board.py's move_piece(), just accounting for different
        class calls"""
        sq1_row, sq1_col = sq1
        sq2_row, sq2_col = sq2
        if not self.board.board_simulation:
            print(f"(({sq1_row}, {sq1_col}), ({sq2_row}, {sq2_col}, '{move_type}'))")
        else:
            print(f"sim move: (({sq1_row}, {sq1_col}), ({sq2_row}, {sq2_col}, '{move_type}'))")

        # NOTE: captured_pieces.append is removed from here vs Board"s move_piece()
        if move_type == "c" or move_type == "pc": 
            if self.board.turn == PLAYER_COLOR:
                self.board.opponent_material -= self.board.layout[sq2_row][sq2_col].value
            else:
                self.board.player_material -= self.board.layout[sq2_row][sq2_col].value

        if move_type == "e":
            if self.board.turn == PLAYER_COLOR:
                self.board.opponent_material -= self.board.layout[sq2_row][sq2_col].value
            else:
                self.board.player_material -= self.board.layout[sq2_row][sq2_col].value

            
        # en passant logic
        # check if piece is a color
        #   if it's a pawn and moved two rows (can only happen on first move), that
        #   pawn is eligible to be captured by en passant. Else, reset en passant for this color
        if (self.board.layout[sq1_row][sq1_col].color == "white"):
            if (self.board.layout[sq1_row][sq1_col].piece_type == "p" and sq1_row - sq2_row == 2):
                self.board.en_passant_pieces["white"] = (sq2_row, sq2_col)
            else:
                self.board.en_passant_pieces["white"] = (-1, -1)
        if (self.board.layout[sq1_row][sq1_col].color == "black"):
            if (self.board.layout[sq1_row][sq1_col].piece_type == "p" and sq1_row - sq2_row == 2):
                self.board.en_passant_pieces["black"] = (sq2_row, sq2_col)
            else:
                self.board.en_passant_pieces["black"] = (-1, -1)                     

        self.board.layout[sq2_row][sq2_col] = self.board.layout[sq1_row][sq1_col]
        # the piece that was initially in sq1...
        self.board.layout[sq2_row][sq2_col].row = sq2_row
        self.board.layout[sq2_row][sq2_col].col = sq2_col
        self.board.layout[sq2_row][sq2_col].num_moves += 1

        # capturing with en passant removes the piece below (row + 1) where the pawn ends up
        if move_type == "e":
            self.board.layout[sq2_row + 1][sq2_col] = Piece("x_x", sq2_row + 1, sq2_col)

        # castling logic
        # white turn
        # if king-side, king goes to (7,6) with rook on (7,7) moving to (7,5)
        # if queen-side, king goes to (7,2) with rook on (7,0) moving to (7,3)
        if move_type == "y" and self.board.turn == PLAYER_COLOR:
            # king-side
            if sq2 == (7,6):    
                self.board.layout[7][5] = self.board.layout[7][7]
                self.board.layout[7][7] = Piece("x_x", sq1_row, sq1_col)
                self.board.layout[7][5].row = 7
                self.board.layout[7][5].col = 5
                self.board.layout[7][5].num_moves += 1 # not technically a rook move but idt this matters
            if sq2 == (7,2):
                self.board.layout[7][3] = self.board.layout[7][0]
                self.board.layout[7][0] = Piece("x_x", sq1_row, sq1_col)
                self.board.layout[7][3].row = 7
                self.board.layout[7][3].col = 3
                self.board.layout[7][3].num_moves += 1
        # mirrored logic for black
        if move_type == "y" and self.board.turn == OPPOSING_COLOR:
            if sq2 == (7,1):    
                self.board.layout[7][2] = self.board.layout[7][0]
                self.board.layout[7][0] = Piece("x_x", sq1_row, sq1_col)
                self.board.layout[7][2].row = 7
                self.board.layout[7][2].col = 2
                self.board.layout[7][2].num_moves += 1 # not technically a rook move but idt this matters
            if sq2 == (7,5):
                self.board.layout[7][4] = self.board.layout[7][7]
                self.board.layout[7][7] = Piece("x_x", sq1_row, sq1_col)
                self.board.layout[7][4].row = 7
                self.board.layout[7][4].col = 4
                self.board.layout[7][4].num_moves += 1

        # ... and sq1 always becomes empty
        self.board.layout[sq1_row][sq1_col] = Piece("x_x", sq1_row, sq1_col)

        # reads much better without distributing the not. Shoutout DeMorgan tho
        if not (move_type == "c" or move_type == "e"):
            self.board.moves_since_capture += 1
        else:
            self.board.moves_since_capture = 0
        self.board.update_board()
    
    def get_legal_moves(self):
        """gets all legal moves for the current board state (so takes into account turn, etc).
        Returns dict of (sq1 row, sq1 col) : [(sq2 row, sq2 col, move_type), other moves for the sq1 piece...].
        To use this dict in do_moves() you need to do something like:
        self.do_move((sq1 row, sq1 col, move_type), (sq2 row, sq2 col)) """
        moves_dict = {}
        for row in range(8):
            for col in range(8):
                if self.board.layout[row][col].color == self.board.turn:
                    self.board.selected_piece = (row, col)
                    self.board.legal_moves = self.board.layout[row][col].get_legal_moves(self.board.layout, self.board.en_passant_pieces)
                    self.board.legal_moves.extend(self.board.get_castle_moves())
                    self.board.legal_moves = self.board.exclude_check_moves(self.board.legal_moves)
                    # I initially had 
                    # curr_piece_moves = copy.deepcopy(self.board.legal_moves)
                    # here and then set moves_dict[(row,col)] to curr_p_m, but I don't think
                    # I need to copy it... but leaving here for future reference
                    moves_dict[(row, col)] = self.board.legal_moves
        return moves_dict