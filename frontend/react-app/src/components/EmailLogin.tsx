import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import EmailServiceSelector from "./EmailServiceSelector";
import emailAPIService, {
  EmailService,
  UserProfile,
} from "../services/EmailService";

interface EmailLoginProps {
  onLogin: () => void;
}

const EmailLogin: React.FC<EmailLoginProps> = ({ onLogin }) => {
  const [service, setService] = useState<EmailService | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    // Listen for messages from the popup window
    const handleAuthMessage = (event: MessageEvent) => {
      // Only accept messages from the same origin
      if (event.origin !== window.location.origin) return;

      if (
        event.data &&
        event.data.type === "auth_callback" &&
        event.data.code
      ) {
        handleAuthCallback(event.data.code);
      }
    };

    window.addEventListener("message", handleAuthMessage);

    // Check for OAuth callback in URL (in case we're not using popup)
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    const service = emailAPIService.getService();

    if (code && service) {
      handleAuthCallback(code);

      // Remove code from URL without refreshing
      const url = new URL(window.location.href);
      url.searchParams.delete("code");
      window.history.replaceState({}, document.title, url.toString());
    } else if (emailAPIService.isAuthenticated()) {
      // Already authenticated, try to get user profile
      fetchUserProfile();
    }

    return () => {
      window.removeEventListener("message", handleAuthMessage);
    };
  }, []);

  const handleAuthCallback = async (code: string) => {
    setIsLoading(true);
    setError(null);

    try {
      await emailAPIService.handleAuthCallback(code);

      // Fetch user profile
      await fetchUserProfile();

      onLogin();
    } catch (error) {
      console.error("Auth callback error:", error);
      setError("Échec de l'authentification. Veuillez réessayer.");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUserProfile = async () => {
    try {
      if (emailAPIService.isAuthenticated()) {
        const profile = await emailAPIService.getUserProfile();
        setUserProfile(profile);
      }
    } catch (error) {
      console.error("Error fetching user profile:", error);
      // Token might be expired, clear it
      emailAPIService.clearTokens();
    }
  };

  const handleServiceSelect = (selectedService: EmailService) => {
    setService(selectedService);
  };

  const handleLogout = () => {
    emailAPIService.clearTokens();
    setUserProfile(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 max-w-md w-full mx-auto"
    >
      <h2 className="text-2xl font-bold text-center mb-6 dark:text-white">
        Connectez-vous à votre messagerie
      </h2>

      {userProfile ? (
        <div className="flex flex-col items-center">
          <div className="mb-4 text-center">
            {userProfile.picture && (
              <img
                src={userProfile.picture}
                alt={userProfile.name}
                className="w-16 h-16 rounded-full mx-auto mb-2"
              />
            )}
            <h3 className="text-lg font-semibold dark:text-white">
              {userProfile.name || userProfile.email}
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              {userProfile.email}
            </p>
          </div>

          <div className="flex space-x-4 mt-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              onClick={onLogin}
            >
              Continuer
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-white"
              onClick={handleLogout}
            >
              Se déconnecter
            </motion.button>
          </div>
        </div>
      ) : (
        <>
          {error && (
            <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
              {error}
            </div>
          )}

          <EmailServiceSelector
            onServiceSelect={handleServiceSelect}
            className="mb-6"
          />

          {isLoading && (
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          )}
        </>
      )}
    </motion.div>
  );
};

export default EmailLogin;
