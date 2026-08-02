import asyncio


import pygame
from pygame import *
import sys

pygame.init()

FPS = 60
frame_clock = time.Clock()

BLUE  = (0, 0, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
screen = display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen.fill(WHITE)
display.set_caption("Bozo")


class Player(sprite.Sprite):
    def __init__(self):
        super().__init__()
        original = image.load("Screenshot 2026-06-15 101146.png").convert()
        self.image = transform.scale(original, (100, 100))
        self.rect = self.image.get_rect()
        self.rect.center = (160, 520)
    def update(self):
        global FPS
        pressed_keys = key.get_pressed()
        if pressed_keys[K_UP]:
            if self.rect.top > 0:
                self.rect.move_ip(0, -5)
        if pressed_keys[K_DOWN]:
            if self.rect.bottom < SCREEN_HEIGHT:
                self.rect.move_ip(0, 5)
        if pressed_keys[K_LEFT]:
            if self.rect.left > 0:
                self.rect.move_ip(-5, 0)
        if pressed_keys[K_RIGHT]:
            if self.rect.right < SCREEN_WIDTH:
                self.rect.move_ip(5, 0)
        if pressed_keys[K_q]:
            FPS += 1
        if pressed_keys[K_a]:
            FPS -= 1
    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Enemy(sprite.Sprite):
    def __init__(self):
        super().__init__()


P = Player()
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
    
    P.update()
    screen.fill(WHITE)
    P.draw(screen)
    pygame.display.update()
    frame_clock.tick(FPS)

