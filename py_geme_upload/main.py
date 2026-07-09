# main.py - 植物大战僵尸主文件
import pygame
import sys
import random
import math

from constants import *
from plants import create_plant
from zombies import create_zombie
from projectile import Pea, SunToken, Explosion
from ui import (draw_background, draw_topbar, draw_plant_selector,
                draw_hover_preview, draw_gameover, draw_wave_banner,
                hit_test_plant_selector, hit_test_shovel,
                draw_lawn_mowers, draw_drag_preview)
from menu import MainMenu
import sound


def make_fonts():
    """创建字体，优先使用支持中文的系统字体"""
    import os
    # Windows 中文字体文件路径（按优先级排列）
    font_candidates = [
        "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑（首选）
        "C:/Windows/Fonts/msyhbd.ttc",     # 微软雅黑粗体
        "C:/Windows/Fonts/simhei.ttf",     # 黑体
        "C:/Windows/Fonts/simsun.ttc",     # 宋体
        "C:/Windows/Fonts/Deng.ttf",       # 等线
    ]
    font_path = None
    for p in font_candidates:
        if os.path.isfile(p):
            font_path = p
            break
    if font_path:
        font = pygame.font.Font(font_path, 22)
        font_small = pygame.font.Font(font_path, 16)
        font_big = pygame.font.Font(font_path, 38)
        font.set_bold(True)
        font_big.set_bold(True)
        return font, font_small, font_big
    # 兜底：默认字体（可能不支持中文）
    return (pygame.font.Font(None, 22),
            pygame.font.Font(None, 16),
            pygame.font.Font(None, 38))


class Game:
    def __init__(self, level_idx=0):
        self.level_cfg = LEVELS[level_idx]
        self.wave_config = self.level_cfg["waves"]
        self.bg_mode = self.level_cfg.get("bg_mode", "day")

    def reset(self, screen, clock, fonts):
        self.screen = screen
        self.clock = clock
        self.font, self.font_small, self.font_big = fonts

        self.frame = 0
        self.sun = self.level_cfg.get("starting_sun", STARTING_SUN)
        self.sun_drop_interval = self.level_cfg.get("sun_drop_interval", SUN_DROP_INTERVAL)
        self.sun_drop_timer = 0

        self.plants = {}
        self.zombies = []
        self.peas = []
        self.suns = []
        self.explosions = []
        self.game_over = False
        self.win = False
        self.wave_idx = 0
        self.wave_timer = 0
        self.wave_banner_frame = 0
        self.invasion = False
        self.hover_col = -1
        self.hover_row = -1
        self.return_to_menu = False

        # 拖拽系统
        self.drag_type = None      # None / "plant" / "shovel"
        self.drag_plant_type = None
        self.drag_pos = (0, 0)
        self.drag_start = None

        # 每行一辆小推车
        self.lawn_mowers = [
            {"row": i, "x": float(LAWN_MOWER_X), "triggered": False, "alive": True}
            for i in range(GRID_ROWS)
        ]

    def run(self, screen, clock, fonts):
        self.reset(screen, clock, fonts)
        while True:
            result = self.handle_events()
            if result == "menu":
                return "menu"
            if not self.game_over:
                self.update()
            self.draw()
            self.clock.tick(FPS)

    # ─────────────────────────────────────────
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                if event.key == pygame.K_r:
                    self.reset(self.screen, self.clock,
                               (self.font, self.font_small, self.font_big))
                if event.key == pygame.K_m:
                    muted = sound.toggle_mute()
                    if muted:
                        sound.stop_music()
                    else:
                        sound.start_music()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._on_drag_start(event.pos)

            if event.type == pygame.MOUSEMOTION:
                self.drag_pos = event.pos
                self._update_hover(event.pos)
                if self.drag_start:
                    # 拖拽进行中，判断是否移动足够距离才算真正拖拽
                    dx = event.pos[0] - self.drag_start[0]
                    dy = event.pos[1] - self.drag_start[1]
                    if math.hypot(dx, dy) > 5:
                        if self.drag_type is None and self.drag_plant_type:
                            # 正式开始拖拽
                            self.drag_type = "plant"

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self._on_drag_end(event.pos)

        return None

    def _on_drag_start(self, pos):
        mx, my = pos
        # 检查是否点击了植物卡片
        ptype = hit_test_plant_selector(mx, my)
        if ptype:
            cost = PLANT_DATA[ptype]["cost"]
            if self.level_cfg.get("night_discount"):
                cost = max(1, cost // 2)
            if self.sun >= cost:
                self.drag_start = pos
                self.drag_plant_type = ptype
                self.drag_type = None   # 先不正式拖拽，等移动距离
                return
            # 阳光不够，只高亮显示但不开始拖拽
            return

        # 检查是否点击了铲子
        if hit_test_shovel(mx, my):
            self.drag_start = pos
            self.drag_type = "shovel"
            return

        # 检查是否点击了阳光球
        for sun_tok in self.suns:
            if sun_tok.alive and not sun_tok.collected:
                if sun_tok.get_rect().collidepoint(mx, my):
                    self.sun += sun_tok.value
                    sun_tok.collected = True
                    sun_tok.alive = False
                    sound.play("sun_collect", 0.6)
                    return

    def _update_hover(self, pos):
        mx, my = pos
        self.hover_col = (mx - GRID_X) // CELL_W
        self.hover_row = (my - GRID_Y) // CELL_H

    def _on_drag_end(self, pos):
        mx, my = pos

        if self.drag_type == "plant":
            col = (mx - GRID_X) // CELL_W
            row = (my - GRID_Y) // CELL_H
            if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                self.place_plant(row, col, self.drag_plant_type)

        elif self.drag_type == "shovel":
            col = (mx - GRID_X) // CELL_W
            row = (my - GRID_Y) // CELL_H
            if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                if (row, col) in self.plants:
                    del self.plants[(row, col)]
                    sound.play("shovel", 0.5)

        # 重置拖拽
        self.drag_type = None
        self.drag_plant_type = None
        self.drag_start = None

    def place_plant(self, row, col, plant_type):
        pdata = PLANT_DATA[plant_type]
        cost = pdata["cost"]
        if self.level_cfg.get("night_discount"):
            cost = max(1, cost // 2)
        if self.sun < cost:
            return
        if (row, col) in self.plants:
            return
        self.sun -= cost
        plant = create_plant(plant_type, row, col)
        self.plants[(row, col)] = plant
        sound.play("plant", 0.6)

    # ─────────────────────────────────────────
    def update(self):
        self.frame += 1
        self._update_wave()
        self._update_suns()
        self._update_plants()
        self._update_zombies()
        self._update_lawn_mowers()
        self._update_peas()
        self._update_explosions()
        self._check_win()
        # 偶尔播放僵尸 groan（有僵尸时每 ~5 秒一次）
        if self.zombies and self.frame % 300 == 0:
            sound.play("zombie_groan", 0.25)

    def _update_wave(self):
        if self.wave_idx >= len(self.wave_config):
            return
        wave = self.wave_config[self.wave_idx]
        self.wave_timer += 1
        if self.wave_timer >= wave["delay"]:
            self.wave_timer = 0
            self.wave_idx += 1
            self.wave_banner_frame = 0
            sound.play("wave_start", 0.5)
            for (ztype, row) in wave["zombies"]:
                z = create_zombie(ztype, row)
                z.x += random.randint(0, 80)
                self.zombies.append(z)
        self.wave_banner_frame += 1

    def _update_suns(self):
        if self.sun_drop_interval > 0:
            self.sun_drop_timer += 1
            if self.sun_drop_timer >= self.sun_drop_interval:
                self.sun_drop_timer = 0
                sx = random.randint(GRID_X, GRID_X + GRID_COLS * CELL_W - 20)
                sy = GRID_Y - 30
                self.suns.append(SunToken(sx, sy, SUN_VALUE, fall=True))

        for plant in list(self.plants.values()):
            if plant.type in ("sunflower", "sunshroom") and plant.alive:
                amt = plant.collect_sun()
                if amt > 0:
                    self.suns.append(SunToken(
                        plant.x + random.randint(-20, 20),
                        plant.y - 30, amt, fall=False))
                    sound.play("sun_produce", 0.3)

        self.suns = [s for s in self.suns if s.alive]
        for s in self.suns:
            s.update()

    def _update_plants(self):
        rows_with_zombies = set()
        for z in self.zombies:
            if z.alive:
                rows_with_zombies.add(z.row)

        dead_keys = []
        for key, plant in self.plants.items():
            if not plant.alive:
                dead_keys.append(key)
                continue
            row, col = key

            if hasattr(plant, "has_zombie_in_row"):
                plant.has_zombie_in_row = (row in rows_with_zombies)

            plant.update()

            # 樱桃炸弹
            if plant.type == "cherrycbomb" and getattr(plant, "exploded", False):
                self._do_cherry_explode(plant)

            # 射手发射
            if hasattr(plant, "try_shoot") and plant.try_shoot():
                count = getattr(plant, "shoot_count", lambda: 1)()
                for offset in range(count):
                    is_fume = (plant.type == "fumeshroom")
                    self.peas.append(Pea(
                        plant.x + 30, plant.y - 8 - offset * 10, row,
                        plant.pea_dmg, plant.pea_speed,
                        freeze=getattr(plant, "freeze", False),
                        color=PURPLE if is_fume else None,
                        poison=is_fume,
                        poison_dmg=3 if is_fume else 0
                    ))
                if is_fume:
                    sound.play("poison", 0.3)
                elif getattr(plant, "freeze", False):
                    sound.play("pea_shoot", 0.35)
                    sound.play("freeze", 0.25)
                else:
                    sound.play("pea_shoot", 0.35)

            # 地刺伤害
            if plant.type == "spikeweed":
                for z in self.zombies:
                    if z.alive and z.row == row:
                        zc = z.get_cell_col()
                        if zc == col:
                            z.take_damage(plant.spike_dmg)

            # 土豆雷
            if plant.type == "potatomine" and getattr(plant, "armed", False):
                for z in self.zombies:
                    if z.alive and z.row == row:
                        zc = z.get_cell_col()
                        if zc == col:
                            z.take_damage(plant.explode_dmg)
                            self.explosions.append(Explosion(plant.x, plant.y))
                            sound.play("explosion", 0.5)
                            plant.alive = False
                            break

        for k in dead_keys:
            del self.plants[k]

    def _do_cherry_explode(self, plant):
        self.explosions.append(Explosion(plant.x, plant.y))
        sound.play("explosion", 0.6)
        r_range = plant.explode_radius
        for z in self.zombies:
            if not z.alive:
                continue
            if abs(z.row - plant.row) <= r_range:
                zc = z.get_cell_col()
                if abs(zc - plant.col) <= r_range + 1:
                    z.take_damage(plant.explode_dmg)

    def _update_zombies(self):
        new_zombies = []
        # 预建行->植物索引，避免每个僵尸都遍历全部植物
        plants_by_row = {}
        for (r, c), p in self.plants.items():
            if not p.alive:
                continue
            plants_by_row.setdefault(r, []).append(p)
        for lst in plants_by_row.values():
            lst.sort(key=lambda p: p.col, reverse=True)

        for z in self.zombies:
            if not z.alive:
                continue
            plants_in_row = plants_by_row.get(z.row, [])
            invaded = z.update(plants_in_row)

            if invaded:
                lm = next((m for m in self.lawn_mowers if m["row"] == z.row), None)
                if lm and lm["alive"] and not lm["triggered"]:
                    lm["triggered"] = True
                    sound.play("lawn_mower", 0.6)
                else:
                    self.invasion = True
                    self.game_over = True

            if hasattr(z, "should_summon") and z.should_summon:
                z.should_summon = False
                nearby_rows = [r for r in range(GRID_ROWS) if r != z.row]
                if nearby_rows:
                    summon_row = random.choice(nearby_rows)
                    backup = create_zombie("normal", summon_row)
                    backup.x = z.x + random.randint(-40, 40)
                    new_zombies.append(backup)

        self.zombies = [z for z in self.zombies if z.alive] + new_zombies

    def _update_lawn_mowers(self):
        for lm in self.lawn_mowers:
            if not lm["alive"] or not lm["triggered"]:
                continue
            lm["x"] += 12

            mx = int(lm["x"])
            my = GRID_Y + lm["row"] * CELL_H + CELL_H // 2
            for z in self.zombies:
                if not z.alive or z.row != lm["row"]:
                    continue
                if abs(z.x - mx) < 35 and abs(z.y - my) < 40:
                    z.take_damage(9999)
                    z.alive = False

            if lm["x"] > SCREEN_WIDTH + 50:
                lm["alive"] = False
                for z in self.zombies:
                    if z.alive and z.row == lm["row"]:
                        z.take_damage(9999)
                        z.alive = False

    def _update_peas(self):
        for pea in self.peas:
            pea.update()
            if not pea.alive:
                continue
            for z in self.zombies:
                if not z.alive or z.row != pea.row:
                    continue
                dist = abs(pea.x - z.x)
                if dist < 22:
                    z.take_damage(pea.dmg, freeze=pea.freeze)
                    if pea.poison:
                        z.poisoned = 180
                        z.poison_dmg = pea.poison_dmg
                    pea.alive = False
                    sound.play("pea_hit", 0.3)
                    break

        self.peas = [p for p in self.peas if p.alive]

    def _update_explosions(self):
        for ex in self.explosions:
            ex.update()
        self.explosions = [e for e in self.explosions if e.alive]

    def _check_win(self):
        if (self.wave_idx >= len(self.wave_config)
                and len(self.zombies) == 0
                and not self.game_over):
            self.game_over = True
            self.win = True
            sound.play("win", 0.7)
            sound.stop_music()

        if self.invasion and not self.win:
            sound.play("lose", 0.7)
            sound.stop_music()

    # ─────────────────────────────────────────
    def draw(self):
        draw_background(self.screen, self.frame, self.bg_mode)

        # 拖拽植物时显示格子高亮
        if self.drag_type == "plant" and not self.game_over:
            if (0 <= self.hover_col < GRID_COLS
                    and 0 <= self.hover_row < GRID_ROWS
                    and (self.hover_row, self.hover_col) not in self.plants):
                draw_hover_preview(self.screen, self.hover_col, self.hover_row,
                                   self.drag_plant_type, self.font_small)

        # 拖拽铲子时显示目标植物高亮
        if self.drag_type == "shovel" and not self.game_over:
            if (0 <= self.hover_col < GRID_COLS
                    and 0 <= self.hover_row < GRID_ROWS
                    and (self.hover_row, self.hover_col) in self.plants):
                x = GRID_X + self.hover_col * CELL_W
                y = GRID_Y + self.hover_row * CELL_H
                s = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA)
                s.fill((255, 0, 0, 80))
                self.screen.blit(s, (x, y))
                pygame.draw.rect(self.screen, RED, (x, y, CELL_W, CELL_H), 2)

        for plant in self.plants.values():
            plant.draw(self.screen, self.font_small)

        for z in self.zombies:
            z.draw(self.screen)

        for pea in self.peas:
            pea.draw(self.screen)

        for sun_tok in self.suns:
            sun_tok.draw(self.screen)

        for ex in self.explosions:
            ex.draw(self.screen)

        draw_lawn_mowers(self.screen, self.lawn_mowers)

        pygame.draw.line(self.screen, RED,
                         (GRID_X - 5, GRID_Y),
                         (GRID_X - 5, GRID_Y + GRID_ROWS * CELL_H), 3)

        draw_topbar(self.screen, self.sun, self.wave_idx,
                    len(self.wave_config), self.font, self.font_small,
                    self.level_cfg["name"])

        # 高亮显示被拖拽的植物卡片
        if self.drag_type == "shovel":
            highlight = "_shovel_"
        elif self.drag_type == "plant" or self.drag_plant_type:
            highlight = self.drag_plant_type
        else:
            highlight = None
        draw_plant_selector(self.screen, self.sun, self.font_small,
                            night_discount=self.level_cfg.get("night_discount", False),
                            highlight_plant=highlight)

        if self.wave_idx > 0 and self.wave_banner_frame < 150:
            draw_wave_banner(self.screen, self.font_big,
                             self.wave_idx, self.wave_banner_frame)

        # 拖拽预览（跟随鼠标）
        if self.drag_type:
            draw_drag_preview(self.screen, self.drag_type,
                              self.drag_plant_type, *self.drag_pos, self.font_small)

        # 提示文字
        hint = self.font_small.render(
            "拖拽卡片种植  铲子铲除  R重置  M静音  ESC返回菜单",
            True, (220, 220, 220))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                BOTTOM_BAR_Y + BOTTOM_BAR_H - 18))

        if self.game_over:
            draw_gameover(self.screen, self.font_big, self.font, win=self.win)

        pygame.display.flip()


# ─────────────────────────────────────────
# 入口
# ─────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    fonts = make_fonts()
    sound.init()
    sound.start_music()

    while True:
        menu = MainMenu(screen, clock, fonts)
        level_idx = menu.run()
        if level_idx is None:
            break
        game = Game(level_idx)
        result = game.run(screen, clock, fonts)
        if result != "menu":
            break

    sound.stop_music()
    pygame.quit()


if __name__ == "__main__":
    main()
