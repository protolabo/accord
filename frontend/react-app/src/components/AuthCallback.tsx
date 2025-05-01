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
      const token = searchParams.get("token"); // Changement ici: récupérer le token au lieu du code
      const email = searchParams.get("email");
      const service = searchParams.get("service") || "gmail";

      if (!token) {
        setStatus("Erreur: Token d'authentification manquant");
        return;
      }

      try {
        // Définir le service explicitement
        emailAPIService.setService(service as "gmail" | "outlook");

        // Stocker directement le token JWT au lieu d'échanger le code
        localStorage.setItem("jwt_token", token);
        if (email) localStorage.setItem("userEmail", email);

        // Marquer comme authentifié
        setStatus("Authentification réussie!");

        // Si dans une fenêtre popup, envoyer un message à la fenêtre parente
        if (window.opener && !window.opener.closed) {
          window.opener.postMessage(
            {
              type: "authSuccess",
              service,
              email: email
            },
            window.location.origin
          );

          // Fermer la popup après envoi du message
          setTimeout(() => window.close(), 1000);
        } else {
          // Gestion de repli si ce n'est pas une fenêtre popup
          setStatus("Authentification réussie! Redirection...");
          setTimeout(() => navigate("/"), 1500);
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