import pygame
#from pygame import *
import sys
import time

from constants import *
import chess_board as chess_board
import chess_engine as chess_engine

# command line format:
# python chess.py (0 for board to flip every turn, 1 for white to stay on bottom and black on top),
#                  ({moves_file_name}.txt for a sequence of moves (white and black) to get played)
if __name__ == "__main__":
    pygame.init()

    frame_clock = pygame.time.Clock()

    print(f"len argv: {len(sys.argv)}")
    if len(sys.argv) == 2:
        mode = int(sys.argv[1])
        moves_file = None
    elif len(sys.argv) == 3:
        mode = int(sys.argv[1])
        moves_file = sys.argv[2]
    else:
        mode = 0
        moves_file = None

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.fill(WHITE)
    pygame.display.set_caption("Chess")

    engine = chess_engine.Engine_Process(moves_file)
    board = chess_board.Board(mode, engine)

    fps_list = []
    fps_list_whole = []

    time_start = time.perf_counter()
    time_printed = False
    while True:
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print(f"entire fps average: {sum(fps_list_whole)/len(fps_list_whole)}")
                engine.in_queue.put("QUIT")
                pygame.quit()
                sys.exit()
            else:
                board.handle_event(event, screen)
        board.draw_everything(screen)

        if not engine.out_queue.empty():
            out_queue_item = engine.out_queue.get()
            engine_event = pygame.event.Event(ENGINE_MOVE, {"move" : out_queue_item})
            pygame.event.post(engine_event)
        elif moves_file and not time_printed:
            time_end = time.perf_counter()
            runtime = time_end - time_start
            print(f"running {moves_file} took {runtime:.6}")
            time_printed = True
            # include these if running snakeviz so the program ends at same time

            print(f"white, black POM: {board.white_material}, {board.black_material}")
            # pygame.quit()
            # sys.exit()

        fps_list.append(frame_clock.get_fps())
        if len(fps_list) >= 10:
            average = sum(fps_list)/len(fps_list)
            #print(f"fps average:{average}")
            fps_list_whole.append(average)
            fps_list.clear()

        # update the board every frame, but only update the side bars if there was a capture
        if board.moves_since_capture == 0:
            pygame.display.update()
        else:
            pygame.display.update(BOARD_RECT)
        frame_clock.tick(FPS) 
