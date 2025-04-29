import React from "react";
import { Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import AuthCallback from "./components/AuthCallback";
import ExportStatusPage from './pages/ExportStatusPage';
import Login from "./pages/Login";

function App() {
  return (
    <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/home" element={<Home />} />
        <Route path="/export-status" element={<ExportStatusPage />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
    </Routes>
  );
}

export default App;
