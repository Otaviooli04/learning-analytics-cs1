import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList,
} from 'recharts'
import { getTurma, getTurmaAnalytics } from '../api/exam'
import Spinner from '../components/Spinner'

const PASS_COLOR = '#7c3aed'
const ERR_COLOR = '#e11d48'

function KpiCard({ label, value, sub }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-1">
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value ?? '—'}</p>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  )
}

function PassRateBar({ rate }) {
  if (rate == null) return <span className="text-xs text-gray-400">sem dados</span>
  const color = rate >= 70 ? 'bg-emerald-500' : rate >= 40 ? 'bg-amber-400' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2 mt-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${rate}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-500 w-10 text-right">{rate}%</span>
    </div>
  )
}

function DiffBadge({ rate }) {
  if (rate == null) return null
  const [label, cls] =
    rate >= 70 ? ['Fácil', 'text-emerald-700 bg-emerald-50 border-emerald-100']
    : rate >= 40 ? ['Médio', 'text-amber-700 bg-amber-50 border-amber-100']
    : ['Difícil', 'text-red-700 bg-red-50 border-red-100']
  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${cls}`}>
      {label}
    </span>
  )
}

const SHORT_LABELS = {
  'Erro de Compilação': 'Compilação',
  'Saída Incorreta': 'Saída incorreta',
  'Acesso Indevido à Memória': 'Memória',
  'Acesso Fora dos Limites — Off-by-One': 'Off-by-one',
  'Loop Infinito — Controle de Fluxo': 'Loop infinito',
  'Timeout Anômalo': 'Timeout',
  'Tudo no Main': 'Tudo no main',
  'Recursão Faltando': 'Sem recursão',
  'Função Ausente': 'Função ausente',
  'Assinatura Incorreta': 'Assinatura',
  'Solução Sequencial — Sem Controle de Fluxo': 'Sem controle',
  'Erro Desconhecido': 'Desconhecido',
}

export default function TurmaDetailPage() {
  const { turmaId } = useParams()
  const navigate = useNavigate()
  const [turma, setTurma] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getTurma(turmaId), getTurmaAnalytics(turmaId)])
      .then(([{ data: t }, { data: a }]) => {
        setTurma(t)
        setAnalytics(a)
      })
      .catch(() => setError('Erro ao carregar turma.'))
      .finally(() => setLoading(false))
  }, [turmaId])

  const formatDate = (iso) => {
    if (!iso) return ''
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>
  if (error) return <p className="text-red-600 text-sm">{error}</p>

  const examAnalyticsMap = Object.fromEntries((analytics?.provas ?? []).map(p => [p.id, p]))

  const evolucaoData = (analytics?.provas ?? []).map(p => ({
    name: p.filename.replace(/\.[^.]+$/, ''),
    taxa: p.pass_rate ?? 0,
  }))

  const errosData = (analytics?.top_erros ?? []).map(e => ({
    name: SHORT_LABELS[e.error_category] ?? e.error_category,
    count: e.count,
  }))

  return (
    <div className="space-y-8">
      {/* Breadcrumb + header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-gray-400 mb-4">
          <Link to="/" className="hover:text-gray-600">Turmas</Link>
          <span>›</span>
          <span className="text-gray-600">{turma.nome}</span>
        </div>
        <div className="flex items-center justify-between">
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
      </div>

      {/* KPIs */}
      {analytics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <KpiCard
            label="Alunos únicos"
            value={analytics.total_alunos}
          />
          <KpiCard
            label="Aproveitamento médio"
            value={analytics.aproveitamento_medio != null ? `${analytics.aproveitamento_medio}%` : null}
            sub="taxa de aprovação por prova"
          />
          <KpiCard
            label="Total de submissões"
            value={analytics.total_submissoes}
          />
          <KpiCard
            label="Provas cadastradas"
            value={turma.exams.length}
          />
        </div>
      )}

      {/* Charts — só mostra se há dados */}
      {analytics && (evolucaoData.length > 0 || errosData.length > 0) && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Evolução entre provas */}
          {evolucaoData.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Taxa de aprovação por prova</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={evolucaoData} barSize={28}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={v => [`${v}%`, 'Aprovação']} />
                  <Bar dataKey="taxa" radius={[4, 4, 0, 0]} fill={PASS_COLOR}>
                    <LabelList dataKey="taxa" position="top" formatter={v => `${v}%`} style={{ fontSize: 11, fill: '#6b7280' }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top erros */}
          {errosData.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Erros mais frequentes</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={errosData} layout="vertical" barSize={18}>
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={v => [v, 'Submissões']} />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {errosData.map((_, i) => (
                      <Cell key={i} fill={i === 0 ? ERR_COLOR : '#f43f5e'} opacity={1 - i * 0.12} />
                    ))}
                    <LabelList dataKey="count" position="right" style={{ fontSize: 11, fill: '#6b7280' }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Provas */}
      <div>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Provas</h2>
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
            {turma.exams.map(exam => {
              const ea = examAnalyticsMap[exam.id]
              return (
                <button
                  key={exam.id}
                  onClick={() => navigate(`/exam/${exam.id}`)}
                  className="bg-white rounded-xl border border-gray-200 p-5 text-left hover:border-purple-300 hover:shadow-sm transition-all"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h2 className="text-sm font-semibold text-gray-900 leading-tight truncate flex-1">{exam.filename}</h2>
                    {ea && <DiffBadge rate={ea.pass_rate} />}
                  </div>
                  <div className="flex gap-4 text-xs text-gray-500 mb-1">
                    <span>{exam.question_count} {exam.question_count === 1 ? 'questão' : 'questões'}</span>
                    <span>{exam.submission_count} {exam.submission_count === 1 ? 'submissão' : 'submissões'}</span>
                    {ea && <span>{ea.total_alunos} {ea.total_alunos === 1 ? 'aluno' : 'alunos'}</span>}
                  </div>
                  {ea && <PassRateBar rate={ea.pass_rate} />}
                  <p className="text-xs text-gray-400 mt-2">{formatDate(exam.created_at)}</p>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
