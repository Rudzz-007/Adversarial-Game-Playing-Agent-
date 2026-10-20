import { useState, useEffect } from "react";
import { fetchAIMove } from "./services/api";
import "./App.css";

const ROWS = 6;
const COLS = 7;
const EMPTY = 0;
const PLAYER = 1;
const AI = 2;

function createEmptyBoard() {
  return Array(ROWS)
    .fill(null)
    .map(() => Array(COLS).fill(EMPTY));
}

export default function App() {
  const [board, setBoard] = useState(createEmptyBoard());
  const [turn, setTurn] = useState(PLAYER); // PLAYER (1) goes first, AI (2) second
  const [winner, setWinner] = useState(null);
  const [depth, setDepth] = useState(4); // 2: Easy, 4: Medium, 6: Hard
  const [isThinking, setIsThinking] = useState(false);
  const [winningCells, setWinningCells] = useState([]);

  // Check win condition locally on frontend for instant UI feedback
  const checkWin = (currentBoard, piece) => {
    // Horizontal
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS - 3; c++) {
        if (currentBoard[r][c] === piece && currentBoard[r][c+1] === piece && currentBoard[r][c+2] === piece && currentBoard[r][c+3] === piece) {
          return [[r,c], [r,c+1], [r,c+2], [r,c+3]];
        }
      }
    }
    // Vertical
    for (let r = 0; r < ROWS - 3; r++) {
      for (let c = 0; c < COLS; c++) {
        if (currentBoard[r][c] === piece && currentBoard[r+1][c] === piece && currentBoard[r+2][c] === piece && currentBoard[r+3][c] === piece) {
          return [[r,c], [r+1,c], [r+2,c], [r+3,c]];
        }
      }
    }
    // Positive Diagonal
    for (let r = 0; r < ROWS - 3; r++) {
      for (let c = 0; c < COLS - 3; c++) {
        if (currentBoard[r][c] === piece && currentBoard[r+1][c+1] === piece && currentBoard[r+2][c+2] === piece && currentBoard[r+3][c+3] === piece) {
          return [[r,c], [r+1,c+1], [r+2,c+2], [r+3,c+3]];
        }
      }
    }
    // Negative Diagonal
    for (let r = 3; r < ROWS; r++) {
      for (let c = 0; c < COLS - 3; c++) {
        if (currentBoard[r][c] === piece && currentBoard[r-1][c+1] === piece && currentBoard[r-2][c+2] === piece && currentBoard[r-3][c+3] === piece) {
          return [[r,c], [r-1,c+1], [r-2,c+2], [r-3,c+3]];
        }
      }
    }
    return null;
  };

  // Handle player column click
  const handleColumnClick = async (colIndex) => {
    if (winner || turn !== PLAYER || isThinking) return;

    // Find bottom-most open row in this column
    let targetRow = -1;
    for (let r = ROWS - 1; r >= 0; r--) {
      if (board[r][colIndex] === EMPTY) {
        targetRow = r;
        break;
      }
    }

    if (targetRow === -1) return; // Column is full

    // Make player move
    const newBoard = board.map(row => [...row]);
    newBoard[targetRow][colIndex] = PLAYER;
    setBoard(newBoard);

    const winCoords = checkWin(newBoard, PLAYER);
    if (winCoords) {
      setWinner("Player");
      setWinningCells(winCoords);
      return;
    }

    // Switch turn to AI
    setTurn(AI);
    setIsThinking(true);

    // Call Backend for AI Move
    const aiResponse = await fetchAIMove(newBoard, depth);
    setIsThinking(false);

    if (aiResponse && aiResponse.column !== null && aiResponse.row !== -1) {
      const aiBoard = newBoard.map(row => [...row]);
      aiBoard[aiResponse.row][aiResponse.column] = AI;
      setBoard(aiBoard);

      const aiWinCoords = checkWin(aiBoard, AI);
      if (aiWinCoords) {
        setWinner("AI Agent");
        setWinningCells(aiWinCoords);
      } else {
        setTurn(PLAYER);
      }
    } else {
      setTurn(PLAYER); // Fallback if full/error
    }
  };

  const resetGame = () => {
    setBoard(createEmptyBoard());
    setTurn(PLAYER);
    setWinner(null);
    setWinningCells([]);
    setIsThinking(false);
  };

  return (
    <div className="game-container">
      <h1>Connect Four: Adversarial AI Agent</h1>
      
      <div className="controls-panel">
        <div className="status-indicator">
          {winner ? (
            <span className="winner-text">🎉 Winner: {winner}!</span>
          ) : isThinking ? (
            <span className="thinking-text">🤖 AI is thinking...</span>
          ) : (
            <span>Current Turn: {turn === PLAYER ? "👤 Player (Red)" : "🤖 AI (Yellow)"}</span>
          )}
        </div>

        <div className="settings">
          <label>Difficulty: </label>
          <select value={depth} onChange={(e) => setDepth(Number(e.target.value))} disabled={isThinking || turn === AI}>
            <option value={2}>Easy (Depth 2)</option>
            <option value={4}>Medium (Depth 4)</option>
            <option value={6}>Hard (Depth 6)</option>
          </select>
          <button className="reset-btn" onClick={resetGame}>Reset Game</button>
        </div>
      </div>

      <div className="board">
        {board.map((row, rIdx) =>
          row.map((cell, cIdx) => {
            const isWinningCell = winningCells.some(([r, c]) => r === rIdx && c === cIdx);
            return (
              <div
                key={`${rIdx}-${cIdx}`}
                className={`cell ${cell === PLAYER ? "player" : cell === AI ? "ai" : ""} ${isWinningCell ? "winning" : ""}`}
                onClick={() => handleColumnClick(cIdx)}
              />
            );
          })
        )}
      </div>
    </div>
  );
}