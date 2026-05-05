import api from './client'

export const uploadExam = (file) => {
  const form = new FormData()
  form.append('file', file)
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

export const submitCode = (examId, questionNumber, code) =>
  api.post('/submission/evaluate', { exam_id: Number(examId), question_number: questionNumber, code })
