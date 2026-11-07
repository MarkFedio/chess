import pygame
from pygame import *
import math
import copy

from chess_piece import Piece
import hashable_chess_board
import chess_engine as chess_engine
from constants import *

class Board():
    # Output move files (engine_file for use in this program's read_moves_file(), lan_file for external use)
    engine_file = "engine_moves_output.txt"
    lan_file = "lan_move_output.txt"

    def __init__(self, mode, engine=None):
        # stores how many points of material each player has. Initialized in init_pieces_array()
        self.white_material = 0
        self.black_material = 0
        self.player_layout_dict, self.opponent_layout_dict = self.init_pieces_array(INITIAL_STRING_LAYOUT)
        self.player_layout_dict: dict[(int, int), Piece]
        self.opponent_layout_dict: dict[(int, int), Piece]

        # internal stuff (idrk man)
        self.mode = mode # 0 (default) flips the screen after every move, 1 keeps orientation the same
        self.game_state = 0
        self.moves_since_capture = 0
        # is this board a simulation (used in exclude_check_moves())
        self.board_simulation = False 
        self.turn = WHITE_TURN

        self.board_repetition_dict = {}
        
        # useless (but used :P) stuff
        self.row_range = range(8) 
        self.col_range = range(8) 
        
        # move stuff
        # first two values are the end square of where a pawn is trying to move to promote, and the string
        # is the move type (either p or pc)
        self.promotion_square = (-1, -1, "")
        self.selected_piece = (-1, -1)
        self.legal_moves: list[tuple[int, int, str]] = []
        # denotes a color's pawn who can be taken by en passant next turn
        self.en_passant_pieces = {"white": (-1, -1), "black": (-1, -1)}

        # holds something like:
        # ({k : count, q : count, p: count, etc for all pieces},
        # {k : count, q : count, p: count, etc for all pieces})
        # where the first dict is white and the second dict is black
        self.count_pieces_dict = {}

        

        # tracks pieces that are captured. Piece names get appended to create a cumulative list
        self.captured_pieces = []

        # visual stuff
        self.font = pygame.font.SysFont("georgia", 12)
        self.piece_images: dict[str, pygame.Surface] = self.init_piece_images()
        self.piece_images_width
        self.piece_images_height

        self.captured_piece_images: dict[str, pygame.Surface] = self.init_captured_piece_images()
        self.captured_piece_images_width
        self.captured_piece_images_height

        self.engine: chess_engine.Engine_Process = engine

        
    
    def init_pieces_array(self, string_layout):
        """takes in 2D array of a string representation of the board and 
        returns two dicts: one for each player with their pieces. Also
        initializes the two points of material variables """
        player_layout = {}
        opponent_layout = {}
        for row in range(8):
            for col in range(8):
                curr_piece = Piece(string_layout[row][col], row, col)
                if curr_piece.color == "white":
                    player_layout[(row, col)] = curr_piece
                    self.white_material += curr_piece.value
                elif curr_piece.color == "black":
                    opponent_layout[(row, col)] = curr_piece
                    self.black_material += curr_piece.value

        return player_layout, opponent_layout
    
    def init_piece_images(self):
        """Caches the piece images as surfaces into the self.piece_images dict"""
        self.piece_images = {}
        piece_names = ["white_r", "white_n", "white_b", "white_q", "white_k", "white_p",
                            "black_r", "black_n", "black_b", "black_q", "black_k", "black_p"]

        self.piece_images_width = round(SQUARE_SIZE*.8)
        self.piece_images_height = round(SQUARE_SIZE*.8)
        for name in piece_names:
            self.piece_images[name] = pygame.image.load(name + ".png").convert_alpha()
            self.piece_images[name] = transform.scale(self.piece_images[name], (self.piece_images_width, 
                                                                                self.piece_images_height))
            
        return self.piece_images

    def init_captured_piece_images(self):
        """Caches the captured piece images as surfaces into the self.captured_piece_images dict.
        Equivalent to init_piece_images, just with smaller piece dimensions (I think it's better to
        cache two different sizes than cache one size and do a transformation each time)"""
        self.captured_piece_images = {}
        piece_names = ["white_r", "white_n", "white_b", "white_q", "white_k", "white_p",
                            "black_r", "black_n", "black_b", "black_q", "black_k", "black_p"]

        self.captured_piece_images_width = math.floor(SCREEN_HEIGHT/16)
        self.captured_piece_images_height = math.floor(SCREEN_HEIGHT/16)
        for name in piece_names:
            self.captured_piece_images[name] = pygame.image.load(name + ".png").convert_alpha()
            self.captured_piece_images[name] = transform.scale(self.piece_images[name], (self.captured_piece_images_width, 
                                                                                         self.captured_piece_images_height))
            
        return self.captured_piece_images
        

    # ----------------------
    #     VISUAL STUFF
    # ----------------------

    def draw_everything(self, screen):
        """calls the draw functions that happen every frame. Order matters."""
        self.draw_board(screen)
        
        if self.game_state == 0:
            self.draw_hover(screen)
            self.draw_pieces(screen)
            
            self.draw_legal_moves(screen)
            self.draw_select(screen)
        else:
            self.draw_pieces(screen)
            self.draw_game_end(screen)
        
        if self.promotion_square != (-1, -1, ""):
            self.draw_promotion(screen)
        if self.moves_since_capture == 0:
            self.draw_sides(screen)
        

    # ------- Every frame -------

    def draw_board(self, screen):
        """draw just the squares"""
        
        for row in self.row_range:
            for col in self.row_range:
                if (row + col) % 2 == 0:
                    color = LIGHT
                else:
                    color = DARK
                pygame.draw.rect(screen, color, (col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                # For testing
                lan_text = self.get_chess_notation((row, col), "white")
                #lan_text = (f"{row, col}")
                coord_text = self.font.render(lan_text, True, BLACK)
                #coord_text = self.font.render((f"{row, col}"), True, BLACK)
                screen.blit(coord_text, ((col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE)))

    def draw_pieces(self, screen):
        """draw just the pieces"""
        if self.mode == 1 and self.turn == OPPOSING_COLOR:
            for pos in self.player_layout_dict.keys():
                row = 7 - pos[0]
                col = 7 - pos[1]
                curr_piece = self.player_layout_dict[pos]
                if self.piece_images[curr_piece.name] is None:
                    piece_text = self.font.render(curr_piece.name, True, BLACK)
                    screen.blit(piece_text, ((col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE)))
                else:
                    screen.blit(self.piece_images[curr_piece.name], ((col*SQUARE_SIZE + SIDE_BAR_WIDTH + (SQUARE_SIZE-self.piece_images_width)/2, 
                                            row*SQUARE_SIZE + (SQUARE_SIZE-self.piece_images_height)/2)))
            for pos in self.opponent_layout_dict.keys():
                row = 7 - pos[0]
                col = 7 - pos[1]
                curr_piece = self.opponent_layout_dict[pos]
                if self.piece_images[curr_piece.name] is None:
                    piece_text = self.font.render(curr_piece.name, True, BLACK)
                    screen.blit(piece_text, ((col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE)))
                else:
                    screen.blit(self.piece_images[curr_piece.name], ((col*SQUARE_SIZE + SIDE_BAR_WIDTH + (SQUARE_SIZE-self.piece_images_width)/2, 
                                            row*SQUARE_SIZE + (SQUARE_SIZE-self.piece_images_height)/2)))
        # else, either default mode or 1 mode but player turn
        else:
            for pos in self.player_layout_dict.keys():
                row = pos[0]
                col = pos[1]
                curr_piece = self.player_layout_dict[pos]
                if self.piece_images[curr_piece.name] is None:
                    piece_text = self.font.render(curr_piece.name, True, BLACK)
                    screen.blit(piece_text, ((col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE)))
                else:
                    screen.blit(self.piece_images[curr_piece.name], ((col*SQUARE_SIZE + SIDE_BAR_WIDTH + (SQUARE_SIZE-self.piece_images_width)/2, 
                                            row*SQUARE_SIZE + (SQUARE_SIZE-self.piece_images_height)/2)))
            for pos in self.opponent_layout_dict.keys():
                row = pos[0]
                col = pos[1]
                curr_piece = self.opponent_layout_dict[pos]
                if self.piece_images[curr_piece.name] is None:
                    piece_text = self.font.render(curr_piece.name, True, BLACK)
                    screen.blit(piece_text, ((col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE)))
                else:
                    screen.blit(self.piece_images[curr_piece.name], ((col*SQUARE_SIZE + SIDE_BAR_WIDTH + (SQUARE_SIZE-self.piece_images_width)/2, 
                                            row*SQUARE_SIZE + (SQUARE_SIZE-self.piece_images_height)/2)))

    def draw_hover(self, screen):
        """draw the hover effect"""
        mouse_pos = mouse.get_pos()
        row, col = self.get_square_from_screen_coords(mouse_pos)
        if col >= 0 and col <= 7:
            hover_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            hover_surface.fill(HOVER_COLOR)
            screen.blit(hover_surface, (col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE))
    
    def draw_select(self, screen):
        """draws the select box over a clicked piece (if applicable)"""
        row, col = self.selected_piece
        if row >= 0 and col >= 0:
            if self.mode == 0:
                selected_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                selected_surface.fill(SELECTED_COLOR)
                screen.blit(selected_surface, (col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE))
            if self.mode == 1 and self.turn == OPPOSING_COLOR:
                selected_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                selected_surface.fill(SELECTED_COLOR)
                screen.blit(selected_surface, ((7-col)*SQUARE_SIZE + SIDE_BAR_WIDTH, (7-row)*SQUARE_SIZE))
            if self.mode == 1 and self.turn == PLAYER_COLOR:
                selected_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                selected_surface.fill(SELECTED_COLOR)
                screen.blit(selected_surface, (col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE))

    def draw_legal_moves(self, screen):
        """draws indicators on squares where a move can be made.
        self.legal_moves is a list of tuples in the form (col, row, z), where 
        row/col is the square of the legal move and z is a type of move (see chess_piece.py dictionary) """

        for square in self.legal_moves:
            row = square[0]
            col = square[1]
            move_type = square[2]
            if move_type == "o" or move_type == "y" or move_type == "p":
                diameter = SQUARE_SIZE/3
                circle_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
                pygame.draw.circle(circle_surface, LEGAL_MOVE_COLOR, (diameter/2, diameter/2),
                                diameter/2)
                if self.turn == PLAYER_COLOR or self.mode == 0:
                    screen.blit(circle_surface, (col*SQUARE_SIZE + SIDE_BAR_WIDTH + SQUARE_SIZE/2 - diameter/2, row*SQUARE_SIZE + SQUARE_SIZE/2 - diameter/2))
                else:
                    screen.blit(circle_surface, ((7-col)*SQUARE_SIZE + SIDE_BAR_WIDTH + SQUARE_SIZE/2 - diameter/2, (7-row)*SQUARE_SIZE + SQUARE_SIZE/2 - diameter/2))
            else:     
                diameter = SQUARE_SIZE/2
                circle_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
                pygame.draw.circle(circle_surface, LEGAL_MOVE_COLOR, (diameter/2, diameter/2),
                                diameter/2, width = 3)
                if self.turn == PLAYER_COLOR or self.mode == 0:
                    screen.blit(circle_surface, (col*SQUARE_SIZE + SIDE_BAR_WIDTH + SQUARE_SIZE/2 - diameter/2, row*SQUARE_SIZE + SQUARE_SIZE/2 - diameter/2))
                else:
                    screen.blit(circle_surface, ((7-col)*SQUARE_SIZE + SIDE_BAR_WIDTH + SQUARE_SIZE/2 - diameter/2, (7-row)*SQUARE_SIZE + SQUARE_SIZE/2 - diameter/2))

    def draw_sides(self, screen):

        # Gray side bar backgrounds
        pygame.draw.rect(screen, GRAY, (0, 0, SIDE_BAR_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(screen, GRAY, (SCREEN_WIDTH - SIDE_BAR_WIDTH, 0, SIDE_BAR_WIDTH, SCREEN_HEIGHT))
        # TODO: finish and fix
        captured_dict = {
            "white_q" : 0, 
            "white_r" : 0, 
            "white_b" : 0, 
            "white_n" : 0, 
            "white_p" : 0,
            # "white_k" : 0, 
            "black_q" : 0, 
            "black_r" : 0,
            "black_b" : 0,  
            "black_n" : 0, 
            "black_p" : 0
            # "black_k" : 0, 
        }
        for name in self.captured_pieces:
            captured_dict[name] += 1
        # print(f"captured_dict: {captured_dict}")
        SCREEN_EDGE_OFFSET = 10
        # a max of 16 pieces can be captured and stacked (technically 
        # 15 because no king, so that gives room for spacing)
        piece_width = self.captured_piece_images_width
        piece_height = self.captured_piece_images_height
        y_spacing = math.floor(SCREEN_HEIGHT/16/16)

        # lowest positional (highest magnitude) y-coordinate drawn by a captured piece 
        # (ie the bottom of the 15th piece captured). Used to get equal spacing on the
        # very top and bottom of the column of drawn captured pieces
        last_y_pixel_drawn = 14 * (piece_height + y_spacing) + piece_height
        start_y = math.floor((SCREEN_HEIGHT - last_y_pixel_drawn)/2)

        # counts number of pieces already drawn. Initialized to -1 for spacing calculation
        white_count = -1
        black_count = -1
        for name in captured_dict.keys():
            color = name.split("_")[0]
            for num in range(captured_dict[name]):       
                if color == "white":
                    draw_x_coord = SCREEN_EDGE_OFFSET
                    white_count += 1
                    draw_y_coord = white_count * (piece_height + y_spacing) + start_y
                    # print(f"last y pixel drawn: {last_y_pixel_drawn}")
                    # print(f"y_coord: {draw_y_coord} from {white_count} * ({piece_height} + {y_spacing}) + {start_y}")
                else:
                    draw_x_coord = SCREEN_WIDTH - SCREEN_EDGE_OFFSET - piece_width
                    black_count += 1
                    draw_y_coord = black_count * (piece_height + y_spacing) + start_y
                screen.blit(self.captured_piece_images[name], (draw_x_coord, draw_y_coord))
    # ------- End every frame -------

    def draw_promotion(self, screen):
        """Draws promotion GUI"""
        col = self.promotion_square[1]
        promotion_piece_names = [(self.turn + "_q"), (self.turn + "_n"), (self.turn + "_r"), (self.turn + "_b")]
        # r, n, b, q
        if self.turn == PLAYER_COLOR or self.mode == 0:
            for row in range(4):
                pygame.draw.rect(screen, PROMOTION_BACKGROUND_COLOR, (col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                screen.blit(self.piece_images[promotion_piece_names[row]], ((col*SQUARE_SIZE + SIDE_BAR_WIDTH + (SQUARE_SIZE-self.piece_images_width)/2, 
                                                    row*SQUARE_SIZE + (SQUARE_SIZE-self.piece_images_height)/2)))
        else:
            col = 7 - col
            for row in range(4):
                pygame.draw.rect(screen, PROMOTION_BACKGROUND_COLOR, (col*SQUARE_SIZE + SIDE_BAR_WIDTH, (7-row)*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                screen.blit(self.piece_images[promotion_piece_names[row]], ((col*SQUARE_SIZE + SIDE_BAR_WIDTH + (SQUARE_SIZE-self.piece_images_width)/2, 
                                                    (7-row)*SQUARE_SIZE + (SQUARE_SIZE-self.piece_images_height)/2)))

    def draw_game_end(self, screen):
        """Draws end of game visuals (squares with two kings get highlighted: green/red for respective winner/loser
        upon checkmate, or both gray upon draw/stalemate)"""
        # Get position of winning and losing king
        # I think the losing king should always come from player dict, but this just checks both
        for dict in [self.player_layout_dict, self.opponent_layout_dict]:
            for pos, piece in dict.items():
                if piece.piece_type == "k":
                    if piece.color == self.turn:
                        loss_king_pos = pos
                    else:
                        win_king_pos = pos
        if self.game_state == CHECKMATE_ID:
            self.draw_game_end_square_highlights(screen, win_king_pos, loss_king_pos, WIN_KING_COLOR, LOSS_KING_COLOR)
        else:
            # there isn't a win/loss king because it's a draw/stalemate, but those variables already
            # have the positions we need.
            self.draw_game_end_square_highlights(screen, win_king_pos, loss_king_pos, DRAW_KING_COLOR, DRAW_KING_COLOR)

    def draw_game_end_square_highlights(self, screen, king_1, king_2, color_1, color_2):
        """Helper function to draw_game_end(). Draws a highlight of color_1 over the square stored
        in king_1, and color_2 over king_2."""
        # just copied from draw_select
        row, col = king_1
        if self.mode == 0:
            selected_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            selected_surface.fill(color_1)
            screen.blit(selected_surface, (col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE))
        if self.mode == 1 and self.turn == OPPOSING_COLOR:
            selected_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            selected_surface.fill(color_1)
            screen.blit(selected_surface, ((7-col)*SQUARE_SIZE + SIDE_BAR_WIDTH, (7-row)*SQUARE_SIZE))
        if self.mode == 1 and self.turn == PLAYER_COLOR:
            selected_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            selected_surface.fill(color_1)
            screen.blit(selected_surface, (col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE))

        # same code as above. Ugly, but I don't want to make a loop for king_1/2 and color_1/2
        row, col = king_2
        if self.mode == 0:
            selected_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            selected_surface.fill(color_2)
            screen.blit(selected_surface, (col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE))
        if self.mode == 1 and self.turn == OPPOSING_COLOR:
            selected_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            selected_surface.fill(color_2)
            screen.blit(selected_surface, ((7-col)*SQUARE_SIZE + SIDE_BAR_WIDTH, (7-row)*SQUARE_SIZE))
        if self.mode == 1 and self.turn == PLAYER_COLOR:
            selected_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            selected_surface.fill(color_2)
            screen.blit(selected_surface, (col*SQUARE_SIZE + SIDE_BAR_WIDTH, row*SQUARE_SIZE))

        
    # ----------------------
    #    END VISUAL STUFF
    # ----------------------

    def update_board(self, turn_num=-1):
        """  update values for the board (like orientation, turn, etc). Default turnNum
             switches the turn
        """
        if self.game_state == 0:
            self.change_turn(turn_num)
            self.flip_layout_dicts()
            self.flip_en_passant_pieces()
            # self.selected_piece = (-1, -1)
            # self.legal_moves.clear()
            
            if not self.board_simulation:
                
                # engine stuff
                # this if is needed for moves_file implementation as that's the only time the queue has more
                # than 1 move in it at a time. Without this, the engine computes a move for the current board
                # but adds it to the end of a sequence of moves from moves_file

                if self.engine.out_queue.empty() and not self.engine.moves_file_bool:
                    # use if True to do moves for both players
                    if self.turn == OPPOSING_COLOR:
                        self.engine.in_queue.put(hashable_chess_board.Hashable_Board(self))

                self.count_pieces_dict = self.count_pieces()
                self.game_state = self.check_draw_stalemate_checkmate()
                if self.game_state != 0:
                    self.handle_end_of_game()
                # import os
                # os.system('cls')
    
    def change_turn(self, turn_num):
        """Helper function to swap turn instance variable (defaults to swapping, but turn can be specified)"""
        if turn_num == -1:
            if self.turn == WHITE_TURN:
                self.turn = BLACK_TURN
            else:
                self.turn = WHITE_TURN
        else:
            self.turn = turn_num

    def handle_event(self, event, screen):
        if self.game_state == 0:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_click(event, screen)
            if event.type == ENGINE_MOVE:
                out_queue_item = getattr(event, "move")
                self.handle_engine_move(out_queue_item)
    
    def handle_click(self, event, screen):
        """calls the functions that deal with a click TODO: among other things...""" 

        # left click
        if event.button == 1:
            
            mouse_row, mouse_col = self.get_square_from_screen_coords(event.pos)
            if mouse_col < 0 or mouse_col > 7:
                return
            # if the user clicked a promotion option or opponent clicked promotion in mode 0
            if (self.turn == PLAYER_COLOR or self.mode == 0) and mouse_col == self.promotion_square[1] and mouse_row <= 3:
                self.complete_promotion(mouse_row)
                return

            # flip mouse pos for black
            if self.mode == 1 and self.turn == OPPOSING_COLOR:
                mouse_row = 7 - mouse_row
                mouse_col = 7 - mouse_col
            
            # opponent clicked promotion in mode 1
            if self.mode == 1 and self.turn == OPPOSING_COLOR and mouse_col == self.promotion_square[1] and mouse_row <= 3:
                self.complete_promotion(mouse_row)
                return

            # try new selection
            if self.selected_piece == (-1, -1):
                if (mouse_row, mouse_col) in self.player_layout_dict:
                    self.selected_piece = (mouse_row, mouse_col)
                    # TODO: can maybe optimize to call pawn moves separately so that en_passant_pieces doesn't
                    #       need to be passed to other pieces' get_legal_moves() call. If you do this,
                    #       update it in chess_engine.py's get_legal_moves() too
                    self.legal_moves = self.player_layout_dict[(mouse_row, mouse_col)].get_legal_moves(self.player_layout_dict, self.opponent_layout_dict, self.en_passant_pieces)
                    self.legal_moves.extend(self.get_castle_moves())
                    # if layout_dict[(mouse_row, mouse_col)].piece_type == "k":
                    #     print(f"king legal moves before check check: {self.legal_moves}")
                    self.legal_moves = self.exclude_check_moves(self.legal_moves)

                    
            # otherwise, update selected piece: 
            else:
                self.promotion_square = (-1, -1, "")
                # clicked same piece so deselect
                if self.selected_piece == (mouse_row, mouse_col):
                    self.selected_piece = (-1, -1)
                    self.legal_moves.clear()
                # clicked same color piece, update selection
                elif (mouse_row, mouse_col) in self.player_layout_dict:
                    self.selected_piece = (mouse_row, mouse_col)
                    self.legal_moves = self.player_layout_dict[(mouse_row, mouse_col)].get_legal_moves(self.player_layout_dict, self.opponent_layout_dict, self.en_passant_pieces)
                    self.legal_moves.extend(self.get_castle_moves())
                    self.legal_moves = self.exclude_check_moves(self.legal_moves)
                    


                # clicked open square or opposing piece, initiate move
                else:
                    self.initiate_piece_move((mouse_row, mouse_col))

    def handle_engine_move(self, move):
        """ translates the engine's returned move into Board's required format.
        move parameter is of form: (sq1 row, sq1 col), (sq2 row, sq2 col, move_type)"""
        # the engine returns -1 if there's no valid move

        if move == -1:
            self.check_draw_stalemate_checkmate()
            return
        sq2_row, sq2_col, move_type = move[1]
        if move_type == "p" or move_type == "pc":
            self.selected_piece = (move[0][0], move[0][1])
            self.promotion_square = (sq2_row, sq2_col, move_type)
            # just promote to queen bruh like let's not overthink this
            self.complete_promotion(0)
        else:
            self.move_piece(move[0], (sq2_row, sq2_col), move_type)
        

    def initiate_piece_move(self, sq):
        """indirectly/directly performs all steps of moving a piece (validation, visual stuff, actual move, etc).
        sq = (row, col) of destination, self.selected_piece contains the piece to move
        
        Because of the way selecting a piece works, at function call it's guaranteed that a player's piece
        has been selected and they've just clicked an opposing piece or open square (aka I capped about it
        performing all validation :P).  """
        move_type = ""
        for row, col, move in self.legal_moves:
            if row == sq[0] and col == sq[1]:
                move_type = move
                if move_type == "p" or move_type == "pc":
                    self.initiate_promotion(sq, move_type)
                else:
                    self.move_piece(self.selected_piece, sq, move_type)
        # clear selected piece unless we're doing a promotion 
        if move_type != "p" and move_type != "pc":
            self.selected_piece = (-1, -1)
        self.legal_moves.clear()

    def initiate_promotion(self, sq, move_type):
        """Helper function to put the Board in a promotion state. self.promotion_square
        is equal to the square where the pawn to be promoted is moving to"""
        
        self.promotion_square = (sq[0], sq[1], move_type)    
    
    def complete_promotion(self, mouse_row):
        """Promotes a pawn. Upon function call, the promotion GUI was clicked and the mouse row
        location is passed in to determine which piece to promote to. Swaps the pawn for the chosen
        piece and then immediately calls move_piece() to finish the move. Resets self.promotion_square"""
        selected_row = self.selected_piece[0]
        selected_col = self.selected_piece[1]

        # queen promotion
        if mouse_row == 0:
            # put queen where the pawn is currently
            self.player_layout_dict[(selected_row, selected_col)] = Piece((self.turn + "_q"), selected_row, selected_col)
            # lose pawn (-1) to get queen (+9)
            if self.turn == "white":
                self.white_material += 8
            else:
                self.black_material += 8
        # knight promotion
        if mouse_row == 1:
            # put knight where the pawn is currently
            self.player_layout_dict[(selected_row, selected_col)] = Piece((self.turn + "_n"), selected_row, selected_col)
            if self.turn == "white":
                self.white_material += 2
            else:
                self.black_material += 2
        # rook promotion
        if mouse_row == 2:
            # put rook where the pawn is currently
            self.player_layout_dict[(selected_row, selected_col)] = Piece((self.turn + "_r"), selected_row, selected_col)
            if self.turn == "white":
                self.white_material += 4
            else:
                self.black_material += 4
        # bishop promotion
        if mouse_row == 3:
            # put bishop where the pawn is currently
            self.player_layout_dict[(selected_row, selected_col)] = Piece((self.turn + "_b"), selected_row, selected_col)
            if self.turn == "white":
                self.white_material += 2
            else:
                self.black_material += 2
        if self.promotion_square[2] == "p": 
            self.move_piece((self.selected_piece), (self.promotion_square[0], self.promotion_square[1]), "o")
        else: # pc (promotion capture)
            self.move_piece((self.selected_piece), (self.promotion_square[0], self.promotion_square[1]), "pc")
        self.promotion_square = (-1, -1, "")


    def move_piece(self, sq1, sq2, move_type):
        """moves the piece on square1 to square2. Move validation must happen prior to this function.
        Handles en passant logic and castling logic. Calls update board."""


        sq1_row, sq1_col = sq1
        sq2_row, sq2_col = sq2

        # Move files output
        if not self.board_simulation:
            if self.turn == "black" and self.mode == 1:
                print(f"(({7-sq1_row}, {7-sq1_col}), ({7-sq2_row}, {7-sq2_col}, '{move_type}'))")
            else:
                print(f"(({sq1_row}, {sq1_col}), ({sq2_row}, {sq2_col}, '{move_type}'))")
            sq1_lan = self.get_chess_notation(sq1, self.turn)
            sq2_lan = self.get_chess_notation(sq2, self.turn)
            lan = sq1_lan + sq2_lan
            if move_type == "p" or move_type == "pc":
                lan += self.player_layout_dict[(sq1_row, sq1_col)].piece_type
            lan += " "

            with open(Board.engine_file, "a", encoding="utf-8") as file:
                file.write(f"(({sq1_row}, {sq1_col}), ({sq2_row}, {sq2_col}, '{move_type}'))\n")
            with open(Board.lan_file, "a", encoding="utf-8") as file:
                file.write(lan)

        # if capture, add the captured piece to the captured_pieces list
        if move_type == "c" or move_type == "pc":
            # this should work even though it looks wrong, because opp_layout_dict is always going to
            # be the opposite color of whatever is on the other side of the -= 
            if self.turn == "white":
                self.black_material -= self.opponent_layout_dict[(sq2_row, sq2_col)].value
            else:
                self.white_material -= self.opponent_layout_dict[(sq2_row, sq2_col)].value

            self.captured_pieces.append(self.opponent_layout_dict[(sq2_row, sq2_col)].name)
        if move_type == "e":
            if self.turn == "white":
                self.black_material -= self.opponent_layout_dict[(sq2_row + 1, sq2_col)].value
            else:
                self.white_material -= self.opponent_layout_dict[(sq2_row + 1, sq2_col)].value

            self.captured_pieces.append(self.opponent_layout_dict[(sq2_row + 1, sq2_col)].name)
            
        
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

        if not self.board_simulation:
            # reads much better without distributing the not. Shoutout DeMorgan tho
            if not (move_type == "c" or move_type == "e"):
                self.moves_since_capture += 1
            else:
                self.moves_since_capture = 0
        self.update_board()

        # if not self.board_simulation:
        #     self.reverse_move(sq1, sq2, move_type)

    def reverse_move(self, sq1, sq2, move_type):
        """
        Reverses the move in the parameters. To undo move_piece(x,y,z), you do
        reverse_move(x,y,z). Updates board pieces as well as all required object attributes. Used
        to avoid deepcopying boards during engine calculations and exclude_check_moves().
        Currently only reverses "o" moves.
        I think (0_0) the only thing that doesn't get reversed is the
                self.selected_piece = (-1, -1)
                self.legal_moves.clear()
        in update_board(), but that shouldn't matter because you need to update those to move a piece again
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


    # ----------------------
    #     BOARD STUFF (as opposed to the not board stuff in the Board class...)
    # ----------------------
    
    def get_square_from_screen_coords(self, coords):
        """returns tuple of form (row, col) (i.e. (y,x) ).
            0-based, so the board is 0-7 x 0-7"""
        return (math.floor(coords[1] / SQUARE_SIZE ), math.floor((coords[0] - SIDE_BAR_WIDTH) / SQUARE_SIZE))
    
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


    # def exclude_check_moves(self, moves):
    #     """takes in a list of currently valid moves but scans through them to see if any of them would
    #     put this color's king in check and removes those moves."""

    #     #print(f"exclude_check_moves moves: {moves}")
    #     # could definitely store king_row/col as an instance variable and just update throughout for
    #     # constant time access here, but that's the least of the problems given the hot
    #     # mess of what follows this loop
    #     for pos, piece in self.player_layout_dict.items():
    #         if piece.piece_type == "k":
    #             king_row = pos[0]
    #             king_col = pos[1]
    #     # loop through list of moves backwards so that they can be deleted if needed
    #     for i in reversed(range(len(moves))):
            
    #         move = moves[i]
            
    #         # simulate board after this move
    #         check_board = copy.deepcopy(self)            
    #         check_board.board_simulation = True
            
    #         # print(f"\nc_b_l_d 1: {check_board_layout_dict}")
    #         # print(f"\nc_b_o_l_d: {check_board_opp_layout_dict}")
            
    #         selected_piece = check_board.player_layout_dict[(check_board.selected_piece[0], check_board.selected_piece[1])]
    #         #print(f"\n{selected_piece.name} on {selected_piece.row, selected_piece.col} doing {move}\n")
    #         check_board.move_piece((selected_piece.row, selected_piece.col), (move[0], move[1]), move[2])
    #         #print(f"\nc_b_l_d 2: {check_board_layout_dict}")

    #         # update king pos if that move was a king move. move[0]/[1] have the user POV coords
    #         # while selected.row/col have the simulated boards coords. The final if before the del
    #         # accounts for the flip already with a 7 -, so use user POV coords here
    #         if selected_piece.piece_type == "k":
    #             king_row = move[0]
    #             king_col = move[1]

    #         # look at every piece in simulated board
    #         # when moving black piece, piece is white perspective
    #         for piece in check_board.player_layout_dict.values():
                
    #             legal_moves_set = piece.get_legal_moves_set(check_board.player_layout_dict, check_board.opponent_layout_dict,
    #                                                             check_board.en_passant_pieces)
    #             if ((7-king_row, 7-king_col, "c") in legal_moves_set or
    #                 (7-king_row, 7-king_col, "e") in legal_moves_set or
    #                 (7-king_row, 7-king_col, "pc") in legal_moves_set):
    #                     del moves[i]
    #                     break

    #     return moves

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
        #print(f"selected_row/col: {selected_row}, {selected_col}")
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

        """Checks if there is a stalemate or checkmate on the board."""
        if self.moves_since_capture >= 100:
            return DRAW_50_MOVE_RULE_ID
        
        # 3 move repitition or whatever tf it is
        
        hash_board = hashable_chess_board.Hashable_Board(self)
        hashed_board = hash(hash_board)
        if hashed_board in self.board_repetition_dict:
            self.board_repetition_dict[hashed_board] += 1
            #print(f"{hashed_board}  :  {self.board_repetition_dict[hashed_board]}")
            if self.board_repetition_dict[hashed_board] == 3:
                return DRAW_REPETITION_ID
        else:
            self.board_repetition_dict[hashed_board] = 1
            #print(f"{hashed_board}  :  {self.board_repetition_dict[hashed_board]}")
        
        # Insufficient material logic
        white_pieces, black_pieces = self.count_pieces_dict
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

    def handle_end_of_game(self):
        if self.game_state == 1:
            print(f"end of game due to checkmate")
        elif self.game_state == 2:
            print(f"end of game due to stalemate")
        elif self.game_state == 3:
            print(f"end of game due to draw by 50 move rule")
        elif self.game_state == 4:
            print(f"end of game due to draw by repetition")
        elif self.game_state == 5:
            print(f"end of game due to draw by insufficient material")
        else:
            print(f"catastrophic failure")

    def __deepcopy__(self, dict):
        if id(self) in dict:
            return id(dict[self])

        # prevents __init__ from running so init funcs don't get called for this Board (namely loading images)
        new_board = Board.__new__(Board)
        dict[id(self)] = new_board

        # TODO: add other uneccesary fields, and store these two sets as class level attributes
        # so they don't get recursively stored...
        excluded = {"engine", "piece_images", "captured_piece_images", "legal_moves", "font"}
        # for ex: a Board copy's legal_moves field gets used, but it doesn't need the value
        # from the original Board, just for the field to exist.
        excluded_but_needs_value = {"legal_moves"}
        for key, value in self.__dict__.items():
            if key not in excluded:
                setattr(new_board, key, copy.deepcopy(value, dict))
            if key in excluded_but_needs_value:
                setattr(new_board, key, [])
        return new_board