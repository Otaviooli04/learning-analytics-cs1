import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getTurma } from '../api/exam'
import Spinner from '../components/Spinner'

export default function TurmaDetailPage() {
  const { turmaId } = useParams()
  const navigate = useNavigate()
  const [turma, setTurma] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getTurma(turmaId)
      .then(({ data }) => setTurma(data))
      .catch(() => setError('Erro ao carregar turma.'))
      .finally(() => setLoading(false))
  }, [turmaId])

  const formatDate = (iso) => {
    if (!iso) return ''
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>
  if (error) return <p className="text-red-600 text-sm">{error}</p>

  return (
    <div>
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to="/" className="hover:text-gray-600">Turmas</Link>
        <span>›</span>
        <span className="text-gray-600">{turma.nome}</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-gray-900">{turma.nome}</h1>
          <span className="text-xs font-medium text-purple-700 bg-purple-50 border border-purple-100 px-2 py-0.5 rounded-md">
            {turma.codigo}
          </span>
        </div>
        <button
          onClick={() => navigate(`/turma/${turmaId}/upload`)}
          className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          Upload de prova
        </button>
      </div>

      {turma.exams.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <svg className="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          <p className="text-sm">Nenhuma prova cadastrada.</p>
          <p className="text-xs mt-1">Clique em "Upload de prova" para adicionar.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {turma.exams.map(exam => (
            <button
              key={exam.id}
              onClick={() => navigate(`/exam/${exam.id}`)}
              className="bg-white rounded-xl border border-gray-200 p-5 text-left hover:border-purple-300 hover:shadow-sm transition-all"
            >
              <h2 className="text-sm font-semibold text-gray-900 leading-tight mb-3 truncate">{exam.filename}</h2>
              <div className="flex gap-4 text-xs text-gray-500">
                <span>{exam.question_count} {exam.question_count === 1 ? 'questão' : 'questões'}</span>
                <span>{exam.submission_count} {exam.submission_count === 1 ? 'submissão' : 'submissões'}</span>
              </div>
              <p className="text-xs text-gray-400 mt-2">{formatDate(exam.created_at)}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
