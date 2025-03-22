import { Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";

function App() {
  // Désactivé temporairement pour le développement
  const isAuthenticated = true; // On force l'authentification à true

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/home" replace /> : <Login />}
      />
      <Route
        path="/home"
        element={<Home />} // Retiré la vérification d'authentification
      />
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/auth/callback" element={<Login />} />
    </Routes>
  );
}

export default App;
