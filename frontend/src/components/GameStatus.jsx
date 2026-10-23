export function GameStatus({
  status,
  turn,
  winner,
  isThinking,
  gameMode,
  moveCount,
  onPlayAgain,
}) {
  if (status === 'won') {
    const isHumanWinner = winner === 1;
    const title =
      gameMode === 'human_vs_ai'
        ? isHumanWinner
          ? '🎉 Victory! You Defeated the AI Agent!'
          : '🤖 Game Over — AI Agent Won!'
        : `🎉 Victory! Player ${winner} (${winner === 1 ? 'Red' : 'Yellow'}) Won!`;

    return (
      <div className={`status-banner status-won ${isHumanWinner ? 'winner-human' : 'winner-ai'}`}>
        <div className="status-content">
          <span className="status-icon">{isHumanWinner ? '🏆' : '🤖'}</span>
          <span className="status-text">{title}</span>
        </div>
        <button className="btn-play-again" onClick={onPlayAgain}>
          Play Again
        </button>
      </div>
    );
  }

  if (status === 'draw') {
    return (
      <div className="status-banner status-draw">
        <div className="status-content">
          <span className="status-icon">🤝</span>
          <span className="status-text">Game Drawn — Board is completely full with no winner.</span>
        </div>
        <button className="btn-play-again" onClick={onPlayAgain}>
          Play Again
        </button>
      </div>
    );
  }

  // Active game status
  return (
    <div className="status-banner status-active">
      <div className="status-turn">
        {isThinking ? (
          <div className="thinking-indicator">
            <span className="spinner-dots" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </span>
            <span className="turn-label">AI Agent is thinking...</span>
          </div>
        ) : (
          <div className="turn-indicator">
            <span
              className={`turn-disc ${turn === 1 ? 'turn-red' : 'turn-yellow'}`}
              aria-hidden="true"
            ></span>
            <span className="turn-label">
              {gameMode === 'human_vs_ai'
                ? turn === 1
                  ? 'Your Turn (Player 1 — Red)'
                  : 'AI Turn (Player 2 — Yellow)'
                : `Player ${turn}'s Turn (${turn === 1 ? 'Red' : 'Yellow'})`}
            </span>
          </div>
        )}
      </div>

      <div className="status-meta">
        <span className="move-counter">Move #{moveCount + 1}</span>
      </div>
    </div>
  );
}
