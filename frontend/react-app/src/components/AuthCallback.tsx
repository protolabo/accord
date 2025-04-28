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
      const email = searchParams.get("email");

      if (!code) {
        setStatus("Erreur: Code d'autorisation manquant");
        return;
      }

      try {
        const service = emailAPIService.getService();

        if (!service) {
          setStatus("Erreur: Service de messagerie non spécifié");
          return;
        }

        // Traiter le code d'authentification
        await emailAPIService.handleAuthCallback(code);
        setStatus("Authentification réussie!");

        // Si cette page est dans une fenêtre popup, envoyer un message à la fenêtre parente
        if (window.opener && !window.opener.closed) {
          // Obtenir l'email de l'utilisateur si possible
          let userEmail = email;
          try {
            if (!userEmail) {
              const profile = await emailAPIService.getUserProfile();
              userEmail = profile.email;
            }
          } catch (e) {
            console.error(
              "Impossible de récupérer le profil de l'utilisateur:",
              e
            );
          }

          // Envoyer un message à la fenêtre parente indiquant que l'authentification est réussie
          window.opener.postMessage(
            {
              type: "authSuccess",
              service,
              email: userEmail,
            },
            window.location.origin
          );

          // Si le service est Gmail, lancer l'exportation automatiquement
          if (service === "gmail" && userEmail) {
            try {
              // Tenter de lancer l'exportation directement depuis la fenêtre de callback
              await emailAPIService.exportGmailEmails(
                userEmail,
                null, // max_emails - null pour tous récupérer
                "../data", // répertoire de sortie par défaut
                5000 // taille de lot par défaut
              );

              // Informer la fenêtre parente que l'exportation a été lancée
              window.opener.postMessage(
                {
                  type: "exportStarted",
                  service: "gmail",
                  email: userEmail,
                },
                window.location.origin
              );
            } catch (exportError) {
              console.error(
                "Erreur lors de l'exportation des emails:",
                exportError
              );
            }
          }

          // Fermer la fenêtre popup après l'envoi du message
          setTimeout(() => window.close(), 1000);
        } else {
          // Gestion si ce n'est pas une fenêtre popup (repli)
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
