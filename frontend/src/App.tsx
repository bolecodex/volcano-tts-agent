import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import TTSAgentPage from './pages/TTSAgent'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<TTSAgentPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
