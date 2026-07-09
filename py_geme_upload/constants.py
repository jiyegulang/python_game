# constants.py - 游戏常量配置

# 窗口设置
SCREEN_WIDTH  = 1100
SCREEN_HEIGHT = 780
TITLE = "植物大战僵尸 - Python版"
FPS = 60

# 底部植物选择栏
BOTTOM_BAR_H   = 90   # 底部选择栏高度
BOTTOM_BAR_Y   = SCREEN_HEIGHT - BOTTOM_BAR_H  # 690

# 网格设置
GRID_COLS = 9
GRID_ROWS = 5
CELL_W = 100
CELL_H = 110
GRID_X = 60        # 网格左上角 X（左侧留少量边距）
GRID_Y = 75        # 网格左上角 Y（顶栏下方）

# 小推车位置（红线在 GRID_X - 5，推车再靠左）
LAWN_MOWER_X = GRID_X - 40

# 颜色
WHITE     = (255, 255, 255)
BLACK     = (0,   0,   0  )
GREEN     = (34,  139, 34 )
DARK_GREEN= (0,   100, 0  )
YELLOW    = (255, 215, 0  )
ORANGE    = (255, 140, 0  )
RED       = (220, 50,  50 )
BROWN     = (139, 90,  43 )
GRAY      = (150, 150, 150)
LIGHT_BLUE= (173, 216, 230)
SKY_BLUE  = (135, 206, 235)
DARK_GRAY = (80,  80,  80 )
PINK      = (255, 182, 193)
PURPLE    = (128, 0,   128)
LIME      = (50,  205, 50 )

# 植物数据
PLANT_DATA = {
    "sunflower": {
        "name": "向日葵",
        "cost": 50,
        "hp": 300,
        "color": YELLOW,
        "desc": "产生阳光",
        "sun_per_tick": 0.0025,  # 每帧产生阳光量（约400帧/6.7秒产一次）
    },
    "peashooter": {
        "name": "豌豆射手",
        "cost": 100,
        "hp": 300,
        "color": LIME,
        "desc": "发射豌豆",
        "shoot_cd": 90,
        "pea_dmg": 20,
        "pea_speed": 5,
    },
    "wallnut": {
        "name": "坚果墙",
        "cost": 50,
        "hp": 2400,
        "color": BROWN,
        "desc": "高血量防御",
    },
    "snowpea": {
        "name": "寒冰射手",
        "cost": 175,
        "hp": 300,
        "color": LIGHT_BLUE,
        "desc": "冻结僵尸",
        "shoot_cd": 90,
        "pea_dmg": 20,
        "pea_speed": 5,
        "freeze": True,
    },
    "cherrycbomb": {
        "name": "樱桃炸弹",
        "cost": 150,
        "hp": 1,
        "color": RED,
        "desc": "范围爆炸",
        "explode_delay": 90,
        "explode_dmg": 1800,
        "explode_radius": 1,
    },
    "repeater": {
        "name": "双重射手",
        "cost": 200,
        "hp": 300,
        "color": (80, 200, 80),
        "desc": "双发豌豆",
        "shoot_cd": 90,
        "pea_dmg": 20,
        "pea_speed": 5,
    },
    "spikeweed": {
        "name": "地刺",
        "cost": 100,
        "hp": 600,
        "color": (120, 160, 60),
        "desc": "持续地面伤害",
        "spike_dmg": 2,
    },
    "potatomine": {
        "name": "土豆雷",
        "cost": 25,
        "hp": 1,
        "color": (180, 140, 80),
        "desc": "踩踏后爆炸",
        "arm_delay": 180,
        "explode_dmg": 1800,
    },
    "sunshroom": {
        "name": "阳光菇",
        "cost": 25,
        "hp": 300,
        "color": (255, 200, 50),
        "desc": "夜晚免费产阳光",
        "sun_per_tick": 0.003,
    },
    "fumeshroom": {
        "name": "毒菇",
        "cost": 150,
        "hp": 300,
        "color": PURPLE,
        "desc": "发射毒烟伤害",
        "shoot_cd": 60,
        "pea_dmg": 30,
        "pea_speed": 6,
    },
}

PLANT_TYPES = list(PLANT_DATA.keys())

# 僵尸数据
ZOMBIE_DATA = {
    "normal": {
        "name": "普通僵尸",
        "hp": 200,
        "speed": 0.4,
        "dmg": 1,
        "color": (160, 200, 140),
    },
    "cone": {
        "name": "路锥僵尸",
        "hp": 560,
        "speed": 0.4,
        "dmg": 1,
        "color": (200, 160, 100),
    },
    "bucket": {
        "name": "铁桶僵尸",
        "hp": 1280,
        "speed": 0.35,
        "dmg": 1,
        "color": (160, 160, 190),
    },
    "newspaper": {
        "name": "报纸僵尸",
        "hp": 300,
        "speed": 0.35,
        "dmg": 1,
        "color": (200, 200, 160),
        "paper_hp": 200,       # 报纸被打掉后速度暴增
        "enrage_speed": 1.2,
    },
    "football": {
        "name": "橄榄球僵尸",
        "hp": 1600,
        "speed": 0.6,
        "dmg": 2,
        "color": (180, 130, 90),
    },
    "dancer": {
        "name": "舞王僵尸",
        "hp": 500,
        "speed": 0.45,
        "dmg": 1,
        "color": (200, 100, 200),
        "summon_cd": 300,      # 每隔N帧召唤一只伴舞
    },
    "jumping": {
        "name": "跳跳僵尸",
        "hp": 400,
        "speed": 0.4,
        "dmg": 1,
        "color": (140, 200, 170),
        "jump_cd": 180,        # 跳跃冷却帧
        "jump_dist": 2,        # 跳过几列
    },
}

# 阳光设置
STARTING_SUN = 150
SUN_DROP_INTERVAL = 1200  # 每N帧从天上掉一个阳光（约20秒）
SUN_VALUE = 25
SUN_FALL_SPEED = 1.5

# ─────────────────────────────────────────
# 关卡定义
# ─────────────────────────────────────────
LEVELS = [
    {
        "id": 1,
        "name": "白天 · 第一关",
        "desc": "阳光明媚，僵尸初次入侵！",
        "bg_mode": "day",
        "waves": [
            {"delay": 1200, "zombies": [("normal", 1), ("normal", 3)]},
            {"delay": 1500, "zombies": [("normal", 1), ("normal", 2), ("cone", 4)]},
            {"delay": 1500, "zombies": [("normal", 0), ("cone", 2), ("normal", 3), ("bucket", 4)]},
            {"delay": 1800, "zombies": [("cone", 0), ("normal", 1), ("bucket", 2), ("cone", 3), ("normal", 4)]},
            {"delay": 2000, "zombies": [("bucket", 0), ("bucket", 1), ("cone", 2), ("bucket", 3), ("bucket", 4)]},
        ],
    },
    {
        "id": 2,
        "name": "夜晚 · 第二关",
        "desc": "黑夜降临，报纸僵尸出没！无天降阳光，植物费用5折！",
        "bg_mode": "night",
        "sun_drop_interval": 0,      # 夜晚不掉天降阳光
        "starting_sun": 100,
        "night_discount": True,      # 夜晚植物费用折半
        "waves": [
            {"delay": 1200, "zombies": [("normal", 0), ("newspaper", 2), ("normal", 4)]},
            {"delay": 1500, "zombies": [("cone", 1), ("newspaper", 2), ("newspaper", 3)]},
            {"delay": 1500, "zombies": [("normal", 0), ("cone", 1), ("newspaper", 2), ("bucket", 4)]},
            {"delay": 1800, "zombies": [("newspaper", 0), ("bucket", 1), ("cone", 2), ("newspaper", 3), ("cone", 4)]},
            {"delay": 2000, "zombies": [("bucket", 0), ("newspaper", 1), ("bucket", 2), ("newspaper", 3), ("bucket", 4)]},
        ],
    },
    {
        "id": 3,
        "name": "雾天 · 第三关",
        "desc": "大雾弥漫，橄榄球和舞王僵尸入侵！",
        "bg_mode": "fog",
        "waves": [
            {"delay": 1000, "zombies": [("normal", 0), ("football", 2), ("normal", 4)]},
            {"delay": 1200, "zombies": [("cone", 1), ("football", 2), ("dancer", 3)]},
            {"delay": 1400, "zombies": [("football", 0), ("dancer", 1), ("jumping", 2), ("cone", 4)]},
            {"delay": 1600, "zombies": [("jumping", 0), ("football", 1), ("dancer", 2), ("bucket", 3), ("jumping", 4)]},
            {"delay": 1800, "zombies": [("football", 0), ("dancer", 1), ("football", 2), ("jumping", 3), ("football", 4)]},
        ],
    },
]

# 向后兼容
WAVE_CONFIG = LEVELS[0]["waves"]
