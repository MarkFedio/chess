import pygame

ENGINE_MOVE = pygame.event.custom_type()

FPS = 60

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600

SQUARE_SIZE = SCREEN_HEIGHT/8
SIDE_BAR_WIDTH = (SCREEN_WIDTH - 8*SQUARE_SIZE)/2

BOARD_RECT = pygame.Rect(SIDE_BAR_WIDTH, 0, SQUARE_SIZE*8, SCREEN_HEIGHT)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT = (199, 178, 119)
DARK = (101, 67, 33)
HOVER_COLOR = (255, 255, 0, 200)
SELECTED_COLOR = (255, 255, 0, 100)
LEGAL_MOVE_COLOR = (128, 128, 128, 128)
PROMOTION_BACKGROUND_COLOR = (29, 105, 34)

INITIAL_STRING_LAYOUT = [["black_r", "black_n", "black_b", "black_q", "black_k", "black_b", "black_n", "black_r"],
                        ["black_p", "black_p", "black_p", "black_p", "black_p", "black_p", "black_p", "black_p"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"], 
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["white_p", "white_p", "white_p", "white_p", "white_p", "white_p", "white_p", "white_p"],
                        ["white_r", "white_n", "white_b", "white_q", "white_k", "white_b", "white_n", "white_r"]]

CASTLE_STRING_LAYOUT = [["black_r", "x_x", "x_x", "x_x", "black_k", "x_x", "x_x", "black_r"],
                        ["black_p", "black_p", "black_p", "black_p", "black_p", "black_p", "black_p", "black_p"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"], 
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["white_p", "white_p", "white_p", "white_p", "white_p", "white_p", "white_p", "white_p"],
                        ["white_r", "x_x", "x_x", "x_x", "white_k", "x_x", "x_x", "white_r"]]

PROMOTION_STRING_LAYOUT = [["x_x", "black_n", "black_b", "black_q", "black_k", "black_b", "black_n", "black_r"],
                        ["white_p", "black_p", "black_p", "black_p", "black_p", "black_p", "black_p", "x_x"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"], 
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "white_p", "white_p", "white_p", "white_p", "white_p", "white_p", "black_p"],
                        ["white_r", "white_n", "white_b", "white_q", "white_k", "white_b", "white_n", "x_x"]]

CHECKMATE_STRING_LAYOUT = [["black_k", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "white_q", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"], 
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "white_q"],
                        ["white_p", "white_p", "white_p", "white_p", "white_p", "white_p", "white_p", "white_p"],
                        ["white_r", "white_n", "white_b", "white_q", "white_k", "white_b", "white_n", "white_r"]]

KING_ONLY_STRING_LAYOUT = [["x_x", "x_x", "x_x", "x_x", "black_k", "x_x", "x_x", "x_x"],
                            ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                            ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"], 
                            ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                            ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                            ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                            ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                            ["x_x", "x_x", "x_x", "white_k", "x_x", "x_x", "x_x", "x_x"]]

INSUFFICIENT_MATERIAL_STRING_LAYOUT = [["x_x", "x_x", "x_x", "x_x", "black_k", "x_x", "x_x", "x_x"],
                                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "white_p", "x_x"],
                                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"], 
                                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "x_x"],
                                        ["x_x", "x_x", "x_x", "x_x", "x_x", "x_x", "black_p", "x_x"],
                                        ["x_x", "x_x", "x_x", "white_k", "x_x", "x_x", "x_x", "x_x"]]


WHITE_TURN = "white"
BLACK_TURN = "black"
PLAYER_COLOR = "white"
OPPOSING_COLOR = "black"

VALID_MOVE_EXISTS_ID = 0
CHECKMATE_ID = 1
STALEMATE_ID = 2
DRAW_50_MOVE_RULE_ID = 3
DRAW_REPETITION_ID = 4
DRAW_INSUFFICIENT_MATERIAL_ID = 5