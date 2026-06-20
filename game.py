#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gomoku (五子棋) - Console-based game
Supports PvP and PvE modes, bilingual (Chinese/English), timer, undo, score tracking.
"""

import json
import os
import sys
import time
import threading
import atexit
from i18n import STRINGS, t as i18n_t

if os.name == 'nt':
    import msvcrt  # Windows keyboard input
else:
    import select
    import termios
    import tty

# ── Constants ──────────────────────────────────────────────────────────────
BOARD_SIZE = 15
EMPTY = 0
BLACK = 1  # ●
WHITE = 2  # ○
STONE_CHARS = {EMPTY: ' ', BLACK: '●', WHITE: '○'}
STONE_NAMES = {BLACK: '黑棋', WHITE: '白棋'}
STONE_NAMES_EN = {BLACK: 'Black', WHITE: 'White'}

DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]  # H, V, D1, D2

# ── Language support ───────────────────────────────────────────────────────
LANG = STRINGS  # Reference to i18n module for backwards compatibility

# ── File paths ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCORES_FILE = os.path.join(BASE_DIR, 'scores.json')
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')


# ── Terminal helpers ───────────────────────────────────────────────────────

def getch():
    """Get a single keypress from stdin (cross-platform)."""
    if os.name == 'nt':
        return msvcrt.getch().decode('utf-8', errors='replace')
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def play_sound():
    """Play system bell sound."""
    print('\a', end='', flush=True)


def say_text(text):
    """Use macOS 'say' command or Windows PowerShell to speak text."""
    try:
        if sys.platform == 'darwin':
            os.system(f'say "{text}" &')
        elif os.name == 'nt':
            os.system(f'powershell -Command "Add-Type -AssemblyName System.Speech; '
                      f'(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')" &')
    except Exception:
        pass


# ── Board class ────────────────────────────────────────────────────────────

class Board:
    """15x15 Gomoku board."""

    def __init__(self):
        self.grid = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.move_history = []  # list of (row, col, player)

    def reset(self):
        self.grid = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.move_history = []

    def clone(self):
        """Return a deep copy of the board."""
        b = Board()
        b.grid = [row[:] for row in self.grid]
        b.move_history = list(self.move_history)
        return b

    def is_valid(self, row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def is_empty(self, row, col):
        return self.is_valid(row, col) and self.grid[row][col] == EMPTY

    def place(self, row, col, player):
        if not self.is_empty(row, col):
            return False
        self.grid[row][col] = player
        self.move_history.append((row, col, player))
        return True

    def undo(self):
        if not self.move_history:
            return None
        row, col, player = self.move_history.pop()
        self.grid[row][col] = EMPTY
        return row, col, player

    def is_full(self):
        return all(self.grid[r][c] != EMPTY for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))

    def check_win(self, row, col, player):
        """Check if placing at (row, col) wins for player."""
        for dr, dc in DIRECTIONS:
            count = 1
            # Positive direction
            r, c = row + dr, col + dc
            while self.is_valid(r, c) and self.grid[r][c] == player:
                count += 1
                r += dr
                c += dc
            # Negative direction
            r, c = row - dr, col - dc
            while self.is_valid(r, c) and self.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 5:
                return True
        return False

    def get_empty_cells(self):
        return [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.grid[r][c] == EMPTY]

    def display(self, lang='zh'):
        """Display the board with coordinates."""
        t = LANG[lang]
        print()
        # Column headers
        print('   ', end='')
        for c in range(BOARD_SIZE):
            print(f' {chr(ord("A") + c)}', end='')
        print()
        # Board rows
        for r in range(BOARD_SIZE):
            print(f'{r+1:2d} ', end='')
            for c in range(BOARD_SIZE):
                val = self.grid[r][c]
                if val == BLACK:
                    print(f' {t["black_stone"]}', end='')
                elif val == WHITE:
                    print(f' {t["white_stone"]}', end='')
                else:
                    print(' .', end='')
            print(f' {r+1:2d}')
        # Column footer
        print('   ', end='')
        for c in range(BOARD_SIZE):
            print(f' {chr(ord("A") + c)}', end='')
        print()
        print()


# ── AI ─────────────────────────────────────────────────────────────────────

class AI:
    """Simple scoring-based AI for Gomoku."""

    @staticmethod
    def evaluate_cell(board, row, col, player):
        """Score a cell for a given player based on consecutive stones in 4 directions."""
        score = 0
        for dr, dc in DIRECTIONS:
            count = 1  # the stone itself
            open_ends = 0

            # Positive direction
            r, c = row + dr, col + dc
            while board.is_valid(r, c) and board.grid[r][c] == player:
                count += 1
                r += dr
                c += dc
            if board.is_valid(r, c) and board.grid[r][c] == EMPTY:
                open_ends += 1

            # Negative direction
            r, c = row - dr, col - dc
            while board.is_valid(r, c) and board.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if board.is_valid(r, c) and board.grid[r][c] == EMPTY:
                open_ends += 1

            # Scoring weights
            if count >= 5:
                score += 100000
            elif count == 4:
                if open_ends == 2:
                    score += 10000
                elif open_ends == 1:
                    score += 5000
            elif count == 3:
                if open_ends == 2:
                    score += 1000
                elif open_ends == 1:
                    score += 200
            elif count == 2:
                if open_ends == 2:
                    score += 100
                elif open_ends == 1:
                    score += 20
            elif count == 1:
                if open_ends == 2:
                    score += 10
                elif open_ends == 1:
                    score += 2
        return score

    @staticmethod
    def get_best_move(board, ai_player):
        """Get the best move for AI. ai_player is BLACK or WHITE."""
        human_player = WHITE if ai_player == BLACK else BLACK
        best_score = -1
        best_moves = []

        empty_cells = board.get_empty_cells()

        # If board is empty, play center
        if len(empty_cells) == BOARD_SIZE * BOARD_SIZE:
            center = BOARD_SIZE // 2
            return center, center

        for row, col in empty_cells:
            # Attack score (AI's own pattern)
            attack = AI.evaluate_cell(board, row, col, ai_player)
            # Defense score (block human)
            defense = AI.evaluate_cell(board, row, col, human_player)
            # Combined: prioritize attack slightly
            total = attack * 1.1 + defense

            if total > best_score:
                best_score = total
                best_moves = [(row, col)]
            elif total == best_score:
                best_moves.append((row, col))

        if best_moves:
            # Prefer center-ish positions among ties
            center = BOARD_SIZE // 2
            best_moves.sort(key=lambda p: abs(p[0] - center) + abs(p[1] - center))
            return best_moves[0]
        return empty_cells[0] if empty_cells else (-1, -1)


# ── Score tracking ─────────────────────────────────────────────────────────

def load_scores():
    """Load scores from JSON file."""
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_scores(scores):
    """Save scores to JSON file."""
    try:
        with open(SCORES_FILE, 'w', encoding='utf-8') as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def update_score(player_name, result, opponent_name=None):
    """Update score for a player. result: 'win', 'lose', 'draw'."""
    scores = load_scores()
    today = time.strftime('%Y-%m-%d')

    if player_name not in scores:
        scores[player_name] = {'wins': 0, 'losses': 0, 'draws': 0, 'last_game': today}

    if result == 'win':
        scores[player_name]['wins'] += 1
    elif result == 'lose':
        scores[player_name]['losses'] += 1
    elif result == 'draw':
        scores[player_name]['draws'] += 1

    scores[player_name]['last_game'] = today
    save_scores(scores)


def show_scoreboard(lang='zh'):
    """Display top 10 scoreboard."""
    t = LANG[lang]
    scores = load_scores()
    clear_screen()
    print(t['score_title'])
    print()

    if not scores:
        print(t['no_scores'])
    else:
        # Calculate win rate and sort
        ranking = []
        for name, data in scores.items():
            total = data['wins'] + data['losses'] + data['draws']
            win_rate = data['wins'] / total if total > 0 else 0
            ranking.append((win_rate, data['wins'], data['losses'], data['draws'], data['last_game'], name))

        ranking.sort(key=lambda x: (-x[0], -x[1], x[5]))
        top10 = ranking[:10]

        print(t['score_header'])
        print(t.get('dash_line', '─' * 60))
        for i, (wr, w, l, d, last, name) in enumerate(top10, 1):
            print(t['score_row'].format(i, name, w, l, d, wr, last))

    print()
    input(t['press_enter'])


# ── Settings ───────────────────────────────────────────────────────────────

def load_settings():
    """Load settings from JSON file."""
    defaults = {'language': 'zh', 'sound': True}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for k in defaults:
                    data.setdefault(k, defaults[k])
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return dict(defaults)


def save_settings(settings):
    """Save settings to JSON file."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


# ── Game class ─────────────────────────────────────────────────────────────

class Game:
    """Main game controller."""

    def __init__(self):
        self.settings = load_settings()
        self.lang = self.settings.get('language', 'zh')
        self.sound_enabled = self.settings.get('sound', True)
        self.board = Board()
        self.state = 'menu'  # menu, playing, paused, game_over
        self.mode = 'pvp'  # pvp or pve
        self.current_player = BLACK
        self.player_names = {BLACK: '', WHITE: ''}
        self.time_limit = 60  # seconds per move
        self.timer_remaining = self.time_limit
        self.timer_active = False
        self.timer_thread = None
        self.timer_lock = threading.Lock()
        self.timer_expired = False
        self.running = True
        self.last_move = None  # (row, col) for display

    def t(self, key):
        """Get translated string."""
        return LANG[self.lang].get(key, key)

    def toggle_language(self):
        """Toggle between zh and en."""
        self.lang = 'en' if self.lang == 'zh' else 'zh'
        self.settings['language'] = self.lang
        save_settings(self.settings)
        if self.lang == 'zh':
            print(self.t('lang_zh'))
        else:
            print(self.t('lang_en'))
        time.sleep(0.5)

    def toggle_sound(self):
        """Toggle sound on/off."""
        self.sound_enabled = not self.sound_enabled
        self.settings['sound'] = self.sound_enabled
        save_settings(self.settings)
        print(self.t('sound_on') if self.sound_enabled else self.t('sound_off'))
        time.sleep(0.5)

    def adjust_time(self, delta):
        """Adjust time limit by delta seconds."""
        new_time = self.time_limit + delta
        if 10 <= new_time <= 300:
            self.time_limit = new_time
            self.timer_remaining = self.time_limit
            print(self.t('time_set').format(t=self.time_limit))
        else:
            print(self.t('time_range'))
        time.sleep(0.5)

    def start_timer(self):
        """Start the move timer in a background thread."""
        self.stop_timer()
        with self.timer_lock:
            self.timer_remaining = self.time_limit
            self.timer_expired = False
        self.timer_active = True
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()

    def stop_timer(self):
        """Stop the timer."""
        self.timer_active = False
        if self.timer_thread:
            self.timer_thread.join(timeout=0.5)
            self.timer_thread = None

    def _timer_loop(self):
        """Timer countdown loop."""
        while self.timer_active and self.state == 'playing':
            time.sleep(0.1)
            with self.timer_lock:
                self.timer_remaining -= 0.1
                if self.timer_remaining <= 0:
                    self.timer_remaining = 0
                    self.timer_expired = True
                    self.timer_active = False
                    break

    def get_timer_display(self):
        """Get formatted timer string."""
        with self.timer_lock:
            remaining = max(0, int(self.timer_remaining))
        minutes = remaining // 60
        seconds = remaining % 60
        return f'{minutes:02d}:{seconds:02d}'

    def is_timer_expired(self):
        with self.timer_lock:
            return self.timer_expired

    def show_controls(self):
        """Display control help."""
        t = self.t
        clear_screen()
        print(t('controls_title'))
        print()
        for line in t('controls'):
            print(f'  {line}')
        print()
        input(t('press_enter'))

    def show_menu(self):
        """Display main menu."""
        t = self.t
        clear_screen()
        print(t('menu_title'))
        print(t('welcome'))
        print()
        print(t('pvp'))
        print(t('pve'))
        print(t('scoreboard'))
        print(t('quit'))
        print()

    def parse_coord(self, text):
        """Parse coordinate like 'H8' into (row, col). Returns None on invalid."""
        text = text.strip().upper()
        if len(text) < 2:
            return None
        col_char = text[0]
        row_part = text[1:]
        if col_char < 'A' or col_char > 'O':
            return None
        if not row_part.isdigit():
            return None
        col = ord(col_char) - ord('A')
        row = int(row_part) - 1
        if row < 0 or row >= BOARD_SIZE:
            return None
        return row, col

    def handle_move_input(self, text):
        """Handle a move input. Returns (row, col) or special command or None."""
        text = text.strip().upper()

        if text == 'U':
            return ('undo',)
        if text == 'P':
            return ('pause',)
        if text == 'Q':
            return ('quit',)
        if text == 'R':
            return ('restart',)
        if text == 'S':
            return ('sound',)
        if text == 'L':
            return ('language',)
        if text == '+':
            return ('time_up',)
        if text == '-':
            return ('time_down',)

        coord = self.parse_coord(text)
        if coord is None:
            return None
        return coord

    def do_undo(self):
        """Perform undo based on game mode."""
        t = self.t
        if self.mode == 'pvp':
            result = self.board.undo()
            if result:
                self.current_player = result[2]
                print(t('undo_ok'))
                return True
            else:
                print(t('no_undo'))
                return False
        else:  # pve - undo 2 moves (AI + player)
            # Undo AI move
            r1 = self.board.undo()
            if not r1:
                print(t('no_undo'))
                return False
            # Undo player move
            r2 = self.board.undo()
            if r2:
                self.current_player = r2[2]
                print(t('undo_pve'))
                return True
            else:
                # Only AI move was undone, put it back
                self.board.place(r1[0], r1[1], r1[2])
                print(t('no_undo'))
                return False

    def process_turn(self, row, col):
        """Process a stone placement. Returns True if game continues, False if game over."""
        t = self.t
        player = self.current_player

        if not self.board.place(row, col, player):
            print(t('cell_occupied'))
            return True  # continue, re-prompt

        self.last_move = (row, col)

        if self.sound_enabled:
            play_sound()

        # Check win
        if self.board.check_win(row, col, player):
            self.state = 'game_over'
            self.stop_timer()
            self.display_board()
            winner_name = self.player_names[player]
            print(t('win_msg').format(winner=winner_name))
            if self.sound_enabled:
                # Announce winner
                en_name = STONE_NAMES_EN[player]
                say_text(f'{en_name} wins')
            return False

        # Check draw
        if self.board.is_full():
            self.state = 'game_over'
            self.stop_timer()
            self.display_board()
            print(t('draw_msg'))
            return False

        # Switch player
        self.current_player = WHITE if player == BLACK else BLACK
        return True

    def ai_move(self):
        """Generate and process AI move."""
        t = self.t
        ai_player = self.current_player
        print(t('ai_thinking'))
        time.sleep(0.3)  # Brief pause for dramatic effect

        row, col = AI.get_best_move(self.board, ai_player)
        return self.process_turn(row, col)

    def display_board(self):
        """Clear screen and show board with status."""
        clear_screen()
        t = self.t
        print(t('title'))
        if self.mode == 'pvp':
            print(f'  {t("pvp")}')
        else:
            print(f'  {t("pve")}')
        print(f'  {t("black_turn")}: {self.player_names[BLACK]}')
        print(f'  {t("white_turn")}: {self.player_names[WHITE]}')
        print(f'  ⏱️  {self.get_timer_display()}  |  S={t("sound_on") if self.sound_enabled else t("sound_off")}  |  L={self.lang.upper()}')
        self.board.display(self.lang)

    def play(self):
        """Main game loop."""
        t = self.t

        while self.running:
            if self.state == 'menu':
                self.show_menu()
                choice = input(t('choose_mode')).strip()

                if choice == '1':
                    self.mode = 'pvp'
                    self.start_new_game()
                elif choice == '2':
                    self.mode = 'pve'
                    self.start_new_game()
                elif choice == '3':
                    show_scoreboard(self.lang)
                elif choice == '4':
                    self.running = False
                    print(t('bye'))
                else:
                    print(t('invalid_choice'))
                    time.sleep(1)

            elif self.state == 'playing':
                self.game_loop()

            elif self.state == 'paused':
                print(t('paused'))
                ch = getch().upper()
                if ch == 'P':
                    self.state = 'playing'
                    self.start_timer()
                elif ch == 'Q':
                    self.confirm_quit()

            elif self.state == 'game_over':
                print(t('game_over'))
                ch = getch().upper()
                if ch == 'R':
                    self.start_new_game()
                elif ch == 'Q':
                    self.state = 'menu'
                    self.board.reset()

    def confirm_quit(self):
        """Confirm quitting to menu."""
        t = self.t
        print(t('quit_confirm'), end='', flush=True)
        ch = getch().upper()
        print(ch)
        if ch == 'Y':
            self.stop_timer()
            self.state = 'menu'
            self.board.reset()

    def confirm_restart(self):
        """Confirm restart."""
        t = self.t
        print(t('restart_confirm'), end='', flush=True)
        ch = getch().upper()
        print(ch)
        if ch == 'Y':
            self.start_new_game()
            return True
        return False

    def start_new_game(self):
        """Initialize a new game."""
        t = self.t
        self.board.reset()
        self.current_player = BLACK
        self.last_move = None
        self.state = 'playing'

        if self.mode == 'pvp':
            print()
            name_b = input(t('enter_name_black')).strip()
            self.player_names[BLACK] = name_b if name_b else t('default_name') + '1'
            name_w = input(t('enter_name_white')).strip()
            self.player_names[WHITE] = name_w if name_w else t('default_name') + '2'
        else:
            print()
            name_p = input(t('enter_name_player')).strip()
            self.player_names[BLACK] = name_p if name_p else t('default_name')
            self.player_names[WHITE] = t('ai_name')

        self.start_timer()

    def game_loop(self):
        """Inner game loop for a single move."""
        t = self.t
        self.display_board()

        # Show whose turn
        if self.current_player == BLACK:
            turn_text = t('black_turn')
        else:
            turn_text = t('white_turn')

        print(f'{turn_text}  [{self.get_timer_display()}]')

        # For PvE AI turn
        if self.mode == 'pve' and self.current_player == WHITE:
            continue_game = self.ai_move()
            if not continue_game:
                self.handle_game_over()
            return

        # Get player input
        print(t('enter_move'), end='', flush=True)
        ch = getch()

        # Handle special keys that need immediate response
        if ch.upper() == 'P':
            self.state = 'paused'
            self.stop_timer()
            return
        elif ch.upper() == 'Q':
            self.confirm_quit()
            return
        elif ch.upper() == 'R':
            self.confirm_restart()
            return
        elif ch.upper() == 'S':
            self.toggle_sound()
            return
        elif ch.upper() == 'L':
            self.toggle_language()
            return
        elif ch == '+':
            self.adjust_time(10)
            return
        elif ch == '-':
            self.adjust_time(-10)
            return
        elif ch.upper() == 'U':
            self.do_undo()
            return
        elif ch == '\n' or ch == '\r':
            # Enter with no input - just redisplay
            return
        else:
            # Read remaining input for coordinate
            rest = ''
            while True:
                c2 = getch()
                if c2 == '\n' or c2 == '\r':
                    break
                rest += c2

            text = ch + rest
            result = self.handle_move_input(text)

            if result is None:
                print(t('invalid_coord'))
                time.sleep(0.5)
                return
            elif result[0] == 'undo':
                self.do_undo()
                return
            elif result[0] == 'pause':
                self.state = 'paused'
                self.stop_timer()
                return
            elif result[0] == 'quit':
                self.confirm_quit()
                return
            elif result[0] == 'restart':
                self.confirm_restart()
                return
            elif result[0] == 'sound':
                self.toggle_sound()
                return
            elif result[0] == 'language':
                self.toggle_language()
                return
            elif result[0] == 'time_up':
                self.adjust_time(10)
                return
            elif result[0] == 'time_down':
                self.adjust_time(-10)
                return
            else:
                row, col = result
                continue_game = self.process_turn(row, col)
                if not continue_game:
                    self.handle_game_over()

    def handle_game_over(self):
        """Handle game over state: save scores, prompt."""
        t = self.t
        self.stop_timer()
        self.display_board()

        # Determine result
        if self.is_timer_expired():
            loser = self.current_player
            winner = WHITE if loser == BLACK else BLACK
            winner_name = self.player_names[winner]
            loser_name = self.player_names[loser]
            print(t('timeout_msg').format(player=loser_name, winner=winner_name))
        # win/draw already printed in process_turn

        # Save scores
        if self.mode == 'pvp':
            print()
            save_choice = input(t('save_score_ask')).strip().lower()
            if save_choice in ('y', 'yes', '是'):
                # Determine results from board state
                # Re-check the last move
                if self.board.move_history:
                    last_row, last_col, last_player = self.board.move_history[-1]
                    if self.board.check_win(last_row, last_col, last_player):
                        winner = last_player
                        loser = WHITE if winner == BLACK else BLACK
                        update_score(self.player_names[winner], 'win', self.player_names[loser])
                        update_score(self.player_names[loser], 'lose', self.player_names[winner])
                    elif self.board.is_full():
                        update_score(self.player_names[BLACK], 'draw', self.player_names[WHITE])
                        update_score(self.player_names[WHITE], 'draw', self.player_names[BLACK])
                print(t('score_saved'))
        else:
            # PvE: only save player's score
            print()
            save_choice = input(t('save_score_ask')).strip().lower()
            if save_choice in ('y', 'yes', '是'):
                if self.board.move_history:
                    last_row, last_col, last_player = self.board.move_history[-1]
                    if self.board.check_win(last_row, last_col, last_player):
                        if last_player == BLACK:
                            update_score(self.player_names[BLACK], 'win', self.player_names[WHITE])
                        else:
                            update_score(self.player_names[BLACK], 'lose', self.player_names[WHITE])
                    elif self.board.is_full():
                        update_score(self.player_names[BLACK], 'draw', self.player_names[WHITE])
                print(t('score_saved'))

        self.state = 'game_over'


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    game = Game()
    try:
        game.play()
    except KeyboardInterrupt:
        print('\n\n' + i18n_t(game.lang, 'bye'))
        sys.exit(0)


if __name__ == '__main__':
    main()
