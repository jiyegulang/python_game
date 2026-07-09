# sound.py - 程序化音效合成模块
# 使用 numpy 生成波形，pygame.sndarray 转 Sound，无需外部音频文件
import pygame
import numpy as np
import math

_mixer_ok = False
_sounds = {}        # name -> pygame.mixer.Sound
_music_channel = None  # 背景音乐通道
_muted = False

# ─────────────────────────────────────────
# 初始化
# ─────────────────────────────────────────
def init():
    """初始化混音器，生成所有音效"""
    global _mixer_ok
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        _mixer_ok = True
    except Exception:
        _mixer_ok = False
        return

    _build_all_sounds()


def _make_sound(samples):
    """将 float32 [-1,1] numpy 数组转为 pygame Sound（立体声 16bit）"""
    # 限幅
    samples = np.clip(samples, -1.0, 1.0)
    # 转 int16
    stereo = np.column_stack([samples, samples])
    audio = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(audio)


# ─── 基础波形生成器 ───
def _sine(freq, dur, sr=44100, decay=6.0, vol=0.5):
    """正弦波 + 指数衰减"""
    t = np.arange(int(sr * dur)) / sr
    env = np.exp(-t * decay)
    return vol * env * np.sin(2 * np.pi * freq * t)


def _square(freq, dur, sr=44100, decay=6.0, vol=0.3):
    """方波"""
    t = np.arange(int(sr * dur)) / sr
    env = np.exp(-t * decay)
    return vol * env * np.sign(np.sin(2 * np.pi * freq * t))


def _sawtooth(freq, dur, sr=44100, decay=6.0, vol=0.3):
    """锯齿波"""
    t = np.arange(int(sr * dur)) / sr
    env = np.exp(-t * decay)
    phase = (freq * t) % 1.0
    return vol * env * (2 * phase - 1)


def _noise(dur, sr=44100, decay=8.0, vol=0.4, lowpass=0.5):
    """白噪声 + 低通滤波 + 衰减"""
    n = int(sr * dur)
    raw = np.random.randn(n)
    # 简单一阶低通
    smoothed = np.zeros(n)
    a = lowpass
    for i in range(1, n):
        smoothed[i] = a * raw[i] + (1 - a) * smoothed[i - 1]
    t = np.arange(n) / sr
    env = np.exp(-t * decay)
    return vol * env * smoothed


def _freq_sweep(f0, f1, dur, sr=44100, decay=4.0, vol=0.4, wave_type="sine"):
    """频率扫频"""
    t = np.arange(int(sr * dur)) / sr
    freq = f0 + (f1 - f0) * (t / dur)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    env = np.exp(-t * decay)
    if wave_type == "square":
        wave = np.sign(np.sin(phase))
    elif wave_type == "saw":
        phase_mod = (freq * t) % 1.0
        wave = 2 * phase_mod - 1
    else:
        wave = np.sin(phase)
    return vol * env * wave


def _mix(*arrays):
    """混合多个音频（取最大长度，短的补零）"""
    max_len = max(len(a) for a in arrays)
    result = np.zeros(max_len)
    for a in arrays:
        result[:len(a)] += a
    return result / max(1, len(arrays))


# ─────────────────────────────────────────
# 音效定义
# ─────────────────────────────────────────
def _build_all_sounds():
    """生成所有音效并存入 _sounds"""
    sr = 44100

    # 1. 种植植物 — 柔和的土落声
    s = _mix(
        _sine(180, 0.08, decay=15, vol=0.4),
        _noise(0.06, decay=20, vol=0.15, lowpass=0.3),
        _sine(90, 0.12, decay=10, vol=0.3),
    )
    _sounds["plant"] = _make_sound(s)

    # 2. 收集阳光 — 闪亮的上升音
    s = _mix(
        _freq_sweep(600, 1200, 0.15, decay=8, vol=0.35),
        _sine(1500, 0.1, decay=12, vol=0.15),
    )
    _sounds["sun_collect"] = _make_sound(s)

    # 3. 豌豆射击 — 短促 pop
    s = _mix(
        _sine(800, 0.05, decay=25, vol=0.3),
        _noise(0.03, decay=30, vol=0.1, lowpass=0.6),
    )
    _sounds["pea_shoot"] = _make_sound(s)

    # 4. 豌豆命中 — 湿润 splat
    s = _noise(0.08, decay=15, vol=0.35, lowpass=0.25)
    _sounds["pea_hit"] = _make_sound(s)

    # 5. 僵尸 groan — 低频喉音 + 颤音
    t = np.arange(int(sr * 0.4)) / sr
    freq = 80 + 10 * np.sin(2 * np.pi * 5 * t)  # 颤音
    phase = 2 * np.pi * np.cumsum(freq) / sr
    groan = 0.4 * np.exp(-t * 3) * np.sin(phase)
    groan += 0.15 * np.exp(-t * 4) * np.sin(2 * phase)  # 泛音
    _sounds["zombie_groan"] = _make_sound(groan)

    # 6. 爆炸 — 大 boom
    s = _mix(
        _noise(0.5, decay=4, vol=0.5, lowpass=0.3),
        _sine(60, 0.5, decay=5, vol=0.4),
        _sine(40, 0.6, decay=3, vol=0.3),
    )
    _sounds["explosion"] = _make_sound(s)

    # 7. 小推车 — 引擎运转声
    t = np.arange(int(sr * 0.8)) / sr
    engine = 0.3 * np.exp(-t * 0.5) * _sawtooth(120, 0.8, decay=0.5, vol=1.0)
    engine += 0.15 * np.exp(-t * 0.5) * _noise(0.8, decay=0.5, vol=1.0, lowpass=0.4)
    _sounds["lawn_mower"] = _make_sound(engine)

    # 8. 铲除 — 挖掘声
    s = _mix(
        _noise(0.15, decay=10, vol=0.3, lowpass=0.3),
        _sine(150, 0.1, decay=12, vol=0.2),
    )
    _sounds["shovel"] = _make_sound(s)

    # 9. 按钮点击 — UI blip
    s = _sine(1000, 0.05, decay=25, vol=0.3)
    _sounds["button_click"] = _make_sound(s)

    # 10. 游戏开始 — 上升音阶
    s = _mix(
        _sine(523, 0.1, decay=6, vol=0.3),   # C5
        _sine(659, 0.1, decay=6, vol=0.3),   # E5 (delayed)
        _sine(784, 0.15, decay=5, vol=0.3),  # G5 (more delayed)
    )
    # 手动延迟各音符
    n1 = int(sr * 0.0)
    n2 = int(sr * 0.1)
    n3 = int(sr * 0.2)
    total = n3 + int(sr * 0.15)
    wave = np.zeros(total)
    wave[n1:n1 + int(sr * 0.1)] += _sine(523, 0.1, decay=6, vol=0.3)
    wave[n2:n2 + int(sr * 0.1)] += _sine(659, 0.1, decay=6, vol=0.3)
    wave[n3:n3 + int(sr * 0.15)] += _sine(784, 0.15, decay=5, vol=0.35)
    _sounds["game_start"] = _make_sound(wave)

    # 11. 波次开始 — 警报/鼓点
    t = np.arange(int(sr * 0.6)) / sr
    drum = np.zeros(len(t))
    for beat in range(4):
        start = int(beat * sr * 0.15)
        end = min(start + int(sr * 0.1), len(t))
        seg_t = np.arange(end - start) / sr
        drum[start:end] += 0.4 * np.exp(-seg_t * 15) * np.sin(2 * np.pi * 100 * seg_t)
    _sounds["wave_start"] = _make_sound(drum)

    # 12. 胜利 — 欢快上升旋律
    notes = [(523, 0), (659, 0.12), (784, 0.24), (1047, 0.36)]
    total = int(sr * 0.6)
    wave = np.zeros(total)
    for freq, delay in notes:
        start = int(sr * delay)
        dur = 0.2
        end = min(start + int(sr * dur), total)
        seg_t = np.arange(end - start) / sr
        wave[start:end] += 0.35 * np.exp(-seg_t * 5) * np.sin(2 * np.pi * freq * seg_t)
    _sounds["win"] = _make_sound(wave)

    # 13. 失败 — 下降旋律
    notes = [(400, 0), (350, 0.15), (280, 0.3), (200, 0.5)]
    total = int(sr * 0.8)
    wave = np.zeros(total)
    for freq, delay in notes:
        start = int(sr * delay)
        dur = 0.25
        end = min(start + int(sr * dur), total)
        seg_t = np.arange(end - start) / sr
        wave[start:end] += 0.35 * np.exp(-seg_t * 4) * np.sin(2 * np.pi * freq * seg_t)
    _sounds["lose"] = _make_sound(wave)

    # 14. 冰冻 — 晶体声
    s = _mix(
        _freq_sweep(2000, 3000, 0.15, decay=10, vol=0.25),
        _sine(2500, 0.1, decay=15, vol=0.15),
    )
    _sounds["freeze"] = _make_sound(s)

    # 15. 毒烟 — 嘶嘶气泡声
    s = _noise(0.2, decay=6, vol=0.25, lowpass=0.5)
    _sounds["poison"] = _make_sound(s)

    # 16. 土豆雷启动 — 机械 tick
    s = _mix(
        _square(1500, 0.03, decay=40, vol=0.2),
        _sine(2000, 0.03, decay=40, vol=0.1),
    )
    _sounds["potato_arm"] = _make_sound(s)

    # 17. 报纸撕裂
    s = _noise(0.15, decay=12, vol=0.3, lowpass=0.6)
    _sounds["paper_tear"] = _make_sound(s)

    # 18. 阳光产出 — 轻柔叮
    s = _sine(880, 0.12, decay=10, vol=0.2)
    _sounds["sun_produce"] = _make_sound(s)


# ─────────────────────────────────────────
# 背景音乐 — 简单循环旋律
# ─────────────────────────────────────────
_bg_music_data = None

def _build_bg_music():
    """生成一段循环背景音乐"""
    sr = 44100
    # 简单的 8 小节旋律 (C大调)
    # 音符: (频率, 时长秒)
    melody = [
        # 第一句
        (523, 0.2), (587, 0.2), (659, 0.2), (523, 0.2),
        (587, 0.2), (659, 0.2), (784, 0.4),
        (659, 0.2), (587, 0.2), (523, 0.4),
        # 第二句
        (440, 0.2), (523, 0.2), (587, 0.2), (659, 0.4),
        (523, 0.2), (440, 0.2), (392, 0.4),
        # 第三句
        (523, 0.2), (659, 0.2), (784, 0.2), (880, 0.4),
        (784, 0.2), (659, 0.2), (523, 0.4),
        # 第四句（收尾）
        (587, 0.2), (523, 0.2), (440, 0.2), (392, 0.2),
        (440, 0.2), (523, 0.6),
    ]
    # 低音线
    bass = [
        (131, 0.8), (147, 0.8), (131, 0.8), (165, 0.8),
        (131, 0.8), (147, 0.8), (131, 0.8), (165, 0.8),
        (131, 0.8), (147, 0.8), (131, 0.8), (165, 0.8),
        (131, 0.8), (147, 0.8), (131, 0.8), (165, 0.8),
    ]

    total_dur = sum(n[1] for n in melody)
    total_samples = int(sr * total_dur)
    wave = np.zeros(total_samples)

    # 旋律
    pos = 0
    for freq, dur in melody:
        n = int(sr * dur)
        end = min(pos + n, total_samples)
        seg_t = np.arange(end - pos) / sr
        # 轻微颤音
        vibrato = 1 + 0.005 * np.sin(2 * np.pi * 6 * seg_t)
        wave[pos:end] += 0.15 * np.exp(-seg_t * 2) * np.sin(2 * np.pi * freq * vibrato * seg_t)
        pos += n

    # 低音
    pos = 0
    for freq, dur in bass:
        n = int(sr * dur)
        end = min(pos + n, total_samples)
        seg_t = np.arange(end - pos) / sr
        wave[pos:end] += 0.1 * np.exp(-seg_t * 1) * np.sin(2 * np.pi * freq * seg_t)
        pos += n

    # 加一点节奏感（每拍加个软打击）
    beat_dur = 0.2
    for i in range(int(total_dur / beat_dur)):
        pos = int(i * sr * beat_dur)
        n = int(sr * 0.03)
        end = min(pos + n, total_samples)
        seg_t = np.arange(end - pos) / sr
        wave[pos:end] += 0.05 * np.exp(-seg_t * 30) * np.sin(2 * np.pi * 80 * seg_t)

    return wave


def start_music():
    """开始循环播放背景音乐"""
    global _bg_music_data, _music_channel
    if not _mixer_ok or _muted:
        return
    try:
        if _bg_music_data is None:
            _bg_music_data = _build_bg_music()
        sound = _make_sound(_bg_music_data)
        if _music_channel is None:
            _music_channel = pygame.mixer.Channel(7)
        _music_channel.play(sound, loops=-1)
        _music_channel.set_volume(0.3)
    except Exception:
        pass


def stop_music():
    """停止背景音乐"""
    global _music_channel
    if _music_channel:
        _music_channel.stop()


def set_music_volume(v):
    if _music_channel:
        _music_channel.set_volume(v)


# ─────────────────────────────────────────
# 播放接口
# ─────────────────────────────────────────
def play(name, volume=0.5):
    """播放指定音效"""
    if not _mixer_ok or _muted:
        return
    s = _sounds.get(name)
    if s:
        s.set_volume(volume)
        s.play()


def toggle_mute():
    """切换静音"""
    global _muted
    _muted = not _muted
    if _muted:
        pygame.mixer.stop()
    else:
        start_music()
    return _muted


def is_muted():
    return _muted
