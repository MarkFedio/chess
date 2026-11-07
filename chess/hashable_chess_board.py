from pygame import *
import copy

import chess_board
from chess_piece import Piece
from constants import *

# threefold repititon happens if same position of
    # 1) same player to move, 
    # 2) same possible moves, 
    # 3) same castling/capturing rights
# happens 3 times. This program does not consider en passant or castling moves for #2, or anything in #3, 
# but I think those are such edge cases that it will never matter. Or I'm wrong; idk
# enough about chess to say. But I'm not implementing it regardless.
class Hashable_Board():
    copy_excluded = {"player_layout_hash", "opponent_layout_hash", "mode", "selected_piece"}
    excluded_but_needs_value = {"legal_moves"}
    copy_count = 0
    def __init__(self, board: chess_board.Board):
        # things to hash
        self.player_layout_hash: frozenset[(int, int), str]
        self.opponent_layout_hash: frozenset[(int, int), str]
        self.turn = board.turn

        # not used in hashing, but used by engine
        self.white_material = board.white_material
        self.black_material = board.black_material
        
        self.player_layout_dict: dict[(int, int), Piece] = board.player_layout_dict
        self.opponent_layout_dict: dict[(int, int), Piece] = board.opponent_layout_dict
        self.init_hash_dicts()
        
        self.mode = board.mode # 0 (default) flips the screen after every move, 1 keeps orientation the same
        self.moves_since_capture = board.moves_since_capture
        
        self.promotion_square = board.promotion_square
        self.selected_piece = board.selected_piece

        # complete list of possible moves in form [ ((sq1 row, sq1 col), (sq2 row, sq2 col, move-type)), ...]
        # NOTE: Different format than Board's legal_moves because this stores 
        # starting piece's square -> end square (and move type), whereas Board's just holds end square (and move type)
        # and gets the starting piece's square from selected_piece
        self.legal_moves: dict[tuple[int, int], tuple[int, int, str]] = []
        self.en_passant_pieces = board.en_passant_pieces

        # not used
        #
        self.king_moves = 0
        self.king_moves_lost = 0

    
    def init_hash_dicts(self):
        """Converts layout dicts into form frozenset[(int, int), str] so
        that they can be hashed"""
        self.player_layout_hash = frozenset((pos, piece.name) for pos, piece in self.player_layout_dict.items())
        self.opponent_layout_hash = frozenset((pos, piece.name) for pos, piece in self.opponent_layout_dict.items())

    
    def __eq__(self, other):
        if not isinstance(other, Hashable_Board):
            return False
        return ((self.turn == other.turn)
                and (self.player_layout_hash == other.player_layout_hash)
                and (self.opponent_layout_hash == other.opponent_layout_hash))
    
    def __hash__(self):
        return hash((self.turn, self.player_layout_hash, self.opponent_layout_hash))

    # -------------------------------------------
    # Board methods copied here for use in engine (make sure to update here if they change in Board).
    # Any differences in methods here vs. Board are noted above the method def
    # -------------------------------------------

    # altered in here vs Board because of no engine stuff
    # TODO: handle draw, stale/checkmate and end of game stuff
    def update_board(self, turn_num=-1):
        """  update values for the board (like orientation, turn, etc). Default turnNum
                switches the turn
        """
        self.change_turn(turn_num)
        self.flip_layout_dicts()
        self.flip_en_passant_pieces()
        self.selected_piece = (-1, -1)
        self.legal_moves.clear()


    def change_turn(self, turn_num):
        """Helper function to swap turn instance variable (defaults to swapping, but turn can be specified)"""
        if turn_num == -1:
            if self.turn == WHITE_TURN:
                self.turn = BLACK_TURN
            else:
                self.turn = WHITE_TURN
        else:
            self.turn = turn_num

    def flip_layout_dicts(self):
        """updates layout dicts to reflect a 180 degree rotation of the board for when
        the player turn changes"""
        
        new_player_layout_dict = {}
        new_opponent_layout_dict = {}

        for pos in self.player_layout_dict.keys():
            row = 7 - pos[0]
            col = 7 - pos[1]
            curr_piece = self.player_layout_dict[pos]
            curr_piece.row = row
            curr_piece.col = col
            new_player_layout_dict[(row, col)] = curr_piece
        self.player_layout_dict.clear()
        self.player_layout_dict.update(new_player_layout_dict)

        for pos in self.opponent_layout_dict.keys():
            row = 7 - pos[0]
            col = 7 - pos[1]
            curr_piece = self.opponent_layout_dict[pos]
            curr_piece.row = row
            curr_piece.col = col
            new_opponent_layout_dict[(row, col)] = curr_piece
        self.opponent_layout_dict.clear()
        self.opponent_layout_dict.update(new_opponent_layout_dict)

        self.player_layout_dict, self.opponent_layout_dict = self.opponent_layout_dict, self.player_layout_dict

    def flip_en_passant_pieces(self):
        """returns a 180 degree rotated en passant dictionary"""
        if self.en_passant_pieces["white"] != (-1, -1):
            new_en_passant_piece = (7 - self.en_passant_pieces["white"][0], 7 - self.en_passant_pieces["white"][1])
            self.en_passant_pieces["white"] = new_en_passant_piece
        if self.en_passant_pieces["black"] != (-1, -1):
            new_en_passant_piece = (7 - self.en_passant_pieces["black"][0], 7 - self.en_passant_pieces["black"][1])
            self.en_passant_pieces["black"] = new_en_passant_piece

    # altered in here vs Board because no need to track captured pieces
    def move_piece(self, sq1, sq2, move_type):
        """moves the piece on square1 to square2. Move validation must happen prior to this function.
        Handles en passant logic and castling logic. Calls update board."""


        sq1_row, sq1_col = sq1
        sq2_row, sq2_col = sq2


        # if capture, add the captured piece to the captured_pieces list
        if move_type == "c" or move_type == "pc":
            # if self.opponent_layout_dict[(sq2_row, sq2_col)].piece_type == "k":
            #     print(f"\n\n({sq1}), ({sq2}, {move_type}) is capturing {self.opponent_layout_dict[(sq2_row, sq2_col)].name}:")
            #     self.print_board()

            # this should work even though it looks wrong, because opp_layout_dict is always going to
            # be the opposite color of whatever is on the other side of the -= 
            if self.turn == "white":
                self.black_material -= self.opponent_layout_dict[(sq2_row, sq2_col)].value
            else:
                self.white_material -= self.opponent_layout_dict[(sq2_row, sq2_col)].value

        if move_type == "e":
            if self.turn == "white":
                self.black_material -= self.opponent_layout_dict[(sq2_row + 1, sq2_col)].value
            else:
                self.white_material -= self.opponent_layout_dict[(sq2_row + 1, sq2_col)].value
            
        # get the piece that's moving 
        if (sq1_row, sq1_col) in self.player_layout_dict:
            curr_piece = self.player_layout_dict[(sq1_row, sq1_col)]
        else:
            print(f"catastrophic failure in move_piece")

        # en passant logic
        #  if it's a pawn and moved two rows (can only happen on first move), that
        #  pawn is eligible to be captured by en passant. Else, reset en passant for this color
        if curr_piece.piece_type == "p" and sq1_row - sq2_row == 2:
            self.en_passant_pieces[curr_piece.color] = (sq2_row, sq2_col)
        else:
            self.en_passant_pieces[curr_piece.color] = (-1, -1)

        # move piece on square 1 to square 2
        self.player_layout_dict[(sq2_row, sq2_col)] = curr_piece
        curr_piece.row = sq2_row
        curr_piece.col = sq2_col
        curr_piece.num_moves += 1
        if move_type == "c" or move_type == "pc":
            self.opponent_layout_dict.pop((sq2_row, sq2_col))

        # capturing with en passant removes the piece below (row + 1) where the pawn ends up
        if move_type == "e":
            self.opponent_layout_dict.pop((sq2_row + 1, sq2_col))

        # castling logic
        # white turn
        # if king-side, king goes to (7,6) with rook on (7,7) moving to (7,5)
        # if queen-side, king goes to (7,2) with rook on (7,0) moving to (7,3)
        if move_type == "y" and self.turn == PLAYER_COLOR:
            # king-side
            if sq2 == (7,6):    

                self.player_layout_dict[(7, 5)] = self.player_layout_dict.pop((7, 7))
                self.player_layout_dict[(7, 5)].row = 7
                self.player_layout_dict[(7, 5)].col = 5
                self.player_layout_dict[(7, 5)].num_moves += 1 # not technically a rook move but idt this matters
            if sq2 == (7,2):
                self.player_layout_dict[(7, 3)] = self.player_layout_dict.pop((7, 0))
                self.player_layout_dict[(7, 3)].row = 7
                self.player_layout_dict[(7, 3)].col = 3
                self.player_layout_dict[(7, 3)].num_moves += 1

        # mirrored logic for black
        if move_type == "y" and self.turn == OPPOSING_COLOR:
            if sq2 == (7,1):    
                self.player_layout_dict[(7, 2)] = self.player_layout_dict.pop((7, 0))
                self.player_layout_dict[(7, 2)].row = 7
                self.player_layout_dict[(7, 2)].col = 2
                self.player_layout_dict[(7, 2)].num_moves += 1

            if sq2 == (7,5):
                self.player_layout_dict[(7, 4)] = self.player_layout_dict.pop((7, 7))
                self.player_layout_dict[(7, 4)].row = 7
                self.player_layout_dict[(7, 4)].col = 4
                self.player_layout_dict[(7, 4)].num_moves += 1

        # sq1 becomes empty as long as sq1 and sq2 aren't the same... the only time they are the
        # same (I think) is when the king "moves" in place to see if it's currently in check 
        if (sq1_row, sq1_col) != (sq2_row, sq2_col):
            self.player_layout_dict.pop((sq1_row, sq1_col))

        # reads much better without distributing the not. Shoutout DeMorgan tho
        if not (move_type == "c" or move_type == "e"):
            self.moves_since_capture += 1
        else:
            self.moves_since_capture = 0
        self.update_board()

    def reverse_move(self, sq1, sq2, move_type):
        """
        Reverses the move in the parameters. To undo move_piece(x,y,z), you do
        reverse_move(x,y,z). Updates board pieces as well as all required object attributes. Used
        to avoid deepcopying boards during engine calculations and exclude_check_moves().
        Currently only reverses "o" moves.
        I think (0_0) the only thing that doesn't get reversed is the
                self.selected_piece = (-1, -1)
        in update_board(), but that shouldn't matter because you need to update those to move a piece again.
        """

        sq1_row = 7 - sq1[0]
        sq1_col = 7 - sq1[1]
        sq2_row = 7 - sq2[0]
        sq2_col = 7 - sq2[1]
        if move_type == "o":
            # use opponent dict because the turn changed since the move_piece() call
            #print(f"moving piece {self.opponent_layout_dict[(sq2_row, sq2_col)].name} at {sq2_row}, {sq2_col} back to {sq1_row}, {sq1_col}")
            self.opponent_layout_dict[(sq1_row, sq1_col)] = self.opponent_layout_dict[(sq2_row, sq2_col)]
            self.opponent_layout_dict[(sq1_row, sq1_col)].row = sq1_row
            self.opponent_layout_dict[(sq1_row, sq1_col)].col = sq1_col
            self.opponent_layout_dict[(sq1_row, sq1_col)].num_moves -= 1

            if (sq1_row, sq1_col) != (sq2_row, sq2_col):
                self.opponent_layout_dict.pop((sq2_row, sq2_col))

        self.change_turn(-1)
        self.flip_layout_dicts()
        self.flip_en_passant_pieces()

    def exclude_check_moves(self, moves):
        # print(f"\n\n")
        # for pos, piece in self.player_layout_dict.items():
        #     print(f"{piece.name} at {pos}")
        """takes in a list of currently valid moves but scans through them to see if any of them would
        put this color's king in check and removes those moves."""

        #print(f"exclude_check_moves moves: {moves}")
        # could definitely store king_row/col as an instance variable and just update throughout for
        # constant time access here, but that's the least of the problems given the hot
        # mess of what follows this loop
        for pos, piece in self.player_layout_dict.items():
            if piece.piece_type == "k":
                king_row = pos[0]
                king_col = pos[1]
                break

        
        selected_row = self.selected_piece[0]
        selected_col = self.selected_piece[1]
        # print(f"selected_row/col: {selected_row}, {selected_col}")
        # loop through list of moves backwards so that they can be deleted if needed
        for i in reversed(range(len(moves))):
            move = moves[i]

            # if it's an "o" move, use reverse_move() to undo. Otherwise, will need to copy it.
            # Terrible modularity, and I know I could just have a variable point to either self or check_board,
            # but I don't really care :P
            if move[2] == "o":
                self.board_simulation = True
                
                selected_piece = self.player_layout_dict[(selected_row, selected_col)]
                self.move_piece((selected_row, selected_col), (move[0], move[1]), move[2])
                if selected_piece.piece_type == "k":
                    king_row = move[0]
                    king_col = move[1]

                for piece in self.player_layout_dict.values():
                    legal_moves_set = piece.get_legal_moves_set(self.player_layout_dict, self.opponent_layout_dict,
                                                                self.en_passant_pieces)
                    if ((7-king_row, 7-king_col, "c") in legal_moves_set or
                        (7-king_row, 7-king_col, "e") in legal_moves_set or
                        (7-king_row, 7-king_col, "pc") in legal_moves_set):
                            del moves[i]
                            break
                    
                self.reverse_move((selected_row, selected_col), (move[0], move[1]), move[2])
                self.board_simulation = False
            else:  
                # simulate board after this move
                check_board = copy.deepcopy(self)            
                check_board.board_simulation = True
                
                
                selected_piece = check_board.player_layout_dict[(selected_row, selected_col)]
                #print(f"\n{selected_piece.name} on {selected_piece.row, selected_piece.col} doing {move}\n")
                check_board.move_piece((selected_piece.row, selected_piece.col), (move[0], move[1]), move[2])

                # update king pos if that move was a king move. move[0]/[1] have the user POV coords
                # while selected.row/col have the simulated boards coords. The final if before the del
                # accounts for the flip already with a 7 -, so use user POV coords here
                if selected_piece.piece_type == "k":
                    king_row = move[0]
                    king_col = move[1]

                # look at every piece in simulated board
                # when moving black piece, piece is white perspective
                for piece in check_board.player_layout_dict.values():
                    
                    legal_moves_set = piece.get_legal_moves_set(check_board.player_layout_dict, check_board.opponent_layout_dict,
                                                                    check_board.en_passant_pieces)
                    if ((7-king_row, 7-king_col, "c") in legal_moves_set or
                        (7-king_row, 7-king_col, "e") in legal_moves_set or
                        (7-king_row, 7-king_col, "pc") in legal_moves_set):
                            del moves[i]
                            break

        self.selected_piece = (selected_row, selected_col)
        return moves


    def get_castle_moves(self):
        if self.turn == WHITE_TURN:
            king_row = 7
            king_col = 4
        else:
            king_row = 7
            king_col = 3


        # only continue if the king is where it needs to be for castling
        if (king_row, king_col) not in self.player_layout_dict or self.player_layout_dict[(king_row, king_col)].piece_type != "k":
            return []
        if (self.selected_piece != (king_row, king_col)):
            return []
        

        moves = []
        individual_castle = []
        
        # necessary to change the direction of castling (eg: white king side castling moves right
        # but black king side castling moves left)
        if self.turn == PLAYER_COLOR:
            DIRECTION = 1
        else:
            DIRECTION = -1
        # king side castling
        if self.player_layout_dict[(king_row, king_col)].num_moves == 0:
            if (7, king_col + DIRECTION*3) in self.player_layout_dict:
                potential_rook = self.player_layout_dict[(7, king_col + DIRECTION*3)]
                if ((7, king_col + DIRECTION*1) not in self.player_layout_dict
                    and (7, king_col + DIRECTION*2) not in self.player_layout_dict
                    and potential_rook.color == self.turn
                    and potential_rook.piece_type == "r"
                    and potential_rook.num_moves == 0):
                    # first one leaves the king in place, but that's used to check if the king is currently in check
                    individual_castle.append((7, king_col, "o"))
                    individual_castle.append((7, king_col + (DIRECTION)*1, "o"))
                    individual_castle.append((7, king_col + (DIRECTION)*2, "o"))
                    individual_castle = self.exclude_check_moves(individual_castle)
                    # ie if no moves put the king in check
                    if len(individual_castle) == 3:
                        individual_castle.clear()
                        individual_castle.append((7, king_col + (DIRECTION)*2, "y"))
                    else:
                        individual_castle.clear()

        moves.extend(individual_castle)
        individual_castle.clear()

        # queen side castling
        if self.player_layout_dict[(king_row, king_col)].num_moves == 0:
            if (7, king_col - DIRECTION*4) in self.player_layout_dict:
                potential_rook = self.player_layout_dict[(7, king_col - DIRECTION*4)]
                if ((7, king_col - DIRECTION*1) not in self.player_layout_dict
                    and (7, king_col - DIRECTION*2) not in self.player_layout_dict
                    and (7, king_col - DIRECTION*3) not in self.player_layout_dict
                    and potential_rook.color == self.turn
                    and potential_rook.piece_type == "r"
                    and potential_rook.num_moves == 0):

                    individual_castle.append((7, king_col, "o"))
                    individual_castle.append((7, king_col - (DIRECTION)*1, "o"))
                    individual_castle.append((7, king_col - (DIRECTION)*2, "o"))
                    individual_castle = self.exclude_check_moves(individual_castle)
                    # ie if no moves put the king in check
                    if len(individual_castle) == 3:
                        individual_castle.clear()
                        individual_castle.append((7, king_col - (DIRECTION)*2, "y"))
                    else:
                        individual_castle.clear()

        moves.extend(individual_castle)
        individual_castle.clear()
        return moves
    
    def check_draw_stalemate_checkmate(self):
        """Checks if there is a stalemate or checkmate on the board. Board
        variables are passed in from Board -> Engine -> here. Does not check
        for 3 move repitition or 50 move rule."""
        
        # Insufficient material logic
        white_pieces, black_pieces = self.count_pieces()
        white_len = len(white_pieces)
        black_len = len(black_pieces)
        if "k" in white_pieces and "k" in black_pieces: # Catastrophic failure if not
            # king vs king
            if white_pieces["k"] == 1 and white_len == 1 and black_pieces["k"] == 1 and black_len == 1:
                return DRAW_INSUFFICIENT_MATERIAL_ID 

            # king and bishop vs king
            if "b" in white_pieces:
                if white_pieces["k"] == 1 and white_pieces["b"] == 1 and white_len == 2 and black_pieces["k"] == 1 and black_len == 1:
                    return DRAW_INSUFFICIENT_MATERIAL_ID 
            if "b" in black_pieces:
                if white_pieces["k"] == 1 and white_len == 1 and black_pieces["k"] == 1 and black_pieces["b"] == 1 and black_len == 2:
                    return DRAW_INSUFFICIENT_MATERIAL_ID 
             
            # king and knight vs king
            if "n" in white_pieces:
                if white_pieces["k"] == 1 and white_pieces["n"] == 1 and white_len == 2 and black_pieces["k"] == 1 and black_len == 1:
                    return DRAW_INSUFFICIENT_MATERIAL_ID 
            if "n" in black_pieces:
                if white_pieces["k"] == 1 and white_len == 1 and black_pieces["k"] == 1 and black_pieces["n"] == 1 and black_len == 2:
                    return DRAW_INSUFFICIENT_MATERIAL_ID 

            # king and bishop vs king and bishop (if both bishops are on same color squares (bruh))
            if "b" in white_pieces and "b" in black_pieces:
                if (white_pieces["k"] == 1 and white_pieces["b"] == 1 and white_len == 2 and 
                    black_pieces["k"] == 1 and black_pieces["b"] == 1 and black_len == 2):
                    # square colors...
                    first_color = -1
                    second_color = -1

                    for pos, piece in self.player_layout_dict.items():
                        if piece.piece_type == "b":
                            first_color = (pos[0] + pos[1]) % 2
                            break
                    for pos, piece in self.opponent_layout_dict.items():
                        if piece.piece_type == "b":
                            second_color = (pos[0] + pos[1]) % 2
                            break

                    if first_color == second_color:
                        return DRAW_INSUFFICIENT_MATERIAL_ID
        # End insufficient material logic

        # Stalemate and checkmate logic
        curr_piece_possible_moves = []
        found_valid_move = False
        king_row = -1
        king_col = -1

        # makes copy of keys because reverse_move() in exclude_check_moves() re-inserts pieces
        for pos in list(self.player_layout_dict.keys()):
            piece = self.player_layout_dict[pos]
            self.selected_piece = (pos)
            curr_piece_possible_moves.extend(piece.get_legal_moves(self.player_layout_dict, self.opponent_layout_dict, self.en_passant_pieces))
            if piece.piece_type == "k":
                # store king pos for later
                king_row = pos[0]
                king_col = pos[1]
                curr_piece_possible_moves.extend(self.get_castle_moves())
            curr_piece_possible_moves = self.exclude_check_moves(curr_piece_possible_moves)
            if len(curr_piece_possible_moves) > 0:
                found_valid_move = True
                #break
            curr_piece_possible_moves.clear()

        self.selected_piece = (-1, -1)
        if found_valid_move:
            return VALID_MOVE_EXISTS_ID
        else:
            self.selected_piece = (king_row, king_col)
            king_moves = [(king_row, king_col, "o")]
            king_moves = self.exclude_check_moves(king_moves)
            if (len(king_moves) == 1):
                return STALEMATE_ID
            elif (len(king_moves) == 0):
                return CHECKMATE_ID
        
        # End stalemate and checkmate logic

    def count_pieces(self):
        """Counts the number and types of pieces for both colors. Returns a tuple with 2 dicts. Ex:
        (
            {k : count, q : count, p: count, etc for all pieces},
            {k : count, q : count, p: count, etc for all pieces}
        )
        where the first dict is white and the second dict is black"""
        white_dict = {}
        black_dict = {}

        for piece in self.player_layout_dict.values():
            if piece.color == "white":
                if piece.piece_type in white_dict:
                    white_dict[piece.piece_type] += 1
                else:
                    white_dict[piece.piece_type] = 1
            else: # must be black (or catastrophic failure)
                if piece.piece_type in black_dict:
                    black_dict[piece.piece_type] += 1
                else:
                    black_dict[piece.piece_type] = 1
        for piece in self.opponent_layout_dict.values():
            if piece.color == "white":
                if piece.piece_type in white_dict:
                    white_dict[piece.piece_type] += 1
                else:
                    white_dict[piece.piece_type] = 1
            else: # must be black (or catastrophic failure)
                if piece.piece_type in black_dict:
                    black_dict[piece.piece_type] += 1
                else:
                    black_dict[piece.piece_type] = 1

        return (white_dict, black_dict)
    
    def print_board(self):
        """Prints string layout of board for debugging with perspective of white pieces on bottom"""
        if self.turn == "white":
            print(f"     0       1       2       3       4       5       6       7    ")
            for row in range(8):
                print(f"{row} ", end="")
                for col in range(8):
                    pos = (row, col)
                    if pos in self.player_layout_dict:
                        print(f"{self.player_layout_dict[pos].name} ", end="")
                    elif pos in self.opponent_layout_dict:
                        print(f"{self.opponent_layout_dict[pos].name} ", end="")
                    else:
                        print(f"  x_x   ", end="")
                print(f"")
        else:
            print(f"     0       1       2       3       4       5       6       7    ")
            for row in reversed(range(8)):
                print(f"{7-row} ", end="")
                for col in reversed(range(8)):
                    pos = (row, col)
                    if pos in self.player_layout_dict:
                        print(f"{self.player_layout_dict[pos].name} ", end="")
                    elif pos in self.opponent_layout_dict:
                        print(f"{self.opponent_layout_dict[pos].name} ", end="")
                    else:
                        print(f"  x_x   ", end="")
                print(f"")

    def __deepcopy__(self, dict):
        if id(self) in dict:
            return id(dict[self])

        # prevents __init__ from running so init funcs don't get called for this Board (namely loading images)
        new_board = Hashable_Board.__new__(Hashable_Board)
        dict[id(self)] = new_board

        # TODO: add other uneccesary fields, and store these two sets as class level attributes
        # so they don't get recursively stored...
        #excluded = {"engine", "piece_images", "captured_piece_images", "legal_moves", "font"}
        # for ex: a Board copy's legal_moves field gets used, but it doesn't need the value
        # from the original Board, just for the field to exist.
        #excluded_but_needs_value = {"legal_moves"}
        for key, value in self.__dict__.items():
            if key not in Hashable_Board.copy_excluded:
                setattr(new_board, key, copy.deepcopy(value, dict))
            if key in Hashable_Board.excluded_but_needs_value:
                setattr(new_board, key, [])
        return new_board