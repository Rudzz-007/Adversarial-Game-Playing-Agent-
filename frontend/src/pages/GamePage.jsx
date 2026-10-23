import { useGame } from '../hooks/useGame.js';
import { GameBoard } from '../components/GameBoard.jsx';
import { GameControls } from '../components/GameControls.jsx';
import { GameStatus } from '../components/GameStatus.jsx';
import { MetricsPanel } from '../components/MetricsPanel.jsx';
import { ErrorBanner } from '../components/ErrorBanner.jsx';

export function GamePage() {
  const {
    board,
    turn,
    status,
    winner,
    winningCoords,
    moveHistory,
    isThinking,
    errorMessage,
    errorCode,
    telemetry,
    gameMode,
    depth,
    startingPlayer,
    selectedAlgorithm,
    handleColumnClick,
    retryAIMove,
    dismissError,
    resetGame,
    setSelectedAlgorithm,
  } = useGame();

  // Can retry only if active, turn === 2, not currently thinking, and error is set
  const canRetry = status === 'active' && turn === 2 && !isThinking && Boolean(errorMessage);

  // Board interaction disabled when game not active, thinking, or in unresolved error state
  const isBoardDisabled =
    status !== 'active' || isThinking || Boolean(errorMessage) || (gameMode === 'human_vs_ai' && turn !== 1);

  return (
    <div className="game-page-container">
      {errorMessage && (
        <ErrorBanner
          code={errorCode}
          message={errorMessage}
          onRetry={retryAIMove}
          onDismiss={dismissError}
          canRetry={canRetry}
        />
      )}

      <div className="game-layout">
        {/* Left / Center Column: Game Board and Status */}
        <div className="board-section">
          <GameStatus
            status={status}
            turn={turn}
            winner={winner}
            isThinking={isThinking}
            gameMode={gameMode}
            moveCount={moveHistory.length}
            onPlayAgain={() => resetGame()}
          />

          <GameBoard
            board={board}
            turn={turn}
            status={status}
            isThinking={isThinking}
            winningCoords={winningCoords}
            onColumnClick={handleColumnClick}
            disabled={isBoardDisabled}
          />
        </div>

        {/* Right Column: Controls & Real-Time Telemetry */}
        <div className="sidebar-section">
          <GameControls
            gameMode={gameMode}
            onGameModeChange={(mode) => resetGame({ gameMode: mode })}
            depth={depth}
            onDepthChange={(d) => resetGame({ depth: d })}
            startingPlayer={startingPlayer}
            onStartingPlayerChange={(p) => resetGame({ startingPlayer: p })}
            selectedAlgorithm={selectedAlgorithm}
            onAlgorithmChange={(algo) => setSelectedAlgorithm(algo)}
            onReset={() => resetGame()}
            disabled={isThinking}
          />

          <MetricsPanel telemetry={telemetry} gameMode={gameMode} />
        </div>
      </div>
    </div>
  );
}
