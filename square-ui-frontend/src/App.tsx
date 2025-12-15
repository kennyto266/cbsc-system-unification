import React from 'react'
import { LayoutProvider, Layout } from '@/components/Layout'
import NavigationProvider from '@/navigation/NavigationProvider'
import type { User } from '@/types'

// Mock user data - in real app, this would come from authentication
const mockUser: User = {
  id: '1',
  name: 'John Doe',
  email: 'john.doe@example.com',
  avatar: undefined,
  role: 'Administrator',
}

const App: React.FC = () => {
  return (
    <LayoutProvider>
      <NavigationProvider>
        <Layout user={mockUser} />
      </NavigationProvider>
    </LayoutProvider>
  )
}

export default App