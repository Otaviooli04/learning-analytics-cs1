import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getResults } from '../api/exam'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'

const ERROR_COLORS = [
  '#7c3aed', '#0ea5e9', '#10b981', '#f59e0b',
  '#ef4444', '#8b5cf6', '#06b6d4', '#f97316',
]

export default function ResultsPage() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState({})

  useEffect(() => {
    getResults(id)
      .then(res => setData(res.data))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>
  if (!data) return <p className="text-sm text-red-600">Erro ao carregar resultados.</p>

  const toggle = (num) => setExpanded(e => ({ ...e, [num]: !e[num] }))

  return (
    <div>
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to={`/exam/${id}`} className="hover:text-gray-600">Prova #{id}</Link>
        <span>›</span>
        <span className="text-gray-600">Resultados</span>
      </div>

      <h1 className="text-xl font-semibold text-gray-900 mb-6">Resultados — {data.filename}</h1>

      <div className="space-y-4">
        {data.questions.map((q) => {
          const passRate = q.total_submissions > 0
            ? Math.round((q.passed_count / q.total_submissions) * 100)
            : 0

          return (
            <div key={q.question_number} className="bg-white rounded-xl border border-gray-200">
              <div className="p-5">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-semibold text-purple-600 bg-purple-50 px-2 py-0.5 rounded-md">
                        Q{q.question_number}
                      </span>
                      <Badge color={passRate >= 70 ? 'green' : passRate >= 40 ? 'yellow' : 'red'}>
                        {passRate}% corretos
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-2">{q.statement}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-2xl font-bold text-gray-900">{q.total_submissions}</p>
                    <p className="text-xs text-gray-400">submissões</p>
                  </div>
                </div>

                <div className="w-full bg-gray-100 rounded-full h-1.5 mb-4">
                  <div
                    className="h-1.5 rounded-full bg-purple-500 transition-all"
                    style={{ width: `${passRate}%` }}
                  />
                </div>

                {q.error_distribution.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-2">Distribuição de erros</p>
                    <ResponsiveContainer width="100%" height={120}>
                      <BarChart data={q.error_distribution} layout="vertical" margin={{ left: 8, right: 16 }}>
                        <XAxis type="number" tick={{ fontSize: 10 }} />
                        <YAxis dataKey="error_category" type="category" width={180} tick={{ fontSize: 10 }} />
                        <Tooltip
                          contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
                          formatter={(v) => [v, 'submissões']}
                        />
                        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                          {q.error_distribution.map((_, i) => (
                            <Cell key={i} fill={ERROR_COLORS[i % ERROR_COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {q.submissions.length > 0 && (
                <div className="border-t border-gray-100">
                  <button
                    onClick={() => toggle(q.question_number)}
                    className="w-full flex items-center justify-between px-5 py-3 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    <span>Ver submissões individuais ({q.submissions.length})</span>
                    <svg className={`w-4 h-4 transition-transform ${expanded[q.question_number] ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {expanded[q.question_number] && (
                    <div className="divide-y divide-gray-50">
                      {q.submissions.map((s) => (
                        <div key={s.id} className="px-5 py-3">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge color={s.all_tests_passed ? 'green' : s.compile_error ? 'red' : 'yellow'}>
                              {s.all_tests_passed ? 'Correto' : s.compile_error ? 'Erro compilação' : s.diagnosis.error_category}
                            </Badge>
                            <span className="text-xs text-gray-400">{new Date(s.submitted_at).toLocaleString('pt-BR')}</span>
                          </div>
                          <p className="text-xs text-gray-500">{s.diagnosis.pedagogical_diagnosis}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
