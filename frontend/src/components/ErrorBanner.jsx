export function ErrorBanner({ code, message, onRetry, onDismiss, canRetry }) {
  if (!message) return null;

  return (
    <div className="error-banner" role="alert" aria-live="assertive">
      <div className="error-icon" aria-hidden="true">
        ⚠️
      </div>
      <div className="error-body">
        <div className="error-header">
          <span className="error-title">Request Issue</span>
          {code && <span className="error-code">[{code}]</span>}
        </div>
        <p className="error-message">{message}</p>
      </div>
      <div className="error-actions">
        {canRetry && onRetry && (
          <button className="btn-error-retry" onClick={onRetry}>
            Retry AI Move
          </button>
        )}
        <button className="btn-error-dismiss" onClick={onDismiss} aria-label="Dismiss error">
          Dismiss
        </button>
      </div>
    </div>
  );
}
