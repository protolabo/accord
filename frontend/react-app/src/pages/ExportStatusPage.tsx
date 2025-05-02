import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import ExportStatus from '../components/ExportStatus';

interface LocationState {
  email: string;
}

const ExportStatusPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Récupérer l'email depuis l'état de navigation
    const state = location.state as LocationState;

    if (state && state.email) {
      setEmail(state.email);
    } else {
      // Si pas d'email, essayer de le récupérer du localStorage ou d'une autre source
      const savedEmail = localStorage.getItem('userEmail');

      if (savedEmail) {
        setEmail(savedEmail);
      } else {
        // Si vraiment aucun email disponible, rediriger vers la page de connexion
        setError("Impossible de suivre l'exportation. Veuillez vous reconnecter.");
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      }
    }
  }, [location, navigate]);

  // Gérer la fin de l'exportation
  const handleExportComplete = () => {
    navigate('/home');
  };

  // Gérer les erreurs d'exportation
  const handleExportError = (message: string) => {
    setError(message);
    // Attendre un peu avant de rediriger
    setTimeout(() => {
      navigate('/login');
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Exportation des emails
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Veuillez patienter pendant que nous préparons vos données
          </p>
        </div>

        {error ? (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-lg mb-4 dark:bg-red-900 dark:text-red-300">
            {error}
            <p className="mt-2 text-sm">Redirection vers la page de connexion...</p>
          </div>
        ) : email ? (
          <ExportStatus
            email={email}
            onComplete={handleExportComplete}
            onError={handleExportError}
          />
        ) : (
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
          </div>
        )}

        <div className="mt-6 text-center">
          <button
            onClick={() => navigate('/login')}
            className="text-blue-500 hover:underline dark:text-blue-400"
          >
            Retour à la page de connexion
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default ExportStatusPage;