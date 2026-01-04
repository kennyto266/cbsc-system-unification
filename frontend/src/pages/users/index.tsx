import { Routes, Route, Navigate } from 'react-router-dom'
import UserList from './UserList'
import RoleManagement from './RoleManagement'

export default function Users() {
  return (
    <Routes>
      <Route path="/" element={<UserList />} />
      <Route path="/list" element={<UserList />} />
      <Route path="/roles" element={<RoleManagement />} />
      <Route path="*" element={<Navigate to="/users" replace />} />
    </Routes>
  )
}
