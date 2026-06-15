#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive pytest tests for Gomoku (五子棋) game.
All tests are self-contained with no external dependencies.
"""

import sys
import os
import json
import tempfile
import pytest

# Add game directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game import Board, AI, BOARD_SIZE, EMPTY, BLACK, WHITE, DIRECTIONS


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def board():
    """Create a fresh board for each test."""
    return Board()


# ── Board Initialization ───────────────────────────────────────────────────

class TestBoardInitialization:
    """Test board creation and basic properties."""

    def test_board_size(self, board):
        """Board should be 15x15."""
        assert len(board.grid) == BOARD_SIZE
        for row in board.grid:
            assert len(row) == BOARD_SIZE

    def test_board_empty(self, board):
        """All cells should be empty initially."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                assert board.grid[r][c] == EMPTY

    def test_move_history_empty(self, board):
        """Move history should be empty initially."""
        assert board.move_history == []

    def test_reset(self, board):
        """Reset should clear the board and history."""
        board.place(7, 7, BLACK)
        board.place(7, 8, WHITE)
        board.reset()
        assert board.move_history == []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                assert board.grid[r][c] == EMPTY

    def test_clone(self, board):
        """Clone should create an independent copy."""
        board.place(7, 7, BLACK)
        clone = board.clone()
        assert clone.grid[7][7] == BLACK
        assert clone.move_history == board.move_history
        # Modify clone, original should be unchanged
        clone.place(7, 8, WHITE)
        assert board.grid[7][8] == EMPTY

    def test_is_valid(self, board):
        """is_valid should check bounds correctly."""
        assert board.is_valid(0, 0) is True
        assert board.is_valid(14, 14) is True
        assert board.is_valid(7, 7) is True
        assert board.is_valid(-1, 0) is False
        assert board.is_valid(0, -1) is False
        assert board.is_valid(15, 0) is False
        assert board.is_valid(0, 15) is False

    def test_is_empty(self, board):
        """is_empty should check if cell is unoccupied."""
        assert board.is_empty(7, 7) is True
        board.place(7, 7, BLACK)
        assert board.is_empty(7, 7) is False

    def test_place_stone(self, board):
        """Place a stone and verify."""
        assert board.place(7, 7, BLACK) is True
        assert board.grid[7][7] == BLACK
        assert board.move_history == [(7, 7, BLACK)]

    def test_place_occupied(self, board):
        """Cannot place on occupied cell."""
        board.place(7, 7, BLACK)
        assert board.place(7, 7, WHITE) is False
        assert board.grid[7][7] == BLACK  # unchanged

    def test_place_invalid(self, board):
        """Cannot place outside board."""
        assert board.place(-1, 0, BLACK) is False
        assert board.place(15, 15, BLACK) is False

    def test_is_full_false(self, board):
        """Board should not be full initially."""
        assert board.is_full() is False

    def test_is_full_true(self, board):
        """Fill the board completely."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                board.grid[r][c] = BLACK
        assert board.is_full() is True

    def test_get_empty_cells(self, board):
        """Should return all cells initially."""
        empty = board.get_empty_cells()
        assert len(empty) == BOARD_SIZE * BOARD_SIZE

    def test_get_empty_cells_after_placement(self, board):
        """Should return remaining empty cells."""
        board.place(7, 7, BLACK)
        empty = board.get_empty_cells()
        assert len(empty) == BOARD_SIZE * BOARD_SIZE - 1
        assert (7, 7) not in empty


# ── Win Detection ─────────────────────────────────────────────────────────

class TestWinDetection:
    """Test win detection in all 4 directions."""

    def test_no_win_empty(self, board):
        """No win on empty board."""
        assert board.check_win(7, 7, BLACK) is False

    def test_no_win_single(self, board):
        """No win with single stone."""
        board.place(7, 7, BLACK)
        assert board.check_win(7, 7, BLACK) is False

    def test_no_win_four(self, board):
        """No win with only 4 in a row."""
        for c in range(4):
            board.place(7, c, BLACK)
        # Place a different color to break
        board.place(7, 4, WHITE)
        assert board.check_win(7, 3, BLACK) is False

    def test_win_horizontal(self, board):
        """Win with 5 horizontal consecutive stones."""
        for c in range(5):
            board.place(7, c, BLACK)
        assert board.check_win(7, 0, BLACK) is True
        assert board.check_win(7, 2, BLACK) is True
        assert board.check_win(7, 4, BLACK) is True

    def test_win_horizontal_6(self, board):
        """Win with 6 horizontal consecutive stones (>=5)."""
        for c in range(6):
            board.place(7, c, BLACK)
        assert board.check_win(7, 0, BLACK) is True
        assert board.check_win(7, 5, BLACK) is True

    def test_win_vertical(self, board):
        """Win with 5 vertical consecutive stones."""
        for r in range(5):
            board.place(r, 7, BLACK)
        assert board.check_win(0, 7, BLACK) is True
        assert board.check_win(2, 7, BLACK) is True
        assert board.check_win(4, 7, BLACK) is True

    def test_win_diagonal_down_right(self, board):
        """Win with 5 diagonal (down-right) consecutive stones."""
        for i in range(5):
            board.place(i, i, BLACK)
        assert board.check_win(0, 0, BLACK) is True
        assert board.check_win(2, 2, BLACK) is True
        assert board.check_win(4, 4, BLACK) is True

    def test_win_diagonal_up_right(self, board):
        """Win with 5 diagonal (up-right) consecutive stones."""
        for i in range(5):
            board.place(4 - i, i, BLACK)
        assert board.check_win(4, 0, BLACK) is True
        assert board.check_win(2, 2, BLACK) is True
        assert board.check_win(0, 4, BLACK) is True

    def test_win_white(self, board):
        """White should also be detected as winner."""
        for c in range(5):
            board.place(7, c, WHITE)
        assert board.check_win(7, 2, WHITE) is True

    def test_no_win_opposite_color(self, board):
        """Black stones should not trigger white win."""
        for c in range(5):
            board.place(7, c, BLACK)
        assert board.check_win(7, 2, WHITE) is False

    def test_win_at_edge(self, board):
        """Win detection at board edge."""
        for c in range(11, 15):
            board.place(7, c, BLACK)
        # Only 4 stones, no win yet
        assert board.check_win(7, 14, BLACK) is False
        # Add 5th
        board.place(7, 10, BLACK)
        assert board.check_win(7, 10, BLACK) is True

    def test_win_with_gap(self, board):
        """No win if there's a gap."""
        positions = [0, 1, 2, 4]  # missing column 3
        for c in positions:
            board.place(7, c, BLACK)
        assert board.check_win(7, 2, BLACK) is False

    def test_win_broken_by_opponent(self, board):
        """No win if opponent stone breaks the line."""
        for c in range(5):
            if c == 2:
                board.place(7, c, WHITE)
            else:
                board.place(7, c, BLACK)
        assert board.check_win(7, 1, BLACK) is False

    def test_win_multiple_directions(self, board):
        """Win detection should work when multiple directions have stones."""
        # Place a cross pattern
        board.place(7, 7, BLACK)
        board.place(7, 8, BLACK)
        board.place(7, 9, BLACK)
        board.place(7, 10, BLACK)
        board.place(7, 11, BLACK)  # horizontal win
        assert board.check_win(7, 11, BLACK) is True

    def test_win_last_stone_triggers(self, board):
        """Only the last placed stone should trigger win check."""
        for c in range(4):
            board.place(7, c, BLACK)
        board.place(8, 0, WHITE)  # unrelated move
        # No win yet
        assert board.check_win(7, 3, BLACK) is False
        # Place the 5th
        board.place(7, 4, BLACK)
        assert board.check_win(7, 4, BLACK) is True


# ── Draw Detection ─────────────────────────────────────────────────────────

class TestDrawDetection:
    """Test draw (full board) detection."""

    def test_draw_not_full(self, board):
        """Board not full should not be draw."""
        assert board.is_full() is False

    def test_draw_full_board(self, board):
        """Full board should be detected as draw."""
        # Fill board in a pattern that doesn't create a win
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                board.grid[r][c] = BLACK if (r + c) % 2 == 0 else WHITE
        assert board.is_full() is True

    def test_draw_one_empty(self, board):
        """Board with one empty cell should not be draw."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                board.grid[r][c] = BLACK
        board.grid[7][7] = EMPTY
        assert board.is_full() is False


# ── Input Validation ───────────────────────────────────────────────────────

class TestInputValidation:
    """Test coordinate parsing and validation."""

    def test_valid_center(self):
        """H8 should map to (7, 7)."""
        from game import Game
        g = Game()
        result = g.parse_coord('H8')
        assert result == (7, 7)

    def test_valid_top_left(self):
        """A1 should map to (0, 0)."""
        from game import Game
        g = Game()
        result = g.parse_coord('A1')
        assert result == (0, 0)

    def test_valid_bottom_right(self):
        """O15 should map to (14, 14)."""
        from game import Game
        g = Game()
        result = g.parse_coord('O15')
        assert result == (14, 14)

    def test_valid_lowercase(self):
        """h8 should map to (7, 7) (case insensitive)."""
        from game import Game
        g = Game()
        result = g.parse_coord('h8')
        assert result == (7, 7)

    def test_invalid_too_short(self):
        """Single character should be invalid."""
        from game import Game
        g = Game()
        assert g.parse_coord('H') is None

    def test_invalid_column(self):
        """P is out of range (A-O only)."""
        from game import Game
        g = Game()
        assert g.parse_coord('P8') is None

    def test_invalid_row_zero(self):
        """Row 0 is out of range."""
        from game import Game
        g = Game()
        assert g.parse_coord('H0') is None

    def test_invalid_row_16(self):
        """Row 16 is out of range."""
        from game import Game
        g = Game()
        assert g.parse_coord('H16') is None

    def test_invalid_non_digit_row(self):
        """Non-digit row should be invalid."""
        from game import Game
        g = Game()
        assert g.parse_coord('HX') is None

    def test_invalid_empty(self):
        """Empty string should be invalid."""
        from game import Game
        g = Game()
        assert g.parse_coord('') is None

    def test_invalid_special_chars(self):
        """Special characters should be invalid."""
        from game import Game
        g = Game()
        assert g.parse_coord('@#') is None

    def test_handle_move_input_undo(self):
        """U should return undo command."""
        from game import Game
        g = Game()
        result = g.handle_move_input('U')
        assert result == ('undo',)

    def test_handle_move_input_pause(self):
        """P should return pause command."""
        from game import Game
        g = Game()
        result = g.handle_move_input('P')
        assert result == ('pause',)

    def test_handle_move_input_quit(self):
        """Q should return quit command."""
        from game import Game
        g = Game()
        result = g.handle_move_input('Q')
        assert result == ('quit',)

    def test_handle_move_input_restart(self):
        """R should return restart command."""
        from game import Game
        g = Game()
        result = g.handle_move_input('R')
        assert result == ('restart',)

    def test_handle_move_input_sound(self):
        """S should return sound command."""
        from game import Game
        g = Game()
        result = g.handle_move_input('S')
        assert result == ('sound',)

    def test_handle_move_input_language(self):
        """L should return language command."""
        from game import Game
        g = Game()
        result = g.handle_move_input('L')
        assert result == ('language',)

    def test_handle_move_input_time_up(self):
        """+ should return time_up command."""
        from game import Game
        g = Game()
        result = g.handle_move_input('+')
        assert result == ('time_up',)

    def test_handle_move_input_time_down(self):
        """- should return time_down command."""
        from game import Game
        g = Game()
        result = g.handle_move_input('-')
        assert result == ('time_down',)

    def test_handle_move_valid_coord(self):
        """Valid coordinate should return (row, col)."""
        from game import Game
        g = Game()
        result = g.handle_move_input('H8')
        assert result == (7, 7)

    def test_handle_move_invalid(self):
        """Invalid input should return None."""
        from game import Game
        g = Game()
        assert g.handle_move_input('ZZ') is None


# ── Undo Functionality ─────────────────────────────────────────────────────

class TestUndo:
    """Test undo functionality."""

    def test_undo_single(self, board):
        """Undo should remove the last placed stone."""
        board.place(7, 7, BLACK)
        board.place(7, 8, WHITE)
        result = board.undo()
        assert result == (7, 8, WHITE)
        assert board.grid[7][8] == EMPTY
        assert board.grid[7][7] == BLACK  # first stone still there

    def test_undo_all(self, board):
        """Undo all moves should empty the board."""
        board.place(7, 7, BLACK)
        board.place(7, 8, WHITE)
        board.undo()
        board.undo()
        assert board.move_history == []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                assert board.grid[r][c] == EMPTY

    def test_undo_empty(self, board):
        """Undo on empty board should return None."""
        assert board.undo() is None

    def test_undo_restores_correct_player(self, board):
        """Undo should return the player who placed the stone."""
        board.place(7, 7, BLACK)
        board.place(7, 8, WHITE)
        result = board.undo()
        assert result[2] == WHITE
        result = board.undo()
        assert result[2] == BLACK

    def test_undo_then_place(self, board):
        """After undo, the cell should be available for placement."""
        board.place(7, 7, BLACK)
        board.undo()
        assert board.place(7, 7, WHITE) is True
        assert board.grid[7][7] == WHITE


# ── AI Move Generation ─────────────────────────────────────────────────────

class TestAI:
    """Test AI move generation."""

    def test_ai_first_move_center(self):
        """AI should play center on empty board."""
        board = Board()
        row, col = AI.get_best_move(board, BLACK)
        assert row == 7
        assert col == 7

    def test_ai_returns_valid_move(self):
        """AI should always return a valid empty cell."""
        board = Board()
        board.place(7, 7, BLACK)
        row, col = AI.get_best_move(board, WHITE)
        assert board.is_empty(row, col)

    def test_ai_blocks_four_in_row(self):
        """AI should block opponent's 4-in-a-row."""
        board = Board()
        # Place 4 black stones in a row at columns 0-3
        for c in range(4):
            board.place(7, c, BLACK)
        # AI (white) should block at column 4 (right end)
        row, col = AI.get_best_move(board, WHITE)
        assert row == 7 and col == 4

    def test_ai_takes_winning_move(self):
        """AI should take an immediate winning move."""
        board = Board()
        # Place 4 white stones in a row (AI is white)
        for c in range(4):
            board.place(7, c, WHITE)
        # AI should complete the 5
        row, col = AI.get_best_move(board, WHITE)
        assert row == 7 and col == 4

    def test_ai_prefers_center(self):
        """AI should prefer center-ish positions among equal scores."""
        board = Board()
        # Place one stone off-center
        board.place(0, 0, BLACK)
        row, col = AI.get_best_move(board, WHITE)
        # Should be closer to center than corner
        center_dist = abs(row - 7) + abs(col - 7)
        assert center_dist < 14  # better than opposite corner

    def test_ai_evaluate_cell(self):
        """AI evaluate_cell should return non-negative score."""
        board = Board()
        board.place(7, 7, BLACK)
        score = AI.evaluate_cell(board, 7, 8, BLACK)
        assert score >= 0

    def test_ai_blocks_vertical(self):
        """AI should block vertical threats."""
        board = Board()
        for r in range(4):
            board.place(r, 7, BLACK)
        row, col = AI.get_best_move(board, WHITE)
        assert col == 7 and row == 4

    def test_ai_blocks_diagonal(self):
        """AI should block diagonal threats."""
        board = Board()
        for i in range(4):
            board.place(i, i, BLACK)
        row, col = AI.get_best_move(board, WHITE)
        # Should block at (4,4)
        assert (row, col) == (4, 4)

    def test_ai_not_random(self):
        """AI should produce deterministic results for same board state."""
        board = Board()
        board.place(7, 7, BLACK)
        board.place(7, 8, WHITE)
        result1 = AI.get_best_move(board, BLACK)
        result2 = AI.get_best_move(board, BLACK)
        assert result1 == result2

    def test_ai_defense_vs_attack_priority(self):
        """AI should defend against immediate threat over building own pattern."""
        board = Board()
        # Black has 4 in a row at columns 0-3 (immediate threat)
        for c in range(4):
            board.place(7, c, BLACK)
        # White has 3 in a row at columns 0-2
        for c in range(3):
            board.place(8, c, WHITE)
        # AI is white - should block black's 4
        row, col = AI.get_best_move(board, WHITE)
        # Should block at column 4 (row 7)
        assert row == 7 and col == 4


# ── Score Tracking ─────────────────────────────────────────────────────────

class TestScoreTracking:
    """Test score tracking functions."""

    def test_load_scores_empty(self):
        """Loading scores from non-existent file should return empty dict."""
        from game import load_scores
        # Temporarily change SCORES_FILE path
        import game as gm
        original = gm.SCORES_FILE
        gm.SCORES_FILE = '/tmp/nonexistent_scores_test.json'
        try:
            scores = load_scores()
            assert scores == {}
        finally:
            gm.SCORES_FILE = original

    def test_save_and_load_scores(self):
        """Saving then loading should return same data."""
        from game import save_scores, load_scores
        import game as gm
        original = gm.SCORES_FILE
        gm.SCORES_FILE = '/tmp/test_scores_gomoku.json'
        try:
            test_data = {'TestPlayer': {'wins': 5, 'losses': 3, 'draws': 1, 'last_game': '2024-01-01'}}
            save_scores(test_data)
            loaded = load_scores()
            assert loaded == test_data
        finally:
            gm.SCORES_FILE = original
            if os.path.exists('/tmp/test_scores_gomoku.json'):
                os.remove('/tmp/test_scores_gomoku.json')

    def test_update_score_new_player(self):
        """Update score for a new player should create entry."""
        from game import update_score, load_scores
        import game as gm
        original = gm.SCORES_FILE
        gm.SCORES_FILE = '/tmp/test_scores_gomoku2.json'
        try:
            update_score('NewPlayer', 'win')
            scores = load_scores()
            assert 'NewPlayer' in scores
            assert scores['NewPlayer']['wins'] == 1
            assert scores['NewPlayer']['losses'] == 0
            assert scores['NewPlayer']['draws'] == 0
        finally:
            gm.SCORES_FILE = original
            if os.path.exists('/tmp/test_scores_gomoku2.json'):
                os.remove('/tmp/test_scores_gomoku2.json')

    def test_update_score_increment(self):
        """Update score should increment existing player."""
        from game import update_score, load_scores
        import game as gm
        original = gm.SCORES_FILE
        gm.SCORES_FILE = '/tmp/test_scores_gomoku3.json'
        try:
            update_score('Player1', 'win')
            update_score('Player1', 'win')
            update_score('Player1', 'lose')
            update_score('Player1', 'draw')
            scores = load_scores()
            assert scores['Player1']['wins'] == 2
            assert scores['Player1']['losses'] == 1
            assert scores['Player1']['draws'] == 1
        finally:
            gm.SCORES_FILE = original
            if os.path.exists('/tmp/test_scores_gomoku3.json'):
                os.remove('/tmp/test_scores_gomoku3.json')


# ── Settings ───────────────────────────────────────────────────────────────

class TestSettings:
    """Test settings persistence."""

    def test_load_settings_default(self):
        """Loading settings from non-existent file should return defaults."""
        from game import load_settings
        import game as gm
        original = gm.SETTINGS_FILE
        gm.SETTINGS_FILE = '/tmp/nonexistent_settings_test.json'
        try:
            settings = load_settings()
            assert settings['language'] == 'zh'
            assert settings['sound'] is True
        finally:
            gm.SETTINGS_FILE = original

    def test_save_and_load_settings(self):
        """Saving then loading settings should return same data."""
        from game import save_settings, load_settings
        import game as gm
        original = gm.SETTINGS_FILE
        gm.SETTINGS_FILE = '/tmp/test_settings_gomoku.json'
        try:
            test_data = {'language': 'en', 'sound': False}
            save_settings(test_data)
            loaded = load_settings()
            assert loaded == test_data
        finally:
            gm.SETTINGS_FILE = original
            if os.path.exists('/tmp/test_settings_gomoku.json'):
                os.remove('/tmp/test_settings_gomoku.json')


# ── Language / Translation ─────────────────────────────────────────────────

class TestLanguage:
    """Test bilingual support."""

    def test_lang_keys_exist(self):
        """Both languages should have the same keys."""
        from game import LANG
        zh_keys = set(LANG['zh'].keys())
        en_keys = set(LANG['en'].keys())
        assert zh_keys == en_keys, f"Missing keys: zh={zh_keys - en_keys}, en={en_keys - zh_keys}"

    def test_lang_zh_default(self):
        """Default language should be Chinese."""
        from game import load_settings
        import game as gm
        original = gm.SETTINGS_FILE
        gm.SETTINGS_FILE = '/tmp/nonexistent_lang_test.json'
        try:
            settings = load_settings()
            assert settings['language'] == 'zh'
        finally:
            gm.SETTINGS_FILE = original


# ── Run tests ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    pytest.main(['-v', __file__])
