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
        setStatus("Authentification réussie!");

        // If this is running in a popup window, send the auth code to the parent window
        if (window.opener && !window.opener.closed) {
          window.opener.postMessage(
            {
              type: "auth_callback",
              code,
            },
            window.location.origin
          );

          // Close the popup after sending the message
          setTimeout(() => window.close(), 1000);
        } else {
          // Handle the case where it's not in a popup (fallback)
          const service = emailAPIService.getService();

          if (!service) {
            setStatus("Erreur: Service de messagerie non spécifié");
            return;
          }

          await emailAPIService.handleAuthCallback(code);
          setStatus("Authentification réussie! Redirection...");
          setTimeout(() => navigate("/"), 1500);
        }
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
