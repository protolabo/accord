import React, {useEffect, useState} from "react";
import { motion } from "framer-motion";
import { FaMicrosoft, FaGoogle } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import ExportStatus from "../components/ExportStatus";

interface LoginProps {}

const Login: React.FC<LoginProps> = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('user@accord.com');
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [showExportStatus, setShowExportStatus] = useState(false);

  const handleOutlookLogin = () => {
    navigate("/home");
  };

  useEffect(() => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      navigate('/home');
    }
  }, [navigate]);

  const handleGmailLogin = async () => {
  try {
    setIsProcessing(true);
    setErrorMessage('');

    // Check if we're in development mode
    const isDevelopment = false;

    if (isDevelopment) {
      // Development mode - Create a more structured mock token
      // This includes an expiration time and basic user data
      const now = Math.floor(Date.now() / 1000);
      const mockPayload = {
        email: email || 'user@example.com',
        user_id: 'dev-user-123',
        exp: now + 3600, // Expires in 1 hour
        iat: now,
      };

      // Base64 encode a minimal mock JWT (header.payload.signature)
      const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
      const payload = btoa(JSON.stringify(mockPayload));
      const signature = 'dev-signature';

      const mockToken = `${header}.${payload}.${signature}`;

      localStorage.setItem('jwt_token', mockToken);
      localStorage.setItem('userEmail', email || 'user@example.com');

      // Redirect to home
      navigate('/home');
    } else {
      // Production mode - Use real OAuth login
      // This initiates the OAuth flow, redirecting to Google
      const response = await fetch('http://localhost:8000/auth/gmail');

      if (!response.ok) {
        throw new Error('Failed to start authentication');
      }

      const data = await response.json();
      // Redirect to Google's OAuth page
      window.location.href = data.auth_url;

      // The rest of the flow will be handled by the callback route
    }
  } catch (error) {
    console.error('Erreur lors de l\'authentification:', error);
    setErrorMessage('Une erreur de connexion est survenue. Veuillez réessayer.');
    setIsProcessing(false);
  }
};

  // Fonction appelée lorsque l'exportation est terminée avec succès
  const handleExportComplete = () => {
    navigate('/home');
  };

  // Fonction appelée en cas d'erreur lors de l'exportation
  const handleExportError = (message: string) => {
    setErrorMessage(message);
    setShowExportStatus(false);
    setIsProcessing(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center p-4">
      {!showExportStatus ? (
        // Écran de connexion normal
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 max-w-md w-full"
        >
          <div className="text-center mb-8">
            <motion.h1
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              className="text-3xl font-bold text-gray-900 dark:text-white mb-2"
            >
              Accord
            </motion.h1>
            <p className="text-gray-600 dark:text-gray-400">
              Connectez-vous avec votre compte email
            </p>
          </div>



          {/* Message d'erreur */}
          {errorMessage && (
            <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 dark:bg-red-900 dark:text-red-300">
              {errorMessage}
            </div>
          )}

          <div className="space-y-4">
            <motion.button
              whileHover={{ scale: isProcessing ? 1 : 1.02 }}
              whileTap={{ scale: isProcessing ? 1 : 0.98 }}
              onClick={handleOutlookLogin}
              disabled={isProcessing}
              className={`w-full flex items-center justify-center space-x-3 px-4 py-3 
              ${isProcessing 
                ? 'bg-gray-300 cursor-not-allowed' 
                : 'bg-[#0078d4] hover:bg-[#006abc]'} 
              text-white rounded-lg transition-colors`}
            >
              <FaMicrosoft className="text-xl" />
              <span>Continuer avec Outlook</span>
            </motion.button>

            <motion.button
              whileHover={{ scale: isProcessing ? 1 : 1.02 }}
              whileTap={{ scale: isProcessing ? 1 : 0.98 }}
              onClick={handleGmailLogin}
              disabled={isProcessing}
              className={`w-full flex items-center justify-center space-x-3 px-4 py-3 
              ${isProcessing 
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                : 'bg-white hover:bg-gray-50 text-gray-700'} 
              border border-gray-300 rounded-lg transition-colors`}
            >
              {isProcessing ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-500 mr-2"></div>
              ) : (
                <FaGoogle className="text-xl text-[#4285f4]" />
              )}
              <span>{isProcessing ? 'Connexion en cours...' : 'Continuer avec Gmail'}</span>
            </motion.button>
          </div>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              En vous connectant, vous acceptez nos{" "}
              <a href="#" className="text-blue-500 hover:underline">
                conditions d'utilisation
              </a>
            </p>
          </div>
        </motion.div>
      ) : (
        <div className="w-full max-w-md">
          <ExportStatus
            email={email}
            onComplete={handleExportComplete}
            onError={handleExportError}
          />
        </div>
      )}
    </div>
  );
};

export default Login;