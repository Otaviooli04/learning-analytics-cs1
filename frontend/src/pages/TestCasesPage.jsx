import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getExam, addTestCases } from '../api/exam'
import Spinner from '../components/Spinner'

export default function TestCasesPage() {
  const { id, num } = useParams()
  const [question, setQuestion] = useState(null)
  const [pending, setPending] = useState([])
  const [input, setInput] = useState('')
  const [expected, setExpected] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getExam(id).then(({ data }) => {
      setQuestion(data.questions.find(q => q.number === num))
    })
  }, [id, num])

  const addLocal = () => {
    if (!input.trim() || !expected.trim()) return
    setPending(prev => [...prev, { input, expected_output: expected }])
    setInput('')
    setExpected('')
  }

  const remove = (i) => setPending(prev => prev.filter((_, idx) => idx !== i))

  const save = async () => {
    if (pending.length === 0) return
    setSaving(true)
    setError('')
    try {
      await addTestCases(id, num, pending)
      setPending([])
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao salvar.')
    } finally {
      setSaving(false)
    }
  }

  if (!question) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to={`/exam/${id}`} className="hover:text-gray-600">Prova #{id}</Link>
        <span>›</span>
        <span className="text-gray-600">Questão {num} — Test cases</span>
      </div>

      <h1 className="text-xl font-semibold text-gray-900 mb-1">Test cases</h1>
      <p className="text-sm text-gray-500 line-clamp-2 mb-6">{question.statement}</p>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
        <h2 className="text-sm font-medium text-gray-700 mb-3">Adicionar caso de teste</h2>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Entrada (stdin)</label>
            <textarea
              rows={4}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ex: 5 3"
              className="w-full text-sm font-mono rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Saída esperada (stdout)</label>
            <textarea
              rows={4}
              value={expected}
              onChange={e => setExpected(e.target.value)}
              placeholder="Ex: 8"
              className="w-full text-sm font-mono rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
          </div>
        </div>
        <button
          onClick={addLocal}
          disabled={!input.trim() || !expected.trim()}
          className="mt-3 text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          + Adicionar à lista
        </button>
      </div>

      {pending.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100 mb-4">
          {pending.map((tc, i) => (
            <div key={i} className="flex items-center gap-4 px-5 py-3">
              <div className="flex-1 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-400 mb-0.5">Entrada</p>
                  <code className="text-xs text-gray-700 bg-gray-50 px-2 py-1 rounded block truncate">{tc.input}</code>
                </div>
                <div>
                  <p className="text-xs text-gray-400 mb-0.5">Saída esperada</p>
                  <code className="text-xs text-gray-700 bg-gray-50 px-2 py-1 rounded block truncate">{tc.expected_output}</code>
                </div>
              </div>
              <button onClick={() => remove(i)} className="text-gray-300 hover:text-red-400 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      {saved && (
        <div className="mb-3 rounded-lg bg-green-50 border border-green-200 px-4 py-2.5 text-sm text-green-700">
          Test cases salvos com sucesso.
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          onClick={save}
          disabled={saving || pending.length === 0}
          className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {saving && <Spinner className="w-4 h-4" />}
          Salvar {pending.length > 0 && `(${pending.length})`}
        </button>
        <Link to={`/exam/${id}`} className="text-sm text-gray-400 hover:text-gray-600">
          Voltar
        </Link>
      </div>
    </div>
  )
}
