"""
============================================
    敲砖块 (Breakout) — 怪物金币主题 v3
============================================
修复版：解决渲染重叠、图片变形、状态混乱等所有视觉问题
"""

import pygame
import sys
import random
import math
import os

pygame.init()
pygame.mixer.init()

# ==================== 常量 ====================
W, H = 800, 600
FPS = 60

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "assets", "images")
SND = os.path.join(BASE, "assets", "sounds")

# 尺寸 — 根据原始图片比例合理设置
PAD_W, PAD_H = 140, 65       # board.png 原始比例约 217:104 → 保持人物可见
BALL_R = 10
BRICK_W, BRICK_H = 58, 28
BRICK_GAP = 4
GOLD_S = 30
LIFE_S = 26


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD_C = (255, 215, 0)


class BrickBreaker:
    def __init__(self):
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("敲砖块 — 怪物金币")

        ico_path = os.path.join(BASE, "assets", "monster.ico")
        if os.path.exists(ico_path):
            try:
                pygame.display.set_icon(pygame.image.load(ico_path))
            except Exception:
                pass

        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "start"

        self._load_assets()
        self._init_fonts()
        self.reset_game()

    # ==================== 资源加载 ====================
    def _load_assets(self):
        S = pygame.transform.scale

        def load(name, size=None):
            img = pygame.image.load(os.path.join(IMG, name)).convert_alpha()
            if size:
                return S(img, size)
            return img

        # 背景 — 创建不透明Surface再贴图，确保无alpha通道干扰
        raw_bg = pygame.image.load(os.path.join(IMG, "bg1.png")).convert()
        self.bg = pygame.Surface((W, H))
        self.bg.fill((0, 0, 0))
        self.bg.blit(S(raw_bg, (W, H)), (0, 0))

        # 挡板 — board.png 是两个卡通人物，保持比例
        self.pad_img = load("board.png", (PAD_W, PAD_H))

        # 球
        self.ball_img = load("ball.png", (BALL_R * 2, BALL_R * 2))

        # 砖块皮肤
        self.brick_imgs = {
            "red":   load("c1.png", (BRICK_W, BRICK_H)),
            "orange": load("c2.png", (BRICK_W, BRICK_H)),
            "purple": load("enemy1.png", (BRICK_W, BRICK_H)),
            "gold":  load("enemy2.png", (BRICK_W, BRICK_H)),
            "steel": load("enemy3.png", (BRICK_W, BRICK_H)),
        }

        # 装饰性资源
        self.gold_img  = load("gold.png", (GOLD_S, GOLD_S))
        self.life_img  = load("life.png", (LIFE_S, LIFE_S))
        self.win_img   = load("win.png", (380, 250))
        self.lose_img  = load("lose.png", (380, 250))

        # 音效
        self.sfx = None
        try:
            pygame.mixer.music.load(os.path.join(SND, "music.wav"))
            pygame.mixer.music.set_volume(0.25)
            self.sfx = pygame.mixer.Sound(os.path.join(SND, "score.wav"))
            self.sfx.set_volume(0.4)
        except Exception:
            pass

    def _init_fonts(self):
        for name in ["simhei", "microsoft yahei", "simsun", "arial"]:
            try:
                self.f_sm = pygame.font.SysFont(name, 18)
                self.f_md = pygame.font.SysFont(name, 24)
                self.f_lg = pygame.font.SysFont(name, 40)
                return
            except Exception:
                continue
        self.f_sm = pygame.font.Font(None, 18)
        self.f_md = pygame.font.Font(None, 24)
        self.f_lg = pygame.font.Font(None, 40)

    # ==================== 游戏重置 ====================
    def reset_game(self):
        # 挡板
        self.pad_x = W // 2 - PAD_W // 2
        self.pad_y = H - 75

        # 球 — 初始附着在挡板上
        self.ball_on_pad = True
        self.ball_x = W / 2
        self.ball_y = self.pad_y - BALL_R - 2
        spd = 5.5
        angle = random.uniform(-0.5, 0.5)
        self.ball_dx = math.sin(angle) * spd
        self.ball_dy = -math.cos(angle) * spd

        # 砖块
        self.bricks = []
        self._build_bricks()

        # 掉落物
        self.golds = []

        # 粒子效果
        self.particles = []

        # 分数与生命
        self.score = 0
        self.lives = 3

    def _build_bricks(self):
        """构建经典打砖块砖阵：10列 × 6行"""
        cols = 10
        total_w = cols * BRICK_W + (cols - 1) * BRICK_GAP
        sx = (W - total_w) // 2
        sy = 95

        # 每行配置：(皮肤key, HP, 分数, 颜色)
        rows_config = [
            ("purple", 2, 40),
            ("purple", 2, 40),
            ("gold",   2, 50),
            ("orange", 1, 20),
            ("red",    1, 15),
            ("red",    1, 15),
        ]

        for row_idx, (skin, hp, pts) in enumerate(rows_config):
            for col in range(cols):
                x = sx + col * (BRICK_W + BRICK_GAP)
                y = sy + row_idx * (BRICK_H + BRICK_GAP)

                # 第4行（row_idx=4）混入几个钢铁砖（不可破坏）
                if row_idx == 4 and col in (2, 5, 7):
                    skin_key = "steel"
                    hp_val = 999
                    pts_val = 0
                    img = self.brick_imgs["steel"]
                else:
                    skin_key = skin
                    hp_val = hp
                    pts_val = pts
                    img = self.brick_imgs[skin]

                self.bricks.append({
                    "rect": pygame.Rect(x, y, BRICK_W, BRICK_H),
                    "img": img.copy(),
                    "hp": hp_val,
                    "max_hp": hp_val,
                    "points": pts_val,
                    "skin": skin_key,
                    "alive": True,
                    "flash": 0,                 # 受伤闪烁计时器
                })

    # ==================== 事件处理 ====================
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "playing":
                        self.state = "start"
                        try:
                            pygame.mixer.music.stop()
                        except Exception:
                            pass
                    else:
                        self.running = False

                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if self.state == "start":
                        self.state = "playing"
                        self.reset_game()
                        try:
                            pygame.mixer.music.play(-1)
                        except Exception:
                            pass
                    elif self.state == "playing" and self.ball_on_pad:
                        # 首次按空格发球
                        self.ball_on_pad = False

                elif event.key == pygame.K_r:
                    if self.state in ("win", "lose"):
                        self.state = "playing"
                        self.reset_game()
                        try:
                            pygame.mixer.music.play(-1)
                        except Exception:
                            pass

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "start":
                    self.state = "playing"
                    self.reset_game()
                    try:
                        pygame.mixer.music.play(-1)
                    except Exception:
                        pass
                elif self.state == "playing" and self.ball_on_pad:
                    self.ball_on_pad = False

    # ==================== 游戏逻辑更新 ====================
    def update(self):
        if self.state != "playing":
            return

        # ---- 挡板跟随鼠标 ----
        mx, _ = pygame.mouse.get_pos()
        self.pad_x = mx - PAD_W // 2
        self.pad_x = max(0, min(W - PAD_W, self.pad_x))

        # 如果球还在挡板上，跟随挡板移动
        if self.ball_on_pad:
            self.ball_x = self.pad_x + PAD_W / 2
            self.ball_y = self.pad_y - BALL_R - 2
            return  # 不做其他更新

        # ---- 球运动与碰撞 ----
        self._move_ball()

        # ---- 掉落金币 ----
        self._update_golds()

        # ---- 砖块闪烁计时器 ----
        for b in self.bricks:
            if b["flash"] > 0:
                b["flash"] -= 1

        # ---- 粒子 ----
        self._update_particles()

        # ---- 胜利检测 ----
        alive_breakable = [b for b in self.bricks if b["skin"] != "steel" and b["alive"]]
        if not alive_breakable:
            self.state = "win"
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def _move_ball(self):
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # 左右墙壁
        if self.ball_x - BALL_R <= 0:
            self.ball_x = BALL_R
            self.ball_dx = abs(self.ball_dx)
        elif self.ball_x + BALL_R >= W:
            self.ball_x = W - BALL_R
            self.ball_dx = -abs(self.ball_dx)

        # 顶部天花板
        if self.ball_y - BALL_R <= 0:
            self.ball_y = BALL_R
            self.ball_dy = abs(self.ball_dy)

        # 掉出底部 — 扣命
        if self.ball_y + BALL_R >= H:
            self.lives -= 1
            if self.lives <= 0:
                self.state = "lose"
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                return
            # 重置球位置
            self.ball_on_pad = True
            self.ball_x = self.pad_x + PAD_W / 2
            self.ball_y = self.pad_y - BALL_R - 2
            angle = random.uniform(-0.5, 0.5)
            self.ball_dx = math.sin(angle) * 5.5
            self.ball_dy = -math.cos(angle) * 5.5
            return

        br = pygame.Rect(self.ball_x - BALL_R, self.ball_y - BALL_R,
                         BALL_R * 2, BALL_R * 2)

        # --- 挡板碰撞 ---
        pr = pygame.Rect(self.pad_x, self.pad_y, PAD_W, PAD_H)
        if br.colliderect(pr) and self.ball_dy > 0:
            hit_pos = (self.ball_x - (self.pad_x + PAD_W / 2)) / (PAD_W / 2)
            hit_pos = max(-0.95, min(0.95, hit_pos))
            angle = hit_pos * 1.15  # 最大反弹角 ~66°
            speed = math.hypot(self.ball_dx, self.ball_dy)
            speed = max(speed, 5.0)  # 保证最低速度
            self.ball_dx = math.sin(angle) * speed
            self.ball_dy = -abs(math.cos(angle) * speed)
            self.ball_y = self.pad_y - BALL_R - 1
            self._play_sfx()

        # --- 砖块碰撞 ---
        for brick in self.bricks:
            if not brick["alive"]:
                continue
            if br.colliderect(brick["rect"]):
                brick["hp"] -= 1
                if brick["hp"] <= 0 and brick["skin"] != "steel":
                    brick["alive"] = False
                    self.score += brick["points"]
                    # 碎裂粒子
                    cx, cy = brick["rect"].center
                    self._spawn_particles(cx, cy, brick["skin"])
                    # 掉金币
                    if random.random() < 0.22:
                        self.golds.append({
                            "x": float(cx),
                            "y": float(cy),
                            "vy": random.uniform(1.5, 3.0),
                        })
                else:
                    # 受伤闪烁 — 用计时器，不污染原图
                    brick["flash"] = 10

                self._precise_bounce(br, brick["rect"])
                self._play_sfx()
                break  # 每帧只处理一块砖

    def _precise_bounce(self, ball_rect, target_rect):
        """根据碰撞位置精确计算反弹方向"""
        bcx, bcy = ball_rect.center
        tcx, tcy = target_rect.center

        dx = (bcx - tcx) / (target_rect.width / 2) if target_rect.width > 0 else 0
        dy = (bcy - tcy) / (target_rect.height / 2) if target_rect.height > 0 else 0

        if abs(dx) >= abs(dy):
            # 从左右方向碰撞
            self.ball_dx = abs(self.ball_dx) if dx > 0 else -abs(self.ball_dx)
        else:
            # 从上下方向碰撞
            self.ball_dy = abs(self.ball_dy) if dy > 0 else -abs(self.ball_dy)

        # 速度上限
        spd = math.hypot(self.ball_dx, self.ball_dy)
        max_spd = 9.0
        if spd > max_spd:
            ratio = max_spd / spd
            self.ball_dx *= ratio
            self.ball_dy *= ratio

    def _update_golds(self):
        pr = pygame.Rect(self.pad_x, self.pad_y, PAD_W, PAD_H)
        for g in self.golds[:]:
            g["y"] += g["vy"]
            gr = pygame.Rect(int(g["x"]) - GOLD_S // 2,
                             int(g["y"]) - GOLD_S // 2,
                             GOLD_S, GOLD_S)
            if gr.colliderect(pr):
                self.golds.remove(g)
                self.score += 50
                self._play_sfx()
            elif g["y"] > H + GOLD_S:
                self.golds.remove(g)

    def _update_particles(self):
        for p in self.particles[:]:
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            p["dy"] += 0.12  # 微重力
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

    def _spawn_particles(self, x, y, skin):
        colors = {
            "purple": (200, 100, 220),
            "gold":   (255, 200, 50),
            "orange": (255, 160, 50),
            "red":    (255, 80, 80),
        }
        color = colors.get(skin, (220, 220, 220))
        for _ in range(8):
            ang = random.uniform(0, math.pi * 2)
            sp = random.uniform(1.5, 4.0)
            self.particles.append({
                "x": x,
                "y": y,
                "dx": math.cos(ang) * sp,
                "dy": math.sin(ang) * sp - 1.5,
                "life": random.randint(20, 35),
                "color": color,
                "size": random.randint(3, 6),
            })

    def _play_sfx(self):
        if self.sfx:
            try:
                self.sfx.play()
            except Exception:
                pass

    # ==================== 绘制 ====================
    def draw(self):
        """严格按状态绘制，每个状态完全清屏后重新画"""

        if self.state == "start":
            self._draw_start_screen()
        elif self.state == "playing":
            self._draw_playing_screen()
        elif self.state in ("win", "lose"):
            self._draw_end_screen()

        pygame.display.flip()

    # ---------- 开始界面 ----------
    def _draw_start_screen(self):
        # 0) 清除残影 — 关键：每帧必须全屏擦除
        self.screen.fill(BLACK)
        # 1) 先铺满背景
        self.screen.blit(self.bg, (0, 0))

        # 2) 半透明遮罩
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        # 3) 标题
        title = self.f_lg.render("敲 砖 块", True, GOLD_C)
        tr = title.get_rect(center=(W // 2, 100))
        self.screen.blit(title, tr)

        # 5) 操作说明
        lines = [
            "鼠标移动 — 控制挡板",
            "点击鼠标 / 按空格 — 发球",
            "弹球打碎砖块获得分数",
            "接住掉落的金币  +50分",
            "",
            "点击或按空格 开始游戏",
            "ESC 退出",
        ]
        y0 = 260
        for i, line in enumerate(lines):
            if line == "":
                continue
            txt = self.f_md.render(line, True, WHITE)
            rect = txt.get_rect(center=(W // 2, y0 + i * 34))
            self.screen.blit(txt, rect)

        # 6) 金币装饰
        gs = 36
        gd = pygame.transform.scale(self.gold_img, (gs, gs))
        self.screen.blit(gd, (W // 2 - 170, y0 + 3 * 34 - gs // 2))
        self.screen.blit(gd, (W // 2 + 135, y0 + 3 * 34 - gs // 2))

    # ---------- 游戏中界面 ----------
    def _draw_playing_screen(self):
        # 0) 清除残影 — 关键：每帧必须全屏擦除
        self.screen.fill(BLACK)
        # 背景
        self.screen.blit(self.bg, (0, 0))

        # === 砖块 ===
        for b in self.bricks:
            if b["alive"]:
                if b["flash"] > 0:
                    # 受伤闪烁：淡入淡出
                    alpha = 255 if (b["flash"] // 2) % 2 == 0 else 100
                    img = b["img"].copy()
                    img.set_alpha(alpha)
                    self.screen.blit(img, b["rect"].topleft)
                else:
                    self.screen.blit(b["img"], b["rect"].topleft)

        # === 掉落金币 ===
        for g in self.golds:
            gx = int(g["x"]) - GOLD_S // 2
            gy = int(g["y"]) - GOLD_S // 2
            self.screen.blit(self.gold_img, (gx, gy))

        # === 粒子 ===
        for p in self.particles:
            alpha = int(min(255, p["life"] * 8))
            s = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
            s.fill((*p["color"], alpha))
            self.screen.blit(s, (int(p["x"]), int(p["y"])))

        # === 挡板 ===
        self.screen.blit(self.pad_img, (int(self.pad_x), int(self.pad_y)))

        # === 球 ===
        bx = int(self.ball_x - BALL_R)
        by = int(self.ball_y - BALL_R)
        self.screen.blit(self.ball_img, (bx, by))

        # === HUD 信息栏 ===
        self._draw_hud()

        # === 等待发球提示 ===
        if self.ball_on_pad:
            hint = self.f_sm.render("点击或按空格发球", True, WHITE)
            hr = hint.get_rect(center=(W // 2, H // 2 + 60))
            # 半透明背景
            hb_w = hr.width + 24
            hb_h = hr.height + 8
            hb_surf = pygame.Surface((hb_w, hb_h), pygame.SRCALPHA)
            hb_surf.fill((0, 0, 0, 140))
            self.screen.blit(hb_surf, (hr.x - 12, hr.y - 4))
            self.screen.blit(hint, hr)

    def _draw_hud(self):
        # 分数（左上）
        st = self.f_md.render(f"得分 {self.score}", True, WHITE)
        self.screen.blit(st, (14, 10))

        # 剩余砖块数（中上）
        remain = sum(1 for b in self.bricks if b["skin"] != "steel" and b["alive"])
        rt = self.f_sm.render(f"剩余 {remain}", True, WHITE)
        rr = rt.get_rect(center=(W // 2, 14))
        self.screen.blit(rt, rr)

        # 生命值（右上）
        for i in range(self.lives):
            lx = W - 16 - (i + 1) * (LIFE_S + 5)
            self.screen.blit(self.life_img, (lx, 10))

    # ---------- 结算界面 ----------
    def _draw_end_screen(self):
        # 0) 清除残影 — 关键：每帧必须全屏擦除
        self.screen.fill(BLACK)
        # 背景
        self.screen.blit(self.bg, (0, 0))

        # 遮罩
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # 图片
        end_img = self.win_img if self.state == "win" else self.lose_img
        eix = W // 2 - 190
        self.screen.blit(end_img, (eix, 45))

        # 文字
        if self.state == "win":
            msg = f"恭喜通关！得分: {self.score}"
        else:
            msg = f"游戏结束  得分: {self.score}"
        t = self.f_lg.render(msg, True, WHITE)
        tr = t.get_rect(center=(W // 2, 340))
        self.screen.blit(t, tr)

        # 提示
        hint = self.f_md.render("按 R 重新开始   |   ESC 退出", True, GOLD_C)
        hr = hint.get_rect(center=(W // 2, 410))
        self.screen.blit(hint, hr)

    # ==================== 主循环 ====================
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


# ==================== 启动 ====================
if __name__ == "__main__":
    game = BrickBreaker()
    game.run()
