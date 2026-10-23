export function GameCell({ row, col, value, isWinningCell, onClick }) {
  const getCellLabel = () => {
    if (value === 1) return `Row ${row + 1}, Column ${col + 1}: Player 1 (Red)`;
    if (value === 2) return `Row ${row + 1}, Column ${col + 1}: Player 2 / AI (Yellow)`;
    return `Row ${row + 1}, Column ${col + 1}: Empty`;
  };

  return (
    <div
      className={`board-cell ${value === 1 ? 'player-1' : value === 2 ? 'player-2' : 'empty'} ${
        isWinningCell ? 'winning-cell' : ''
      }`}
      onClick={onClick}
      role="gridcell"
      aria-label={getCellLabel()}
    >
      <div className="disc-slot">
        {value !== 0 && (
          <div
            className={`disc ${value === 1 ? 'disc-red' : 'disc-yellow'} ${
              isWinningCell ? 'pulse-win' : ''
            }`}
          />
        )}
      </div>
    </div>
  );
}
