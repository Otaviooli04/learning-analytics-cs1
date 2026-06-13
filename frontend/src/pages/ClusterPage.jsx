import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getExam, runClustering } from '../api/exam'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'

const STRATEGIES = [
  { value: 'tfidf', label: 'TF-IDF (padrão)' },
  { value: 'tfidf_ngram', label: 'TF-IDF + N-gramas' },
  { value: 'tfidf_category', label: 'TF-IDF + Categoria de erro' },
  { value: 'tfidf_behavioral', label: 'TF-IDF + Comportamental' },
  { value: 'tfidf_functional', label: 'TF-IDF + Funcional' },
]

const CLUSTER_COLORS = ['#7c3aed', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function ClusterPage() {
  const { id, num } = useParams()
  const [question, setQuestion] = useState(null)
  const [strategy, setStrategy] = useState('tfidf')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getExam(id).then(({ data }) => {
      setQuestion(data.questions.find(q => q.number === num))
    })
  }, [id, num])

  const run = async () => {
    setRunning(true)
    setResult(null)
    setError('')
    try {
      const { data } = await runClustering(id, num, strategy)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao executar clustering.')
    } finally {
      setRunning(false)
    }
  }

  const scatterByCluster = (clusterData) => {
    if (!result) return []
    return result.scatter.filter(p => p.cluster_id === clusterData.cluster_id)
  }

  const noisePoints = result?.scatter.filter(p => p.cluster_id === -1) ?? []

  return (
    <div>
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to={`/exam/${id}`} className="hover:text-gray-600">Prova #{id}</Link>
        <span>›</span>
        <span className="text-gray-600">Questão {num} — Clustering</span>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Clustering</h1>
          {question && <p className="text-sm text-gray-500 mt-1 line-clamp-1">{question.statement}</p>}
        </div>
        <Link
          to={`/exam/${id}/questions/${num}/insights`}
          className="text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Ver insights LLM →
        </Link>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Estratégia de features</label>
            <select
              value={strategy}
              onChange={e => setStrategy(e.target.value)}
              className="text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {STRATEGIES.map(s => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <button
            onClick={run}
            disabled={running}
            className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {running && <Spinner className="w-4 h-4" />}
            {running ? 'Executando…' : 'Executar clustering'}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 mb-4">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Badge color="purple">{result.total_submissions} submissões</Badge>
            <Badge color="gray">{result.clusters.length} clusters</Badge>
            {result.silhouette_score != null && (
              <Badge color={result.silhouette_score >= 0.5 ? 'green' : result.silhouette_score >= 0.25 ? 'yellow' : 'gray'}>
                Silhouette: {result.silhouette_score.toFixed(3)}
              </Badge>
            )}
            <Badge color="gray">{STRATEGIES.find(s => s.value === result.strategy)?.label}</Badge>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-medium text-gray-700 mb-4">Projeção UMAP 2D</h2>
            <ResponsiveContainer width="100%" height={360}>
              <ScatterChart margin={{ top: 8, right: 24, bottom: 8, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="x" name="UMAP 1" tick={{ fontSize: 10 }} label={{ value: 'UMAP 1', position: 'insideBottom', offset: -4, fontSize: 10 }} />
                <YAxis dataKey="y" name="UMAP 2" tick={{ fontSize: 10 }} label={{ value: 'UMAP 2', angle: -90, position: 'insideLeft', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
                  formatter={(v, name) => [v.toFixed(3), name]}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                {result.clusters.map((c, i) => (
                  <Scatter
                    key={c.cluster_id}
                    name={`Cluster ${c.cluster_id} (${c.dominant_error})`}
                    data={scatterByCluster(c)}
                    fill={CLUSTER_COLORS[i % CLUSTER_COLORS.length]}
                  />
                ))}
                {noisePoints.length > 0 && (
                  <Scatter name="Ruído" data={noisePoints} fill="#d1d5db" />
                )}
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {result.clusters.map((c, i) => {
              const alunos = result.scatter
                .filter(p => p.cluster_id === c.cluster_id && p.matricula)
                .map(p => p.matricula)
              return (
                <div key={c.cluster_id} className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{ backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }}
                    />
                    <span className="text-sm font-medium text-gray-800">Cluster {c.cluster_id}</span>
                    <span className="ml-auto text-xs text-gray-400">{c.size} aluno{c.size !== 1 ? 's' : ''}</span>
                  </div>
                  <Badge color="gray">{c.dominant_error}</Badge>
                  {alunos.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {alunos.map(m => (
                        <span key={m} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-md font-mono">{m}</span>
                      ))}
                    </div>
                  )}
                  {c.representative_code && (
                    <pre className="mt-3 text-xs font-mono bg-gray-50 rounded-lg p-3 overflow-x-auto text-gray-600 max-h-32 whitespace-pre-wrap">
                      {c.representative_code}
                    </pre>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
