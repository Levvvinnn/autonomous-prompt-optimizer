import { useState } from "react"

interface Props {
  history: {
    iteration: number
    prompt: string
    output: string
    score: number
    failure_analysis: string
  }[]
}

export default function VersionHistory({ history }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null)

  return (
    <div className="history-card">
      <h3>Iteration History</h3>
      {history.map(entry => (
        <div
          key={entry.iteration}
          className={`history-entry ${expanded === entry.iteration ? "expanded" : ""}`}
          onClick={() => setExpanded(
            expanded === entry.iteration ? null : entry.iteration
          )}
        >
          <div className="history-header">
            <span className="iter-badge">#{entry.iteration}</span>
            <span className="iter-score">{entry.score.toFixed(2)}</span>
            <span className="iter-toggle">{expanded === entry.iteration ? "▲" : "▼"}</span>
          </div>

          {expanded === entry.iteration && (
            <div className="history-body">
              <div className="history-section">
                <span className="section-label">Prompt</span>
                <p>{entry.prompt}</p>
              </div>
              <div className="history-section">
                <span className="section-label">Output</span>
                <p>{entry.output}</p>
              </div>
              <div className="history-section">
                <span className="section-label">Failure Analysis</span>
                <p>{entry.failure_analysis}</p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}