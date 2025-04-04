import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { FaGoogle, FaMicrosoft } from "react-icons/fa";
import emailAPIService, { EmailService } from "../services/EmailService";

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

  useEffect(() => {
    // Check if a service is already selected
    const currentService = emailAPIService.getService();
    if (currentService) {
      setSelectedService(currentService);
    }
  }, []);

  const handleServiceSelect = async (service: EmailService) => {
    try {
      setSelectedService(service);
      emailAPIService.setService(service);
      onServiceSelect(service);

      // If not authenticated, redirect to auth URL
      if (!emailAPIService.isAuthenticated()) {
        const authUrl = await emailAPIService.getAuthUrl();
        window.location.href = authUrl;
      }
    } catch (error) {
      console.error("Error selecting service:", error);
    }
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
        >
          <FaMicrosoft className="text-3xl mb-2" />
          <span>Outlook</span>
        </motion.button>
      </div>
    </div>
  );
};

export default EmailServiceSelector;
