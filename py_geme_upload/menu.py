# menu.py - 主菜单、关卡选择界面
import pygame
import math
import sys
from constants import *
import sound


class MainMenu:
    """主菜单界面：标题 + 关卡选择 + 开始游戏"""

    _bg_cache = None  # 类级背景缓存

    def __init__(self, screen, clock, fonts):
        self.screen = screen
        self.clock = clock
        self.font, self.font_small, self.font_big = fonts
        self.frame = 0
        self.selected_level = 0   # 0-based index
        self.state = "main"       # "main" | "level_select"
        self.hover_btn = -1
        self.particles = []
        self._init_particles()
        # 预渲染静态背景
        if MainMenu._bg_cache is None:
            MainMenu._bg_cache = self._build_static_bg()

    def _build_static_bg(self):
        """预渲染菜单静态背景（渐变天空+底部草地）"""
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for i in range(SCREEN_HEIGHT):
            t = i / SCREEN_HEIGHT
            r = int(20 + 80 * t)
            g = int(60 + 100 * t)
            b = int(20 + 80 * t)
            pygame.draw.line(surf, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        # 底部草地
        pygame.draw.rect(surf, (40, 120, 40),
                         (0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 80))
        for gi in range(0, SCREEN_WIDTH, 40):
            h = 10 + (gi % 15)
            pygame.draw.polygon(surf, (60, 160, 60), [
                (gi, SCREEN_HEIGHT - 80),
                (gi + 20, SCREEN_HEIGHT - 80 - h),
                (gi + 40, SCREEN_HEIGHT - 80),
            ])
        return surf

    def _init_particles(self):
        import random
        for _ in range(25):
            self.particles.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "vy": random.uniform(0.3, 1.2),
                "vx": random.uniform(-0.3, 0.3),
                "r": random.randint(6, 14),
                "phase": random.uniform(0, math.pi * 2),
            })

    def _update_particles(self):
        import random
        for p in self.particles:
            p["y"] += p["vy"]
            p["x"] += p["vx"]
            p["phase"] += 0.03
            if p["y"] > SCREEN_HEIGHT + 20:
                p["y"] = -20
                p["x"] = random.randint(0, SCREEN_WIDTH)

    def run(self):
        """运行菜单，返回选中的关卡index（0-based），或 None 表示退出"""
        while True:
            self.frame += 1
            self._update_particles()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "level_select":
                            self.state = "main"
                        else:
                            pygame.quit()
                            sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    result = self._handle_click(*event.pos)
                    if result is not None:
                        return result
                if event.type == pygame.MOUSEMOTION:
                    self._handle_hover(*event.pos)

            self._draw()
            self.clock.tick(FPS)

    def _handle_hover(self, mx, my):
        if self.state == "main":
            btns = self._get_main_buttons()
        else:
            btns = self._get_level_buttons()
        self.hover_btn = -1
        for i, (bx, by, bw, bh, _) in enumerate(btns):
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.hover_btn = i
                break

    def _handle_click(self, mx, my):
        if self.state == "main":
            btns = self._get_main_buttons()
            for i, (bx, by, bw, bh, label) in enumerate(btns):
                if bx <= mx <= bx + bw and by <= my <= by + bh:
                    sound.play("button_click", 0.5)
                    if label == "开始游戏":
                        self.state = "level_select"
                    elif label == "退出游戏":
                        pygame.quit()
                        sys.exit()
        else:
            btns = self._get_level_buttons()
            for i, (bx, by, bw, bh, label) in enumerate(btns):
                if bx <= mx <= bx + bw and by <= my <= by + bh:
                    if label == "返回":
                        sound.play("button_click", 0.5)
                        self.state = "main"
                    else:
                        sound.play("game_start", 0.6)
                        return i
        return None

    def _get_main_buttons(self):
        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 240, 56
        return [
            (cx - btn_w // 2, 400, btn_w, btn_h, "开始游戏"),
            (cx - btn_w // 2, 470, btn_w, btn_h, "退出游戏"),
        ]

    def _get_level_buttons(self):
        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 480, 80
        btns = []
        for i, lv in enumerate(LEVELS):
            btns.append((cx - btn_w // 2, 240 + i * 100, btn_w, btn_h,
                         f"关卡{lv['id']} - {lv['name']}"))
        btns.append((cx - 100, 240 + len(LEVELS) * 100 + 10, 200, 50, "返回"))
        return btns

    def _draw(self):
        self._draw_bg()
        if self.state == "main":
            self._draw_main()
        else:
            self._draw_level_select()
        pygame.display.flip()

    def _draw_bg(self):
        # blit 缓存的静态背景
        self.screen.blit(MainMenu._bg_cache, (0, 0))

        # 飘落阳光粒子（动态）
        for p in self.particles:
            alpha_val = int(abs(math.sin(p["phase"])) * 160 + 80)
            r_size = p["r"]
            surf = pygame.Surface((r_size * 2 + 2, r_size * 2 + 2), pygame.SRCALPHA)
            color = (255, 215, 0, min(255, alpha_val))
            pygame.draw.circle(surf, color, (r_size + 1, r_size + 1), r_size)
            self.screen.blit(surf, (int(p["x"]) - r_size, int(p["y"]) - r_size))

    def _draw_title(self):
        """绘制游戏标题"""
        cx = SCREEN_WIDTH // 2
        # 大背景光晕
        glow_r = int(abs(math.sin(self.frame * 0.02)) * 20 + 60)
        glow_surf = pygame.Surface((500, 160), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (255, 200, 0, 40), (0, 0, 500, 160))
        self.screen.blit(glow_surf, (cx - 250, 60))

        # 标题文字（逐字描边）
        title1 = self.font_big.render("植物大战僵尸", True, (50, 200, 50))
        title2 = self.font_big.render("植物大战僵尸", True, YELLOW)
        # 阴影
        self.screen.blit(title1, (cx - title1.get_width() // 2 + 3, 103))
        self.screen.blit(title2, (cx - title2.get_width() // 2, 100))

        sub = self.font.render("Python 复刻版", True, (200, 255, 200))
        self.screen.blit(sub, (cx - sub.get_width() // 2, 155))

        # 小植物装饰
        self._draw_deco_plants(cx)

    def _draw_deco_plants(self, cx):
        """标题两侧装饰植物"""
        f = self.frame
        for side, sx in [(-1, cx - 260), (1, cx + 240)]:
            bob = int(math.sin(f * 0.05) * 4)
            # 向日葵
            angle_off = f * 0.03
            for pi in range(8):
                ang = angle_off + pi * math.pi / 4
                px = sx + int(math.cos(ang) * 18)
                py = 130 + int(math.sin(ang) * 18) + bob
                pygame.draw.circle(self.screen, ORANGE, (px, py), 7)
            pygame.draw.circle(self.screen, YELLOW, (sx, 130 + bob), 13)

    def _draw_main(self):
        self._draw_title()
        cx = SCREEN_WIDTH // 2
        btns = self._get_main_buttons()
        for i, (bx, by, bw, bh, label) in enumerate(btns):
            is_hover = (self.hover_btn == i)
            self._draw_button(bx, by, bw, bh, label, is_hover,
                              color=(60, 160, 60) if i == 0 else (160, 60, 60))

        # 操作提示
        tip = self.font_small.render("点击「开始游戏」选择关卡", True, (180, 255, 180))
        self.screen.blit(tip, (cx - tip.get_width() // 2, 545))

    def _draw_level_select(self):
        cx = SCREEN_WIDTH // 2

        # 标题
        title = self.font_big.render("选择关卡", True, YELLOW)
        self.screen.blit(title, (cx - title.get_width() // 2, 150))

        btns = self._get_level_buttons()
        level_count = len(LEVELS)
        for i, (bx, by, bw, bh, label) in enumerate(btns):
            is_hover = (self.hover_btn == i)
            if i < level_count:
                lv = LEVELS[i]
                self._draw_level_card(bx, by, bw, bh, lv, is_hover, i)
            else:
                self._draw_button(bx, by, bw, bh, "返回", is_hover,
                                  color=(100, 100, 100))

    def _draw_level_card(self, bx, by, bw, bh, lv, is_hover, idx):
        """绘制关卡卡片"""
        bg_colors = {
            "day": (60, 120, 40),
            "night": (20, 30, 80),
            "fog": (100, 100, 100),
        }
        accent_colors = {
            "day": (120, 220, 80),
            "night": (80, 100, 200),
            "fog": (180, 180, 180),
        }
        bg = bg_colors.get(lv["bg_mode"], (60, 100, 60))
        accent = accent_colors.get(lv["bg_mode"], YELLOW)

        if is_hover:
            bg = tuple(min(255, c + 30) for c in bg)

        pygame.draw.rect(self.screen, bg, (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(self.screen, accent, (bx, by, bw, bh), 3, border_radius=10)

        # 关卡编号徽章
        badge_r = 22
        pygame.draw.circle(self.screen, accent, (bx + 32, by + bh // 2), badge_r)
        num_txt = self.font.render(str(lv["id"]), True, (20, 20, 20))
        self.screen.blit(num_txt, (bx + 32 - num_txt.get_width() // 2,
                                   by + bh // 2 - num_txt.get_height() // 2))

        # 关卡名
        name_txt = self.font.render(lv["name"], True, WHITE)
        self.screen.blit(name_txt, (bx + 68, by + 14))

        # 关卡描述
        desc_txt = self.font_small.render(lv["desc"], True, (200, 220, 200))
        self.screen.blit(desc_txt, (bx + 68, by + 44))

    def _draw_button(self, bx, by, bw, bh, label, is_hover, color=(60, 140, 60)):
        bg = tuple(min(255, c + 30) for c in color) if is_hover else color
        pygame.draw.rect(self.screen, bg, (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(self.screen, WHITE, (bx, by, bw, bh), 2, border_radius=10)

        txt = self.font.render(label, True, WHITE)
        self.screen.blit(txt, (bx + bw // 2 - txt.get_width() // 2,
                               by + bh // 2 - txt.get_height() // 2))
