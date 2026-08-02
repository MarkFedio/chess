import pygame
from pygame import *
import math

from constants import *

class Piece:
    def __init__(self, name, row, col):
        # name is the whole "black_p" thing, piece_type & color splits it individually
        self.name = name
        self.piece_type = name.split("_")[1]
        self.color = name.split("_")[0]
        self.opposing_color = "black" if self.color == "white" else "white"
        self.row = row
        self.col = col

        self.num_moves = 0
        self.value = self.init_piece_value()
        

    def init_piece_value(self):
        match self.piece_type:
            case "r":
                return 5
            case "n":
                return 3
            case "b":
                return 3
            case "q":
                return 9
            case "p":
                return 1
            case "k" | "x":
                return 0

    # ---------------------
    #     MOVE METHODS
    # ---------------------

    """
    Move letter dictionary (z in a move of the form (row, col, z)):
    o = moving to open square
    c = capturing on square
    e = capture is an en passant
    y = castle (-_-)
    p = promotion
    pc = promotion & capture

    """

    def get_legal_moves(self, layout, en_passant_dict):
        """wrapper function to get the legal moves for any piece this function is called on"""
        moves = []
        if self.piece_type == "p":
            moves = self.get_pawn_moves(layout, en_passant_dict)
        elif self.piece_type == "n":
            moves = self.get_knight_moves(layout)
        elif self.piece_type == "b":
            moves = self.get_bishop_moves(layout)
        elif self.piece_type == "r":
            moves = self.get_rook_moves(layout)
        elif self.piece_type == "q":
            moves = self.get_queen_moves(layout)
        elif self.piece_type == "k":
            moves = self.get_king_moves(layout)
        return moves
        
    def get_pawn_moves(self, layout, en_passant_dict):
        """gets valid moves for the pawn Piece this was called on. Returns a list of 
        tuples in the form (col, row, z), where row/col is the square of the legal move 
        and z denotes a move type (see dict at top of move methods)"""
        
        row = self.row
        col = self.col
        moves = []

        # straight infront
        if (row-1 >= 0):
            if layout[row-1][col].color == "x":
                if (row - 1) == 0:
                    moves.append((row-1, col, "p"))
                else:
                    moves.append((row-1, col, "o"))
        
        # two infront
        if (row-2 >= 0):
            if layout[row-2][col].color == "x" and self.num_moves == 0:
                moves.append((row-2, col, "o"))
        
        # up and left capture
        if (row-1 >= 0 and col-1 >= 0):
            if layout[row-1][col-1].color == self.opposing_color:
                # if promotion too (ends on row 0)
                if (row - 1) == 0:
                    moves.append((row-1, col-1, "pc"))
                else:
                    moves.append((row-1, col-1, "c"))

        # up and right capture
        if (row-1 >= 0 and col+1 <= 7):
            if layout[row-1][col+1].color == self.opposing_color:
                # if promotion too (ends on row 0)
                if (row - 1) == 0:
                    moves.append((row-1, col+1, "pc"))
                else:
                    moves.append((row-1, col+1, "c"))

        return moves + self.get_en_passant_moves(layout, en_passant_dict)
    
    def get_en_passant_moves(self, layout, en_passant_dict):
        """gets valid en passant moves for the pawn Piece this was called on. Returns a list of 
        tuples in the form (col, row, z), where row/col is the square of the legal move 
        and z denotes a move type (see dict at top of move methods)"""
        moves = []
        if self.row == 3:
            # print(f"1: {self.name} to {self.row, self.col + 1} {self.row, self.col + 1}")
            # print(f"2: {self.name} to {self.row, self.col + 1} {self.row, self.col - 1}")
    
            if ((self.col - 1 >= 0) and # bound-check using short circuit evaluation
                (layout[self.row][self.col - 1].piece_type == "p") and 
                (layout[self.row][self.col - 1].color == self.opposing_color) and
                (layout[self.row][self.col - 1].num_moves == 1) and
                # if the current piece is adjacent to the opposite color's potential en passant piece
                ((self.row, self.col - 1) == (en_passant_dict[layout[self.row][self.col - 1].color]))):
                moves.append((self.row - 1, self.col - 1, "e"))
            if ((self.col + 1 <= 7) and 
                (layout[self.row][self.col + 1].piece_type == "p") and 
                (layout[self.row][self.col + 1].color == self.opposing_color) and
                (layout[self.row][self.col + 1].num_moves == 1) and
                ((self.row, self.col + 1) == (en_passant_dict[layout[self.row][self.col + 1].color]))):
                moves.append((self.row - 1, self.col + 1, "e"))
        #print(f"returning en passant moves: {moves}")
        return moves

    def get_knight_moves(self, layout):
        """gets valid moves for the knight Piece this was called on. Returns a list of 
        tuples in the form (col, row, z), where row/col is the square of the legal move 
        and z denotes a move type (see dict at top of move methods)"""
        
        row = self.row
        col = self.col
        moves = []

        # why'd it work first try
        for row_move in (-2, -1, 1, 2):
            for col_move in (-2, -1, 1, 2):
                if abs(row_move) + abs(col_move) != 3:
                    continue
                if (row + row_move < 0 or row + row_move > 7) or (col + col_move < 0 or col + col_move > 7):
                    continue
                if layout[row + row_move][col + col_move].color == "x":
                    moves.append((row + row_move, col + col_move, "o"))
                if layout[row + row_move][col + col_move].color == self.opposing_color:
                    moves.append((row + row_move, col + col_move, "c"))
        return moves

    def get_bishop_moves(self, layout):
        """gets valid moves for the bishop Piece this was called on. Returns a list of 
        tuples in the form (col, row, z), where row/col is the square of the legal move 
        and z denotes a move type (see dict at top of move methods)"""
        
        moves = []
        # why'd it work first try 2

        # up-left
        row_iter = self.row - 1
        col_iter = self.col - 1
        while (row_iter >= 0 and row_iter <= 7) and (col_iter >= 0 and col_iter <= 7):
            if (layout[row_iter][col_iter].color == "x"):
                moves.append((row_iter, col_iter, "o"))
                row_iter -= 1
                col_iter -=1
                continue
            if (layout[row_iter][col_iter].color == self.opposing_color):
                moves.append((row_iter, col_iter, "c"))
                break
            break

        # up-right
        row_iter = self.row - 1
        col_iter = self.col + 1
        while (row_iter >= 0 and row_iter <= 7) and (col_iter >= 0 and col_iter <= 7):
            if (layout[row_iter][col_iter].color == "x"):
                moves.append((row_iter, col_iter, "o"))
                row_iter -= 1
                col_iter +=1
                continue
            if (layout[row_iter][col_iter].color == self.opposing_color):
                moves.append((row_iter, col_iter, "c"))
                break
            break

        # down-left
        row_iter = self.row + 1
        col_iter = self.col - 1
        while (row_iter >= 0 and row_iter <= 7) and (col_iter >= 0 and col_iter <= 7):
            if (layout[row_iter][col_iter].color == "x"):
                moves.append((row_iter, col_iter, "o"))
                row_iter += 1
                col_iter -=1
                continue
            if (layout[row_iter][col_iter].color == self.opposing_color):
                moves.append((row_iter, col_iter, "c"))
                break
            break
        
        # down-right
        row_iter = self.row + 1
        col_iter = self.col + 1
        while (row_iter >= 0 and row_iter <= 7) and (col_iter >= 0 and col_iter <= 7):
            if (layout[row_iter][col_iter].color == "x"):
                moves.append((row_iter, col_iter, "o"))
                row_iter += 1
                col_iter +=1
                continue
            if (layout[row_iter][col_iter].color == self.opposing_color):
                moves.append((row_iter, col_iter, "c"))
                break
            break
        return moves
    
    def get_rook_moves(self, layout):
        """gets valid moves for the rook Piece this was called on. Returns a list of 
        tuples in the form (col, row, z), where row/col is the square of the legal move 
        and z denotes a move type (see dict at top of move methods)"""
        
        # they keep working first try. im done
        #       me when I can copy paste
        moves = []

        # up
        row_iter = self.row - 1
        while (row_iter >= 0 and row_iter <= 7):
            if (layout[row_iter][self.col].color == "x"):
                moves.append((row_iter, self.col, "o"))
                row_iter -= 1
                continue
            if (layout[row_iter][self.col].color == self.opposing_color):
                moves.append((row_iter, self.col, "c"))
                break
            break
    
        # down
        row_iter = self.row + 1
        while (row_iter >= 0 and row_iter <= 7):
            if (layout[row_iter][self.col].color == "x"):
                moves.append((row_iter, self.col, "o"))
                row_iter += 1
                continue
            if (layout[row_iter][self.col].color == self.opposing_color):
                moves.append((row_iter, self.col, "c"))
                break
            break

        # left
        col_iter = self.col - 1
        while (col_iter >= 0 and col_iter <= 7):
            if (layout[self.row][col_iter].color == "x"):
                moves.append((self.row, col_iter, "o"))
                col_iter -= 1
                continue
            if (layout[self.row][col_iter].color == self.opposing_color):
                moves.append((self.row, col_iter, "c"))
                break
            break

        # right
        col_iter = self.col + 1
        while (col_iter >= 0 and col_iter <= 7):
            if (layout[self.row][col_iter].color == "x"):
                moves.append((self.row, col_iter, "o"))
                col_iter += 1
                continue
            if (layout[self.row][col_iter].color == self.opposing_color):
                moves.append((self.row, col_iter, "c"))
                break
            break

        return moves
    
    def get_queen_moves(self, layout):
        """gets valid moves for the queen Piece this was called on. Returns a list of 
        tuples in the form (col, row, z), where row/col is the square of the legal move 
        and z denotes a move type (see dict at top of move methods)"""
        
        # dazit
        return self.get_bishop_moves(layout) + self.get_rook_moves(layout)
    
    def get_king_moves(self, layout):
        """gets valid moves for the king Piece this was called on. Castling handled in
        chess_board.py Returns a list of tuples in the form (col, row, z), where row/col 
        is the square of the legal move and z denotes a move type (see dict at top of move methods)"""

        moves = []
        row = self.row
        col = self.col

        for row_move in (-1, 0, 1):
            for col_move in (-1, 0, 1):
                if (row_move == 0) and (col_move == 0):
                    continue
                if (row + row_move < 0 or row + row_move > 7) or (col + col_move < 0 or col + col_move > 7):
                    continue
                if layout[row + row_move][col + col_move].color == "x":
                    moves.append((row + row_move, col + col_move, "o"))
                if layout[row + row_move][col + col_move].color == self.opposing_color:
                    moves.append((row + row_move, col + col_move, "c"))


                
        return moves
    
