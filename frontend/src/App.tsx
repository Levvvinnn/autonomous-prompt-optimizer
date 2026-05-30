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

interface OptimizeJobResponse {
  job_id: string
  status: string
}

interface JobStatusResponse {
  job_id: string
  status: string
  result: OptimizeResponse | null
  error: string | null
}

export default function App() {
  const [result, setResult] = useState<OptimizeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [statusMessage, setStatusMessage] = useState("")

  const handleOptimize = async (
    taskType: string,
    initialPrompt: string,
    testInputs: string[]
  ) => {
    setLoading(true)
    setError("")
    setResult(null)
    setStatusMessage("Starting optimization job...")
    try {
      const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"
      const API_AUTH_TOKEN = import.meta.env.VITE_API_AUTH_TOKEN
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      }

      if (API_AUTH_TOKEN) {
        headers["X-API-Key"] = API_AUTH_TOKEN
      }

      const res = await fetch(`${API_URL}/optimize`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          task_type: taskType,
          initial_prompt: initialPrompt,
          test_inputs: testInputs,
        }),
      })
      if (!res.ok) throw new Error(await res.text())

      const job: OptimizeJobResponse = await res.json()
      setStatusMessage("Job queued. Waiting for agents...")

      const eventsRes = await fetch(`${API_URL}/jobs/${job.job_id}/events`, { headers })
      if (!eventsRes.ok) throw new Error(await eventsRes.text())
      if (!eventsRes.body) throw new Error("Streaming is not supported by this browser.")

      const reader = eventsRes.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split("\n\n")
        buffer = events.pop() ?? ""

        for (const event of events) {
          const dataLine = event
            .split("\n")
            .find(line => line.startsWith("data: "))

          if (!dataLine) continue

          const jobStatus: JobStatusResponse = JSON.parse(dataLine.slice(6))
          if (jobStatus.status === "completed" && jobStatus.result) {
            setResult(jobStatus.result)
            setStatusMessage("")
            return
          }

          if (jobStatus.status === "failed") {
            throw new Error(jobStatus.error ?? "Optimization job failed.")
          }

          setStatusMessage(
            jobStatus.status === "running"
              ? "Agents running. Streaming progress..."
              : "Job queued. Waiting for agents..."
          )
        }
      }

      throw new Error("Optimization stream ended before the job completed.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.")
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
          <p className="tagline">Autonomous prompt improvement via multi-agent feedback loops</p>
        </div>
      </header>

      <main className="main">
        <PromptInput onSubmit={handleOptimize} loading={loading} />

        {error && <div className="error">{error}</div>}

        {loading && (
          <div className="loading-state">
            <div className="spinner" />
            <p>{statusMessage || "Agents running. Please wait..."}</p>
          </div>
        )}

        {result && (
          <div className="results">
            <div className="result-summary">
              <div className="stat">
                <span className="stat-value">{result.final_score.toFixed(2)}</span>
                <span className="stat-label">Final score</span>
              </div>
              <div className="stat">
                <span className="stat-value">{result.total_iterations}</span>
                <span className="stat-label">Iterations</span>
              </div>
              <div className="stat">
                <span className="stat-value">
                  {result.history[0]?.score.toFixed(2)}
                </span>
                <span className="stat-label">Initial score</span>
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
