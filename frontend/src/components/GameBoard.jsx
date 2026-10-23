import { useState } from 'react';
import { GameCell } from './GameCell.jsx';
import { COLS, isValidLocation, getNextOpenRow } from '../utils/gameLogic.js';

export function GameBoard({
  board,
  turn,
  status,
  isThinking,
  winningCoords,
  onColumnClick,
  disabled,
}) {
  const [hoveredCol, setHoveredCol] = useState(null);

  const isColInteractive = (colIndex) => {
    if (disabled || status !== 'active' || isThinking) return false;
    return isValidLocation(board, colIndex);
  };

  const handleKeyDown = (e, colIndex) => {
    if ((e.key === 'Enter' || e.key === ' ') && isColInteractive(colIndex)) {
      e.preventDefault();
      onColumnClick(colIndex);
    }
  };

  const isWinning = (r, c) => {
    if (!winningCoords) return false;
    return winningCoords.some(([wr, wc]) => wr === r && wc === c);
  };

  return (
    <div
      className={`board-wrapper ${disabled ? 'board-disabled' : ''} ${
        isThinking ? 'board-thinking' : ''
      }`}
    >
      {/* Column Hover & Drop Indicator Row */}
      <div className="board-indicators" role="row" aria-label="Column Drop Controls">
        {Array.from({ length: COLS }).map((_, colIndex) => {
          const canDrop = isColInteractive(colIndex);
          const targetRow = canDrop ? getNextOpenRow(board, colIndex) : -1;
          const isHovered = hoveredCol === colIndex && canDrop;

          return (
            <button
              key={`col-indicator-${colIndex}`}
              className={`col-drop-btn ${canDrop ? 'can-drop' : 'col-full'} ${
                isHovered ? 'hovered' : ''
              }`}
              onClick={() => canDrop && onColumnClick(colIndex)}
              onMouseEnter={() => setHoveredCol(colIndex)}
              onMouseLeave={() => setHoveredCol(null)}
              onKeyDown={(e) => handleKeyDown(e, colIndex)}
              disabled={!canDrop}
              tabIndex={canDrop ? 0 : -1}
              aria-label={`Column ${colIndex + 1} of 7${
                canDrop ? `, lands at row ${targetRow + 1}` : ' (Full)'
              }`}
            >
              <span className={`ghost-disc ${isHovered ? `ghost-player-${turn}` : ''}`} />
              <span className="arrow-indicator">↓</span>
            </button>
          );
        })}
      </div>

      {/* Main 6x7 Grid Container */}
      <div
        className="board-grid"
        role="grid"
        aria-label="Connect Four Grid"
        aria-readonly={disabled || status !== 'active'}
      >
        {board.map((rowArr, rIdx) => (
          <div key={`row-${rIdx}`} className="board-row" role="row">
            {rowArr.map((cellValue, cIdx) => (
              <GameCell
                key={`cell-${rIdx}-${cIdx}`}
                row={rIdx}
                col={cIdx}
                value={cellValue}
                isWinningCell={isWinning(rIdx, cIdx)}
                onClick={() => isColInteractive(cIdx) && onColumnClick(cIdx)}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
