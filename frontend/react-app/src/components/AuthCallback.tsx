import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import emailAPIService from "../services/EmailService";
import { authService } from "../services/authService";

const AuthCallback: React.FC = () => {
  const [status, setStatus] = useState("Traitement de l'authentification...");
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleCallback = async () => {
      const searchParams = new URLSearchParams(location.search);
      const token = searchParams.get("token");
      const email = searchParams.get("email");
      const service = searchParams.get("service") || "gmail";

      if (!token) {
        setStatus("Erreur: Token d'authentification manquant");
        return;
      }

      try {
        emailAPIService.setService(service as "gmail" | "outlook");
        localStorage.setItem("jwt_token", token);
        if (email) localStorage.setItem("userEmail", email);

        setStatus("Authentification réussie! Démarrage de l'exportation des emails...");

        //  Déclencher l'exportation des emails
        if (service === "gmail" && email) {
          try {
            const exportResponse = await fetch('http://localhost:8000/export/gmail', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                email: email,
                max_emails: 1,
                output_dir: '../data',
                batch_size: 5000
              }),
            });

            if (exportResponse.ok) {
              setStatus("Exportation des emails en cours. Redirection vers le tableau de bord...");
              // Rediriger vers la page d'état d'exportation
              setTimeout(() => navigate("/export-status"), 1500);
            } else {
              const errorData = await exportResponse.json();
              setStatus(`Erreur lors du démarrage de l'exportation: ${errorData.detail || 'Erreur inconnue'}`);
              setTimeout(() => navigate("/home"), 2000);
            }
          } catch (exportError) {
            console.error("Erreur lors de l'exportation:", exportError);
            setStatus("Authentification réussie, mais l'exportation a échoué. Redirection...");
            setTimeout(() => navigate("/home"), 2000);
          }
        } else {
          setStatus("Authentification réussie! Redirection...");
          setTimeout(() => navigate("/home"), 1500);
        }

        // Gestion des fenêtres popup
        if (window.opener && !window.opener.closed) {
          window.opener.postMessage(
            {
              type: "authSuccess",
              service,
              email: email
            },
            window.location.origin
          );
          setTimeout(() => window.close(), 1000);
        }
      } catch (error) {
        console.error("Erreur d'authentification:", error);
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