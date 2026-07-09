# zombies.py - 僵尸类
import pygame
import math
import random
from constants import *
import sound


class Zombie:
    """僵尸基类：通用动画、状态效果"""

    def __init__(self, ztype, row, data):
        self.type = ztype
        self.row = row
        self.data = data
        self.x = float(SCREEN_WIDTH + 40 + random.randint(0, 40))
        self.y = GRID_Y + row * CELL_H + CELL_H // 2 + 10
        self.alive = True
        self.hp = data["hp"]
        self.max_hp = data["hp"]
        self.speed = data["speed"]
        self.dmg = data["dmg"]
        self.frame = 0

        self.eating = False
        self.eat_target = None

        # 状态效果
        self.frozen = 0       # 冰冻帧数
        self.slowed = 0       # 减速帧数
        self.poisoned = 0     # 中毒帧数
        self.poison_dmg = 0
        self.hit_flash = 0    # 被击中闪烁
        self.knockback = 0.0  # 被击退距离
        self.dying = 0        # 死亡倒地帧

        # 动画
        self.eat_anim_frame = 0

    def update(self, plants_in_row):
        self.frame += 1

        # 中毒伤害
        if self.poisoned > 0:
            self.poisoned -= 1
            if self.frame % 10 == 0:
                self.take_damage(self.poison_dmg)

        # 冰冻和减速
        if self.frozen > 0:
            self.frozen -= 1
        if self.slowed > 0:
            self.slowed -= 1

        # 被击退恢复 + 位移
        if self.knockback > 0:
            self.x += self.knockback * 0.5  # 向后推移
            self.knockback = max(0, self.knockback - 0.3)

        # 被击中闪烁
        if self.hit_flash > 0:
            self.hit_flash -= 1

        # 死亡倒地
        if self.dying > 0:
            self.dying -= 1
            if self.dying <= 0:
                self.alive = False
            return False

        # 检查是否吃植物
        self.eating = False
        self.eat_target = None
        for plant in plants_in_row:
            if not plant.alive:
                continue
            if plant.type == "spikeweed":
                continue  # 地刺不阻挡
            px = plant.x
            if abs(self.x - px) < 35:
                self.eating = True
                self.eat_target = plant
                plant.take_damage(self.dmg)
                self.eat_anim_frame = self.frame
                break

        # 移动
        if not self.eating:
            actual_speed = self.speed
            if self.frozen > 0:
                actual_speed = 0  # 冰冻完全停止
            elif self.slowed > 0:
                actual_speed *= 0.5
            self.x -= actual_speed

        # 入侵检测
        if self.x < GRID_X - 60:
            self.alive = False
            return True
        return False

    def take_damage(self, dmg, freeze=False):
        self.hp -= dmg
        self.hit_flash = 4
        self.knockback = min(5.0, dmg * 0.15)  # 击退量与伤害成正比，上限5
        if freeze:
            self.frozen = 120   # 2秒冰冻
            self.slowed = 180   # 3秒减速
        if self.hp <= 0 and self.dying == 0:
            self.dying = 30  # 死亡倒地动画时长

    def draw(self, screen):
        if not self.alive and self.dying <= 0:
            return

        # 阴影
        pygame.draw.ellipse(screen, (20, 40, 20),
                            (int(self.x) - 18, int(self.y) + 18, 36, 10))

        # 被击中闪烁
        if self.hit_flash > 0 and self.hit_flash % 2 == 0:
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            s.fill((255, 100, 100, 80))
            screen.blit(s, (int(self.x) - 30, int(self.y) - 35))

        # 死亡倒地
        if self.dying > 0:
            self._draw_dying(screen)
            return

        # 正常绘制
        self._draw_body(screen)

        # 负面状态覆盖
        if self.frozen > 0:
            self._draw_frozen_overlay(screen)
        elif self.slowed > 0:
            self._draw_slowed_overlay(screen)
        if self.poisoned > 0:
            self._draw_poison_overlay(screen)

        # 血条
        self._draw_hp_bar(screen)

    def _draw_body(self, screen):
        """子类实现"""
        pass

    # ─── 通用僵尸绘制组件 ───
    def _draw_base(self, screen, body_color, head_color, head_dx=0, head_dy=0):
        """绘制标准僵尸身体结构"""
        f = self.frame
        bx = int(self.x)
        by = int(self.y)

        # 冰冻时停止动画
        anim_f = f if self.frozen <= 0 else 0

        # 腿部（交替步态）
        leg_swing = int(math.sin(anim_f * 0.15) * 6) if not self.eating else 3
        leg_color = (100, 120, 100)
        # 左腿
        pygame.draw.rect(screen, leg_color, (bx - 10 - leg_swing, by + 10, 7, 18))
        pygame.draw.rect(screen, (80, 100, 80), (bx - 10 - leg_swing, by + 24, 7, 4), 1)
        # 右腿
        pygame.draw.rect(screen, leg_color, (bx + 3 + leg_swing, by + 10, 7, 18))
        pygame.draw.rect(screen, (80, 100, 80), (bx + 3 + leg_swing, by + 24, 7, 4), 1)
        # 鞋子
        pygame.draw.ellipse(screen, (80, 60, 40), (bx - 12 - leg_swing, by + 26, 10, 5))
        pygame.draw.ellipse(screen, (80, 60, 40), (bx + 1 + leg_swing, by + 26, 10, 5))

        # 身体
        pygame.draw.rect(screen, body_color, (bx - 12, by - 10, 24, 22),
                         border_radius=4)
        pygame.draw.rect(screen, (100, 110, 90), (bx - 12, by - 10, 24, 22), 1, border_radius=4)
        # 衣服褶皱
        for fi in range(-1, 2):
            pygame.draw.line(screen, (90, 100, 80),
                             (bx - 8 + fi * 7, by - 5), (bx - 8 + fi * 7, by + 8), 1)

        # 领带
        pygame.draw.polygon(screen, (180, 60, 60), [
            (bx - 3, by - 2), (bx + 3, by - 2), (bx, by + 6)
        ])

        # 手臂（走路摆动 / 吃植物前伸）
        if self.eating:
            # 吃：手臂前伸 + 嘴咬合
            arm_y = by - 2
            # 左臂
            pygame.draw.rect(screen, body_color, (bx - 16, arm_y, 10, 6))
            pygame.draw.circle(screen, (120, 130, 110), (bx - 18, arm_y + 3), 4)
            # 右臂
            pygame.draw.rect(screen, body_color, (bx + 6, arm_y, 10, 6))
            pygame.draw.circle(screen, (120, 130, 110), (bx + 18, arm_y + 3), 4)
            # 爪子
            pygame.draw.line(screen, (80, 80, 80), (bx - 20, arm_y + 2), (bx - 24, arm_y - 2), 2)
            pygame.draw.line(screen, (80, 80, 80), (bx + 20, arm_y + 2), (bx + 24, arm_y - 2), 2)
        else:
            # 走路：交替摆动
            left_arm = int(math.sin(anim_f * 0.15) * 8)
            right_arm = int(math.sin(anim_f * 0.15 + math.pi) * 8)
            # 左臂
            pygame.draw.rect(screen, body_color, (bx - 14, by - 4 + left_arm // 2, 6, 12))
            pygame.draw.circle(screen, (120, 130, 110), (bx - 12, by + 6 + left_arm // 2), 4)
            # 右臂
            pygame.draw.rect(screen, body_color, (bx + 8, by - 4 - right_arm // 2, 6, 12))
            pygame.draw.circle(screen, (120, 130, 110), (bx + 12, by + 6 - right_arm // 2), 4)

        # 头
        hx = bx + head_dx
        hy = by - 20 + head_dy
        # 呼吸微动
        breath = int(math.sin(anim_f * 0.06) * 1)
        hy += breath

        pygame.draw.circle(screen, head_color, (hx, hy), 14)
        pygame.draw.circle(screen, (120, 150, 110), (hx, hy), 14, 1)
        # 高光
        pygame.draw.ellipse(screen, (180, 210, 170), (hx - 8, hy - 12, 8, 6))

        # 头发
        for hi in range(-3, 4):
            pygame.draw.line(screen, (80, 70, 50), (hx + hi * 3, hy - 12),
                             (hx + hi * 3 + random.randint(-1, 1), hy - 16), 1)

        # 眼睛
        self._draw_zombie_eyes(screen, hx, hy)

        # 嘴（吃时张开）
        if self.eating and self.eat_anim_frame % 15 < 8:
            # 张开嘴咬合
            pygame.draw.ellipse(screen, (40, 20, 20), (hx - 6, hy + 4, 12, 8))
            pygame.draw.line(screen, WHITE, (hx - 5, hy + 6), (hx - 3, hy + 10), 2)
            pygame.draw.line(screen, WHITE, (hx + 1, hy + 6), (hx + 3, hy + 10), 2)
            pygame.draw.line(screen, (180, 60, 60), (hx - 4, hy + 8), (hx + 4, hy + 8), 1)
        else:
            # 闭合嘴
            pygame.draw.arc(screen, (80, 50, 50), (hx - 5, hy + 4, 10, 5), 0.2, 2.9, 1)

        # 牙齿
        for tx in range(-4, 5, 3):
            pygame.draw.line(screen, (220, 220, 200), (hx + tx, hy + 5), (hx + tx + 1, hy + 7), 1)

        return hx, hy

    def _draw_zombie_eyes(self, screen, hx, hy):
        """绘制僵尸眼睛"""
        # 眼白
        pygame.draw.ellipse(screen, WHITE, (hx - 7, hy - 4, 6, 7))
        pygame.draw.ellipse(screen, WHITE, (hx + 1, hy - 4, 6, 7))
        # 瞳孔（红眼）
        pygame.draw.circle(screen, RED, (hx - 4, hy - 1), 2)
        pygame.draw.circle(screen, RED, (hx + 4, hy - 1), 2)
        # 高光
        pygame.draw.circle(screen, (255, 150, 150), (hx - 5, hy - 2), 1)
        pygame.draw.circle(screen, (255, 150, 150), (hx + 3, hy - 2), 1)

    def _draw_dying(self, screen):
        """死亡倒地"""
        t = 1 - self.dying / 30.0  # 0~1 倒下进度
        bx = int(self.x + t * 30)  # 向后倒
        by = int(self.y + int(t * 20))  # 向下倒
        angle = t * 90  # 旋转角度

        # 简化：画一个倒地的身体
        body_color = (160, 200, 140)
        # 头（滚到旁边）
        pygame.draw.circle(screen, (140, 180, 120), (bx + 15, by + 5), 12)
        # 身体（横倒）
        pygame.draw.rect(screen, body_color, (bx - 20, by - 5, 30, 14), border_radius=3)
        # 腿
        pygame.draw.rect(screen, (100, 120, 100), (bx - 28, by - 2, 12, 6))
        pygame.draw.rect(screen, (100, 120, 100), (bx - 28, by + 4, 12, 6))
        # 手臂
        pygame.draw.rect(screen, body_color, (bx - 8, by - 10, 6, 8))
        # X眼
        pygame.draw.line(screen, (40, 40, 40), (bx + 10, by), (bx + 18, by + 8), 2)
        pygame.draw.line(screen, (40, 40, 40), (bx + 18, by), (bx + 10, by + 8), 2)
        # 血迹
        pygame.draw.ellipse(screen, (150, 30, 30), (bx - 5, by + 8, 20, 8))

    def _draw_frozen_overlay(self, screen):
        """冰冻冰晶覆盖"""
        bx = int(self.x)
        by = int(self.y)
        # 冰层
        ice = pygame.Surface((50, 55), pygame.SRCALPHA)
        ice.fill((150, 200, 255, 80))
        screen.blit(ice, (bx - 25, by - 30))
        # 冰晶
        for ci in range(6):
            cx = bx + int(math.cos(self.frame * 0.05 + ci) * 20)
            cy = by + int(math.sin(self.frame * 0.05 + ci) * 22) - 10
            pygame.draw.polygon(screen, (200, 230, 255), [
                (cx, cy - 4), (cx + 2, cy), (cx, cy + 4), (cx - 2, cy)
            ])
        # 冰面反光
        pygame.draw.line(screen, (220, 240, 255), (bx - 15, by - 20), (bx + 5, by - 25), 2)

    def _draw_slowed_overlay(self, screen):
        """减速半透明拖影"""
        bx = int(self.x)
        by = int(self.y)
        # 白色半透明覆盖
        s = pygame.Surface((44, 50), pygame.SRCALPHA)
        s.fill((200, 220, 255, 40))
        screen.blit(s, (bx - 22, by - 30))
        # 拖影粒子
        for i in range(3):
            px = bx + 15 + i * 8
            py = by + random.randint(-15, 15)
            a = max(0, 80 - i * 20)
            ps = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(ps, (200, 220, 255, a), (3, 3), 2)
            screen.blit(ps, (px - 3, py - 3))

    def _draw_poison_overlay(self, screen):
        """中毒紫色粒子"""
        bx = int(self.x)
        by = int(self.y)
        # 紫色环绕
        for pi in range(4):
            ang = self.frame * 0.08 + pi * math.pi / 2
            px = bx + int(math.cos(ang) * 18)
            py = by + int(math.sin(ang) * 18) - 10
            pygame.draw.circle(screen, (180, 80, 200), (px, py), 3)
        # 间歇跳动（中毒每20帧跳一次）
        if self.frame % 20 < 5:
            ps = pygame.Surface((44, 44), pygame.SRCALPHA)
            pygame.draw.circle(ps, (200, 100, 220, 100), (22, 22), 20)
            screen.blit(ps, (bx - 22, by - 32))

    def _draw_hp_bar(self, screen):
        """血条"""
        if self.hp >= self.max_hp:
            return
        bx = int(self.x)
        by = int(self.y)
        ratio = max(0, self.hp / self.max_hp)
        bar_w = 30
        bar_h = 4
        bar_x = bx - bar_w // 2
        bar_y = by - 35
        # 背景
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        # 血条颜色
        if ratio > 0.6:
            color = (50, 200, 50)
        elif ratio > 0.3:
            color = (200, 200, 50)
        else:
            color = (200, 50, 50)
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            pygame.draw.rect(screen, color, (bar_x, bar_y, fill_w, bar_h), border_radius=2)

    def get_cell_col(self):
        return int((self.x - GRID_X) // CELL_W)


# ─────────────────────────────────────────
# 普通僵尸
# ─────────────────────────────────────────
class NormalZombie(Zombie):
    def __init__(self, row):
        super().__init__("normal", row, ZOMBIE_DATA["normal"])

    def _draw_body(self, screen):
        self._draw_base(screen, (140, 160, 130), (160, 200, 140))


# ─────────────────────────────────────────
# 路锥僵尸
# ─────────────────────────────────────────
class ConeZombie(Zombie):
    def __init__(self, row):
        super().__init__("cone", row, ZOMBIE_DATA["cone"])

    def _draw_body(self, screen):
        hx, hy = self._draw_base(screen, (150, 140, 110), (200, 160, 100))
        # 路锥（帽子）
        cone_y = hy - 14
        # 锥底
        pygame.draw.polygon(screen, ORANGE, [
            (hx - 10, cone_y), (hx + 10, cone_y), (hx + 4, cone_y - 6), (hx - 4, cone_y - 6)
        ])
        # 锥体
        pygame.draw.polygon(screen, (255, 140, 0), [
            (hx - 4, cone_y - 6), (hx + 4, cone_y - 6), (hx, cone_y - 26)
        ])
        # 白色条纹
        pygame.draw.line(screen, WHITE, (hx - 3, cone_y - 10), (hx + 3, cone_y - 10), 2)
        pygame.draw.line(screen, WHITE, (hx - 2, cone_y - 16), (hx + 2, cone_y - 16), 2)
        # 锥尖
        pygame.draw.circle(screen, (220, 120, 0), (hx, cone_y - 26), 2)
        # 倒刺轮廓
        pygame.draw.polygon(screen, (200, 100, 0), [
            (hx - 10, cone_y), (hx + 10, cone_y), (hx + 4, cone_y - 6), (hx - 4, cone_y - 6)
        ], 1)


# ─────────────────────────────────────────
# 铁桶僵尸
# ─────────────────────────────────────────
class BucketZombie(Zombie):
    def __init__(self, row):
        super().__init__("bucket", row, ZOMBIE_DATA["bucket"])

    def _draw_body(self, screen):
        hx, hy = self._draw_base(screen, (130, 130, 150), (160, 160, 190))
        # 铁桶（头盔）
        bucket_y = hy - 14
        # 桶身
        pygame.draw.rect(screen, (160, 160, 170), (hx - 11, bucket_y - 22, 22, 24), border_radius=3)
        pygame.draw.rect(screen, (120, 120, 130), (hx - 11, bucket_y - 22, 22, 24), 2, border_radius=3)
        # 金属铆钉
        for dy in [-16, -8, 0]:
            pygame.draw.circle(screen, (100, 100, 110), (hx - 8, bucket_y + dy), 2)
            pygame.draw.circle(screen, (100, 100, 110), (hx + 8, bucket_y + dy), 2)
        # 金属高光
        pygame.draw.line(screen, (200, 200, 210), (hx - 7, bucket_y - 18), (hx - 7, bucket_y - 2), 2)
        # 桶沿
        pygame.draw.rect(screen, (140, 140, 150), (hx - 13, bucket_y - 2, 26, 4), border_radius=1)
        # 把手
        pygame.draw.arc(screen, (120, 120, 130), (hx - 8, bucket_y - 28, 16, 10), 0, 3.1, 2)


# ─────────────────────────────────────────
# 报纸僵尸
# ─────────────────────────────────────────
class NewspaperZombie(Zombie):
    def __init__(self, row):
        super().__init__("newspaper", row, ZOMBIE_DATA["newspaper"])
        self.paper_hp = ZOMBIE_DATA["newspaper"].get("paper_hp", 200)
        self.paper_max = self.paper_hp
        self.enraged = False

    def take_damage(self, dmg, freeze=False):
        # 报纸仍在时，先由报纸吸收伤害
        if self.paper_hp > 0:
            self.paper_hp -= dmg
            self.hit_flash = 4
            self.knockback = 3.0
            if freeze:
                self.frozen = 120
                self.slowed = 180
            if self.paper_hp <= 0 and not self.enraged:
                self.enraged = True
                self.speed = ZOMBIE_DATA["newspaper"].get("enrage_speed", 1.2)
                sound.play("paper_tear", 0.5)
            return
        # 报纸被打掉后，伤害才作用于本体
        super().take_damage(dmg, freeze)

    def _draw_body(self, screen):
        hx, hy = self._draw_base(screen, (180, 170, 140), (200, 200, 160))

        if self.paper_hp > 0:
            # 报纸（盾牌）
            px = hx - 20
            py = hy - 5
            # 报纸主体
            pygame.draw.rect(screen, (220, 210, 180), (px, py, 16, 22), border_radius=2)
            pygame.draw.rect(screen, (180, 170, 150), (px, py, 16, 22), 1, border_radius=2)
            # 报头
            pygame.draw.rect(screen, (40, 40, 40), (px + 2, py + 2, 12, 4))
            # 行文字
            for li in range(4):
                pygame.draw.line(screen, (120, 120, 120), (px + 2, py + 9 + li * 3), (px + 13, py + 9 + li * 3), 1)
            # 折痕
            pygame.draw.line(screen, (180, 170, 150), (px + 8, py), (px + 8, py + 22), 1)
            # 报纸破损（低血量时）
            if self.paper_hp < self.paper_max * 0.5:
                for _ in range(3):
                    pygame.draw.ellipse(screen, (200, 190, 170), (px + random.randint(2, 10), py + random.randint(5, 18), 4, 3))

        # 暴怒速度线
        if self.enraged:
            for _ in range(5):
                sx = hx + random.randint(10, 30)
                sy = hy + random.randint(-20, 20)
                pygame.draw.line(screen, (255, 100, 50), (sx, sy), (sx + 10, sy), 1)


# ─────────────────────────────────────────
# 橄榄球僵尸
# ─────────────────────────────────────────
class FootballZombie(Zombie):
    def __init__(self, row):
        super().__init__("football", row, ZOMBIE_DATA["football"])

    def _draw_body(self, screen):
        bx = int(self.x)
        by = int(self.y)
        f = self.frame
        anim_f = f if self.frozen <= 0 else 0

        # 橄榄球服（红色）
        body_color = (180, 50, 50)
        head_color = (180, 130, 90)

        # 腿部（更快步态）
        leg_swing = int(math.sin(anim_f * 0.25) * 8) if not self.eating else 4
        leg_color = (130, 100, 70)
        pygame.draw.rect(screen, leg_color, (bx - 10 - leg_swing, by + 10, 7, 18))
        pygame.draw.rect(screen, leg_color, (bx + 3 + leg_swing, by + 10, 7, 18))
        # 运动鞋
        pygame.draw.ellipse(screen, (60, 60, 120), (bx - 12 - leg_swing, by + 26, 10, 5))
        pygame.draw.ellipse(screen, (60, 60, 120), (bx + 1 + leg_swing, by + 26, 10, 5))
        # 白鞋带
        pygame.draw.line(screen, WHITE, (bx - 10 - leg_swing, by + 27), (bx - 8 - leg_swing, by + 28), 1)
        pygame.draw.line(screen, WHITE, (bx + 3 + leg_swing, by + 27), (bx + 5 + leg_swing, by + 28), 1)

        # 身体（加大肩甲）
        pygame.draw.rect(screen, body_color, (bx - 14, by - 12, 28, 24), border_radius=5)
        pygame.draw.rect(screen, (140, 40, 40), (bx - 14, by - 12, 28, 24), 2, border_radius=5)
        # 中线条纹
        pygame.draw.line(screen, WHITE, (bx, by - 10), (bx, by + 10), 2)
        # 号码
        pygame.draw.line(screen, WHITE, (bx - 6, by - 2), (bx - 2, by + 2), 2)
        pygame.draw.line(screen, WHITE, (bx + 3, by - 2), (bx + 7, by + 2), 2)

        # 肩甲（大）
        pygame.draw.ellipse(screen, (160, 50, 50), (bx - 20, by - 10, 10, 14))
        pygame.draw.ellipse(screen, (160, 50, 50), (bx + 10, by - 10, 10, 14))
        pygame.draw.ellipse(screen, (200, 80, 80), (bx - 18, by - 8, 6, 10))
        pygame.draw.ellipse(screen, (200, 80, 80), (bx + 12, by - 8, 6, 10))

        # 手臂（粗壮）
        if not self.eating:
            la = int(math.sin(anim_f * 0.25) * 10)
            ra = int(math.sin(anim_f * 0.25 + math.pi) * 10)
        else:
            la = 8
            ra = 8
        pygame.draw.rect(screen, body_color, (bx - 16, by - 4 + la // 2, 7, 14))
        pygame.draw.rect(screen, body_color, (bx + 9, by - 4 - ra // 2, 7, 14))
        pygame.draw.circle(screen, (160, 120, 80), (bx - 14, by + 8 + la // 2), 5)
        pygame.draw.circle(screen, (160, 120, 80), (bx + 14, by + 8 - ra // 2), 5)

        # 头（头盔）
        hx = bx
        hy = by - 20
        breath = int(math.sin(anim_f * 0.06) * 1)
        hy += breath
        # 面罩
        pygame.draw.circle(screen, head_color, (hx, hy), 15)
        pygame.draw.rect(screen, (100, 100, 110), (hx - 10, hy - 2, 20, 8), border_radius=2)
        # 面罩格栅
        for gx in range(-6, 7, 4):
            pygame.draw.line(screen, (60, 60, 70), (hx + gx, hy - 2), (hx + gx, hy + 4), 1)
        # 眼睛（透过面罩）
        pygame.draw.ellipse(screen, (200, 50, 50), (hx - 5, hy - 2, 4, 5))
        pygame.draw.ellipse(screen, (200, 50, 50), (hx + 1, hy - 2, 4, 5))
        # 头盔高光
        pygame.draw.ellipse(screen, (200, 160, 140), (hx - 8, hy - 12, 10, 6))


# ─────────────────────────────────────────
# 舞王僵尸
# ─────────────────────────────────────────
class DancerZombie(Zombie):
    def __init__(self, row):
        super().__init__("dancer", row, ZOMBIE_DATA["dancer"])
        self.summon_timer = 0
        self.summon_cd = ZOMBIE_DATA["dancer"].get("summon_cd", 300)
        self.should_summon = False

    def update(self, plants_in_row):
        invaded = super().update(plants_in_row)
        self.summon_timer += 1
        if self.summon_timer >= self.summon_cd:
            self.summon_timer = 0
            self.should_summon = True
        return invaded

    def _draw_body(self, screen):
        bx = int(self.x)
        by = int(self.y)
        f = self.frame
        anim_f = f if self.frozen <= 0 else 0

        # 舞王姿态（更优雅）
        body_color = (160, 60, 160)
        head_color = (200, 100, 200)

        # 腿部（舞步）
        leg_swing = int(math.sin(anim_f * 0.2) * 8)
        pygame.draw.rect(screen, (80, 80, 120), (bx - 10 - leg_swing, by + 10, 7, 18))
        pygame.draw.rect(screen, (80, 80, 120), (bx + 3 + leg_swing, by + 10, 7, 18))
        # 皮鞋
        pygame.draw.ellipse(screen, (40, 40, 60), (bx - 12 - leg_swing, by + 26, 10, 5))
        pygame.draw.ellipse(screen, (40, 40, 60), (bx + 1 + leg_swing, by + 26, 10, 5))
        # 鞋亮
        pygame.draw.ellipse(screen, (80, 80, 100), (bx - 10 - leg_swing, by + 26, 6, 2))
        pygame.draw.ellipse(screen, (80, 80, 100), (bx + 3 + leg_swing, by + 26, 6, 2))

        # 身体
        pygame.draw.rect(screen, body_color, (bx - 12, by - 10, 24, 22), border_radius=4)
        pygame.draw.rect(screen, (120, 40, 120), (bx - 12, by - 10, 24, 22), 1, border_radius=4)

        # 彩虹领带
        tie_colors = [(255, 50, 50), (255, 150, 50), (255, 255, 50), (50, 255, 50), (50, 50, 255), (200, 50, 200)]
        for ti, tc in enumerate(tie_colors):
            tx = bx - 4 + ti
            pygame.draw.rect(screen, tc, (tx, by - 2, 2, 8))

        # 手臂（高举舞蹈姿势）
        left_arm = int(math.sin(anim_f * 0.15) * 12)
        right_arm = int(math.sin(anim_f * 0.15 + math.pi) * 12)
        pygame.draw.rect(screen, (120, 50, 120), (bx - 18, by - 10 + left_arm, 6, 14))
        pygame.draw.rect(screen, (120, 50, 120), (bx + 12, by - 10 - right_arm, 6, 14))
        pygame.draw.circle(screen, (160, 100, 160), (bx - 16, by + 2 + left_arm), 4)
        pygame.draw.circle(screen, (160, 100, 160), (bx + 16, by + 2 - right_arm), 4)

        # 麦克风
        pygame.draw.line(screen, (80, 80, 80), (bx + 14, by - 6 - right_arm), (bx + 20, by - 12 - right_arm), 2)
        pygame.draw.ellipse(screen, (60, 60, 60), (bx + 18, by - 16 - right_arm, 6, 8))

        # 头
        hx = bx
        hy = by - 20
        breath = int(math.sin(anim_f * 0.06) * 1)
        hy += breath
        pygame.draw.circle(screen, head_color, (hx, hy), 14)
        pygame.draw.circle(screen, (160, 80, 160), (hx, hy), 14, 1)
        # 墨镜
        pygame.draw.rect(screen, (40, 40, 40), (hx - 8, hy - 4, 8, 5))
        pygame.draw.rect(screen, (40, 40, 40), (hx + 1, hy - 4, 8, 5))
        pygame.draw.line(screen, (40, 40, 40), (hx - 8, hy - 2), (hx + 9, hy - 2), 2)
        # 墨镜反光
        pygame.draw.line(screen, (100, 100, 120), (hx - 6, hy - 3), (hx - 3, hy - 3), 1)
        pygame.draw.line(screen, (100, 100, 120), (hx + 3, hy - 3), (hx + 6, hy - 3), 1)
        # 嘴（微笑）
        pygame.draw.arc(screen, (80, 40, 80), (hx - 5, hy + 3, 10, 5), 0.2, 2.9, 1)
        # 头发
        for hi in range(-2, 3):
            pygame.draw.line(screen, (80, 50, 80), (hx + hi * 3, hy - 12), (hx + hi * 4, hy - 18), 2)
        # 高光
        pygame.draw.ellipse(screen, (220, 160, 220), (hx - 8, hy - 12, 8, 6))

        # 旋转星光（召唤前预警）
        if self.summon_timer > self.summon_cd - 60:
            for si in range(6):
                ang = f * 0.1 + si * math.pi / 3
                sx = hx + int(math.cos(ang) * 25)
                sy = hy + int(math.sin(ang) * 25) - 10
                pygame.draw.circle(screen, tie_colors[si % 6], (sx, sy), 3)


# ─────────────────────────────────────────
# 跳跳僵尸
# ─────────────────────────────────────────
class JumpingZombie(Zombie):
    def __init__(self, row):
        super().__init__("jumping", row, ZOMBIE_DATA["jumping"])
        self.jump_cd = ZOMBIE_DATA["jumping"].get("jump_cd", 180)
        self.jump_timer = 0
        self.jumping = False
        self.jump_frame = 0

    def update(self, plants_in_row):
        self.jump_timer += 1
        if self.jump_timer >= self.jump_cd and not self.jumping:
            self.jumping = True
            self.jump_frame = 0
            self.jump_timer = 0

        if self.jumping:
            self.jump_frame += 1
            if self.jump_frame < 30:
                # 跳跃上升阶段
                self.x -= self.speed * 3
            elif self.jump_frame < 60:
                # 跳跃下降阶段
                self.x -= self.speed * 0.5
            else:
                self.jumping = False
            return super().update([])  # 跳过植物碰撞
        else:
            return super().update(plants_in_row)

    def _draw_body(self, screen):
        bx = int(self.x)
        by = int(self.y)
        f = self.frame
        anim_f = f if self.frozen <= 0 else 0

        body_color = (140, 180, 160)
        head_color = (140, 200, 170)

        # 跳跃时身体拉伸
        jump_stretch = 0
        if self.jumping:
            if self.jump_frame < 15:
                jump_stretch = int(self.jump_frame * 0.5)
            elif self.jump_frame < 30:
                jump_stretch = int((30 - self.jump_frame) * 0.5)
            elif self.jump_frame < 45:
                jump_stretch = -int((self.jump_frame - 30) * 0.5)
            else:
                jump_stretch = -int((60 - self.jump_frame) * 0.5)

        # 残影
        if self.jumping and self.jump_frame < 45:
            for ri in range(1, 4):
                rx = bx + ri * 20
                alpha = int(80 - ri * 20)
                ghost = pygame.Surface((40, 45), pygame.SRCALPHA)
                ghost.fill((140, 180, 160, alpha))
                screen.blit(ghost, (rx - 20, by - 30))

        # 弹簧腿（特别大）
        leg_color = (120, 120, 120)
        leg_swing = int(math.sin(anim_f * 0.15) * 6) if not self.eating else 3
        # 弹簧效果
        spring_h = 8 + jump_stretch
        # 左腿弹簧
        for si in range(3):
            sy = by + 10 + si * 6
            pygame.draw.rect(screen, leg_color, (bx - 10 - leg_swing, sy, 5, 4))
            pygame.draw.rect(screen, (80, 80, 80), (bx - 10 - leg_swing, sy, 5, 4), 1)
        # 右腿弹簧
        for si in range(3):
            sy = by + 10 + si * 6
            pygame.draw.rect(screen, leg_color, (bx + 5 + leg_swing, sy, 5, 4))
            pygame.draw.rect(screen, (80, 80, 80), (bx + 5 + leg_swing, sy, 5, 4), 1)
        # 脚
        pygame.draw.ellipse(screen, (100, 80, 60), (bx - 12 - leg_swing, by + 26 + jump_stretch, 10, 5))
        pygame.draw.ellipse(screen, (100, 80, 60), (bx + 2 + leg_swing, by + 26 + jump_stretch, 10, 5))

        # 身体
        by_offset = -jump_stretch
        pygame.draw.rect(screen, body_color, (bx - 12, by - 10 + by_offset, 24, 22), border_radius=4)
        pygame.draw.rect(screen, (100, 140, 120), (bx - 12, by - 10 + by_offset, 24, 22), 1, border_radius=4)
        # 条纹衣服
        for yi in range(-5, 10, 6):
            pygame.draw.line(screen, (120, 160, 140), (bx - 10, by + yi + by_offset), (bx + 10, by + yi + by_offset), 1)

        # 手臂
        if not self.eating:
            la = int(math.sin(anim_f * 0.15) * 8)
            ra = int(math.sin(anim_f * 0.15 + math.pi) * 8)
        else:
            la = 8
            ra = 8
        pygame.draw.rect(screen, body_color, (bx - 16, by - 4 + la // 2 + by_offset, 6, 12))
        pygame.draw.rect(screen, body_color, (bx + 10, by - 4 - ra // 2 + by_offset, 6, 12))
        pygame.draw.circle(screen, (160, 200, 180), (bx - 14, by + 6 + la // 2 + by_offset), 4)
        pygame.draw.circle(screen, (160, 200, 180), (bx + 14, by + 6 - ra // 2 + by_offset), 4)

        # 头
        hx = bx
        hy = by - 20 + by_offset
        breath = int(math.sin(anim_f * 0.06) * 1)
        hy += breath
        pygame.draw.circle(screen, head_color, (hx, hy), 14)
        pygame.draw.circle(screen, (100, 160, 130), (hx, hy), 14, 1)
        # 高光
        pygame.draw.ellipse(screen, (180, 230, 200), (hx - 8, hy - 12, 8, 6))
        # 眼睛（大圆眼）
        pygame.draw.circle(screen, WHITE, (hx - 4, hy - 1), 4)
        pygame.draw.circle(screen, WHITE, (hx + 4, hy - 1), 4)
        pygame.draw.circle(screen, (50, 50, 50), (hx - 4, hy - 1), 2)
        pygame.draw.circle(screen, (50, 50, 50), (hx + 4, hy - 1), 2)
        # 嘴（笑）
        pygame.draw.arc(screen, (80, 50, 50), (hx - 5, hy + 3, 10, 5), 0.2, 2.9, 1)
        # 头发（爆炸头）
        for hi in range(8):
            ang = hi * math.pi / 4 + f * 0.02
            hpx = hx + int(math.cos(ang) * 16)
            hpy = hy + int(math.sin(ang) * 16)
            pygame.draw.circle(screen, (100, 80, 60), (hpx, hpy), 3)

        # 跳跃轨迹发光
        if self.jumping:
            glow = int(abs(math.sin(f * 0.2)) * 50 + 30)
            gs = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(gs, (100, 200, 150, glow), (18, 18), 15)
            screen.blit(gs, (bx - 18, by + 15 - 18))


# ─────────────────────────────────────────
# 工厂函数
# ─────────────────────────────────────────
def create_zombie(ztype, row):
    if ztype == "normal":
        return NormalZombie(row)
    elif ztype == "cone":
        return ConeZombie(row)
    elif ztype == "bucket":
        return BucketZombie(row)
    elif ztype == "newspaper":
        return NewspaperZombie(row)
    elif ztype == "football":
        return FootballZombie(row)
    elif ztype == "dancer":
        return DancerZombie(row)
    elif ztype == "jumping":
        return JumpingZombie(row)
    else:
        return NormalZombie(row)
