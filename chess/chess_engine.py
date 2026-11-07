import copy
import multiprocessing
import math
import time
import random
from collections import OrderedDict
import cProfile

import hashable_chess_board
import chess_piece
from constants import *

deep_copy_count = 0
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
        """in_queue is a hashable_board"""
        profiler = cProfile.Profile()
        engine = Engine(None)

        while True:
            curr_board = in_queue.get()
            if curr_board == "QUIT":
                print(f"quitting profiler")
                profiler.disable()
                profiler.dump_stats("engine.prof")
                break
            if curr_board is None:
                break
            #profiler.enable()
            engine.board = curr_board

            #print(f"init len: {len(Engine.cached_evals)}")
            Engine.cached_evals.clear()
            #print(f"cleared len: {len(Engine.cached_evals)}")
            engine.board.legal_moves = engine.get_legal_moves()
            moves_list = []
            # white wants a more negative number so initialize their score to positive inf and vice versa
            if engine.board.turn == "white":
                best_score = POS_INF
            else:
                best_score = NEG_INF

            """
            variable depth placeholder




















            """
            
            for complete_move in engine.board.legal_moves:
                Engine.moves_evaluated += 1

                move_1 = complete_move[0]
                move_2 = complete_move[1]

                # it's an Engine, but we're only using it for the board really
                #print(f"\n\nexploring move ({engine.get_chess_notation(move_1, engine.board.turn)}, {engine.get_chess_notation((move_2[0], move_2[1]), engine.board.turn)}) type {move_2[2]} at HIGHEST depth")
                sim_board = copy.deepcopy(engine)
                sim_board.board.move_piece(move_1, (move_2[0], move_2[1]), move_2[2])
                
                result = sim_board.get_best_move_recursive(best_black=-math.inf,best_white=math.inf, in_trade=False, depth=DEPTH)

                if engine.board.turn == "white":

                    if result == best_score:   
                        append_move = copy.copy((move_1, move_2))
                        moves_list.append(append_move)
                    if result < best_score:
                        moves_list.clear()
                        best_score = result
                        append_move = copy.copy((move_1, move_2))
                        moves_list.append(append_move)

                if engine.board.turn == "black":
                    if result == best_score:   
                        append_move = copy.copy((move_1, move_2))
                        moves_list.append(append_move)
                    if result > best_score:
                        moves_list.clear()
                        best_score = result
                        append_move = copy.copy((move_1, move_2))
                        moves_list.append(append_move)

                print(f"\n\n{engine.board.turn} turn ({engine.get_chess_notation(move_1, engine.board.turn)}, {engine.get_chess_notation(move_2, engine.board.turn)}) gives eval {result}, best score = {best_score}\n")
                            

            #print(f"final len: {len(Engine.cached_evals)}")
            print(f"moves_list (not flipped): {moves_list}")
            if len(moves_list) == 0:
                out_queue.put(-1)
            else:
                #out_queue.put(moves_list[0])
                out_queue.put(random.choice(moves_list))
            profiler.disable()
        

class Engine():
    entry_depth = 0

    cached_evals = OrderedDict()
    max_cache_evals_size = 1000000
    

    moves_evaluated = 0

    move_priority = {"pc" : 0, "p" : 1, "c" : 2, "e" : 3, "y" : 4, "o": 5}

    def __init__(self, board):
        
        self.board: hashable_chess_board.Hashable_Board = board


    def get_best_move_recursive(self, best_black, best_white, in_trade, depth, trade_depth=0):
        """Looks at (and evaluates) all boards to a depth of the input. Returns
        the best evaluation for a board (recursive boards included). Recursive
        calls assume each subsequent move is the best... meaning black will return
        the board eval of the max min evaluation. As an alternative explanation of the
        same concept... If the engine is black, the final eval returned is 
        from the first move in a sequence that results in the best board for black that can be forced.

        best_black/white: best score the respective color has gotten so far. Used for A/B pruning
        in_trade: TODO
        
        depth: number of moves ahead evaluated. Effective depth is depth + 1 because this func
                gets called from get_best_move() which looks through all moves at the immediate depth

        """
        # from perspective of engine being black
        # initially:
        #   black's turn
        #   returns most positive board eval (happens last)
        # first recursion:
        #   white's turn  
        #   returns most negative board eval (assumes white makes best move)
        # second recursion:
        #   black's turn
        #   returns most positive board eval (happens first)
        # player wants a more negative number so initialize their score to positive inf and vice versa

        # base case (technically most deep level):
        if depth == 0:
            hashed_board = self.hash_engine_board()
            result = self.evaluate_board()
                
            Engine.cached_evals[hashed_board] = result
            if len(Engine.cached_evals) > Engine.max_cache_evals_size:
                #print(f"popping")
                Engine.cached_evals.popitem(last=False)
            return result 

        best_score = 0
        if self.board.turn == "white":
            best_score = POS_INF
        else:
            best_score = NEG_INF

        
        self.board.legal_moves = self.get_legal_moves()

        if in_trade:
            if trade_depth >= MAX_TRADE_DEPTH:
                return self.evaluate_board()
            has_capture = any(m[1][2] in {"c", "pc", "e"} for m in self.board.legal_moves)
            if not has_capture:
                return self.evaluate_board()

        #print(f"curr_legal_moves at depth {depth}: {curr_legal_moves}")

        for complete_move in self.board.legal_moves:
        

            move_1 = complete_move[0]
            move_2 = complete_move[1]
            move_type = move_2[2]
            if in_trade and move_type not in {"c", "pc", "e"}:
                continue
            Engine.moves_evaluated += 1
      

            #print(f"start loop curr legal moves items: {curr_legal_moves.items()}")


            #print(f"\n\nexploring move ({self.get_chess_notation(move_1, self.board.turn)}, {self.get_chess_notation(move_2, self.board.turn)}) type {move_type} at depth {depth}")

            curr_legal_moves_backup = []
            if move_type == "o":
                recursive = self
                curr_legal_moves_backup = copy.copy(self.board.legal_moves)
            else:
                recursive = copy.deepcopy(self)
            recursive.board.move_piece(move_1, (move_2[0], move_2[1]), move_type)

            # if move_type not in {"c", "pc","e"}:
            #     new_depth = depth - 1

            if depth == 1 and move_type in {"c", "pc", "e"}:
                # I really don't know if this works logicially, but it did what I thought it should do when testing
                result = recursive.get_best_move_recursive(best_black, best_white, in_trade=True, depth=depth, trade_depth=trade_depth+1)
            else:
                result = recursive.get_best_move_recursive(best_black, best_white, in_trade=False, depth=depth - 1, trade_depth=0)

            if move_type == "o":
                #print(f"\n\nreversing move ({self.get_chess_notation(move_1, self.board.turn)}, {self.get_chess_notation(move_2, self.board.turn)}) type {move_type} at depth {depth}")
                recursive.board.reverse_move(move_1, (move_2[0], move_2[1]), move_type)
                recursive.board.legal_moves = curr_legal_moves_backup
            

            if self.board.turn == "white": 
                best_score = min(result, best_score)
                if best_score == NEG_INF:
                    return best_score

                #a/b pruning
                best_white = min(best_score, best_white)
                # if this score is better than black's best, they wouldn't've let this position happen
                if best_white <= best_black:
                    return best_score
                

            if self.board.turn == "black": 
                best_score = max(result, best_score)
                if best_score == POS_INF:
                    return best_score

                #a/b pruning
                best_black = max(best_score, best_black)
                # if this score is better than white's best, they wouldn't've let this position happen
                if best_black >= best_white:
                    return best_score
                    
            #print(f"end loop curr legal moves items: {curr_legal_moves.items()}")
                        
        if len(self.board.legal_moves) > 0:
            #print(f"{self.board.turn}, depth of {depth} best_score: {best_score}")
            return best_score
        else:
            #print(f"no moves")
            # no moves. Check for checkmate

            game_state = self.board.check_draw_stalemate_checkmate()
            if self.board.turn == "white": 
                # if game_state is checkmate while turn is white, it's good for black.
                # Uses logic that infinities at higher depth are bettern than infinities at lower
                # depth. This solves the issue of mate-in-1s being equals to mate-in->1s
                if game_state == CHECKMATE_ID:
                    print(f"checkmate 1")
                    return POS_INF - (DEPTH - depth)
                else:
                    print(f"draw/stalemate 1")
                    return 0
            else:
                if game_state == CHECKMATE_ID:
                    print(f"checkmate 2")
                    return NEG_INF + (DEPTH - depth)
                else:
                    print(f"draw/stalemate 2")
                    return 0

    def evaluate_board(self):
        # TODO possible criteria:
        # - the more moves a piece can make, the better
        # - a piece guarding another piece is good
        # - having more attackers on an opposing piece than it has defenders (and vice versa).
        #       - But points of material must be considered too
        #       - Probably similar recursion logic to trades 
        # - trades
        """Evaluates a board. Returns an int where a more negative number
        is better for white and a more positive number is better for black.
        Something like: white wins with checkmate <-------- 0 --------> black wins with checkmate
        Current criteria:
        -Difference in points of material
        """
        black_score = self.board.black_material
        white_score = self.board.white_material
        black_update = 0
        white_update = 0


        for i, dict in enumerate([self.board.player_layout_dict, self.board.opponent_layout_dict]):
            # getting a piece's legal moves (happens in the eval_piece() calls) requires
            # the piece to be from the perspective of the bottom player
            if i == 1:
                self.board.flip_layout_dicts()
                # en_passant dict should be flipped if the eval_pawn func needs to get legal moves
                #   (doesn't currently).

            score = 0
            for piece in dict.values():
                if piece.piece_type == "p":
                    score += self.evaluate_pawn(piece)
                    #print(f"score1 : {score}")
                if piece.piece_type == "n":
                    score += self.evaluate_knight(piece, self.board.player_layout_dict, self.board.opponent_layout_dict)
                    #print(f"score2 : {score}")
                if piece.piece_type == "b":
                    score += self.evaluate_bishop(piece, self.board.player_layout_dict, self.board.opponent_layout_dict)
                if piece.piece_type == "r":
                    score += self.evaluate_rook(piece, self.board.player_layout_dict, self.board.opponent_layout_dict)
                if piece.piece_type == "q":
                    score += self.evaluate_queen(piece, self.board.player_layout_dict, self.board.opponent_layout_dict)
                if piece.piece_type == "k":
                    score += self.evaluate_king(piece, self.board.player_layout_dict, self.board.opponent_layout_dict)
                    if piece.color == "white" and self.board.white_material < 2 and self.board.black_material > 2:
                        score += self.evaluate_alone_king(piece, self.board.opponent_layout_dict)
                    if piece.color == "black" and self.board.black_material < 2 and self.board.white_material > 2:
                        score += self.evaluate_alone_king(piece, self.board.opponent_layout_dict)

            # logic to make sure the correct player gets credited with this score update
            if self.board.turn == "white":
                if i == 0:
                    white_update = score
                else:
                    black_update = score
            else:
                if i == 0:
                    black_update = score
                else:
                    white_update = score

            # flip back
            if i == 1:
                self.board.flip_layout_dicts()

        #print(f"black_update, white_update: {black_update}, {white_update}")
        black_score += black_update
        white_score += white_update

        diff = black_score - white_score

        #print(f"returning diff: {diff}")
        return diff
    
    def evaluate_pawn(self, pawn: chess_piece.Piece):
        """ 
        Evaluates the positions of a pawn on the board.
            pawn = a reference to a (pawn) Piece
        Considering things like:
            - The more advanced a pawn, the better
        """
        advanced_pawn_factor = 1/10

        home_row = 6

        score = 0
        score += home_row - pawn.row

        return score * advanced_pawn_factor

    def evaluate_knight(self, knight: chess_piece.Piece, player_layout_dict, opponent_layout_dict):
        """ 
        Evaluates the positions of a knight on the board.
            knight = a reference to a (knight) Piece
        Considering things like:
            - The more legal moves a knight has, the better (in a vacuum, this means it's bad for this
            piece to defend another piece, but that should be overridden by a simulated board's material loss)
        """
        num_moves_factor = 1/10

        score = 0
        moves = knight.get_knight_moves(player_layout_dict, opponent_layout_dict)
        score += len(moves)

        return score * num_moves_factor

    def evaluate_bishop(self, bishop: chess_piece.Piece, player_layout_dict, opponent_layout_dict):
        """ 
        Evaluates the positions of a bishop on the board.
            bishop = a reference to a (bishop) Piece
        Considering things like:
            - The more legal moves a bishop has, the better (in a vacuum, this means it's bad for this
            piece to defend another piece, but that should be overridden by a simulated board's material loss)
        """
        num_moves_factor = 1/10

        score = 0
        moves = bishop.get_bishop_moves(player_layout_dict, opponent_layout_dict)
        score += len(moves)

        return score * num_moves_factor

    def evaluate_rook(self, rook: chess_piece.Piece, player_layout_dict, opponent_layout_dict):
        """ 
        Evaluates the positions of a rook on the board.
            rook = a reference to a (rook) Piece
        Considering things like:
            - The more legal moves a rook has, the better (in a vacuum, this means it's bad for this
            piece to defend another piece, but that should be overridden by a simulated board's material loss)
        """
        num_moves_factor = 1/10

        score = 0
        moves = rook.get_rook_moves(player_layout_dict, opponent_layout_dict)
        score += len(moves)

        return score * num_moves_factor

    def evaluate_queen(self, queen: chess_piece.Piece, player_layout_dict, opponent_layout_dict):
        """ 
        Evaluates the positions of a queen on the board.
            queen = a reference to a (queen) Piece
        Considering things like:
            - The more legal moves a queen has, the better (in a vacuum, this means it's bad for this
            piece to defend another piece, but that should be overridden by a simulated board's material loss)
        """
        num_moves_factor = 1/10

        score = 0
        moves = queen.get_rook_moves(player_layout_dict, opponent_layout_dict)
        score += len(moves)

        return score * num_moves_factor

    def evaluate_king(self, king: chess_piece.Piece, player_layout_dict, opponent_layout_dict):
        """ 
        Evaluates the positions of a king on the board.
            king = a reference to a (king) Piece
        Considering things like:
            - Rewarding castling by rewarding leaving center bottom (starting sq +/- 1 col and 7th row)
                  in 1 move
            - For a king not in the center bottom, having pieces around it is good (max 3)
            - 
        """
        # raw score, not a factor
        castled_score = .5
        protection_on_not_centered_king_factor = .2


        score = 0

        starting_col = -1
        if king.color == "white":
            starting_col = 4
        else:
            starting_col = 3

        # reward castling
        if king.col not in (starting_col - 1, starting_col, starting_col + 1) and king.num_moves < 2:
            score += castled_score

        # reward protection on not-centered king
        if king.col not in (starting_col - 1, starting_col, starting_col + 1):
            count = 0
            for row_move in (-1, 0, 1):
                for col_move in (-1, 0, 1):
                    if (king.row + row_move, king.col + col_move) in player_layout_dict:
                        count += 1
                    if count >= 3:
                        break
            # cap at 3
            if count >= 3:
                count = 3
            score += count*protection_on_not_centered_king_factor

        """
        
        """

        return score

    def evaluate_alone_king(self, king: chess_piece.Piece, opposing_layout_dict):
        """
        Evaluates the position of a king whose color has < 2 POM left
            king = a reference to a (king) Piece
        Considering things like:
            - The further from the center of the board, the worse
            - The closer to the opposing king, the worse
        """
        squares_from_center_factor = -0.8
        squares_from_opp_king_factor = -0.8

        opp_king_row = -1
        opp_king_col = -1
        for piece in opposing_layout_dict.values():
            if piece.piece_type == "k":
                opp_king_row = piece.row
                opp_king_col = piece.col

        # .floor with the 3.5 essentially means anywhere in the 2x2 square in the center is
        # considered centered and wont carry a penalty
        squares_from_center = math.floor(abs(3.5 - king.row)) + math.floor(abs(3.5 - king.col))
        squares_from_opp_king = 7-abs(king.row - opp_king_row) + 7-abs(king.col - opp_king_col)


        return (squares_from_center * squares_from_center_factor) + (squares_from_opp_king * squares_from_opp_king_factor)
    

    def get_legal_moves(self):
        """gets all legal moves for the current board state (so takes into account turn, etc).
        Returns list of [ ((sq1 row, sq1 col), (sq2 row, sq2 col, move-type)), ...]
        sorted in order of Engine.move_priority (prioritizes promotions, captures, then open moves)
        to help A/B pruning cut off paths faster
        """
        all_moves_list = []

        for pos in list(self.board.player_layout_dict.keys()):
            self.board.selected_piece = pos
            piece = self.board.player_layout_dict[pos]

            legal_moves = piece.get_legal_moves(self.board.player_layout_dict, self.board.opponent_layout_dict, self.board.en_passant_pieces)
            
            if piece.piece_type == "k":
                legal_moves.extend(self.board.get_castle_moves())

            
            legal_moves = self.board.exclude_check_moves(legal_moves)




            for move in legal_moves:
                all_moves_list.append((pos, move))
        

        all_moves_list = sorted(all_moves_list, key=lambda x: Engine.move_priority[x[1][2]])
        return all_moves_list
    

    def hash_engine_board(self):
        """hashes the engine instance's board and returns that value"""
        self.board.init_hash_dicts()
        hashed_board = hash(self.board)

        return hashed_board

    def get_chess_notation(self, sq1, turn):
        """Converts a (int,int) coordinate into a (letter, int) format (Long Algebraic Notation).
        Considers perspective so that the returned LAN is universal"""
        # (row, col) = (file, rank)
        
        num = -1
        letter_str = ""
        if turn == "white":
            map = {1 : 'a', 2 : 'b', 3 : 'c', 4 : 'd', 5 : 'e', 6 : 'f', 7 : 'g', 8 : 'h'}
            letter_str = map[sq1[1] + 1]
            num = 8 - sq1[0]
        else:
            map = {8 : 'a', 7 : 'b', 6 : 'c', 5 : 'd', 4 : 'e', 3 : 'f', 2 : 'g', 1 : 'h'}
            letter_str = map[sq1[1] + 1]
            num = sq1[0] + 1

        return letter_str + str(num)