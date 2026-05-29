import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getExam, runInsights } from '../api/exam'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'

const CLUSTER_COLORS = ['#7c3aed', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function InsightsPage() {
  const { id, num } = useParams()
  const [question, setQuestion] = useState(null)
  const [running, setRunning] = useState(false)
  const [insights, setInsights] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getExam(id).then(({ data }) => {
      setQuestion(data.questions.find(q => q.number === num))
    })
  }, [id, num])

  const run = async () => {
    setRunning(true)
    setError('')
    try {
      const { data } = await runInsights(id, num)
      setInsights(data.insights)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao gerar insights.')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to={`/exam/${id}`} className="hover:text-gray-600">Prova #{id}</Link>
        <span>›</span>
        <Link to={`/exam/${id}/questions/${num}/cluster`} className="hover:text-gray-600">Questão {num} — Clustering</Link>
        <span>›</span>
        <span className="text-gray-600">Insights LLM</span>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Insights pedagógicos</h1>
          {question && <p className="text-sm text-gray-500 mt-1 line-clamp-1">{question.statement}</p>}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
        <p className="text-sm text-gray-600 mb-4">
          O Gemini analisa o código representativo de cada cluster e gera um insight pedagógico com o padrão de dificuldade do grupo e uma sugestão de intervenção didática.
        </p>
        <button
          onClick={run}
          disabled={running}
          className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {running && <Spinner className="w-4 h-4" />}
          {running ? 'Gerando com Gemini…' : insights ? 'Regerar insights' : 'Gerar insights'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 mb-4">
          {error}
        </div>
      )}

      {insights && (
        <div className="space-y-3">
          {insights.map((ins, i) => (
            <div key={ins.cluster_id} className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-center gap-2 mb-3">
                <span
                  className="w-3 h-3 rounded-full shrink-0"
                  style={{ backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }}
                />
                <span className="text-sm font-medium text-gray-800">Cluster {ins.cluster_id}</span>
                <Badge color="gray">{ins.size} aluno{ins.size !== 1 ? 's' : ''}</Badge>
                <Badge color="red">{ins.dominant_error}</Badge>
              </div>

              <div className="flex gap-2">
                <div className="w-0.5 bg-purple-200 rounded-full shrink-0" />
                <p className="text-sm text-gray-700 leading-relaxed">{ins.insight}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
