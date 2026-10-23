import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  ROWS,
  COLS,
  EMPTY,
  PLAYER_1,
  PLAYER_2,
  createEmptyBoard,
  isValidLocation,
  getNextOpenRow,
  dropPiece,
  checkWin,
  getWinningCoordinates,
  isBoardFull,
  isDraw,
  validateAIResponse,
} from '../utils/gameLogic.js';

// Verified legal 42-move sequence reachable under gravity without premature win
const DRAW_MOVES_SEQUENCE = [
  6, 6, 6, 6, 6, 5, 4, 5, 5, 6,
  4, 4, 5, 4, 4, 3, 4, 3, 3, 5,
  2, 5, 2, 2, 3, 2, 2, 1, 2, 1,
  1, 3, 0, 3, 0, 0, 1, 0, 0, 1,
  0, 1,
];

describe('Connect Four Frontend Rules Engine (gameLogic.js)', () => {
  it('initializes clean 6x7 empty board', () => {
    const board = createEmptyBoard();
    assert.equal(board.length, ROWS);
    assert.ok(board.every((row) => row.length === COLS));
    assert.ok(board.every((row) => row.every((cell) => cell === EMPTY)));
  });

  it('respects piece gravity and column capacity', () => {
    const board = createEmptyBoard();
    const col = 3;
    for (let expectedRow = ROWS - 1; expectedRow >= 0; expectedRow--) {
      assert.equal(isValidLocation(board, col), true);
      const row = getNextOpenRow(board, col);
      assert.equal(row, expectedRow);
      dropPiece(board, row, col, PLAYER_1);
    }

    // Column is full (row 0 occupied)
    assert.equal(isValidLocation(board, col), false);
    assert.equal(getNextOpenRow(board, col), -1);
  });

  it('detects horizontal win across rows and column offsets', () => {
    for (const r of [0, 2, 5]) {
      for (let startC = 0; startC <= COLS - 4; startC++) {
        const board = createEmptyBoard();
        for (let i = 0; i < 4; i++) {
          dropPiece(board, r, startC + i, PLAYER_1);
        }
        assert.equal(checkWin(board, PLAYER_1), true);
        assert.equal(checkWin(board, PLAYER_2), false);

        const coords = getWinningCoordinates(board, PLAYER_1);
        assert.ok(coords !== null);
        assert.equal(coords.length, 4);
        const expected = [
          [r, startC],
          [r, startC + 1],
          [r, startC + 2],
          [r, startC + 3],
        ];
        assert.deepEqual(coords, expected);
      }
    }
  });

  it('detects vertical win across columns and row offsets', () => {
    for (const c of [0, 3, 6]) {
      for (let startR = 0; startR <= ROWS - 4; startR++) {
        const board = createEmptyBoard();
        for (let i = 0; i < 4; i++) {
          dropPiece(board, startR + i, c, PLAYER_2);
        }
        assert.equal(checkWin(board, PLAYER_2), true);
        assert.equal(checkWin(board, PLAYER_1), false);

        const coords = getWinningCoordinates(board, PLAYER_2);
        assert.ok(coords !== null);
        assert.equal(coords.length, 4);
        const expected = [
          [startR, c],
          [startR + 1, c],
          [startR + 2, c],
          [startR + 3, c],
        ];
        assert.deepEqual(coords, expected);
      }
    }
  });

  it('detects positive diagonal (/) win and extracts coordinates', () => {
    const board = createEmptyBoard();
    const expected = [
      [3, 0],
      [2, 1],
      [1, 2],
      [0, 3],
    ];
    for (const [r, c] of expected) {
      dropPiece(board, r, c, PLAYER_1);
    }
    assert.equal(checkWin(board, PLAYER_1), true);
    assert.equal(checkWin(board, PLAYER_2), false);

    const coords = getWinningCoordinates(board, PLAYER_1);
    assert.deepEqual(
      coords,
      expected.sort((a, b) => a[0] - b[0] || a[1] - b[1])
    );
  });

  it('detects negative diagonal (\\) win and extracts coordinates', () => {
    const board = createEmptyBoard();
    const expected = [
      [0, 0],
      [1, 1],
      [2, 2],
      [3, 3],
    ];
    for (const [r, c] of expected) {
      dropPiece(board, r, c, PLAYER_2);
    }
    assert.equal(checkWin(board, PLAYER_2), true);
    assert.equal(checkWin(board, PLAYER_1), false);

    const coords = getWinningCoordinates(board, PLAYER_2);
    assert.deepEqual(coords, expected);
  });

  it('extracts deterministic 4-coordinate sequence for 5 connected pieces', () => {
    const board = createEmptyBoard();
    // 5 pieces horizontally in bottom row (col 1 to 5)
    for (let c = 1; c <= 5; c++) {
      dropPiece(board, 5, c, PLAYER_1);
    }
    assert.equal(checkWin(board, PLAYER_1), true);

    const coords = getWinningCoordinates(board, PLAYER_1);
    assert.ok(coords !== null);
    assert.equal(coords.length, 4);
    assert.deepEqual(coords, [
      [5, 1],
      [5, 2],
      [5, 3],
      [5, 4],
    ]);
  });

  it('replays verified 42-move legal draw sequence without premature win', () => {
    const board = createEmptyBoard();
    let current = PLAYER_1;

    for (let idx = 0; idx < DRAW_MOVES_SEQUENCE.length; idx++) {
      const col = DRAW_MOVES_SEQUENCE[idx];
      const row = getNextOpenRow(board, col);
      assert.notEqual(row, -1, `Column ${col} full prematurely at move ${idx + 1}`);
      dropPiece(board, row, col, current);

      if (idx < 41) {
        assert.equal(checkWin(board, PLAYER_1), false, `P1 won prematurely at move ${idx + 1}`);
        assert.equal(checkWin(board, PLAYER_2), false, `P2 won prematurely at move ${idx + 1}`);
      }

      current = current === PLAYER_1 ? PLAYER_2 : PLAYER_1;
    }

    assert.equal(isBoardFull(board), true);
    assert.equal(checkWin(board, PLAYER_1), false);
    assert.equal(checkWin(board, PLAYER_2), false);
    assert.equal(isDraw(board), true);
  });

  it('strictly enforces win-over-draw precedence', () => {
    // Fill board from draw fixture, then make a win for player 1 in top row
    const board = createEmptyBoard();
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        dropPiece(board, r, c, (r + c) % 2 === 0 ? PLAYER_1 : PLAYER_2);
      }
    }
    // Make top row have 4 in a row for player 1
    board[0][0] = PLAYER_1;
    board[0][1] = PLAYER_1;
    board[0][2] = PLAYER_1;
    board[0][3] = PLAYER_1;

    assert.equal(isBoardFull(board), true);
    assert.equal(checkWin(board, PLAYER_1), true);
    assert.equal(isDraw(board), false); // Win strictly precludes draw!
  });

  it('strictly validates AI responses without silent substitutions', () => {
    const board = createEmptyBoard();
    // Drop piece in col 3 -> next open row is 4
    dropPiece(board, 5, 3, PLAYER_1);

    // 1. Valid response (col 3, row 4)
    const validRes = validateAIResponse(board, { column: 3, row: 4 });
    assert.equal(validRes.valid, true);

    // 2. Inconsistent row (AI reports row 0, but gravity requires row 4)
    const badRowRes = validateAIResponse(board, { column: 3, row: 0 });
    assert.equal(badRowRes.valid, false);
    assert.match(badRowRes.error, /inconsistent row 0/);

    // 3. Out of bounds column
    const outColRes = validateAIResponse(board, { column: 7, row: 5 });
    assert.equal(outColRes.valid, false);
    assert.match(outColRes.error, /out of bounds/);

    // 4. Out of bounds row
    const outRowRes = validateAIResponse(board, { column: 2, row: -1 });
    assert.equal(outRowRes.valid, false);

    // 5. Already occupied cell
    const occupiedRes = validateAIResponse(board, { column: 3, row: 5 });
    assert.equal(occupiedRes.valid, false);
    assert.match(occupiedRes.error, /inconsistent row 5|already occupied/);

    // 6. Non-integer or malformed payload
    assert.equal(validateAIResponse(board, null).valid, false);
    assert.equal(validateAIResponse(board, { column: '3', row: 4 }).valid, false);
    assert.equal(validateAIResponse(board, { column: 3, row: '4' }).valid, false);
  });
});
