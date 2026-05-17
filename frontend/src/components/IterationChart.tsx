import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from "recharts"

interface Props {
  history: {
    iteration: number
    score: number
    scores: {
      correctness: number
      clarity: number
      completeness: number
      conciseness: number
    }
  }[]
}

export default function IterationChart({ history }: Props) {
  const data = history.map(h => ({
    iteration: `#${h.iteration}`,
    overall: h.score,
    correctness: h.scores.correctness,
    clarity: h.scores.clarity,
    completeness: h.scores.completeness,
    conciseness: h.scores.conciseness,
  }))

  return (
    <div className="chart-card">
      <h3>Score Progression</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="iteration" stroke="#888" />
          <YAxis domain={[0, 1]} stroke="#888" />
          <Tooltip
            contentStyle={{ background: "#111", border: "1px solid #333" }}
          />
          <Legend />
          <Line type="monotone" dataKey="overall" stroke="#fff" strokeWidth={2} dot={{ r: 5 }} />
          <Line type="monotone" dataKey="correctness" stroke="#4ade80" strokeWidth={1} dot={false} />
          <Line type="monotone" dataKey="clarity" stroke="#60a5fa" strokeWidth={1} dot={false} />
          <Line type="monotone" dataKey="completeness" stroke="#f59e0b" strokeWidth={1} dot={false} />
          <Line type="monotone" dataKey="conciseness" stroke="#f472b6" strokeWidth={1} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}