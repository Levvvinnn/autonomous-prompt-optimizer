import { useState } from "react"
import PromptInput from "./components/PromptInput"
import IterationChart from "./components/IterationChart"
import VersionHistory from "./components/VersionHistory"
import "./App.css"

interface HistoryEntry {
  iteration: number
  prompt: string
  output: string
  score: number
  failure_analysis: string
  scores: {
    correctness: number
    clarity: number
    completeness: number
    conciseness: number
  }
}

interface OptimizeResponse {
  session_id: number
  final_prompt: string
  final_score: number
  total_iterations: number
  history: HistoryEntry[]
}

export default function App() {
  const [result, setResult] = useState<OptimizeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleOptimize = async (
    taskType: string,
    initialPrompt: string,
    testInput: string
  ) => {
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"
      const res = await fetch(`${API_URL}/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: taskType,
          initial_prompt: initialPrompt,
          test_input: testInput,
        }),
      })
      if(!res.ok)throw new Error(await res.text())
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setError("Something went wrong. Make sure your backend is running.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <span className="logo">⟳</span>
          <h1>Prompt Optimizer</h1>
          <p className="tagline">autonomous prompt improvement via multi-agent feedback loops</p>
        </div>
      </header>

      <main className="main">
        <PromptInput onSubmit={handleOptimize} loading={loading} />

        {error && <div className="error">{error}</div>}

        {loading && (
          <div className="loading-state">
            <div className="spinner" />
            <p>Agents running — this takes 20–40 seconds...</p>
          </div>
        )}

        {result && (
          <div className="results">
            <div className="result-summary">
              <div className="stat">
                <span className="stat-value">{result.final_score.toFixed(2)}</span>
                <span className="stat-label">final score</span>
              </div>
              <div className="stat">
                <span className="stat-value">{result.total_iterations}</span>
                <span className="stat-label">iterations</span>
              </div>
              <div className="stat">
                <span className="stat-value">
                  {result.history[0]?.score.toFixed(2)}
                </span>
                <span className="stat-label">initial score</span>
              </div>
            </div>

            <div className="final-prompt">
              <h3>Optimized Prompt</h3>
              <p>{result.final_prompt}</p>
            </div>

            <IterationChart history={result.history} />
            <VersionHistory history={result.history} />
          </div>
        )}
      </main>
    </div>
  )
}