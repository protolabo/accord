import React, { useState } from "react";
import { motion } from "framer-motion";
import { FaGoogle, FaMicrosoft } from "react-icons/fa";
import emailAPIService, { EmailService } from "../services/EmailService";
import { useNavigate } from "react-router-dom";
import axios from "axios";

interface EmailServiceSelectorProps {
  onServiceSelect: (service: EmailService) => void;
  className?: string;
}

const EmailServiceSelector: React.FC<EmailServiceSelectorProps> = ({
  onServiceSelect,
  className,
}) => {
  const [selectedService, setSelectedService] = useState<EmailService | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [exportStatus, setExportStatus] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const navigate = useNavigate();

  // Fonction simplifiée pour l'exportation Gmail (sans demande d'email)
  const handleServiceSelect = async (service: EmailService) => {
    try {
      setIsLoading(true);
      setSelectedService(service);
      emailAPIService.setService(service);
      onServiceSelect(service);

      if (service === "gmail") {
        try {
          // Montrer que le processus est en cours
          setExportStatus("waiting");
          setStatusMessage("Préparation de l'exportation des emails...");

          // Email par défaut pour le test - vous pouvez le remplacer par un email spécifique
          const defaultEmail = "utilisateur@gmail.com";

          // Appeler l'endpoint d'exportation via le proxy React
          setStatusMessage(
            "Connexion au backend et lancement de l'exportation..."
          );

          try {
            // Utiliser le chemin relatif avec le proxy configuré dans package.json
            const response = await fetch("/export/gmail", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                email: defaultEmail,
                max_emails: null, // récupérer tous les emails
                output_dir: "../data",
                batch_size: 5000,
              }),
            });

            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Réponse du serveur:", data);

            // Passer à l'état d'exportation
            setExportStatus("exporting");
            setStatusMessage(
              "Exportation et classification des emails en cours..."
            );

            // Afficher un message indiquant que le traitement est en cours
            // et attendre avant de rediriger
            setTimeout(() => {
              setStatusMessage(
                "Traitement terminé! Redirection vers la page principale..."
              );
              setTimeout(() => {
                navigate("/");
              }, 2000);
            }, 15000);
          } catch (error) {
            console.error("Erreur lors de l'appel à /export/gmail:", error);
            setExportStatus("error");
            setStatusMessage(
              "Erreur lors de la connexion au serveur. Veuillez réessayer."
            );
            setIsLoading(false);
          }
        } catch (error) {
          console.error("Erreur lors de l'exportation Gmail:", error);
          setExportStatus("error");
          setStatusMessage("Une erreur s'est produite. Veuillez réessayer.");
          setIsLoading(false);
        }
      } else if (service === "outlook") {
        // Pour Outlook, approche simplifiée
        setStatusMessage("Service Outlook non implémenté pour le moment");
        setTimeout(() => {
          setIsLoading(false);
          setExportStatus(null);
        }, 2000);
      }
    } catch (error) {
      console.error("Erreur lors de la sélection du service:", error);
      setIsLoading(false);
      setExportStatus("error");
      setStatusMessage("Une erreur s'est produite. Veuillez réessayer.");
    }
  };

  // Affichage du statut d'exportation
  const renderStatus = () => {
    if (isLoading) {
      return (
        <div className="mt-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
        </div>
      );
    }

    if (!exportStatus) return null;

    let statusClass =
      exportStatus === "error"
        ? "text-red-500"
        : exportStatus === "completed"
        ? "text-green-500"
        : "text-blue-500";

    return (
      <div className="mt-6 flex flex-col items-center">
        <div className={`text-center mb-2 ${statusClass}`}>{statusMessage}</div>
        {exportStatus !== "completed" && exportStatus !== "error" && (
          <div className="w-full max-w-md bg-gray-200 rounded-full h-2.5 mb-4 dark:bg-gray-700">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-500 animate-pulse"
              style={{
                width: exportStatus === "waiting" ? "30%" : "70%",
              }}
            ></div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <h3 className="text-xl font-semibold mb-4 dark:text-white">
        Choisir un service de messagerie
      </h3>
      <div className="flex space-x-4">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={`flex flex-col items-center p-4 rounded-lg shadow-md transition-colors
            ${
              selectedService === "gmail"
                ? "bg-blue-500 text-white"
                : "bg-white dark:bg-gray-700 text-gray-800 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600"
            }`}
          onClick={() => handleServiceSelect("gmail")}
          disabled={isLoading || exportStatus === "exporting"}
        >
          <FaGoogle className="text-3xl mb-2" />
          <span>Gmail</span>
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={`flex flex-col items-center p-4 rounded-lg shadow-md transition-colors
            ${
              selectedService === "outlook"
                ? "bg-blue-500 text-white"
                : "bg-white dark:bg-gray-700 text-gray-800 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600"
            }`}
          onClick={() => handleServiceSelect("outlook")}
          disabled={isLoading || exportStatus === "exporting"}
        >
          <FaMicrosoft className="text-3xl mb-2" />
          <span>Outlook</span>
        </motion.button>
      </div>

      {/* Affichage des indicateurs de statut */}
      {renderStatus()}
    </div>
  );
};

export default EmailServiceSelector;
