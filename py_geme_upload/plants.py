# plants.py - 植物类
import pygame
import math
import random
from constants import *


class Plant:
    """植物基类"""

    def __init__(self, plant_type, row, col):
        self.type = plant_type
        self.row = row
        self.col = col
        self.x = GRID_X + col * CELL_W + CELL_W // 2
        self.y = GRID_Y + row * CELL_H + CELL_H // 2 + 20
        self.alive = True
        self.frame = 0
        self.hp = PLANT_DATA[plant_type]["hp"]
        self.max_hp = self.hp
        self.has_zombie_in_row = False

        self.hit_flash = 0  # 被击中闪烁帧

    def update(self):
        self.frame += 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

    def take_damage(self, dmg):
        self.hp -= dmg
        self.hit_flash = 5
        if self.hp <= 0:
            self.alive = False

    def draw(self, screen, font):
        if not self.alive:
            return

        self._draw_shadow(screen)
        self._draw_body(screen, font)

        # 受伤闪烁
        if self.hit_flash > 0:
            s = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA)
            s.fill((255, 100, 100, 80))
            screen.blit(s, (self.x - CELL_W//2, self.y - CELL_H//2))

    def _draw_shadow(self, screen):
        """地面阴影"""
        pygame.draw.ellipse(screen, (30, 60, 30), (self.x - 25, self.y + 15, 50, 14))

    def _draw_body(self, screen, font):
        """子类实现"""
        pass

    def _draw_root(self, screen, color=(100, 70, 40)):
        """土壤根部"""
        # 小土丘
        pygame.draw.ellipse(screen, color, (self.x - 18, self.y + 12, 36, 12))
        pygame.draw.ellipse(screen, (80, 50, 30), (self.x - 14, self.y + 14, 28, 8))
        # 草根细线
        for i in range(-2, 3):
            pygame.draw.line(screen, (60, 40, 25),
                             (self.x + i*6, self.y + 12),
                             (self.x + i*6 + 3, self.y + 20), 1)

    def _draw_eyes(self, screen, ex, ey, look_dx=0, blink=False):
        """绘制眼睛（白色底+黑色瞳+高光）"""
        # 眼白
        pygame.draw.ellipse(screen, WHITE, (ex - 8, ey - 5, 8, 10))
        pygame.draw.ellipse(screen, WHITE, (ex + 2, ey - 5, 8, 10))
        # 瞳孔
        if blink and self.frame % 180 < 10:
            # 眨眼
            pygame.draw.line(screen, (40, 40, 40), (ex - 6, ey), (ex - 2, ey), 2)
            pygame.draw.line(screen, (40, 40, 40), (ex + 4, ey), (ex + 8, ey), 2)
        else:
            pygame.draw.circle(screen, (30, 30, 30), (ex - 4 + look_dx, ey), 3)
            pygame.draw.circle(screen, (30, 30, 30), (ex + 6 + look_dx, ey), 3)
            # 高光
            pygame.draw.circle(screen, WHITE, (ex - 5 + look_dx, ey - 1), 1)
            pygame.draw.circle(screen, WHITE, (ex + 5 + look_dx, ey - 1), 1)


# ─────────────────────────────────────────
# 向日葵
# ─────────────────────────────────────────
class Sunflower(Plant):
    def __init__(self, row, col):
        super().__init__("sunflower", row, col)
        self.sun_accum = 0.0
        self.sun_per_tick = PLANT_DATA["sunflower"]["sun_per_tick"]

    def update(self):
        super().update()
        self.sun_accum += self.sun_per_tick

    def collect_sun(self):
        if self.sun_accum >= 1.0:
            self.sun_accum -= 1.0
            return 50
        return 0

    def _draw_body(self, screen, font):
        self._draw_root(screen)

        # 茎（带叶脉）
        stem_color = (50, 150, 50)
        pygame.draw.rect(screen, stem_color, (self.x - 4, self.y - 20, 8, 32))
        pygame.draw.line(screen, (40, 120, 40), (self.x - 1, self.y - 20), (self.x - 1, self.y + 10), 1)

        # 左右叶子（带叶脉）
        for side, sx in [(-1, self.x - 18), (1, self.x + 6)]:
            sway = int(math.sin(self.frame * 0.04) * 3)
            leaf_pts = [(self.x + side * 2, self.y - 5),
                        (sx + sway, self.y - 15),
                        (sx + sway + 6, self.y - 10),
                        (self.x + side * 2, self.y)]
            pygame.draw.polygon(screen, (50, 160, 50), leaf_pts)
            pygame.draw.polygon(screen, (35, 120, 35), leaf_pts, 1)
            # 叶脉
            pygame.draw.line(screen, (40, 130, 40),
                             (self.x + side * 2, self.y - 5),
                             (sx + sway + 3, self.y - 12), 1)

        # 花头（旋转花瓣）
        angle_off = self.frame * 0.03
        for pi in range(8):
            ang = angle_off + pi * math.pi / 4
            petal_x = self.x + int(math.cos(ang) * 18)
            petal_y = self.y - 35 + int(math.sin(ang) * 18)
            pygame.draw.circle(screen, ORANGE, (petal_x, petal_y), 9)
            pygame.draw.circle(screen, (220, 100, 0), (petal_x, petal_y), 9, 1)

        # 花心（纹理点）
        pygame.draw.circle(screen, YELLOW, (self.x, self.y - 35), 14)
        pygame.draw.circle(screen, (220, 180, 0), (self.x, self.y - 35), 14, 1)
        # 花盘纹理点
        for di in range(5):
            dx = int(math.cos(di * 1.2) * 6)
            dy = int(math.sin(di * 1.2) * 6)
            pygame.draw.circle(screen, (200, 160, 0), (self.x + dx, self.y - 35 + dy), 2)
        # 花蕊高光
        pygame.draw.circle(screen, (255, 230, 150), (self.x - 3, self.y - 38), 3)

        # 微笑
        pygame.draw.arc(screen, (60, 40, 0), (self.x - 6, self.y - 32, 12, 8), 0.2, 2.9, 1)

        # 产阳光时发光
        if self.sun_accum >= 0.8:
            glow = int(abs(math.sin(self.frame * 0.1)) * 40 + 30)
            pygame.draw.circle(screen, (255, 255, 200, glow), (self.x, self.y - 35), 26)


# ─────────────────────────────────────────
# 豌豆射手（含寒冰射手）
# ─────────────────────────────────────────
class Peashooter(Plant):
    def __init__(self, row, col, freeze=False):
        super().__init__("snowpea" if freeze else "peashooter", row, col)
        self.freeze = freeze
        self.shoot_cd = PLANT_DATA[self.type]["shoot_cd"]
        self.shoot_timer = 0
        self.pea_dmg = PLANT_DATA[self.type]["pea_dmg"]
        self.pea_speed = PLANT_DATA[self.type]["pea_speed"]
        self.recoil = 0  # 后坐力

    def update(self):
        super().update()
        self.shoot_timer += 1
        if self.recoil > 0:
            self.recoil -= 1

    def try_shoot(self):
        if self.has_zombie_in_row and self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            self.recoil = 6
            return True
        return False

    def _draw_body(self, screen, font):
        self._draw_root(screen)

        bx = self.x + 2
        by = self.y - 25
        recoil_off = self.recoil * 2

        # 茎叶
        pygame.draw.rect(screen, (50, 160, 50), (self.x - 3, self.y - 10, 6, 18))
        # 左叶
        sway = int(math.sin(self.frame * 0.05) * 2)
        pygame.draw.ellipse(screen, (50, 160, 50), (self.x - 18 + sway, self.y - 8, 14, 8))
        pygame.draw.ellipse(screen, (40, 130, 40), (self.x - 18 + sway, self.y - 8, 14, 8), 1)
        # 右叶
        pygame.draw.ellipse(screen, (50, 160, 50), (self.x + 6 + sway, self.y - 8, 14, 8))
        pygame.draw.ellipse(screen, (40, 130, 40), (self.x + 6 + sway, self.y - 8, 14, 8), 1)

        # 头部（带呼吸缩放回弹）
        breath = int(math.sin(self.frame * 0.06) * 2)
        head_color = LIGHT_BLUE if self.freeze else LIME
        head_dark = (80, 160, 200) if self.freeze else (30, 130, 30)
        pygame.draw.circle(screen, head_color, (bx, by + breath), 18)
        pygame.draw.circle(screen, head_dark, (bx, by + breath), 18, 2)
        # 光泽
        pygame.draw.circle(screen, (120, 220, 120, 180), (bx - 6, by - 6 + breath), 6)

        # 炮管（金属感）
        pipe_color = (90, 180, 230) if self.freeze else (60, 180, 60)
        pipe_dark = (60, 130, 180) if self.freeze else (30, 120, 30)
        px = bx + 10 - recoil_off
        py = by - 2 + breath
        pygame.draw.rect(screen, pipe_color, (px, py - 7, 20, 14), border_radius=6)
        pygame.draw.rect(screen, pipe_dark, (px, py - 7, 20, 14), 2, border_radius=6)
        # 炮口
        pygame.draw.ellipse(screen, (20, 40, 20), (px + 16, py - 6, 8, 12))
        # 金属高光
        pygame.draw.line(screen, (150, 220, 255) if self.freeze else (150, 240, 150),
                         (px + 2, py - 5), (px + 15, py - 5), 1)

        # 眼睛
        self._draw_eyes(screen, bx - 2, by - 4 + breath, look_dx=2, blink=True)
        # 眉毛
        pygame.draw.line(screen, (30, 80, 30), (bx - 8, by - 10 + breath), (bx - 2, by - 8 + breath), 2)
        pygame.draw.line(screen, (30, 80, 30), (bx + 4, by - 8 + breath), (bx + 10, by - 10 + breath), 2)

        # 射击火花
        if self.recoil > 0:
            spark_c = (100, 200, 255) if self.freeze else (200, 255, 50)
            for si in range(3):
                sx = px + 22 + random.randint(-3, 5)
                sy = py + random.randint(-4, 4)
                pygame.draw.circle(screen, spark_c, (sx, sy), 2 + self.recoil // 2)

        # 冻结冰晶呼吸
        if self.freeze:
            for ci in range(4):
                cx = bx + int(math.cos(self.frame * 0.05 + ci * 1.5) * 22)
                cy = by + int(math.sin(self.frame * 0.05 + ci * 1.5) * 22) - 35
                pygame.draw.polygon(screen, (150, 200, 255), [
                    (cx, cy - 3), (cx + 2, cy), (cx, cy + 3), (cx - 2, cy)
                ])


# ─────────────────────────────────────────
# 坚果墙
# ─────────────────────────────────────────
class Wallnut(Plant):
    def __init__(self, row, col):
        super().__init__("wallnut", row, col)
        self.max_hp = 2400

    def _draw_body(self, screen, font):
        self._draw_root(screen, (130, 90, 50))

        # 随血量变色
        ratio = self.hp / self.max_hp
        if ratio > 0.6:
            base_color = BROWN
            dark = (100, 60, 30)
        elif ratio > 0.3:
            base_color = (160, 110, 60)
            dark = (90, 50, 20)
        else:
            base_color = (120, 80, 40)
            dark = (70, 40, 15)

        # 受击抖动
        shake_x = random.randint(-2, 2) if self.hit_flash > 0 else 0
        shake_y = random.randint(-2, 2) if self.hit_flash > 0 else 0
        bx = self.x + shake_x
        by = self.y - 5 + shake_y

        # 主轮廓（更椭圆）
        pygame.draw.ellipse(screen, base_color, (bx - 22, by - 20, 44, 40))
        pygame.draw.ellipse(screen, dark, (bx - 22, by - 20, 44, 40), 2)
        # 纹理条纹
        for i in range(-2, 3):
            pygame.draw.arc(screen, dark, (bx - 20 + i*6, by - 18, 20, 36), 0.5, 2.5, 1)

        # 根据血量显示表情
        if ratio > 0.6:
            # 正常：微笑
            self._draw_eyes(screen, bx - 2, by - 6, blink=True)
            pygame.draw.arc(screen, (60, 40, 10), (bx - 8, by - 2, 16, 8), 0.2, 2.9, 2)
        elif ratio > 0.3:
            # 受伤：皱眉
            self._draw_eyes(screen, bx - 2, by - 6, blink=True)
            pygame.draw.line(screen, (60, 40, 10), (bx - 8, by - 10), (bx - 2, by - 7), 2)
            pygame.draw.line(screen, (60, 40, 10), (bx + 4, by - 7), (bx + 10, by - 10), 2)
            pygame.draw.arc(screen, (60, 40, 10), (bx - 6, by + 2, 12, 6), 3.0, 6.2, 2)
        else:
            # 濒死：X眼
            pygame.draw.line(screen, (60, 40, 10), (bx - 8, by - 8), (bx - 2, by - 2), 2)
            pygame.draw.line(screen, (60, 40, 10), (bx - 2, by - 8), (bx - 8, by - 2), 2)
            pygame.draw.line(screen, (60, 40, 10), (bx + 4, by - 8), (bx + 10, by - 2), 2)
            pygame.draw.line(screen, (60, 40, 10), (bx + 10, by - 8), (bx + 4, by - 2), 2)
            pygame.draw.arc(screen, (60, 40, 10), (bx - 6, by + 2, 12, 6), 3.0, 6.2, 2)

        # 被咬缺口（低血量时）
        if ratio < 0.5:
            for _ in range(3):
                nx = bx + random.randint(-18, 18)
                ny = by + random.randint(-15, 15)
                pygame.draw.ellipse(screen, (30, 60, 30), (nx - 3, ny - 3, 6, 6))
        if ratio < 0.2:
            for _ in range(5):
                nx = bx + random.randint(-20, 20)
                ny = by + random.randint(-18, 18)
                pygame.draw.ellipse(screen, (30, 60, 30), (nx - 4, ny - 4, 8, 8))

        # 高光
        pygame.draw.ellipse(screen, (180, 130, 80), (bx - 10, by - 16, 14, 8))


# ─────────────────────────────────────────
# 樱桃炸弹
# ─────────────────────────────────────────
class CherryBomb(Plant):
    def __init__(self, row, col):
        super().__init__("cherrycbomb", row, col)
        self.delay = PLANT_DATA["cherrycbomb"]["explode_delay"]
        self.timer = 0
        self.exploded = False

    def update(self):
        super().update()
        self.timer += 1
        if self.timer >= self.delay and not self.exploded:
            self.exploded = True
            self.alive = False

    def _draw_body(self, screen, font):
        self._draw_root(screen, (120, 70, 70))

        # 倒计时数字
        remaining = max(0, self.delay - self.timer)
        if remaining > 0 and remaining % 30 < 15:
            num = font.render(str(remaining // 30 + 1), True, (255, 200, 0))
            screen.blit(num, (self.x - num.get_width()//2, self.y - 40))

        # 危险警告（超过50%时）
        if self.timer > self.delay * 0.5:
            flash = int(abs(math.sin(self.frame * 0.15)) * 50 + 20)
            pygame.draw.circle(screen, (255, 50, 50, flash), (self.x, self.y - 8), 28)

        # 双樱桃
        for side, ox in [(-1, -12), (1, 12)]:
            cx = self.x + ox
            cy = self.y - 8
            # 果体
            pygame.draw.circle(screen, RED, (cx, cy), 14)
            pygame.draw.circle(screen, (180, 30, 30), (cx, cy), 14, 2)
            # 光泽
            pygame.draw.ellipse(screen, (255, 100, 100), (cx - 6, cy - 10, 8, 6))
            # 果柄
            pygame.draw.line(screen, (60, 120, 60), (cx, cy - 14), (self.x + ox * 0.3, cy - 22), 3)
            # 眼睛
            self._draw_eyes(screen, cx, cy - 2, blink=False)
            # 愤怒嘴
            pygame.draw.arc(screen, (80, 20, 20), (cx - 5, cy + 2, 10, 6), 0.5, 2.6, 2)

        # 连接枝
        pygame.draw.line(screen, (60, 120, 60), (self.x - 6, self.y - 22), (self.x + 6, self.y - 22), 3)
        # 小叶子
        pygame.draw.ellipse(screen, (50, 150, 50), (self.x - 8, self.y - 28, 10, 6))
        pygame.draw.ellipse(screen, (50, 150, 50), (self.x - 2, self.y - 28, 10, 6))


# ─────────────────────────────────────────
# 双重射手
# ─────────────────────────────────────────
class Repeater(Plant):
    def __init__(self, row, col):
        super().__init__("repeater", row, col)
        self.shoot_cd = PLANT_DATA["repeater"]["shoot_cd"]
        self.shoot_timer = 0
        self.pea_dmg = PLANT_DATA["repeater"]["pea_dmg"]
        self.pea_speed = PLANT_DATA["repeater"]["pea_speed"]
        self.recoil = 0

    def update(self):
        super().update()
        self.shoot_timer += 1
        if self.recoil > 0:
            self.recoil -= 1

    def try_shoot(self):
        if self.has_zombie_in_row and self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            self.recoil = 6
            return True
        return False

    def shoot_count(self):
        return 2

    def _draw_body(self, screen, font):
        self._draw_root(screen)

        bx = self.x
        by = self.y - 25
        recoil_off = self.recoil * 2
        breath = int(math.sin(self.frame * 0.06) * 2)

        # 茎
        pygame.draw.rect(screen, (50, 160, 50), (bx - 3, by + 5, 6, 28))
        # 左叶
        sway = int(math.sin(self.frame * 0.05) * 2)
        pygame.draw.ellipse(screen, (50, 160, 50), (bx - 18 + sway, by + 10, 14, 8))
        pygame.draw.ellipse(screen, (40, 130, 40), (bx - 18 + sway, by + 10, 14, 8), 1)
        pygame.draw.ellipse(screen, (50, 160, 50), (bx + 6 + sway, by + 10, 14, 8))
        pygame.draw.ellipse(screen, (40, 130, 40), (bx + 6 + sway, by + 10, 14, 8), 1)

        # 头部（更大）
        pygame.draw.circle(screen, (80, 200, 80), (bx, by + breath), 20)
        pygame.draw.circle(screen, (40, 140, 40), (bx, by + breath), 20, 2)
        pygame.draw.circle(screen, (130, 240, 130, 180), (bx - 7, by - 7 + breath), 7)

        # 双炮管（上下排列）
        for dy in [-6, 6]:
            px = bx + 12 - recoil_off
            py = by + dy - 2 + breath
            pygame.draw.rect(screen, (60, 190, 60), (px, py - 5, 18, 10), border_radius=5)
            pygame.draw.rect(screen, (30, 130, 30), (px, py - 5, 18, 10), 2, border_radius=5)
            pygame.draw.ellipse(screen, (20, 50, 20), (px + 14, py - 4, 6, 8))
            pygame.draw.line(screen, (150, 240, 150), (px + 2, py - 3), (px + 15, py - 3), 1)

        # "双发"标记
        pygame.draw.circle(screen, YELLOW, (bx + 18, by - 8 + breath), 4)
        pygame.draw.circle(screen, YELLOW, (bx + 18, by + 2 + breath), 4)

        # 眼睛
        self._draw_eyes(screen, bx - 2, by - 4 + breath, look_dx=2, blink=True)

        # 射击火花
        if self.recoil > 0:
            for dy in [-6, 6]:
                for si in range(2):
                    sx = bx + 28 - recoil_off + random.randint(-2, 3)
                    sy = by + dy - 2 + breath + random.randint(-3, 3)
                    pygame.draw.circle(screen, (200, 255, 50), (sx, sy), 2 + self.recoil // 2)


# ─────────────────────────────────────────
# 地刺
# ─────────────────────────────────────────
class Spikeweed(Plant):
    def __init__(self, row, col):
        super().__init__("spikeweed", row, col)
        self.spike_dmg = PLANT_DATA["spikeweed"]["spike_dmg"]

    def _draw_body(self, screen, font):
        # 地面裂缝
        pygame.draw.line(screen, (40, 70, 40), (self.x - 20, self.y + 10), (self.x + 20, self.y + 15), 2)
        pygame.draw.line(screen, (40, 70, 40), (self.x - 15, self.y + 14), (self.x + 18, self.y + 8), 2)
        pygame.draw.line(screen, (40, 70, 40), (self.x, self.y + 10), (self.x + 8, self.y + 18), 2)

        # 阴影
        pygame.draw.ellipse(screen, (20, 50, 20), (self.x - 20, self.y + 12, 40, 10))

        # 三层刺（交替摆动）
        for layer in range(3):
            sway = int(math.sin(self.frame * 0.08 + layer * 2) * 3)
            base_y = self.y + 5 - layer * 5
            for side in [-1, 1]:
                tip_x = self.x + side * (10 + layer * 3) + sway
                tip_y = base_y - 12 - layer * 3
                base_x = self.x + side * (6 + layer * 2)
                # 刺主体
                pygame.draw.polygon(screen, (120, 170, 60), [
                    (base_x - 2, base_y), (tip_x, tip_y), (base_x + 2, base_y)
                ])
                pygame.draw.polygon(screen, (80, 130, 40), [
                    (base_x - 2, base_y), (tip_x, tip_y), (base_x + 2, base_y)
                ], 1)
                # 刺尖高光
                pygame.draw.line(screen, (160, 210, 100),
                                 (tip_x - 2, tip_y + 2), (tip_x + 1, tip_y + 6), 1)

        # 低血量刺变黄
        if self.hp < self.max_hp * 0.4:
            for layer in range(3):
                sway = int(math.sin(self.frame * 0.08 + layer * 2) * 3)
                base_y = self.y + 5 - layer * 5
                for side in [-1, 1]:
                    tip_x = self.x + side * (10 + layer * 3) + sway
                    tip_y = base_y - 12 - layer * 3
                    base_x = self.x + side * (6 + layer * 2)
                    pygame.draw.polygon(screen, (180, 160, 60), [
                        (base_x - 2, base_y), (tip_x, tip_y), (base_x + 2, base_y)
                    ])


# ─────────────────────────────────────────
# 阳光菇
# ─────────────────────────────────────────
class SunShroom(Plant):
    def __init__(self, row, col):
        super().__init__("sunshroom", row, col)
        self.sun_accum = 0.0
        self.sun_per_tick = PLANT_DATA["sunshroom"]["sun_per_tick"]
        self.sleep_frames = 600  # 10秒睡眠
        self.high_yield = False

    def update(self):
        super().update()
        self.sun_accum += self.sun_per_tick
        if self.frame > self.sleep_frames and not self.high_yield:
            self.high_yield = True

    def collect_sun(self):
        if self.sun_accum >= 1.0:
            self.sun_accum -= 1.0
            return 40 if self.high_yield else 20
        return 0

    def _draw_body(self, screen, font):
        self._draw_root(screen, (90, 80, 60))

        bx = self.x
        by = self.y - 10

        # 地面发光圈（高产时）
        if self.high_yield:
            glow = int(abs(math.sin(self.frame * 0.08)) * 30 + 15)
            pygame.draw.circle(screen, (255, 220, 100, glow), (bx, by + 10), 30)

        # 菌柄
        pygame.draw.rect(screen, (240, 220, 180), (bx - 6, by + 2, 12, 14))
        pygame.draw.line(screen, (220, 200, 150), (bx - 3, by + 4), (bx - 3, by + 14), 1)

        # 菌帽
        cap_color = (255, 210, 80) if self.high_yield else (220, 190, 120)
        cap_dark = (200, 170, 60) if self.high_yield else (180, 150, 80)
        pygame.draw.ellipse(screen, cap_color, (bx - 18, by - 14, 36, 20))
        pygame.draw.ellipse(screen, cap_dark, (bx - 18, by - 14, 36, 20), 2)
        # 菌帽斑点
        for dx, dy in [(-8, -6), (6, -8), (-2, -10), (10, -4)]:
            pygame.draw.circle(screen, (255, 240, 180), (bx + dx, by + dy), 3)

        # 眼睛
        if self.frame <= self.sleep_frames:
            # 睡眠：Zzz
            self._draw_eyes(screen, bx - 2, by - 2, blink=True)
            # 闭线
            pygame.draw.line(screen, (60, 40, 20), (bx - 8, by - 2), (bx - 2, by - 2), 2)
            pygame.draw.line(screen, (60, 40, 20), (bx + 4, by - 2), (bx + 10, by - 2), 2)
            zzz = font.render("Zzz", True, (200, 200, 200))
            zy = by - 20 - int(self.frame * 0.05) % 10
            screen.blit(zzz, (bx + 8, zy))
        else:
            self._draw_eyes(screen, bx - 2, by - 2, blink=True)
            # 微笑
            pygame.draw.arc(screen, (80, 50, 20), (bx - 5, by + 2, 10, 5), 0.2, 2.9, 1)

        # 菌帽高光
        pygame.draw.ellipse(screen, (255, 240, 200), (bx - 8, by - 12, 10, 5))


# ─────────────────────────────────────────
# 毒菇
# ─────────────────────────────────────────
class FumeShroom(Plant):
    def __init__(self, row, col):
        super().__init__("fumeshroom", row, col)
        self.shoot_cd = PLANT_DATA["fumeshroom"]["shoot_cd"]
        self.shoot_timer = 0
        self.pea_dmg = PLANT_DATA["fumeshroom"]["pea_dmg"]
        self.pea_speed = PLANT_DATA["fumeshroom"]["pea_speed"]
        self._particles = []
        self._drip_timer = 0

    def update(self):
        super().update()
        self.shoot_timer += 1

        # 更新粒子
        self._particles = [(px + dx, py + dy, dx, dy, life - 1, r)
                           for px, py, dx, dy, life, r in self._particles
                           if life > 0]

        if self.has_zombie_in_row and self.frame % 5 == 0:
            self._particles.append((
                self.x + 20,
                self.y - 10,
                random.uniform(0.5, 1.5),
                random.uniform(-0.5, 0.5),
                20,
                random.randint(3, 7)
            ))

        self._drip_timer += 1

    def try_shoot(self):
        if self.has_zombie_in_row and self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            return True
        return False

    def _draw_body(self, screen, font):
        self._draw_root(screen, (100, 70, 100))

        bx = self.x
        by = self.y - 15
        pulse = int(math.sin(self.frame * 0.06) * 3)

        # 菌柄（紫色）
        pygame.draw.rect(screen, (180, 140, 200), (bx - 7, by + 4, 14, 16))
        pygame.draw.line(screen, (150, 110, 170), (bx - 4, by + 6), (bx - 4, by + 18), 1)

        # 菌帽（紫色，脉冲）
        cap_c = (180 + pulse * 5, 80 + pulse * 3, 180 + pulse * 5)
        pygame.draw.ellipse(screen, cap_c, (bx - 20, by - 12 + pulse, 40, 22))
        pygame.draw.ellipse(screen, (120, 40, 120), (bx - 20, by - 12 + pulse, 40, 22), 2)
        # 菌帽斑点
        for dx, dy in [(-10, -4), (8, -6), (0, -10), (12, -2)]:
            pygame.draw.circle(screen, (140, 60, 140), (bx + dx, by + dy + pulse), 3)

        # 眼睛（黄色妖气）
        pygame.draw.ellipse(screen, (255, 255, 100), (bx - 8, by - 2, 7, 8))
        pygame.draw.ellipse(screen, (255, 255, 100), (bx + 3, by - 2, 7, 8))
        pygame.draw.circle(screen, (100, 50, 100), (bx - 5, by + 2), 2)
        pygame.draw.circle(screen, (100, 50, 100), (bx + 6, by + 2), 2)

        # 毒液滴落
        if self._drip_timer % 60 < 30 and self._drip_timer % 60 > 20:
            drop_y = by + 12 + (self._drip_timer % 60 - 20) * 2
            pygame.draw.circle(screen, (150, 50, 200), (bx + 10, drop_y), 3)

        # 地面污渍
        pygame.draw.ellipse(screen, (80, 40, 80, 80), (bx - 15, by + 18, 30, 8))

        # 烟雾粒子
        for px, py, dx, dy, life, r in self._particles:
            alpha = int(life * 10)
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (180, 80, 200, alpha), (r + 1, r + 1), r)
            screen.blit(s, (int(px) - r - 1, int(py) - r - 1))

        # 菌帽高光
        pygame.draw.ellipse(screen, (220, 160, 220), (bx - 6, by - 10 + pulse, 8, 4))


# ─────────────────────────────────────────
# 土豆雷
# ─────────────────────────────────────────
class PotatoMine(Plant):
    def __init__(self, row, col):
        super().__init__("potatomine", row, col)
        self.arm_timer = 0
        self.arm_delay = PLANT_DATA["potatomine"]["arm_delay"]
        self.armed = False
        self.explode_dmg = PLANT_DATA["potatomine"]["explode_dmg"]

    def update(self):
        super().update()
        self.arm_timer += 1
        if self.arm_timer >= self.arm_delay:
            self.armed = True

    def _draw_body(self, screen, font):
        # 泥土堆（未出土）
        dirt_color = (160, 120, 80) if not self.armed else (140, 100, 60)
        pygame.draw.ellipse(screen, dirt_color, (self.x - 22, self.y + 6, 44, 16))
        pygame.draw.ellipse(screen, (120, 90, 60), (self.x - 18, self.y + 10, 36, 10))
        # 出土细线
        for i in range(-3, 4):
            pygame.draw.line(screen, (100, 70, 40),
                             (self.x + i * 7, self.y + 8),
                             (self.x + i * 7 + 3, self.y + 18), 1)

        if not self.armed:
            # 未武装：显示进度%
            progress = min(100, self.arm_timer * 100 // self.arm_delay)
            if self.frame % 60 < 30:
                txt = font.render(f"{progress}%", True, (200, 200, 200))
                screen.blit(txt, (self.x - txt.get_width() // 2, self.y - 20))
            # 只露出一点头顶
            pygame.draw.ellipse(screen, (180, 140, 100), (self.x - 10, self.y + 2, 20, 10))
            return

        # 已武装：完全出土
        bx = self.x
        by = self.y - 8
        # 土豆主体（泥土纹理）
        pygame.draw.ellipse(screen, (180, 140, 100), (self.x - 18, self.y - 10, 36, 28))
        pygame.draw.ellipse(screen, (140, 100, 60), (self.x - 18, self.y - 10, 36, 28), 2)
        # 纹理
        for i in range(3):
            pygame.draw.arc(screen, (150, 110, 70), (self.x - 14 + i*8, self.y - 8, 14, 22), 0.5, 2.5, 1)
        # 眼睛（红眼）
        pygame.draw.ellipse(screen, (255, 50, 50), (bx - 9, by - 6, 7, 8))
        pygame.draw.ellipse(screen, (255, 50, 50), (bx + 4, by - 6, 7, 8))
        pygame.draw.circle(screen, (150, 0, 0), (bx - 6, by - 2), 2)
        pygame.draw.circle(screen, (150, 0, 0), (bx + 7, by - 2), 2)
        # 眉毛（愤怒）
        pygame.draw.line(screen, (100, 40, 40), (bx - 10, by - 8), (bx - 2, by - 4), 2)
        pygame.draw.line(screen, (100, 40, 40), (bx + 4, by - 4), (bx + 12, by - 8), 2)
        # 嘴（缝补线）
        for mx in range(-6, 7, 3):
            pygame.draw.line(screen, (80, 50, 30), (bx + mx, by + 4), (bx + mx, by + 8), 1)
        # 红色指示灯闪烁
        if self.frame % 40 < 20:
            pygame.draw.circle(screen, (255, 30, 30), (bx + 14, by - 8), 4)
            pygame.draw.circle(screen, (255, 100, 100), (bx + 14, by - 8), 2)

        # 天线和顶灯
        pygame.draw.line(screen, (80, 80, 80), (bx, by - 10), (bx, by - 22), 2)
        pygame.draw.circle(screen, (255, 50, 50) if self.frame % 40 < 20 else (100, 50, 50), (bx, by - 22), 4)

        # 出土小石子
        for _ in range(4):
            sx = self.x + random.randint(-20, 20)
            sy = self.y + random.randint(8, 18)
            pygame.draw.circle(screen, (120, 90, 60), (sx, sy), 2)


# ─────────────────────────────────────────
# 工厂函数
# ─────────────────────────────────────────
def create_plant(plant_type, row, col):
    if plant_type == "sunflower":
        return Sunflower(row, col)
    elif plant_type == "peashooter":
        return Peashooter(row, col, freeze=False)
    elif plant_type == "snowpea":
        return Peashooter(row, col, freeze=True)
    elif plant_type == "wallnut":
        return Wallnut(row, col)
    elif plant_type == "cherrycbomb":
        return CherryBomb(row, col)
    elif plant_type == "repeater":
        return Repeater(row, col)
    elif plant_type == "spikeweed":
        return Spikeweed(row, col)
    elif plant_type == "potatomine":
        return PotatoMine(row, col)
    elif plant_type == "sunshroom":
        return SunShroom(row, col)
    elif plant_type == "fumeshroom":
        return FumeShroom(row, col)
    else:
        return Plant(plant_type, row, col)
