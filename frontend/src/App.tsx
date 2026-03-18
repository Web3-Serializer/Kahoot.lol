import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/AdminPage';

function P({children}:{children:React.ReactNode}) {
  const {user,loading} = useAuth();
  if(loading) return <div className="min-h-screen flex items-center justify-center text-zinc-700 text-xs">loading</div>;
  return user ? <>{children}</> : <Navigate to="/login"/>;
}
function Pub({children}:{children:React.ReactNode}) {
  const {user,loading} = useAuth();
  if(loading) return null;
  return user ? <Navigate to="/"/> : <>{children}</>;
}
export default function App() {
  return <AuthProvider><BrowserRouter><Routes>
    <Route path="/login" element={<Pub><LoginPage/></Pub>}/>
    <Route path="/" element={<P><DashboardPage/></P>}/>
    <Route path="/admin" element={<P><AdminPage/></P>}/>
  </Routes></BrowserRouter></AuthProvider>;
}
