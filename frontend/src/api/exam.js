import api from './client'

export const uploadExam = (file, turmaId = null) => {
  const form = new FormData()
  form.append('file', file)
  if (turmaId) form.append('turma_id', String(turmaId))
  return api.post('/exam/upload', form)
}

export const getExam = (id) => api.get(`/exam/${id}`)

export const addTestCases = (examId, questionNumber, testCases) =>
  api.post(`/exam/${examId}/questions/${questionNumber}/testcases`, { test_cases: testCases })

export const getResults = (examId) => api.get(`/exam/${examId}/results`)

export const runClustering = (examId, questionNumber, strategy) =>
  api.post(`/exam/${examId}/questions/${questionNumber}/cluster?strategy=${strategy}`)

export const runInsights = (examId, questionNumber) =>
  api.post(`/exam/${examId}/questions/${questionNumber}/insights`)

export const submitCode = (examId, questionNumber, code, studentName = '') =>
  api.post('/submission/evaluate', {
    exam_id: Number(examId),
    question_number: questionNumber,
    code,
    student_name: studentName || null,
  })

export const createTurma = (nome, codigo) =>
  api.post('/turmas', { nome, codigo })

export const listTurmas = () => api.get('/turmas')

export const getTurma = (id) => api.get(`/turmas/${id}`)

export const getQuestionSubmissions = (examId, questionNumber) =>
  api.get(`/exam/${examId}/questions/${questionNumber}/submissions`)
