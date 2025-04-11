import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import emailAPIService from "../services/EmailService";

const AuthCallback: React.FC = () => {
  const [status, setStatus] = useState("Traitement de l'authentification...");
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleCallback = async () => {
      const searchParams = new URLSearchParams(location.search);
      const code = searchParams.get("code");

      if (!code) {
        setStatus("Erreur: Code d'autorisation manquant");
        return;
      }

      try {
        // Get the service from localStorage since it might not be in the URL
        const service = emailAPIService.getService();

        if (!service) {
          setStatus("Erreur: Service de messagerie non spécifié");
          return;
        }

        await emailAPIService.handleAuthCallback(code);
        setStatus("Authentification réussie! Redirection...");
        // Redirect after a short delay
        setTimeout(() => navigate("/"), 1500);
      } catch (error) {
        console.error("Authentication error:", error);
        setStatus("Erreur d'authentification. Veuillez réessayer.");
      }
    };

    handleCallback();
  }, [location, navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-lg">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
          <h2 className="text-xl font-semibold mb-2 dark:text-white">
            {status}
          </h2>
        </div>
      </div>
    </div>
  );
};

export default AuthCallback;
