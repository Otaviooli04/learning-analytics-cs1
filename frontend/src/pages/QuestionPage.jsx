import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import {
  getExam, getQuestionSubmissions, runClustering, runInsights,
} from '../api/exam'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, Cell,
} from 'recharts'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'

const CLUSTER_COLORS = ['#7c3aed', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
const ERROR_COLORS = ['#7c3aed', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316']
const STRATEGIES = [
  { value: 'tfidf', label: 'TF-IDF (padrão)' },
  { value: 'tfidf_ngram', label: 'TF-IDF + N-gramas' },
  { value: 'tfidf_category', label: 'TF-IDF + Categoria de erro' },
  { value: 'tfidf_behavioral', label: 'TF-IDF + Comportamental' },
]
const TABS = [
  { key: 'respostas', label: 'Respostas' },
  { key: 'cluster', label: 'Clustering' },
  { key: 'insights', label: 'Insights LLM' },
]

export default function QuestionPage() {
  const { id, num } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'respostas'

  const [question, setQuestion] = useState(null)

  // Respostas
  const [submissions, setSubmissions] = useState(null)
  const [subLoading, setSubLoading] = useState(false)
  const [expanded, setExpanded] = useState({})

  // Clustering
  const [strategy, setStrategy] = useState('tfidf')
  const [clusterRunning, setClusterRunning] = useState(false)
  const [clusterResult, setClusterResult] = useState(null)
  const [clusterError, setClusterError] = useState('')

  // Insights
  const [insightsRunning, setInsightsRunning] = useState(false)
  const [insights, setInsights] = useState(null)
  const [insightsError, setInsightsError] = useState('')

  useEffect(() => {
    getExam(id).then(({ data }) => {
      setQuestion(data.questions.find(q => q.number === num))
    })
  }, [id, num])

  useEffect(() => {
    if (tab === 'respostas' && !submissions) {
      setSubLoading(true)
      getQuestionSubmissions(id, num)
        .then(({ data }) => setSubmissions(data.submissions))
        .finally(() => setSubLoading(false))
    }
  }, [tab, id, num])

  const setTab = (key) => setSearchParams({ tab: key })

  const passRate = submissions && submissions.length > 0
    ? Math.round((submissions.filter(s => s.all_tests_passed).length / submissions.length) * 100)
    : 0

  const errorDist = submissions
    ? Object.entries(
        submissions.reduce((acc, s) => {
          const cat = s.error_category || 'desconhecido'
          acc[cat] = (acc[cat] || 0) + 1
          return acc
        }, {})
      ).map(([error_category, count]) => ({ error_category, count }))
        .sort((a, b) => b.count - a.count)
    : []

  const runCluster = async () => {
    setClusterRunning(true)
    setClusterResult(null)
    setClusterError('')
    try {
      const { data } = await runClustering(id, num, strategy)
      setClusterResult(data)
    } catch (e) {
      setClusterError(e.response?.data?.detail || 'Erro ao executar clustering.')
    } finally {
      setClusterRunning(false)
    }
  }

  const runInsightsAction = async () => {
    setInsightsRunning(true)
    setInsightsError('')
    try {
      const { data } = await runInsights(id, num)
      setInsights(data.insights)
    } catch (e) {
      setInsightsError(e.response?.data?.detail || 'Erro ao gerar insights.')
    } finally {
      setInsightsRunning(false)
    }
  }

  const scatterByCluster = (c) =>
    clusterResult?.scatter.filter(p => p.cluster_id === c.cluster_id) ?? []

  const alunosByCluster = (cluster_id) =>
    clusterResult?.scatter
      .filter(p => p.cluster_id === cluster_id && p.matricula)
      .map(p => p.matricula) ?? []

  const noisePoints = clusterResult?.scatter.filter(p => p.cluster_id === -1) ?? []

  return (
    <div>
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to={`/exam/${id}`} className="hover:text-gray-600">Prova #{id}</Link>
        <span>›</span>
        <span className="text-gray-600">Questão {num}</span>
      </div>

      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold text-purple-600 bg-purple-50 px-2 py-0.5 rounded-md">Q{num}</span>
          <Link
            to={`/exam/${id}/questions/${num}/testcases`}
            className="text-xs px-2.5 py-1 rounded-md border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
          >
            + Test cases
          </Link>
        </div>
        {question && <p className="text-sm text-gray-700 mt-1">{question.statement}</p>}
      </div>

      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              tab === t.key
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab: Respostas */}
      {tab === 'respostas' && (
        <div>
          {subLoading && (
            <div className="flex justify-center py-16">
              <Spinner className="w-6 h-6 text-purple-600" />
            </div>
          )}
          {!subLoading && submissions?.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-12">Nenhuma submissão ainda.</p>
          )}
          {submissions && submissions.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Badge color="purple">{submissions.length} submissão{submissions.length !== 1 ? 'ões' : ''}</Badge>
                <Badge color={passRate >= 70 ? 'green' : passRate >= 40 ? 'yellow' : 'red'}>
                  {passRate}% corretos
                </Badge>
              </div>

              <div className="w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full bg-purple-500 transition-all"
                  style={{ width: `${passRate}%` }}
                />
              </div>

              {errorDist.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <p className="text-xs font-medium text-gray-500 mb-3">Distribuição de erros</p>
                  <ResponsiveContainer width="100%" height={Math.max(80, errorDist.length * 28)}>
                    <BarChart data={errorDist} layout="vertical" margin={{ left: 8, right: 16 }}>
                      <XAxis type="number" tick={{ fontSize: 10 }} />
                      <YAxis dataKey="error_category" type="category" width={200} tick={{ fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
                        formatter={(v) => [v, 'submissões']}
                      />
                      <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                        {errorDist.map((_, i) => (
                          <Cell key={i} fill={ERROR_COLORS[i % ERROR_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-50">
                {submissions.map(s => (
                  <div key={s.id} className="p-4">
                    <div
                      className="flex items-center gap-2 cursor-pointer"
                      onClick={() => setExpanded(e => ({ ...e, [s.id]: !e[s.id] }))}
                    >
                      <Badge color={s.all_tests_passed ? 'green' : s.compile_error ? 'red' : 'yellow'}>
                        {s.all_tests_passed ? 'Correto' : s.compile_error ? 'Erro compilação' : s.error_category || 'Parcial'}
                      </Badge>
                      {s.matricula && (
                        <span className="text-xs font-medium text-gray-700">{s.matricula}</span>
                      )}
                      <span className="text-xs text-gray-400 ml-auto">
                        {new Date(s.submitted_at).toLocaleString('pt-BR')}
                      </span>
                      <svg
                        className={`w-4 h-4 text-gray-400 transition-transform ${expanded[s.id] ? 'rotate-180' : ''}`}
                        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                    {expanded[s.id] && (
                      <div className="mt-3 space-y-2">
                        {s.pedagogical_diagnosis && (
                          <p className="text-xs text-gray-600">{s.pedagogical_diagnosis}</p>
                        )}
                        {s.actionable_feedback && (
                          <p className="text-xs text-gray-500 italic">{s.actionable_feedback}</p>
                        )}
                        <pre className="text-xs font-mono bg-gray-50 rounded-lg p-3 overflow-x-auto text-gray-600 whitespace-pre-wrap max-h-48">
                          {s.code}
                        </pre>
                        {s.compile_error && (
                          <pre className="text-xs font-mono bg-red-50 rounded-lg p-3 text-red-600 overflow-x-auto whitespace-pre-wrap">
                            {s.compile_error}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab: Clustering */}
      {tab === 'cluster' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
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
                onClick={runCluster}
                disabled={clusterRunning}
                className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {clusterRunning && <Spinner className="w-4 h-4" />}
                {clusterRunning ? 'Executando…' : 'Executar clustering'}
              </button>
            </div>
          </div>

          {clusterError && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {clusterError}
            </div>
          )}

          {clusterResult && (
            <>
              <div className="flex items-center gap-3 flex-wrap">
                <Badge color="purple">{clusterResult.total_submissions} submissões</Badge>
                <Badge color="gray">{clusterResult.clusters.length} clusters</Badge>
                {clusterResult.silhouette_score != null && (
                  <Badge color={clusterResult.silhouette_score >= 0.5 ? 'green' : clusterResult.silhouette_score >= 0.25 ? 'yellow' : 'gray'}>
                    Silhouette: {clusterResult.silhouette_score.toFixed(3)}
                  </Badge>
                )}
                <Badge color="gray">{STRATEGIES.find(s => s.value === clusterResult.strategy)?.label}</Badge>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="text-sm font-medium text-gray-700 mb-4">Projeção UMAP 2D</h2>
                <ResponsiveContainer width="100%" height={360}>
                  <ScatterChart margin={{ top: 8, right: 24, bottom: 8, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="x" name="UMAP 1" tick={{ fontSize: 10 }} label={{ value: 'UMAP 1', position: 'insideBottom', offset: -4, fontSize: 10 }} />
                    <YAxis dataKey="y" name="UMAP 2" tick={{ fontSize: 10 }} label={{ value: 'UMAP 2', angle: -90, position: 'insideLeft', fontSize: 10 }} />
                    <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }} formatter={(v, name) => [v.toFixed(3), name]} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    {clusterResult.clusters.map((c, i) => (
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
                {clusterResult.clusters.map((c, i) => {
                  const alunos = alunosByCluster(c.cluster_id)
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
            </>
          )}
        </div>
      )}

      {/* Tab: Insights */}
      {tab === 'insights' && (
        <div className="max-w-3xl space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-600 mb-4">
              O Gemini analisa o código representativo de cada cluster e gera um insight pedagógico com o padrão de dificuldade do grupo e uma sugestão de intervenção didática.
            </p>
            <button
              onClick={runInsightsAction}
              disabled={insightsRunning}
              className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {insightsRunning && <Spinner className="w-4 h-4" />}
              {insightsRunning ? 'Gerando com Gemini…' : insights ? 'Regerar insights' : 'Gerar insights'}
            </button>
          </div>

          {insightsError && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {insightsError}
            </div>
          )}

          {insights && insights.map((ins, i) => (
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
