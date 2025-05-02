import React, { useState, FormEvent } from "react";
import { motion } from "framer-motion";
import emailAPIService from "../services/EmailService";

interface ComposePopupProps {
  onClose: () => void;
  onSend: () => void;
  onRecipientChange: () => void;
  recipientAvailability?: number;
}

const ComposePopup: React.FC<ComposePopupProps> = ({
  onClose,
  onSend,
  onRecipientChange,
  recipientAvailability
}) => {
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!emailAPIService.isAuthenticated()) {
      alert("Veuillez vous connecter pour envoyer un email");
      return;
    }

    // Get form data
    const formData = new FormData(e.currentTarget);
    const to = (formData.get("to") as string)
      .split(",")
      .map((e) => e.trim());
    const cc = (formData.get("cc") as string)
      .split(",")
      .map((e) => e.trim());
    const subject = formData.get("subject") as string;
    const body = formData.get("body") as string;

    try {
      const result = await emailAPIService.sendEmail({
        body_type: "",
        subject,
        from: "", // The API will use the authenticated user's email
        to,
        cc,
        body,
        bodyType: "text",
        attachments: [],
        categories: [],
        importance: "normal",
        isRead: true
      });

      if (result.success) {
        alert("Message envoyé avec succès!");
        onSend();
      } else {
        alert("Échec de l'envoi du message. Veuillez réessayer.");
      }
    } catch (error) {
      console.error("Error sending email:", error);
      alert("Une erreur s'est produite lors de l'envoi du message.");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed bottom-24 right-6 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-xl z-50"
    >
      <div className="p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold dark:text-white">
            Nouveau message
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
          >
            ×
          </button>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <input
              type="email"
              name="to"
              placeholder="À"
              className="w-full px-3 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
              onChange={onRecipientChange}
              required
            />
          </div>

          <div>
            <input
              type="email"
              name="cc"
              placeholder="Cc"
              className="w-full px-3 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
            />
          </div>

          <div>
            <input
              type="text"
              name="subject"
              placeholder="Objet"
              className="w-full px-3 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
              required
            />
          </div>

          {recipientAvailability !== undefined && (
            <div className="flex items-center space-x-2">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Disponibilité du destinataire:
              </div>
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full transition-all duration-300"
                  style={{
                    width: `${recipientAvailability}%`,
                    backgroundColor: `hsl(${recipientAvailability}, 70%, 50%)`,
                  }}
                />
              </div>
            </div>
          )}

          <textarea
            name="body"
            placeholder="Message"
            rows={4}
            className="w-full px-3 py-2 border dark:border-gray-600 rounded-lg resize-none dark:bg-gray-700 dark:text-white"
            required
          />

          <div className="flex justify-end">
            <motion.button
              type="submit"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Envoyer
            </motion.button>
          </div>
        </form>
      </div>
    </motion.div>
  );
};

export default ComposePopup;