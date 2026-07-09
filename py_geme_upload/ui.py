# ui.py - 界面绘制
import pygame
import random
import math
from constants import *


# ─────────────────────────────────────────
# 背景
# ─────────────────────────────────────────

# 静态背景缓存：避免每帧重绘天空渐变+草地+山丘
_bg_cache = {}


def _get_static_bg(bg_mode):
    """获取缓存的静态背景 Surface（天空+山丘/树+草地），按 bg_mode 缓存"""
    if bg_mode in _bg_cache:
        return _bg_cache[bg_mode]
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    if bg_mode == "night":
        _build_night_static(surf)
    elif bg_mode == "fog":
        _build_fog_static(surf)
    else:
        _build_day_static(surf)
    _bg_cache[bg_mode] = surf
    return surf


def draw_background(screen, frame, bg_mode="day"):
    # 1. blit 缓存的静态背景
    screen.blit(_get_static_bg(bg_mode), (0, 0))
    # 2. 绘制动态元素
    if bg_mode == "night":
        _draw_night_dynamic(screen, frame)
    elif bg_mode == "fog":
        _draw_fog_dynamic(screen, frame)
    else:
        _draw_day_dynamic(screen, frame)
    _draw_scene_particles(screen, frame, bg_mode)


# ─── 白天（静态部分） ───
def _build_day_static(surf):
    sky_h = GRID_Y
    # 天空渐变
    for i in range(sky_h):
        t = i / sky_h
        r = int(135 + (220 - 135) * t)
        g = int(206 + (240 - 206) * t)
        b = int(235 + (255 - 235) * t)
        pygame.draw.line(surf, (r, g, b), (0, i), (SCREEN_WIDTH, i))

    # 远处山丘
    hill_pts = [(0, sky_h - 5)]
    for hx in range(0, SCREEN_WIDTH + 40, 40):
        hy = sky_h - 35 - int(math.sin(hx * 0.01) * 20) - int(math.sin(hx * 0.005) * 15)
        hill_pts.append((hx, hy))
    hill_pts.append((SCREEN_WIDTH, sky_h - 5))
    pygame.draw.polygon(surf, (60, 170, 60), hill_pts)
    pygame.draw.polygon(surf, (45, 140, 45), hill_pts)

    _draw_grass(surf, dark=False)


# ─── 白天（动态部分：云朵） ───
def _draw_day_dynamic(screen, frame):
    clouds = [
        (120 + frame * 0.3, 35, 60, 20),
        (400 + frame * 0.2, 50, 80, 25),
        (700 + frame * 0.4, 28, 50, 18),
        (950 + frame * 0.25, 45, 70, 22),
    ]
    for cx0, cy, cw, ch in clouds:
        cx = cx0 % (SCREEN_WIDTH + 120) - 60
        for px, py, pr in [(0, 0, ch), (cw//4, -ch//3, ch//2), (cw//2, -ch//5, ch//2), (cw*3//4, 0, ch)]:
            pygame.draw.ellipse(screen, (240, 250, 255), (cx + px - pr, cy + py, pr*2, pr*2))


# ─── 夜晚（静态部分） ───
def _build_night_static(surf):
    sky_h = GRID_Y
    for i in range(sky_h):
        t = i / sky_h
        r = int(5 + 15 * t)
        g = int(5 + 15 * t)
        b = int(20 + 40 * t)
        pygame.draw.line(surf, (r, g, b), (0, i), (SCREEN_WIDTH, i))

    # 月亮 + 光晕（静态）
    mx, my = SCREEN_WIDTH - 80, 50
    for r in range(32, 18, -4):
        a = int(30 - (r - 18) * 2)
        moon_glow = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(moon_glow, (240, 240, 200, a), (r + 1, r + 1), r)
        surf.blit(moon_glow, (mx - r - 1, my - r - 1))
    pygame.draw.circle(surf, (240, 240, 200), (mx, my), 28)
    pygame.draw.circle(surf, (20, 20, 60), (mx - 6, my - 4), 22)
    pygame.draw.circle(surf, (200, 200, 180), (mx + 8, my + 6), 4)
    pygame.draw.circle(surf, (200, 200, 180), (mx - 5, my + 10), 3)

    _draw_grass(surf, dark=True)


# ─── 夜晚（动态部分：闪烁星星） ───
def _draw_night_dynamic(screen, frame):
    sky_h = GRID_Y
    for si in range(50):
        sx = (si * 137 + 47) % SCREEN_WIDTH
        sy = (si * 97 + 23) % (sky_h - 20)
        bright = int(abs(math.sin(frame * 0.02 + si * 0.7)) * 180 + 60)
        sz = 1 + (si % 2)
        pygame.draw.circle(screen, (bright, bright, bright), (sx, sy), sz)


# ─── 雾天（静态部分） ───
def _build_fog_static(surf):
    sky_h = GRID_Y
    for i in range(sky_h):
        t = i / sky_h
        c = int(140 + 50 * t)
        pygame.draw.line(surf, (c, c, c + 10), (0, i), (SCREEN_WIDTH, i))

    # 枯树剪影
    for tx, tw in [(200, 3), (600, 4), (850, 2)]:
        ty = sky_h - 5
        pygame.draw.line(surf, (70, 70, 70), (tx, ty), (tx, ty - 40), tw)
        for bi in range(3):
            bx = tx + int(math.sin(bi * 1.2) * 25)
            by = ty - 30 + bi * 8
            pygame.draw.line(surf, (70, 70, 70), (tx, by + 8), (bx, by), max(1, tw - 1))

    _draw_grass(surf)


# ─── 雾天（动态部分：浓雾层） ───
def _draw_fog_dynamic(screen, frame):
    for fi in range(4):
        fx = (frame * (1 + fi * 0.3)) % (SCREEN_WIDTH + 400) - 200
        fog = pygame.Surface((500, 100), pygame.SRCALPHA)
        for gy in range(0, 100, 20):
            a = int(40 + fi * 10 - gy * 0.2)
            if a > 0:
                pygame.draw.rect(fog, (200, 200, 200, a), (0, gy, 500, 20))
        screen.blit(fog, (int(fx), GRID_Y + fi * 60 - 20))
        screen.blit(fog, (int(fx) + SCREEN_WIDTH + 400, GRID_Y + fi * 60 - 20))


# ─── 草地（带纹理、路径、边缘） ───
def _draw_grass(screen, dark=False):
    grass_top = GRID_Y - 5
    grass_h = GRID_ROWS * CELL_H + 20
    base = (35, 80, 35) if dark else (55, 120, 55)
    pygame.draw.rect(screen, base, (0, grass_top, SCREEN_WIDTH, grass_h))

    # 泥土路径（前3列是灰色砖路）
    for col in range(3):
        px = GRID_X + col * CELL_W
        for row in range(GRID_ROWS):
            py = GRID_Y + row * CELL_H
            brick_color = (120, 110, 90) if dark else (140, 130, 110)
            pygame.draw.rect(screen, brick_color, (px, py, CELL_W, CELL_H))
            # 砖缝
            pygame.draw.line(screen, (100, 90, 70), (px + CELL_W - 1, py), (px + CELL_W - 1, py + CELL_H), 1)
            pygame.draw.line(screen, (100, 90, 70), (px, py + CELL_H - 1), (px + CELL_W, py + CELL_H - 1), 1)
            # 砖块随机污渍
            if (col + row * 3) % 5 == 0:
                pygame.draw.ellipse(screen, (150, 140, 120), (px + 10, py + 15, 15, 8))

    # 草地格子
    for row in range(GRID_ROWS):
        for col in range(3, GRID_COLS):
            x = GRID_X + col * CELL_W
            y = GRID_Y + row * CELL_H
            if dark:
                color = (50, 100, 50) if (row + col) % 2 == 0 else (40, 85, 40)
            else:
                color = (80, 160, 70) if (row + col) % 2 == 0 else (70, 150, 60)
            pygame.draw.rect(screen, color, (x, y, CELL_W, CELL_H))
            pygame.draw.rect(screen, (50, 120, 50), (x, y, CELL_W, CELL_H), 1)
            # 随机草丛点缀
            if (row * 7 + col * 13) % 4 == 0:
                gx = x + 10 + (col * 17) % (CELL_W - 20)
                gy = y + 8 + (row * 11) % (CELL_H - 16)
                for gi in range(3):
                    tx = gx + gi * 6 - 6
                    h = 5 + (gi + row) % 4
                    pygame.draw.polygon(screen, (30 + gi * 15, 100 + gi * 10, 30), [
                        (tx, gy + h), (tx + 3, gy - h), (tx + 6, gy + h)
                    ])

    # 草地顶部/底部边缘（波浪）
    for edge_y in [grass_top, grass_top + grass_h]:
        for ex in range(0, SCREEN_WIDTH, 12):
            wave = int(math.sin(ex * 0.15 + 1.5) * 3)
            top = edge_y if edge_y == grass_top else edge_y - 4
            pygame.draw.polygon(screen, (30, 100, 30), [
                (ex, top + (0 if edge_y == grass_top else 4)),
                (ex + 6, top + wave + (0 if edge_y == grass_top else 4)),
                (ex + 12, top + (0 if edge_y == grass_top else 4))
            ])

    # 行分隔线（小土坡）
    for row in range(1, GRID_ROWS):
        ly = GRID_Y + row * CELL_H - 2
        for lx in range(0, SCREEN_WIDTH, 8):
            bump = int(math.sin(lx * 0.2) * 2)
            pygame.draw.line(screen, (40, 90, 40), (lx, ly + bump), (lx + 4, ly + bump), 2)


# ─── 场景粒子（飘叶/萤火虫等） ───
_scene_particles = []
def _draw_scene_particles(screen, frame, bg_mode):
    global _scene_particles
    # 初始化粒子
    if not _scene_particles:
        for _ in range(30):
            _scene_particles.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, GRID_Y + GRID_ROWS * CELL_H),
                "vx": random.uniform(-0.5, 1.5),
                "vy": random.uniform(0.2, 1.0),
                "phase": random.uniform(0, math.pi * 2),
                "size": random.randint(2, 5),
            })

    for p in _scene_particles:
        p["x"] += p["vx"] + math.sin(frame * 0.01 + p["phase"]) * 0.5
        p["y"] += p["vy"]
        p["phase"] += 0.02
        if p["x"] > SCREEN_WIDTH + 10 or p["y"] > BOTTOM_BAR_Y:
            p["x"] = random.randint(-10, SCREEN_WIDTH // 2)
            p["y"] = random.randint(-10, GRID_Y)

        if bg_mode == "day":
            # 飘叶
            wobble = int(math.sin(p["phase"]) * 4)
            color = (120 + int(math.sin(p["phase"]) * 40), 160 + wobble, 60)
            sx, sy = int(p["x"]), int(p["y"])
            pygame.draw.ellipse(screen, color, (sx, sy, p["size"]*2, p["size"]))
        elif bg_mode == "night":
            # 萤火虫
            glow = int(abs(math.sin(p["phase"])) * 120 + 60)
            pygame.draw.circle(screen, (200, 255, 100, glow), (int(p["x"]), int(p["y"])), p["size"])
        elif bg_mode == "fog":
            # 灰尘
            a = int(30 + abs(math.sin(p["phase"])) * 30)
            s = pygame.Surface((p["size"]*3, p["size"]*3), pygame.SRCALPHA)
            s.fill((180, 180, 180, a))
            screen.blit(s, (int(p["x"]), int(p["y"])))


# ─────────────────────────────────────────
# 顶部信息栏
# ─────────────────────────────────────────
def _draw_sun_icon(screen, cx, cy, r=15):
    pygame.draw.circle(screen, YELLOW, (cx, cy), r)
    pygame.draw.circle(screen, ORANGE, (cx, cy), r, 2)
    for i in range(8):
        angle = i * math.pi / 4
        x1 = cx + int(math.cos(angle) * (r + 2))
        y1 = cy + int(math.sin(angle) * (r + 2))
        x2 = cx + int(math.cos(angle) * (r + 6))
        y2 = cy + int(math.sin(angle) * (r + 6))
        pygame.draw.line(screen, ORANGE, (x1, y1), (x2, y2), 2)


def draw_topbar(screen, sun, wave_idx, total_waves, font, font_small, level_name=""):
    """顶部信息栏"""
    pygame.draw.rect(screen, (25, 25, 25), (0, 0, SCREEN_WIDTH, 62))
    pygame.draw.rect(screen, YELLOW, (0, 60, SCREEN_WIDTH, 2))

    _draw_sun_icon(screen, 32, 31, 15)
    sun_txt = font.render(str(sun), True, YELLOW)
    screen.blit(sun_txt, (54, 18))

    wave_str = f"第 {wave_idx}/{total_waves} 波"
    w_txt = font_small.render(wave_str, True, WHITE)
    screen.blit(w_txt, (SCREEN_WIDTH // 2 - w_txt.get_width() // 2, 22))

    if level_name:
        t = font_small.render(level_name, True, (220, 220, 100))
        screen.blit(t, (SCREEN_WIDTH - t.get_width() - 12, 22))


# ─────────────────────────────────────────
# 底部横向植物选择栏 + 铲子
# ─────────────────────────────────────────
CARD_W = 80
CARD_H = 80
CARD_PAD = 6

SHOVEL_W = 56
SHOVEL_H = 70


def get_plant_card_rect(i):
    total_cards = len(PLANT_TYPES)
    total_width = total_cards * CARD_W + (total_cards - 1) * CARD_PAD
    start_x = (SCREEN_WIDTH - total_width) // 2
    x = start_x + i * (CARD_W + CARD_PAD)
    y = BOTTOM_BAR_Y + (BOTTOM_BAR_H - CARD_H) // 2
    return x, y, CARD_W, CARD_H


def get_shovel_rect():
    total_cards = len(PLANT_TYPES)
    total_width = total_cards * CARD_W + (total_cards - 1) * CARD_PAD
    start_x = (SCREEN_WIDTH - total_width) // 2
    last_x = start_x + (total_cards - 1) * (CARD_W + CARD_PAD)
    x = last_x + CARD_W + 15
    y = BOTTOM_BAR_Y + (BOTTOM_BAR_H - SHOVEL_H) // 2
    return x, y, SHOVEL_W, SHOVEL_H


def draw_plant_selector(screen, sun, font_small,
                        night_discount=False, highlight_plant=None):
    """底部横向植物选择栏"""
    pygame.draw.rect(screen, (25, 35, 25),
                     (0, BOTTOM_BAR_Y, SCREEN_WIDTH, BOTTOM_BAR_H))
    pygame.draw.rect(screen, (60, 120, 60),
                     (0, BOTTOM_BAR_Y, SCREEN_WIDTH, 2))

    if night_discount:
        tip = font_small.render("夜晚关卡  植物费用 5 折", True, ORANGE)
        screen.blit(tip, (8, BOTTOM_BAR_Y + 4))

    for i, ptype in enumerate(PLANT_TYPES):
        data = PLANT_DATA[ptype]
        cx, cy, cw, ch = get_plant_card_rect(i)
        cost = max(1, data["cost"] // 2) if night_discount else data["cost"]
        can_afford = sun >= cost
        is_drag = (highlight_plant == ptype)

        # 卡片背景
        if is_drag:
            bg = (100, 160, 90)
        elif can_afford:
            bg = (45, 75, 45)
        else:
            bg = (70, 40, 40)
        pygame.draw.rect(screen, bg, (cx, cy, cw, ch), border_radius=6)

        if is_drag:
            pygame.draw.rect(screen, YELLOW, (cx, cy, cw, ch), 2, border_radius=6)
        else:
            border = (80, 140, 60) if can_afford else (100, 60, 60)
            pygame.draw.rect(screen, border, (cx, cy, cw, ch), 1, border_radius=6)

        # 图标
        icon_color = data["color"] if can_afford else DARK_GRAY
        icx = cx + cw // 2
        icy = cy + 26
        pygame.draw.circle(screen, icon_color, (icx, icy), 18)
        pygame.draw.circle(screen, BLACK, (icx, icy), 18, 1)
        pygame.draw.circle(screen, (*[min(255, c + 80) for c in icon_color], 180),
                           (icx - 5, icy - 5), 6)

        # 名称
        name = data["name"]
        nc = WHITE if can_afford else GRAY
        nt = font_small.render(name, True, nc)
        screen.blit(nt, (cx + cw // 2 - nt.get_width() // 2, cy + ch - 30))

        # 费用
        cost_color = YELLOW if can_afford else (180, 80, 80)
        if night_discount:
            cost_color = ORANGE if can_afford else (180, 80, 80)
        ct = font_small.render(str(cost), True, cost_color)
        total_w = 10 + 2 + ct.get_width()
        sx = cx + cw // 2 - total_w // 2
        sy = cy + ch - 14
        pygame.draw.circle(screen, YELLOW, (sx + 5, sy + 6), 5)
        screen.blit(ct, (sx + 12, sy))

    # 绘制铲子按钮
    draw_shovel_button(screen, font_small, is_dragging=(highlight_plant == "_shovel_"))


def draw_shovel_button(screen, font_small, is_dragging=False):
    """绘制铲子按钮"""
    sx, sy, sw, sh = get_shovel_rect()

    # 背景
    if is_dragging:
        bg = (90, 70, 55)
        border = (230, 200, 170)
    else:
        bg = (60, 40, 30)
        border = (150, 120, 100)
    pygame.draw.rect(screen, bg, (sx, sy, sw, sh), border_radius=5)
    pygame.draw.rect(screen, border, (sx, sy, sw, sh), 2, border_radius=5)

    cx = sx + sw // 2
    cy = sy + sh // 2 - 6

    # 铲头（金属色）
    pygame.draw.polygon(screen, (120, 120, 120), [
        (cx - 12, cy - 4), (cx + 12, cy - 4),
        (cx + 10, cy + 8), (cx - 10, cy + 8)
    ])
    pygame.draw.polygon(screen, (180, 180, 180), [
        (cx - 12, cy - 4), (cx + 12, cy - 4),
        (cx + 10, cy + 8), (cx - 10, cy + 8)
    ], 2)
    # 高光
    pygame.draw.line(screen, (220, 220, 220), (cx - 8, cy - 2), (cx + 8, cy - 2), 1)

    # 铲柄
    pygame.draw.line(screen, (100, 70, 40), (cx, cy + 8), (cx, cy + 20), 4)
    # 手柄（D形）
    pygame.draw.line(screen, (100, 70, 40), (cx - 5, cy + 20), (cx + 5, cy + 20), 3)
    pygame.draw.line(screen, (100, 70, 40), (cx - 5, cy + 20), (cx - 5, cy + 26), 2)
    pygame.draw.line(screen, (100, 70, 40), (cx + 5, cy + 20), (cx + 5, cy + 26), 2)
    pygame.draw.line(screen, (100, 70, 40), (cx - 5, cy + 26), (cx + 5, cy + 26), 2)

    # 文字
    txt = font_small.render("铲除", True, (220, 200, 180))
    screen.blit(txt, (sx + sw // 2 - txt.get_width() // 2, sy + sh - 14))


def hit_test_plant_selector(mx, my):
    """返回被点击的植物类型，否则返回 None"""
    for i, ptype in enumerate(PLANT_TYPES):
        cx, cy, cw, ch = get_plant_card_rect(i)
        if cx <= mx <= cx + cw and cy <= my <= cy + ch:
            return ptype
    return None


def hit_test_shovel(mx, my):
    """是否点击了铲子按钮"""
    sx, sy, sw, sh = get_shovel_rect()
    return sx <= mx <= sx + sw and sy <= my <= sy + sh


# ─────────────────────────────────────────
# 拖拽预览
# ─────────────────────────────────────────
def draw_drag_preview(screen, drag_type, drag_plant_type, mx, my, font_small):
    """绘制拖拽时的跟随物"""
    if drag_type == "plant":
        color = PLANT_DATA[drag_plant_type]["color"]
        # 半透明圆
        s = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, 200), (20, 20), 18)
        pygame.draw.circle(s, (0, 0, 0, 100), (20, 20), 18, 2)
        # 光泽
        pygame.draw.circle(s, (255, 255, 255, 120), (14, 14), 5)
        screen.blit(s, (mx - 20, my - 20))
        # 文字
        name = PLANT_DATA[drag_plant_type]["name"]
        txt = font_small.render(name, True, WHITE)
        screen.blit(txt, (mx - txt.get_width() // 2, my + 22))

    elif drag_type == "shovel":
        # 绘制铲子跟随鼠标
        cx, cy = mx, my
        pygame.draw.polygon(screen, (140, 140, 140), [
            (cx - 12, cy - 4), (cx + 12, cy - 4),
            (cx + 10, cy + 8), (cx - 10, cy + 8)
        ])
        pygame.draw.polygon(screen, (220, 220, 220), [
            (cx - 12, cy - 4), (cx + 12, cy - 4),
            (cx + 10, cy + 8), (cx - 10, cy + 8)
        ], 2)
        pygame.draw.line(screen, (120, 90, 60), (cx, cy + 8), (cx, cy + 20), 4)
        pygame.draw.line(screen, (120, 90, 60), (cx - 5, cy + 20), (cx + 5, cy + 20), 3)
        # 提示文字
        txt = font_small.render("拖到植物上松手", True, (255, 220, 180))
        screen.blit(txt, (mx - txt.get_width() // 2, my + 24))


# ─────────────────────────────────────────
# 悬停预览（拖拽时显示格子高亮）
# ─────────────────────────────────────────
def draw_hover_preview(screen, col, row, plant_type, font_small):
    if col < 0 or col >= GRID_COLS or row < 0 or row >= GRID_ROWS:
        return
    x = GRID_X + col * CELL_W
    y = GRID_Y + row * CELL_H
    s = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA)
    color = PLANT_DATA[plant_type]["color"]
    s.fill((*color, 80))
    screen.blit(s, (x, y))
    pygame.draw.rect(screen, YELLOW, (x, y, CELL_W, CELL_H), 2)


# ─────────────────────────────────────────
# 游戏结束画面
# ─────────────────────────────────────────
def draw_gameover(screen, font_big, font, win=False):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    cx = SCREEN_WIDTH // 2
    cy = SCREEN_HEIGHT // 2

    if win:
        for i in range(5):
            sx = cx - 80 + i * 40
            _draw_star(screen, sx, cy - 80, 14, YELLOW)
        msg = "胜利！所有僵尸已消灭！"
        color = YELLOW
    else:
        _draw_skull(screen, cx - 175, cy - 75)
        msg = "游戏结束！僵尸入侵了！"
        color = RED

    txt = font_big.render(msg, True, color)
    screen.blit(txt, (cx - txt.get_width() // 2, cy - 50))
    hint = font.render("按 R 重新开始  |  ESC 返回菜单", True, WHITE)
    screen.blit(hint, (cx - hint.get_width() // 2, cy + 24))


def _draw_star(screen, cx, cy, r, color):
    pts = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + int(math.cos(angle) * rad),
                    cy - int(math.sin(angle) * rad)))
    pygame.draw.polygon(screen, color, pts)
    pygame.draw.polygon(screen, (200, 160, 0), pts, 1)


def _draw_skull(screen, cx, cy):
    pygame.draw.circle(screen, WHITE, (cx, cy), 14)
    pygame.draw.circle(screen, (40, 40, 40), (cx - 5, cy - 3), 4)
    pygame.draw.circle(screen, (40, 40, 40), (cx + 5, cy - 3), 4)
    pygame.draw.rect(screen, WHITE, (cx - 8, cy + 8, 16, 8), border_radius=2)
    for tx in range(-6, 7, 4):
        pygame.draw.line(screen, (40, 40, 40),
                         (cx + tx, cy + 8), (cx + tx, cy + 16), 2)


# ─────────────────────────────────────────
# 小推车（Lawn Mower）
# ─────────────────────────────────────────
def draw_lawn_mowers(screen, mowers):
    """绘制红线左侧的小推车，每行一辆"""
    for lm in mowers:
        if not lm.get("alive"):
            continue
        row = lm["row"]
        x = int(lm["x"])
        y = GRID_Y + row * CELL_H + CELL_H // 2

        triggered = lm.get("triggered", False)

        # 车身
        body_w, body_h = 30, 22
        bx = x - body_w // 2
        by = y - body_h // 2
        pygame.draw.rect(screen, (120, 120, 130), (bx, by, body_w, body_h), border_radius=4)
        pygame.draw.rect(screen, (90, 90, 100), (bx, by, body_w, body_h), 1, border_radius=4)

        # 推板（前端红色）
        pygame.draw.polygon(screen, RED, [
            (bx + body_w, by + 3),
            (bx + body_w + 10, by - 3),
            (bx + body_w + 10, by + body_h + 3),
            (bx + body_w, by + body_h - 3),
        ])
        pygame.draw.polygon(screen, (180, 30, 30), [
            (bx + body_w, by + 3),
            (bx + body_w + 10, by - 3),
            (bx + body_w + 10, by + body_h + 3),
            (bx + body_w, by + body_h - 3),
        ], 2)

        # 把手
        pygame.draw.line(screen, (80, 80, 80), (bx, by + 6), (bx - 8, by - 2), 3)
        pygame.draw.line(screen, (80, 80, 80), (bx - 8, by - 2), (bx - 12, by - 2), 3)

        # 轮子（两个）
        wheel_r = 5
        pygame.draw.circle(screen, (40, 40, 40), (bx + 6, by + body_h + 2), wheel_r)
        pygame.draw.circle(screen, (40, 40, 40), (bx + body_w - 6, by + body_h + 2), wheel_r)
        pygame.draw.circle(screen, (60, 60, 60), (bx + 6, by + body_h + 2), wheel_r - 2)
        pygame.draw.circle(screen, (60, 60, 60), (bx + body_w - 6, by + body_h + 2), wheel_r - 2)

        # 触发后速度线
        if triggered:
            for si in range(4):
                lx = x - 15 - si * 8
                ly = y + random.randint(-6, 6)
                pygame.draw.line(screen, (200, 60, 60), (lx, ly), (lx - 6, ly), 2)
            # 车身小抖动
            pygame.draw.line(screen, (180, 180, 190), (bx, by + 10), (bx + body_w, by + 10), 1)

        # 未触发时静止状态标识
        if not triggered:
            # 小旗帜装饰
            pygame.draw.line(screen, (100, 100, 100), (bx + 5, by - 2), (bx + 5, by - 10), 2)
            pygame.draw.polygon(screen, (150, 150, 150), [
                (bx + 5, by - 10),
                (bx + 14, by - 7),
                (bx + 5, by - 4),
            ])


# ─────────────────────────────────────────
# 波次横幅
# ─────────────────────────────────────────
def draw_wave_banner(screen, font_big, wave_idx, frame):
    alpha = 255
    if frame > 90:
        alpha = max(0, 255 - (frame - 90) * 5)
    if alpha <= 0:
        return
    s = pygame.Surface((420, 70), pygame.SRCALPHA)
    s.fill((0, 0, 0, min(160, alpha)))
    screen.blit(s, (SCREEN_WIDTH // 2 - 210, SCREEN_HEIGHT // 2 - 35))
    txt = font_big.render(f"第 {wave_idx} 波僵尸来袭！",
                          True, (*RED[:3], alpha))
    screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                      SCREEN_HEIGHT // 2 - txt.get_height() // 2))
