import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FaCheck,
  FaTimes,
  FaReply,
  FaPaperPlane,
  FaClock,
  FaBell,
  FaListOl
} from 'react-icons/fa';

// @ts-ignore
const ActionButton = ({ icon: Icon, label, onClick, color }) => (
  <motion.button
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
    className={`flex items-center justify-center space-x-2 px-4 py-2 rounded-lg 
    ${color} text-white transition-all duration-200 hover:shadow-lg w-full`}
    onClick={onClick}
  >
    <Icon className="w-4 h-4" />
    <span className="text-sm font-medium">{label}</span>
  </motion.button>
);

// @ts-ignore
const ActionItem = ({ email, actionNumber, totalActions, totalProgress }) => {
  const [isReplying, setIsReplying] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [confirmationType, setConfirmationType] = useState(null);

  const handleAction = (type: string | React.SetStateAction<null>) => {
    // @ts-ignore
    setConfirmationType(type);
    setShowConfirmation(true);
    setTimeout(() => {
      setShowConfirmation(false);
      setConfirmationType(null);
    }, 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4 space-y-4 mb-4"
    >
      {/* Indicateur de progression */}
      <div className="absolute -top-3 right-4 bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
        {totalProgress}
      </div>

      {/* En-tête */}
      <div className="flex justify-between items-start mt-4">
        <div>
          <h3 className="font-semibold text-gray-800 dark:text-white">
            {email.Subject}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            De: {email.From}
          </p>
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
          <FaClock className="mr-1" />
          {new Date(email.Date).toLocaleDateString()}
        </span>
      </div>

      <p className="text-sm text-gray-700 dark:text-gray-300">
        {email.Body}
      </p>

      {/* Boutons d'action */}
      <div className="grid grid-cols-2 gap-2">
        <ActionButton
          icon={FaCheck}
          label="Accepter"
          color="bg-green-500 hover:bg-green-600"
          onClick={() => handleAction('accepted')}
        />
        <ActionButton
          icon={FaTimes}
          label="Refuser"
          color="bg-red-500 hover:bg-red-600"
          onClick={() => handleAction('rejected')}
        />
      </div>

      {/* Section réponse */}
      <div>
        <ActionButton
          icon={isReplying ? FaTimes : FaReply}
          label={isReplying ? "Annuler" : "Répondre"}
          color="bg-blue-500 hover:bg-blue-600"
          onClick={() => setIsReplying(!isReplying)}
        />

        <AnimatePresence>
          {isReplying && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-2 space-y-2"
            >
              <textarea
                className="w-full p-2 rounded-lg bg-gray-50 dark:bg-gray-700
                border border-gray-200 dark:border-gray-600
                focus:ring-2 focus:ring-blue-500 focus:border-transparent
                text-gray-700 dark:text-gray-300"
                placeholder="Votre réponse..."
                rows={3}
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
              />
              <ActionButton
                icon={FaPaperPlane}
                label="Envoyer"
                color="bg-blue-500 hover:bg-blue-600"
                onClick={() => handleAction('replied')}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Confirmation */}
      <AnimatePresence>
        {showConfirmation && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`absolute top-2 right-2 px-4 py-2 rounded-lg text-white ${
              confirmationType === 'accepted' ? 'bg-green-500' :
              confirmationType === 'rejected' ? 'bg-red-500' :
              'bg-blue-500'
            }`}
          >
            {confirmationType === 'accepted' && "Email accepté !"}
            {confirmationType === 'rejected' && "Email refusé"}
            {confirmationType === 'replied' && "Réponse envoyée !"}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default ActionItem;