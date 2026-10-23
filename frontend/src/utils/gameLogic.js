/**
 * Authoritative frontend Connect Four rules engine.
 * Directly mirrors backend/app/core/game_engine.py for single-source rule consistency.
 */

export const ROWS = 6;
export const COLS = 7;
export const EMPTY = 0;
export const PLAYER_1 = 1;
export const PLAYER_2 = 2;

// Aliases for compatibility
export const PLAYER = PLAYER_1;
export const AI = PLAYER_2;

/**
 * Initialize a clean 6x7 board filled with EMPTY (0).
 */
export function createEmptyBoard() {
  return Array.from({ length: ROWS }, () => Array(COLS).fill(EMPTY));
}

/**
 * Deep-clone a 6x7 board matrix.
 */
export function cloneBoard(board) {
  return board.map((row) => [...row]);
}

/**
 * Check if column index is legal and has capacity.
 */
export function isValidLocation(board, col) {
  if (typeof col !== 'number' || !Number.isInteger(col)) return false;
  if (col < 0 || col >= COLS) return false;
  return board[0][col] === EMPTY;
}

/**
 * Return all available legal columns (0-6).
 */
export function getValidLocations(board) {
  const valid = [];
  for (let c = 0; c < COLS; c++) {
    if (isValidLocation(board, c)) {
      valid.push(c);
    }
  }
  return valid;
}

/**
 * Find the lowest available row in column `col` (from 5 up to 0).
 * Returns -1 if column is out of bounds or full.
 */
export function getNextOpenRow(board, col) {
  if (typeof col !== 'number' || !Number.isInteger(col) || col < 0 || col >= COLS) {
    return -1;
  }
  for (let r = ROWS - 1; r >= 0; r--) {
    if (board[r][col] === EMPTY) {
      return r;
    }
  }
  return -1;
}

/**
 * Place a piece into the specified cell (in-place mutation).
 */
export function dropPiece(board, row, col, piece) {
  board[row][col] = piece;
}

/**
 * High-performance boolean 4-in-a-row victory detection.
 * Checks horizontal, vertical, positive diagonal (/), and negative diagonal (\).
 */
export function checkWin(board, piece) {
  // Horizontal check
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      if (
        board[r][c] === piece &&
        board[r][c + 1] === piece &&
        board[r][c + 2] === piece &&
        board[r][c + 3] === piece
      ) {
        return true;
      }
    }
  }

  // Vertical check
  for (let r = 0; r < ROWS - 3; r++) {
    for (let c = 0; c < COLS; c++) {
      if (
        board[r][c] === piece &&
        board[r + 1][c] === piece &&
        board[r + 2][c] === piece &&
        board[r + 3][c] === piece
      ) {
        return true;
      }
    }
  }

  // Positive diagonal (/) - increasing col, decreasing row
  for (let r = 3; r < ROWS; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      if (
        board[r][c] === piece &&
        board[r - 1][c + 1] === piece &&
        board[r - 2][c + 2] === piece &&
        board[r - 3][c + 3] === piece
      ) {
        return true;
      }
    }
  }

  // Negative diagonal (\) - increasing col, increasing row
  for (let r = 0; r < ROWS - 3; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      if (
        board[r][c] === piece &&
        board[r + 1][c + 1] === piece &&
        board[r + 2][c + 2] === piece &&
        board[r + 3][c + 3] === piece
      ) {
        return true;
      }
    }
  }

  return false;
}

/**
 * Deterministically extract exactly 4 coordinates for UI win-line highlighting.
 * Returns sorted array of [row, col] pairs, or null if no 4-in-a-row exists.
 * When 5+ pieces are connected, canonical scan order extracts the first 4-cell window.
 */
export function getWinningCoordinates(board, piece) {
  const isMatch = (coords) => coords.every(([r, c]) => board[r][c] === piece);

  // 1. Horizontal scan (bottom-to-top, left-to-right)
  for (let r = ROWS - 1; r >= 0; r--) {
    for (let c = 0; c < COLS - 3; c++) {
      const coords = [
        [r, c],
        [r, c + 1],
        [r, c + 2],
        [r, c + 3],
      ];
      if (isMatch(coords)) return coords;
    }
  }

  // 2. Vertical scan (left-to-right, bottom-to-top)
  for (let c = 0; c < COLS; c++) {
    for (let r = ROWS - 1; r >= 3; r--) {
      const coords = [
        [r, c],
        [r - 1, c],
        [r - 2, c],
        [r - 3, c],
      ];
      if (isMatch(coords)) {
        return coords.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
      }
    }
  }

  // 3. Positive diagonal (/) - increasing col, decreasing row
  for (let r = ROWS - 1; r >= 3; r--) {
    for (let c = 0; c < COLS - 3; c++) {
      const coords = [
        [r, c],
        [r - 1, c + 1],
        [r - 2, c + 2],
        [r - 3, c + 3],
      ];
      if (isMatch(coords)) {
        return coords.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
      }
    }
  }

  // 4. Negative diagonal (\) - increasing col, increasing row
  for (let r = 0; r < ROWS - 3; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      const coords = [
        [r, c],
        [r + 1, c + 1],
        [r + 2, c + 2],
        [r + 3, c + 3],
      ];
      if (isMatch(coords)) {
        return coords.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
      }
    }
  }

  return null;
}

/**
 * Return true if top row has no empty cells.
 */
export function isBoardFull(board) {
  return board[0].every((cell) => cell !== EMPTY);
}

/**
 * Return true if board is full and neither player has won.
 * Win-over-draw precedence: if a 4-in-a-row exists, returns false.
 */
export function isDraw(board) {
  if (checkWin(board, PLAYER_1) || checkWin(board, PLAYER_2)) {
    return false;
  }
  return isBoardFull(board);
}

/**
 * Strictly validate backend AI response against current board and physical gravity.
 * Checks types, bounds, column capacity, cell vacancy, and exact gravity row match.
 *
 * @param {number[][]} board - Current 6x7 board state.
 * @param {any} response - Backend response object { column, row }.
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateAIResponse(board, response) {
  if (!response || typeof response !== 'object') {
    return { valid: false, error: 'AI response is not an object.' };
  }

  const { column, row } = response;

  if (typeof column !== 'number' || !Number.isInteger(column)) {
    return { valid: false, error: `AI column ${column} is not a valid integer.` };
  }

  if (typeof row !== 'number' || !Number.isInteger(row)) {
    return { valid: false, error: `AI row ${row} is not a valid integer.` };
  }

  if (column < 0 || column >= COLS) {
    return { valid: false, error: `AI column ${column} is out of bounds (0-6).` };
  }

  if (row < 0 || row >= ROWS) {
    return { valid: false, error: `AI row ${row} is out of bounds (0-5).` };
  }

  if (board[0][column] !== EMPTY) {
    return { valid: false, error: `AI selected full column ${column}.` };
  }

  if (board[row][column] !== EMPTY) {
    return { valid: false, error: `AI selected already occupied cell (${row}, ${column}).` };
  }

  const expectedRow = getNextOpenRow(board, column);
  if (row !== expectedRow) {
    return {
      valid: false,
      error: `AI returned inconsistent row ${row} for column ${column}; expected legal gravity row ${expectedRow}.`,
    };
  }

  return { valid: true };
}
