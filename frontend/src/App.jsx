import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import UploadPage from './pages/UploadPage'
import ExamDashboard from './pages/ExamDashboard'
import TestCasesPage from './pages/TestCasesPage'
import SubmitPage from './pages/SubmitPage'
import ResultsPage from './pages/ResultsPage'
import ClusterPage from './pages/ClusterPage'
import InsightsPage from './pages/InsightsPage'
import TurmaListPage from './pages/TurmaListPage'
import TurmaDetailPage from './pages/TurmaDetailPage'
import ExamUploadPage from './pages/ExamUploadPage'
import SubmissionsPage from './pages/SubmissionsPage'
import StudentSubmitPage from './pages/StudentSubmitPage'
import BulkSubmitPage from './pages/BulkSubmitPage'
import StudentsPage from './pages/StudentsPage'
import StudentDetailPage from './pages/StudentDetailPage'
import QuestionPage from './pages/QuestionPage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Público — alunos */}
          <Route path="submit/:examId" element={<StudentSubmitPage />} />

          {/* Auth */}
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />

          {/* Professor — protegido */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route index element={<TurmaListPage />} />
              <Route path="turma/:turmaId" element={<TurmaDetailPage />} />
              <Route path="turma/:turmaId/upload" element={<ExamUploadPage />} />
              <Route path="upload" element={<UploadPage />} />
              <Route path="exam/:id" element={<ExamDashboard />} />
              <Route path="exam/:id/questions/:num" element={<QuestionPage />} />
              <Route path="exam/:id/questions/:num/testcases" element={<TestCasesPage />} />
              <Route path="exam/:id/submit" element={<SubmitPage />} />
              <Route path="exam/:id/results" element={<ResultsPage />} />
              <Route path="exam/:id/questions/:num/cluster" element={<ClusterPage />} />
              <Route path="exam/:id/questions/:num/insights" element={<InsightsPage />} />
              <Route path="exam/:id/questions/:num/submissions" element={<SubmissionsPage />} />
              <Route path="exam/:id/bulk-submit" element={<BulkSubmitPage />} />
              <Route path="exam/:id/students" element={<StudentsPage />} />
              <Route path="exam/:id/students/:matricula" element={<StudentDetailPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
