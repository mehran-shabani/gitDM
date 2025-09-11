import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/layout/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { AISummariesList } from './pages/ai-summaries/AISummariesList';
import { CreateAISummary } from './pages/ai-summaries/CreateAISummary';
import { AISummaryDetail } from './pages/ai-summaries/AISummaryDetail';
import { PatientsList } from './pages/patients/PatientsList';
import { EncountersList } from './pages/encounters/EncountersList';
import { LabResultsList } from './pages/lab-results/LabResultsList';
import { MedicationsList } from './pages/medications/MedicationsList';
import { ClinicalReferencesList } from './pages/clinical-references/ClinicalReferencesList';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/ai-summaries" element={<AISummariesList />} />
                    <Route path="/ai-summaries/new" element={<CreateAISummary />} />
                    <Route path="/ai-summaries/:id" element={<AISummaryDetail />} />
                    <Route path="/patients" element={<PatientsList />} />
                    <Route path="/encounters" element={<EncountersList />} />
                    <Route path="/lab-results" element={<LabResultsList />} />
                    <Route path="/medications" element={<MedicationsList />} />
                    <Route path="/clinical-references" element={<ClinicalReferencesList />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;