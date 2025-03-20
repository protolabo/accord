import React from "react";
import { motion } from "framer-motion";
import { FaMicrosoft, FaGoogle } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

interface LoginProps {}

const Login: React.FC<LoginProps> = () => {
  const navigate = useNavigate();

  const handleOutlookLogin = () => {
    // TODO: Implement Outlook OAuth
    console.log("Outlook login");
    navigate("/home");
  };

  const handleGmailLogin = () => {
    // TODO: Implement Gmail OAuth
    console.log("Gmail login");
    navigate("/home");
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center p-4">
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

        <div className="space-y-4">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleOutlookLogin}
            className="w-full flex items-center justify-center space-x-3 px-4 py-3 bg-[#0078d4] hover:bg-[#006abc] text-white rounded-lg transition-colors"
          >
            <FaMicrosoft className="text-xl" />
            <span>Continuer avec Outlook</span>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleGmailLogin}
            className="w-full flex items-center justify-center space-x-3 px-4 py-3 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 rounded-lg transition-colors"
          >
            <FaGoogle className="text-xl text-[#4285f4]" />
            <span>Continuer avec Gmail</span>
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
    </div>
  );
};

export default Login;
