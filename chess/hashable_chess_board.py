from pygame import *
import copy

from chess_board import Board
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
    def __init__(self, board: Board):
        # things to hash
        self.tuple_layout = self.init_string_layout(board.layout)
        self.turn = board.turn

        # not used in hashing, but used by engine
        self.player_material = 0
        self.opponent_material = 0
        self.layout = board.layout
        self.mode = board.mode # 0 (default) flips the screen after every move, 1 keeps orientation the same
        self.game_state = board.game_state
        self.moves_since_capture = board.moves_since_capture
        self.board_simulation = False #board.board_simulation # is this board a simulation (used in exclude_check_moves())
        self.row_range = range(8) 
        self.col_range = range(8) 

        self.board_repetition_dict = board.board_repetition_dict
        
        
        self.promotion_square = board.promotion_square
        self.selected_piece = board.selected_piece

        # dict of (sq1 row, sq1 col) : [(sq2 row, sq2 col, move_type)
        # NOTE: Different format than Board's legal_moves because this stores 
        # starting piece's square -> end square (and move type), whereas Board's just holds end square (and move type)
        # and gets the starting piece's square from selected_piece
        self.legal_moves: dict[tuple[int, int], tuple[int, int, str]] = []
        self.en_passant_pieces = board.en_passant_pieces

    
    def init_string_layout(self, piece_layout):
        """Converts 2D Piece array into a tuple of tuples of strings so it's hashable"""
        string_layout = [[None for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for col in range(8):
                string_layout[row][col] = piece_layout[row][col].name
        tuple_layout = tuple(tuple(row) for row in string_layout)
        return tuple_layout
    
    def __eq__(self, other):
        if not isinstance(other, Hashable_Board):
            return False
        return (self.turn == other.turn) and (self.tuple_layout == other.tuple_layout)
    
    def __hash__(self):
        return hash((self.tuple_layout, self.turn))

    # -------------------------------------------
    # Board methods copied here for use in engine (make sure to update here if they change in Board).
    # Any differences in methods here vs. Board are noted above the method def
    # -------------------------------------------

    # altered in here vs Board because of no engine
    # TODO: handle draw, stale/checkmate and end of game stuff
    def update_board(self, turn_num=-1):
        """  update values for the board (like orientation, turn, etc). Default turnNum
                switches the turn
        """
        self.change_turn(turn_num)
        self.layout = self.flip_board()
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

    def flip_board(self):
        """returns a layout to reflect a 180 degree rotation of the board for when
        the player turn changes"""
        new_board = copy.deepcopy(self.layout)
        for row in self.row_range:
            for col in self.row_range:
                new_board[row][col] = self.layout[7-row][7-col]
                # update Piece coordinate
                new_board[row][col].row = row
                new_board[row][col].col = col
        return new_board

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
    
            # NOTE: commented out from Board's move_piece
            # if move_type == "c" or move_type == "e" or move_type == "pc":
            #     self.captured_pieces.append(self.layout[sq2_row][sq2_col].name)
                
            # en passant logic
            # check if piece is a color
            #   if it's a pawn and moved two rows (can only happen on first move), that
            #   pawn is eligible to be captured by en passant. Else, reset en passant for this color
            if (self.layout[sq1_row][sq1_col].color == "white"):
                if (self.layout[sq1_row][sq1_col].piece_type == "p" and sq1_row - sq2_row == 2):
                    self.en_passant_pieces["white"] = (sq2_row, sq2_col)
                else:
                    self.en_passant_pieces["white"] = (-1, -1)
            if (self.layout[sq1_row][sq1_col].color == "black"):
                if (self.layout[sq1_row][sq1_col].piece_type == "p" and sq1_row - sq2_row == 2):
                    self.en_passant_pieces["black"] = (sq2_row, sq2_col)
                else:
                    self.en_passant_pieces["black"] = (-1, -1)                     
    
            self.layout[sq2_row][sq2_col] = self.layout[sq1_row][sq1_col]
            # the piece that was initially in sq1...
            self.layout[sq2_row][sq2_col].row = sq2_row
            self.layout[sq2_row][sq2_col].col = sq2_col
            self.layout[sq2_row][sq2_col].num_moves += 1
    
            # capturing with en passant removes the piece below (row + 1) where the pawn ends up
            if move_type == "e":
                self.layout[sq2_row + 1][sq2_col] = Piece("x_x", sq2_row + 1, sq2_col)
    
            # castling logic
            # white turn
            # if king-side, king goes to (7,6) with rook on (7,7) moving to (7,5)
            # if queen-side, king goes to (7,2) with rook on (7,0) moving to (7,3)
            if move_type == "y" and self.turn == PLAYER_COLOR:
                # king-side
                if sq2 == (7,6):    
                    self.layout[7][5] = self.layout[7][7]
                    self.layout[7][7] = Piece("x_x", sq1_row, sq1_col)
                    self.layout[7][5].row = 7
                    self.layout[7][5].col = 5
                    self.layout[7][5].num_moves += 1 # not technically a rook move but idt this matters
                if sq2 == (7,2):
                    self.layout[7][3] = self.layout[7][0]
                    self.layout[7][0] = Piece("x_x", sq1_row, sq1_col)
                    self.layout[7][3].row = 7
                    self.layout[7][3].col = 3
                    self.layout[7][3].num_moves += 1
            # mirrored logic for black
            if move_type == "y" and self.turn == OPPOSING_COLOR:
                if sq2 == (7,1):    
                    self.layout[7][2] = self.layout[7][0]
                    self.layout[7][0] = Piece("x_x", sq1_row, sq1_col)
                    self.layout[7][2].row = 7
                    self.layout[7][2].col = 2
                    self.layout[7][2].num_moves += 1 # not technically a rook move but idt this matters
                if sq2 == (7,5):
                    self.layout[7][4] = self.layout[7][7]
                    self.layout[7][7] = Piece("x_x", sq1_row, sq1_col)
                    self.layout[7][4].row = 7
                    self.layout[7][4].col = 4
                    self.layout[7][4].num_moves += 1
    
            # ... and sq1 always becomes empty
            self.layout[sq1_row][sq1_col] = Piece("x_x", sq1_row, sq1_col)
    
            # reads much better without distributing the not. Shoutout DeMorgan tho
            if not (move_type == "c" or move_type == "e"):
                self.moves_since_capture += 1
            else:
                self.moves_since_capture = 0
            self.update_board()

    def exclude_check_moves(self, moves):
        """takes in a list of currently valid moves but scans through them to see if any of them would
        put this color's king in check and removes those moves."""
        for row in self.row_range:
            for col in self.row_range:
                if (self.layout[row][col].color == self.turn and
                    self.layout[row][col].piece_type == "k"):
                        king_row = row
                        king_col = col
        
        # loop through list of moves backwards so that they can be deleted if needed
        for i in reversed(range(len(moves))):
            # sometimes a move results in a check from multiple opposing pieces. Only remove that move once
            removed_this_move = False
            move = moves[i]
            # simulate board after this move
        
            check_board = copy.deepcopy(self)            
            check_board.board_simulation = True

            selected_piece = check_board.layout[check_board.selected_piece[0]][check_board.selected_piece[1]]
            #print(f"\n{selected_piece.name} on {selected_piece.row, selected_piece.col} doing {move}\n")
            check_board.move_piece((selected_piece.row, selected_piece.col), (move[0], move[1]), move[2])

            # update king pos if that move was a king move. move[0]/[1] have the user POV coords
            # while selected.row/col have the simulated boards coords. The final if before the del
            # accounts for the flip already with a 7 -, so use user POV coords here
            if selected_piece.piece_type == "k":
                king_row = move[0]
                king_col = move[1]

            # look at every piece in simulated board
            for row in self.row_range:
                for col in self.row_range:
                    piece = check_board.layout[row][col]
                    # we just want pieces of opponent color (turn color of simulated board)
                    if piece.color != check_board.turn:
                        continue
                    # get all legal moves for the curr piece and see if any of them can attack the king
                    check_board.legal_moves = piece.get_legal_moves(check_board.layout, check_board.en_passant_pieces)
                    for that_move in check_board.legal_moves:
                        #print(f"{piece.name} on {7-piece.row, 7-piece.col} doing move {(7-that_move[0], 7-that_move[1])}")
                        if ((7 - that_move[0], 7 - that_move[1]) == (king_row, king_col) and not removed_this_move):
                            # print(f"removing check move {move} from {piece.name} on {7-piece.row, 7-piece.col}")
                            del moves[i]
                            removed_this_move = True

        return moves

    def get_castle_moves(self):
            for row in self.row_range:
                for col in self.row_range:
                    if (self.layout[row][col].color == self.turn and
                        self.layout[row][col].piece_type == "k"):
                            king_row = row
                            king_col = col
            # only continue if this piece is the king
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
            if self.layout[king_row][king_col].num_moves == 0:
                potential_rook = self.layout[7][king_col + (DIRECTION)*3]
                if (self.layout[7][king_col + (DIRECTION)*1].color == "x" and self.layout[7][king_col + (DIRECTION)*2].color == "x" and
                    potential_rook.color == self.turn and potential_rook.piece_type == "r" and potential_rook.num_moves == 0):
                    
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
            if self.layout[king_row][king_col].num_moves == 0:
                potential_rook = self.layout[7][king_col - (DIRECTION)*4]
                if (self.layout[7][king_col - (DIRECTION)*1].color == "x" and self.layout[7][king_col - (DIRECTION)*2].color == "x" and self.layout[7][king_col - (DIRECTION)*3].color == "x" and
                    potential_rook.color == self.turn and potential_rook.piece_type == "r" and potential_rook.num_moves == 0):
                    
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

        
        