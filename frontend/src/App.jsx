import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import UploadPage from './pages/UploadPage'
import ExamDashboard from './pages/ExamDashboard'
import TestCasesPage from './pages/TestCasesPage'
import SubmitPage from './pages/SubmitPage'
import ResultsPage from './pages/ResultsPage'
import ClusterPage from './pages/ClusterPage'
import InsightsPage from './pages/InsightsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<UploadPage />} />
          <Route path="exam/:id" element={<ExamDashboard />} />
          <Route path="exam/:id/questions/:num/testcases" element={<TestCasesPage />} />
          <Route path="exam/:id/submit" element={<SubmitPage />} />
          <Route path="exam/:id/results" element={<ResultsPage />} />
          <Route path="exam/:id/questions/:num/cluster" element={<ClusterPage />} />
          <Route path="exam/:id/questions/:num/insights" element={<InsightsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
