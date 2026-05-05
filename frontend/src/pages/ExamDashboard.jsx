import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getExam, getResults } from '../api/exam'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'

export default function ExamDashboard() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [exam, setExam] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const copyStudentLink = () => {
    navigator.clipboard.writeText(`${window.location.origin}/submit/${id}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  useEffect(() => {
    Promise.all([getExam(id), getResults(id).catch(() => null)])
      .then(([examRes, resultsRes]) => {
        setExam(examRes.data)
        if (resultsRes) setResults(resultsRes.data)
      })
      .catch(() => setError('Erro ao carregar a prova.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>
  if (error) return <p className="text-red-600 text-sm">{error}</p>

  const resultsByQuestion = {}
  results?.questions?.forEach(q => { resultsByQuestion[q.question_number] = q })

  return (
    <div>
      {exam.turma_id ? (
        <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
          <Link to="/" className="hover:text-gray-600">Turmas</Link>
          <span>›</span>
          <Link to={`/turma/${exam.turma_id}`} className="hover:text-gray-600">{exam.turma_nome}</Link>
          <span>›</span>
          <span className="text-gray-600">{exam.filename}</span>
        </div>
      ) : null}

      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-xs text-gray-400 mb-0.5">Prova #{id}</p>
          <h1 className="text-xl font-semibold text-gray-900">{exam.filename}</h1>
        </div>
        <div className="flex gap-2">
          <button
            onClick={copyStudentLink}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
            </svg>
            {copied ? 'Link copiado!' : 'Link para alunos'}
          </button>
          <Link
            to={`/exam/${id}/submit`}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V7.5l-4.5-4.5h-9.75A2.25 2.25 0 003.75 5.25v12.75A2.25 2.25 0 006 20.25z" />
            </svg>
            Testar submissão
          </Link>
          <Link
            to={`/exam/${id}/results`}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
            Resultados
          </Link>
        </div>
      </div>

      <div className="space-y-3">
        {exam.questions.map((q) => {
          const qr = resultsByQuestion[q.number]
          const passRate = qr && qr.total_submissions > 0
            ? Math.round((qr.passed_count / qr.total_submissions) * 100)
            : null

          return (
            <div key={q.id} className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs font-semibold text-purple-600 bg-purple-50 px-2 py-0.5 rounded-md">
                      Q{q.number}
                    </span>
                    {q.required_structures.length > 0 && (
                      <span className="text-xs text-gray-400">
                        Exige: {q.required_structures.join(', ')}
                      </span>
                    )}
                    {q.forbidden_structures.length > 0 && (
                      <span className="text-xs text-red-400">
                        Proíbe: {q.forbidden_structures.join(', ')}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2">{q.statement}</p>
                </div>

                <div className="flex items-center gap-4 shrink-0">
                  <div className="text-right">
                    <p className="text-xs text-gray-400">Test cases</p>
                    <p className="text-sm font-semibold text-gray-900">{q.test_case_count}</p>
                  </div>
                  {qr && (
                    <div className="text-right">
                      <p className="text-xs text-gray-400">Submissões</p>
                      <p className="text-sm font-semibold text-gray-900">{qr.total_submissions}</p>
                    </div>
                  )}
                  {passRate !== null && (
                    <Badge color={passRate >= 70 ? 'green' : passRate >= 40 ? 'yellow' : 'red'}>
                      {passRate}% corretos
                    </Badge>
                  )}
                </div>
              </div>

              <div className="flex gap-2 mt-4 pt-4 border-t border-gray-100">
                <Link
                  to={`/exam/${id}/questions/${q.number}/testcases`}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  + Test cases
                </Link>
                <Link
                  to={`/exam/${id}/questions/${q.number}/submissions`}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  Respostas
                </Link>
                <Link
                  to={`/exam/${id}/questions/${q.number}/cluster`}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  Clustering
                </Link>
                <Link
                  to={`/exam/${id}/questions/${q.number}/insights`}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  Insights LLM
                </Link>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
