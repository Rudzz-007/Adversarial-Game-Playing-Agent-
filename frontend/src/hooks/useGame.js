import { useState, useRef, useCallback } from 'react';
import {
  ROWS,
  COLS,
  PLAYER_1,
  PLAYER_2,
  createEmptyBoard,
  cloneBoard,
  isValidLocation,
  getNextOpenRow,
  dropPiece,
  checkWin,
  getWinningCoordinates,
  isDraw,
  validateAIResponse,
} from '../utils/gameLogic.js';
import { fetchAIMove } from '../services/api.js';

export function useGame() {
  const [board, setBoard] = useState(createEmptyBoard());
  const [turn, setTurn] = useState(PLAYER_1);
  const [status, setStatus] = useState('active'); // 'active' | 'won' | 'draw'
  const [winner, setWinner] = useState(null); // null | 1 | 2
  const [winningCoords, setWinningCoords] = useState(null);
  const [moveHistory, setMoveHistory] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [errorCode, setErrorCode] = useState(null);

  // Game configuration
  const [gameMode, setGameMode] = useState('human_vs_ai'); // 'human_vs_ai' | 'human_vs_human'
  const [depth, setDepth] = useState(4); // 2: Easy, 4: Medium, 6: Hard
  const [startingPlayer, setStartingPlayer] = useState(PLAYER_1);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('minimax');

  // Real-time decision telemetry
  const [telemetry, setTelemetry] = useState({
    decisionTimeMs: null,
    searchDepth: null,
    nodesEvaluated: null, // N/A for Phase 3 endpoint
    prunedNodes: null, // N/A for Phase 3 endpoint
    algorithmName: 'Minimax (Active)',
  });

  // Concurrency mutex to prevent duplicate or overlapping AI requests
  const inFlightRef = useRef(false);

  /**
   * Internal function to trigger AI move computation.
   * Sends current unchanged board to backend, strictly validates response,
   * and manages thinking state and error banner.
   */
  const triggerAIMove = useCallback(
    async (currentBoard) => {
      if (inFlightRef.current) return;
      inFlightRef.current = true;
      setIsThinking(true);
      setErrorMessage(null);
      setErrorCode(null);

      try {
        const response = await fetchAIMove(currentBoard, depth, selectedAlgorithm);

        // Strict AI response validation against legal physical gravity
        const validation = validateAIResponse(currentBoard, response);
        if (!validation.valid) {
          // Do NOT mutate board or silently substitute row/col
          setErrorCode('INVALID_AI_RESPONSE');
          setErrorMessage(validation.error);
          setIsThinking(false);
          inFlightRef.current = false;
          return;
        }

        const { column, row, latencyMs, telemetry: serverTelemetry } = response;
        const newBoard = cloneBoard(currentBoard);
        dropPiece(newBoard, row, column, PLAYER_2);

        // Update telemetry with authentic measured metrics
        const algoLabels = {
          minimax: 'Minimax (Active)',
          random: 'Random Agent (Active)',
          greedy: 'Greedy Agent (Active)',
        };
        const algorithmName = algoLabels[selectedAlgorithm] || `${selectedAlgorithm} (Active)`;
        const decisionTimeMs = serverTelemetry?.decision_time_ms ?? latencyMs;
        const searchDepth = serverTelemetry?.search_depth ?? (selectedAlgorithm === 'minimax' ? depth : null);

        setTelemetry({
          decisionTimeMs,
          searchDepth,
          nodesEvaluated: serverTelemetry?.nodes_evaluated ?? null,
          prunedNodes: serverTelemetry?.pruned_nodes ?? null,
          algorithmName,
        });

        const newHistory = [
          ...moveHistory,
          {
            moveNumber: moveHistory.length + 1,
            player: PLAYER_2,
            column,
            row,
            timestamp: new Date().toISOString(),
          },
        ];

        // Evaluate termination: win strictly precedes draw
        if (checkWin(newBoard, PLAYER_2)) {
          const coords = getWinningCoordinates(newBoard, PLAYER_2);
          setBoard(newBoard);
          setMoveHistory(newHistory);
          setStatus('won');
          setWinner(PLAYER_2);
          setWinningCoords(coords);
          setIsThinking(false);
          inFlightRef.current = false;
          return;
        }

        if (isDraw(newBoard)) {
          setBoard(newBoard);
          setMoveHistory(newHistory);
          setStatus('draw');
          setWinner(null);
          setWinningCoords(null);
          setIsThinking(false);
          inFlightRef.current = false;
          return;
        }

        // Active game: return turn to Human Player 1
        setBoard(newBoard);
        setMoveHistory(newHistory);
        setTurn(PLAYER_1);
        setIsThinking(false);
        inFlightRef.current = false;
      } catch (err) {
        // Safe error handling: board remains completely preserved
        setErrorCode(err.code || 'API_ERROR');
        setErrorMessage(err.message || 'Failed to communicate with AI agent backend.');
        setIsThinking(false);
        inFlightRef.current = false;
      }
    },
    [depth, moveHistory, selectedAlgorithm]
  );

  /**
   * Handle player column click or keyboard trigger.
   */
  const handleColumnClick = useCallback(
    (colIndex) => {
      // Input guards
      if (status !== 'active') return;
      if (isThinking) return;
      if (errorMessage !== null) return; // Must resolve or dismiss error first

      // In Human vs AI, human can only move on turn 1
      if (gameMode === 'human_vs_ai' && turn !== PLAYER_1) return;

      if (!isValidLocation(board, colIndex)) return;

      const activePlayer = turn;
      const targetRow = getNextOpenRow(board, colIndex);
      if (targetRow === -1) return;

      const newBoard = cloneBoard(board);
      dropPiece(newBoard, targetRow, colIndex, activePlayer);

      const newHistory = [
        ...moveHistory,
        {
          moveNumber: moveHistory.length + 1,
          player: activePlayer,
          column: colIndex,
          row: targetRow,
          timestamp: new Date().toISOString(),
        },
      ];

      // Check win for current mover
      if (checkWin(newBoard, activePlayer)) {
        const coords = getWinningCoordinates(newBoard, activePlayer);
        setBoard(newBoard);
        setMoveHistory(newHistory);
        setStatus('won');
        setWinner(activePlayer);
        setWinningCoords(coords);
        return;
      }

      // Check draw
      if (isDraw(newBoard)) {
        setBoard(newBoard);
        setMoveHistory(newHistory);
        setStatus('draw');
        setWinner(null);
        setWinningCoords(null);
        return;
      }

      // Update state for active game
      setBoard(newBoard);
      setMoveHistory(newHistory);

      // Branch strictly by game mode
      if (gameMode === 'human_vs_human') {
        // Pass-and-play: alternate turn to Human 2 locally; NEVER call AI
        setTurn(activePlayer === PLAYER_1 ? PLAYER_2 : PLAYER_1);
      } else if (gameMode === 'human_vs_ai') {
        // Human vs AI: transition to turn 2 and dispatch AI request
        setTurn(PLAYER_2);
        triggerAIMove(newBoard);
      }
    },
    [board, turn, status, isThinking, errorMessage, gameMode, moveHistory, triggerAIMove]
  );

  /**
   * Safe AI Retry: Requests an AI move for the CURRENT UNCHANGED board.
   * Never replays or re-drops the human move.
   * Only permitted when active, turn === 2, not currently thinking, and error is set.
   */
  const retryAIMove = useCallback(() => {
    if (status !== 'active' || turn !== PLAYER_2 || isThinking || !errorMessage) {
      return;
    }
    setErrorMessage(null);
    setErrorCode(null);
    triggerAIMove(board);
  }, [status, turn, isThinking, errorMessage, board, triggerAIMove]);

  /**
   * Dismiss the error banner without resetting the game.
   */
  const dismissError = useCallback(() => {
    setErrorMessage(null);
    setErrorCode(null);
  }, []);

  /**
   * Reset game to a fresh state with given or existing settings.
   */
  const resetGame = useCallback(
    (customSettings = {}) => {
      const newMode = customSettings.gameMode ?? gameMode;
      const newDepth = customSettings.depth ?? depth;
      const newStarter = customSettings.startingPlayer ?? startingPlayer;
      const newAlgorithm = customSettings.algorithm ?? selectedAlgorithm;

      inFlightRef.current = false;
      const empty = createEmptyBoard();

      setBoard(empty);
      setStatus('active');
      setWinner(null);
      setWinningCoords(null);
      setMoveHistory([]);
      setIsThinking(false);
      setErrorMessage(null);
      setErrorCode(null);
      setTurn(newStarter);
      setGameMode(newMode);
      setDepth(newDepth);
      setStartingPlayer(newStarter);
      setSelectedAlgorithm(newAlgorithm);
      setTelemetry({
        decisionTimeMs: null,
        searchDepth: null,
        nodesEvaluated: null,
        prunedNodes: null,
        algorithmName: `${newAlgorithm === 'minimax' ? 'Minimax (Active)' : `${newAlgorithm} (Phase 4/5)`}`,
      });

      // If AI is configured to move first in Human vs AI, trigger immediately on empty board
      if (newMode === 'human_vs_ai' && newStarter === PLAYER_2) {
        setTimeout(() => {
          triggerAIMove(empty);
        }, 50);
      }
    },
    [gameMode, depth, startingPlayer, selectedAlgorithm, triggerAIMove]
  );

  return {
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
    ROWS,
    COLS,
    handleColumnClick,
    retryAIMove,
    dismissError,
    resetGame,
    setGameMode,
    setDepth,
    setStartingPlayer,
    setSelectedAlgorithm,
  };
}
