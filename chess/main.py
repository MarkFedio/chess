import asyncio

import pygame
from pygame import *
import sys

from constants import *
import chess_board

pygame.init()

frame_clock = time.Clock()

print(f"len argv: {len(sys.argv)}")
if len(sys.argv) == 2:
    mode = int(sys.argv[1])
else:
    mode = 1

screen = display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen.fill(WHITE)
display.set_caption("Bozo")

board = chess_board.Board(mode)

fps_list = []
fps_list_whole = []
async def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                print(f"entire fps average: {sum(fps_list_whole)/len(fps_list_whole)}")
                pygame.quit()
                sys.exit()
            else:
                board.handle_event(event, screen)
        board.draw_everything(screen)
        fps_list.append(frame_clock.get_fps())
        if len(fps_list) >= 100:
            average = sum(fps_list)/len(fps_list)
            #print(f"fps average:{average}")
            fps_list_whole.append(average)
            fps_list.clear()

        pygame.display.update()
        frame_clock.tick(FPS)

        await asyncio.sleep(0) 

asyncio.run(main())



