# projectile.py - 子弹与特效
import pygame
import math
from constants import *

# 模块级字体缓存，避免每帧创建
_sun_font = None


def _get_sun_font():
    global _sun_font
    if _sun_font is None:
        import os
        # 直接使用 Windows 中文字体文件
        for p in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"]:
            if os.path.isfile(p):
                _sun_font = pygame.font.Font(p, 11)
                _sun_font.set_bold(True)
                return _sun_font
        _sun_font = pygame.font.SysFont("arial", 11, bold=True)
    return _sun_font


class Pea:
    """豌豆子弹"""

    def __init__(self, x, y, row, dmg, speed, freeze=False, color=None, poison=False, poison_dmg=0):
        self.x = float(x)
        self.y = float(y)
        self.row = row
        self.dmg = dmg
        self.speed = speed
        self.freeze = freeze
        self.custom_color = color
        self.poison = poison
        self.poison_dmg = poison_dmg
        self.alive = True
        self.frame = 0

    def update(self):
        self.x += self.speed
        self.frame += 1
        if self.x > SCREEN_WIDTH + 20:
            self.alive = False

    def draw(self, screen):
        if not self.alive:
            return
        if self.custom_color:
            color = self.custom_color
            dark = tuple(max(0, c - 60) for c in color)
        elif self.freeze:
            color = LIGHT_BLUE
            dark = (80, 160, 200)
        else:
            color = LIME
            dark = (30, 130, 30)
        ix, iy = int(self.x), int(self.y)
        pygame.draw.circle(screen, color, (ix, iy), 8)
        pygame.draw.circle(screen, dark, (ix, iy), 8, 2)
        pygame.draw.circle(screen, WHITE, (ix - 3, iy - 3), 2)


class SunToken:
    """阳光球（从天上落下或向日葵产生）"""

    def __init__(self, x, y, value=25, fall=True):
        self.x = float(x)
        self.y = float(y)
        self.target_y = y + (180 if fall else 0)
        self.value = value
        self.alive = True
        self.collected = False
        self.frame = 0
        self.speed = SUN_FALL_SPEED if fall else 0
        self.radius = 18
        self.lifetime = 300   # 5秒后消失

    def update(self):
        self.frame += 1
        if self.y < self.target_y:
            self.y += self.speed
        else:
            self.lifetime -= 1
            if self.lifetime <= 0:
                self.alive = False

    def draw(self, screen):
        if not self.alive or self.collected:
            return
        ix, iy = int(self.x), int(self.y)
        # 光晕
        glow = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        glow_alpha = int(80 + 40 * math.sin(self.frame * 0.1))
        pygame.draw.circle(glow, (255, 255, 100, glow_alpha),
                           (self.radius * 2, self.radius * 2), self.radius * 2)
        screen.blit(glow, (ix - self.radius * 2, iy - self.radius * 2))
        # 太阳主体
        pygame.draw.circle(screen, YELLOW, (ix, iy), self.radius)
        pygame.draw.circle(screen, ORANGE, (ix, iy), self.radius, 2)
        # 光芒
        for i in range(8):
            angle = self.frame * 0.02 + i * math.pi / 4
            x1 = ix + int(math.cos(angle) * (self.radius + 2))
            y1 = iy + int(math.sin(angle) * (self.radius + 2))
            x2 = ix + int(math.cos(angle) * (self.radius + 8))
            y2 = iy + int(math.sin(angle) * (self.radius + 8))
            pygame.draw.line(screen, ORANGE, (x1, y1), (x2, y2), 2)
        # 文字
        font = _get_sun_font()
        txt = font.render(str(self.value), True, (180, 100, 0))
        screen.blit(txt, (ix - txt.get_width() // 2, iy - 6))

    def get_rect(self):
        return pygame.Rect(int(self.x) - self.radius, int(self.y) - self.radius,
                           self.radius * 2, self.radius * 2)


class Explosion:
    """樱桃炸弹爆炸特效"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frame = 0
        self.duration = 40
        self.alive = True

    def update(self):
        self.frame += 1
        if self.frame >= self.duration:
            self.alive = False

    def draw(self, screen):
        if not self.alive:
            return
        t = self.frame / self.duration
        radius = int(t * 90)
        alpha = int((1 - t) * 200)
        surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        color = (255, int(200 * (1 - t)), 0, alpha)
        pygame.draw.circle(surf, color, (radius + 2, radius + 2), radius)
        screen.blit(surf, (self.x - radius - 2, self.y - radius - 2))
        # 内圈白色
        if radius > 10:
            inner = int(radius * 0.4)
            surf2 = pygame.Surface((inner * 2 + 2, inner * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf2, (255, 255, 200, min(255, alpha + 40)),
                               (inner + 1, inner + 1), inner)
            screen.blit(surf2, (self.x - inner - 1, self.y - inner - 1))
