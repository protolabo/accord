import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface ExportStatusProps {
  email: string;
  onComplete?: () => void;
  onError?: (message: string) => void;
}

interface StatusData {
  status: 'not_started' | 'processing' | 'completed' | 'error';
  message: string;
  progress: number;
  updated_at: number;
  extra: Record<string, any>;
}

const ExportStatus: React.FC<ExportStatusProps> = ({ email, onComplete, onError }) => {
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let pollingInterval: NodeJS.Timeout;

    const checkExportStatus = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/export/gmail/status?email=${encodeURIComponent(email)}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          setStatusData(data);
          setIsLoading(false);

          if (data.status === 'completed') {
            // Arrêter le polling et passer à l'écran suivant
            clearInterval(pollingInterval);
            if (onComplete) {
              onComplete();
            } else {
              // Rediriger par défaut vers la page d'accueil
              navigate('/home');
            }
          } else if (data.status === 'error') {
            // Gérer l'erreur
            clearInterval(pollingInterval);
            if (onError) {
              onError(data.message);
            }
          }
          // Si status est 'processing', continuer le polling
        } else {
          setIsLoading(false);
          const errorData = await response.json();
          if (onError) {
            onError(errorData.detail || 'Une erreur est survenue lors de la vérification du statut');
          }
        }
      } catch (error) {
        setIsLoading(false);
        console.error('Erreur lors de la vérification du statut:', error);
        if (onError) {
          onError('Erreur de connexion lors de la vérification du statut');
        }
      }
    };

    // Vérifier immédiatement une première fois
    checkExportStatus();

    // Puis démarrer le polling toutes les 2 secondes
    pollingInterval = setInterval(checkExportStatus, 2000);

    // Nettoyer l'intervalle quand le composant est démonté
    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [email, navigate, onComplete, onError]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-6">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <p className="mt-4 text-lg">Chargement du statut...</p>
      </div>
    );
  }

  if (!statusData) {
    return (
      <div className="bg-yellow-100 text-yellow-800 p-4 rounded-lg">
        Impossible de récupérer le statut de l'exportation.
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-xl font-bold mb-4">Statut de l'exportation</h2>

      {statusData.status === 'not_started' && (
        <div className="bg-gray-100 text-gray-800 p-4 rounded-lg">
          <p>{statusData.message}</p>
        </div>
      )}

      {statusData.status === 'processing' && (
        <div className="bg-blue-50 text-blue-800 p-4 rounded-lg">
          <p className="mb-2">{statusData.message}</p>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full"
              style={{ width: `${statusData.progress}%` }}
            ></div>
          </div>
          <p className="mt-2 text-sm text-right">{statusData.progress}%</p>
        </div>
      )}

      {statusData.status === 'completed' && (
        <div className="bg-green-100 text-green-800 p-4 rounded-lg">
          <p>{statusData.message}</p>
          <button
            className="mt-4 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            onClick={() => navigate('/home')}
          >
            Accéder à ma boîte de réception
          </button>
        </div>
      )}

      {statusData.status === 'error' && (
        <div className="bg-red-100 text-red-800 p-4 rounded-lg">
          <p>{statusData.message}</p>
          <button
            className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            onClick={() => navigate('/login')}
          >
            Retour à la connexion
          </button>
        </div>
      )}
    </div>
  );
};

export default ExportStatus;