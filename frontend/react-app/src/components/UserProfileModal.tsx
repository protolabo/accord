import React from "react";
import { motion } from "framer-motion";
import { authService } from "../services/authService";
import { useNavigate } from "react-router-dom";

interface UserProfileModalProps {
  onClose: () => void;
}

const UserProfileModal: React.FC<UserProfileModalProps> = ({ onClose }) => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      console.log("tentative logout");
      await authService.logout();
    } catch (error) {
      console.error("Erreur lors de la déconnexion:", error);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg max-w-md w-full"
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold dark:text-white">
            Profil Utilisateur
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 dark:text-gray-400"
          >
            Close
          </button>
        </div>
        <div className="space-y-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="font-semibold mb-1 dark:text-white">Settings</h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Placeholder for user settings.
            </p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <h3 className="font-semibold mb-1 dark:text-white">Preferences</h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Placeholder for user preferences.
            </p>
          </div>
          <div
            className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            onClick={handleLogout}
          >
            <h3 className="font-semibold mb-1 dark:text-white text-red-600">
              Déconnexion
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Se déconnecter de l'application
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default UserProfileModal;