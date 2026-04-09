import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { Layout } from '@/components/Layout'
import { Landing } from '@/pages/Landing'
import { Translate } from '@/pages/Translate'
import { Validate } from '@/pages/Validate'
import { Discuss } from '@/pages/Discuss'
import { Leaderboard } from '@/pages/Leaderboard'
import { Browse } from '@/pages/Browse'
import { CrossLanguage } from '@/pages/CrossLanguage'
import { Listen } from '@/pages/Listen'
import { Profile } from '@/pages/Profile'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/translate" element={<Translate />} />
            <Route path="/validate" element={<Validate />} />
            <Route path="/discuss" element={<Discuss />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/browse" element={<Browse />} />
            <Route path="/cross" element={<CrossLanguage />} />
            <Route path="/listen" element={<Listen />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </Layout>
      </AuthProvider>
    </BrowserRouter>
  )
}
