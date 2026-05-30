import { useState } from "react"

interface Props {
  onSubmit: (taskType: string, initialPrompt: string, testInputs: string[]) => void
  loading: boolean
}

export default function PromptInput({ onSubmit, loading }: Props) {
  const [taskType, setTaskType] = useState("summarization")
  const [initialPrompt, setInitialPrompt] = useState("")
  const [testInput, setTestInput] = useState("")

  const handleSubmit = () => {
    if (!initialPrompt.trim() || !testInput.trim()) return
    const testInputs = testInput
      .split(/\n-{3,}\n/)
      .map(input => input.trim())
      .filter(Boolean)

    onSubmit(taskType, initialPrompt, testInputs)
  }

  return (
    <div className="input-card">
      <div className="input-group">
        <label>Task Type</label>
        <select value={taskType} onChange={e => setTaskType(e.target.value)}>
          <option value="summarization">Summarization</option>
          <option value="code_explanation">Code Explanation</option>
          <option value="qa">Question Answering</option>
          <option value="classification">Classification</option>
        </select>
      </div>

      <div className="input-group">
        <label>Initial Prompt</label>
        <textarea
          rows={3}
          placeholder="e.g. Summarize the following text."
          value={initialPrompt}
          onChange={e => setInitialPrompt(e.target.value)}
        />
      </div>

      <div className="input-group">
        <label>Test Inputs</label>
        <textarea
          rows={4}
          placeholder="Add one or more test cases. Separate multiple cases with a line containing ---"
          value={testInput}
          onChange={e => setTestInput(e.target.value)}
        />
      </div>

      <button
        className="run-btn"
        onClick={handleSubmit}
        disabled={loading || !initialPrompt.trim() || !testInput.trim()}
      >
        {loading ? "Running..." : "Run Optimizer"}
      </button>
    </div>
  )
}
