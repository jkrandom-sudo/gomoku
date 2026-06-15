# 五子棋 (Gomoku)

[English](#english) | [中文](#中文)

---

## 中文

### 简介

五子棋是一款经典的两人对弈策略游戏，在 15×15 的棋盘上进行。本实现支持**玩家对战 (PvP)** 和**人机对战 (PvE)** 两种模式，拥有计时器、撤销、声音、排行榜等完整功能。

### 功能特性

| 功能 | 说明 |
|------|------|
| 🎮 **双模式** | 玩家对战 (PvP) 和人机对战 (PvE) |
| 🤖 **AI 对手** | 基于评分算法的智能 AI，非随机落子 |
| ⏱️ **计时器** | 每步 60 秒倒计时，超时判负，支持 +/- 调整 (10-300秒) |
| ↩️ **撤销** | PvP 撤销 1 步，PvE 撤销 2 步回到玩家回合 |
| 🌐 **双语** | 中英文界面实时切换 (按 L 键) |
| 🔊 **音效** | 落子提示音 + 获胜语音播报，可开关 (按 S 键) |
| 🏆 **排行榜** | 记录玩家胜负平数据，按胜率排名 |
| 💾 **持久化** | 设置和分数自动保存到 JSON 文件 |
| ⏸️ **暂停** | 游戏可随时暂停/继续 |
| 🎯 **胜利检测** | 横、竖、斜四个方向五子连珠检测 |

### 安装

```bash
# 克隆或进入游戏目录
cd ~/games/gomoku

# 确保 Python 3.6+
python3 --version

# 直接运行（无需安装依赖）
python3 game.py
```

### 如何游玩

1. 运行 `python3 game.py`
2. 在主菜单中选择模式：PvP (1) 或 PvE (2)
3. 输入玩家名称
4. 轮流输入坐标落子（如 `H8` 表示棋盘中心）
5. 先连成五子者获胜

### 操作键位

| 按键 | 功能 |
|------|------|
| `A1`-`O15` | 落子坐标 |
| `U` | 撤销上一步 |
| `P` | 暂停/继续 |
| `Q` | 退出到主菜单 |
| `R` | 重新开始 |
| `S` | 开关声音 |
| `L` | 切换中英文 |
| `+` | 增加时间限制 (+10秒) |
| `-` | 减少时间限制 (-10秒) |

### AI 策略说明

AI 使用**评分算法**评估每个空位：

1. 对每个空位，在**四个方向**（水平、垂直、两条对角线）上分别计算：
   - 同色连续棋子数量
   - 两端开放程度（空位数量）
2. 根据连子数量和开放端数给予不同权重：
   - 五子连珠：100,000 分
   - 活四（两端开放）：10,000 分
   - 冲四（一端开放）：5,000 分
   - 活三：1,000 分
   - 眠三：200 分
   - 活二：100 分
   - 眠二：20 分
3. 综合攻击分（AI 自己）和防守分（阻挡玩家），攻击权重略高 (1.1x)
4. 选择综合评分最高的位置落子
5. 同分时优先选择靠近中心的位置

### 运行测试

```bash
cd ~/games/gomoku
python3 -m pytest test_game.py -v
```

测试覆盖：
- 棋盘初始化 (尺寸、重置、克隆)
- 胜利检测 (水平、垂直、两条对角线)
- 平局检测 (棋盘满)
- 输入验证 (有效/无效坐标、命令键)
- 撤销功能 (单步、多步、空棋盘)
- AI 落子 (中心开局、堵四子、取胜、防守优先)

### 文件结构

```
~/games/gomoku/
├── game.py          # 主游戏程序
├── test_game.py     # 测试文件
├── scores.json      # 分数记录
├── settings.json    # 设置（语言、声音）
└── README.md        # 本文件
```

---

## English

### Introduction

Gomoku is a classic two-player strategy game played on a 15×15 board. This implementation supports **Player vs Player (PvP)** and **Player vs AI (PvE)** modes, with timer, undo, sound effects, scoreboard, and bilingual interface.

### Features

| Feature | Description |
|---------|-------------|
| 🎮 **Dual Mode** | PvP and PvE (Player vs AI) |
| 🤖 **AI Opponent** | Scoring-based smart AI, not random |
| ⏱️ **Move Timer** | 60s per move, timeout = loss, +/- adjust (10-300s) |
| ↩️ **Undo** | PvP: 1 move, PvE: 2 moves back to player's turn |
| 🌐 **Bilingual** | Switch between Chinese and English (press L) |
| 🔊 **Sound** | Bell on placement + voice on win, toggle with S |
| 🏆 **Scoreboard** | Track wins/losses/draws, ranked by win rate |
| 💾 **Persistence** | Settings and scores auto-saved to JSON |
| ⏸️ **Pause** | Pause/resume anytime |
| 🎯 **Win Detection** | 5+ consecutive stones in any of 4 directions |

### Installation

```bash
# Clone or enter the game directory
cd ~/games/gomoku

# Requires Python 3.6+
python3 --version

# Run directly (no dependencies needed)
python3 game.py
```

### How to Play

1. Run `python3 game.py`
2. Choose mode from menu: PvP (1) or PvE (2)
3. Enter player names
4. Take turns placing stones by entering coordinates (e.g. `H8` for center)
5. First to connect 5 stones in a row wins

### Controls

| Key | Action |
|-----|--------|
| `A1`-`O15` | Place stone at coordinate |
| `U` | Undo last move |
| `P` | Pause/Resume |
| `Q` | Quit to main menu |
| `R` | Restart game |
| `S` | Toggle sound |
| `L` | Toggle language (Chinese/English) |
| `+` | Increase time limit (+10s) |
| `-` | Decrease time limit (-10s) |

### AI Strategy

The AI uses a **scoring algorithm** to evaluate each empty cell:

1. For each empty cell, evaluate **4 directions** (horizontal, vertical, 2 diagonals):
   - Count of consecutive same-color stones
   - Number of open ends (empty spaces at line ends)
2. Weight by stone count and open ends:
   - Five in a row: 100,000 pts
   - Open four (both ends open): 10,000 pts
   - Half-open four: 5,000 pts
   - Open three: 1,000 pts
   - Half-open three: 200 pts
   - Open two: 100 pts
   - Half-open two: 20 pts
3. Combine attack score (AI's own pattern) and defense score (blocking player), with slight attack priority (1.1x)
4. Pick the cell with the highest combined score
5. Prefer center positions when scores are tied

### Running Tests

```bash
cd ~/games/gomoku
python3 -m pytest test_game.py -v
```

Test coverage:
- Board initialization (size, reset, clone)
- Win detection (horizontal, vertical, both diagonals)
- Draw detection (full board)
- Input validation (valid/invalid coordinates, command keys)
- Undo functionality (single, multiple, empty board)
- AI moves (center opening, block four, take win, defense priority)

### File Structure

```
~/games/gomoku/
├── game.py          # Main game program
├── test_game.py     # Test file
├── scores.json      # Score records
├── settings.json    # Settings (language, sound)
└── README.md        # This file
```
