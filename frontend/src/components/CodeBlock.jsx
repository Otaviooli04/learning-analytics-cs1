// Código com numeração de linha; as linhas em `highlight` (1-based) recebem
// destaque visual — onde está o problema que define o grupo (erro de compilação
// localizado pelo gcc ou de lógica atribuído pelo Gemini).
export default function CodeBlock({ code, highlight = [] }) {
  const hot = new Set(highlight)
  const lines = (code || '').split('\n')
  return (
    <div className="mt-2 text-xs font-mono bg-gray-50 rounded-lg overflow-x-auto max-h-60">
      <table className="w-full border-collapse">
        <tbody>
          {lines.map((ln, i) => {
            const n = i + 1
            const flagged = hot.has(n)
            return (
              <tr key={n} className={flagged ? 'bg-red-50' : ''}>
                <td
                  className={`select-none text-right px-3 align-top tabular-nums ${
                    flagged ? 'text-red-400 font-medium' : 'text-gray-300'
                  }`}
                >
                  {n}
                </td>
                <td
                  className={`pr-3 whitespace-pre align-top ${
                    flagged ? 'text-red-700' : 'text-gray-600'
                  }`}
                >
                  {ln || ' '}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
