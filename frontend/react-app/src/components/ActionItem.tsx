import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FaCheck,
  FaTimes,
  FaReply,
  FaPaperPlane,
  FaClock,
  FaUser,
  FaExclamationCircle
} from 'react-icons/fa';
import { Email } from './types';

// Composant pour les boutons d'action avec étiquette et icône
const ActionButton = ({
  icon: Icon,
  label,
  onClick,
  color,
  fullWidth = false
}: {
  icon: React.ComponentType<{ className?: string }>; 
  label: string;
  onClick: () => void;
  color: string;
  fullWidth?: boolean;
}) => (
  <motion.button
    whileHover={{ scale: 1.03 }}
    whileTap={{ scale: 0.97 }}
    className={`flex items-center justify-center space-x-2 px-4 py-2 rounded-lg 
    ${color} text-white transition-all duration-200 hover:shadow-md
    ${fullWidth ? 'w-full' : 'flex-1'}`}
    onClick={onClick}
  >
    <Icon className="w-4 h-4" />
    <span className="text-sm font-medium">{label}</span>
  </motion.button>
);

interface ActionItemProps {
  email: Email;
  actionNumber: number;
  totalActions: number;
  totalProgress: string;
}

const ActionItem: React.FC<ActionItemProps> = ({
  email,
  actionNumber,
  totalActions,
  totalProgress
}) => {
  const [isReplying, setIsReplying] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [confirmationType, setConfirmationType] = useState<string | null>(null);

  const handleAction = (type: string) => {
    setConfirmationType(type);
    setShowConfirmation(true);
    setTimeout(() => {
      setShowConfirmation(false);
      setConfirmationType(null);
    }, 2000);
  };

  // Formatter la date pour un affichage localisé
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).format(date);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative bg-white dark:bg-gray-800 rounded-xl shadow-sm mb-4 overflow-hidden"
    >
      {/* Badge de progression - repositionné et agrandi */}
      <div className="absolute top-0 right-0 bg-blue-500 text-white px-3 py-1 rounded-bl-lg text-sm font-semibold z-10">
        {totalProgress}
      </div>

      {/* En-tête avec priorité */}
      <div className="p-4 pb-2 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-center space-x-2 mb-1">
          <div className="w-2 h-2 rounded-full bg-red-500"></div>
          <h3 className="font-semibold text-gray-800 dark:text-white text-lg">
            {email.Subject}
          </h3>
        </div>

        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-300">
            <FaUser className="w-3.5 h-3.5" />
            <span>{email.From}</span>
          </div>

          <div className="flex items-center space-x-1 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <FaClock className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatDate(email.Date)}
            </span>
          </div>
        </div>
      </div>

      {/* Corps du message */}
      <div className="p-4">
        <div className="prose dark:prose-invert prose-sm max-w-none mb-4">
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">
            {typeof email.Body === 'string'
              ? email.Body
              : email.Body?.plain || email.Body?.html || ""}
          </p>
        </div>
      </div>

      {/* Boutons d'action - redesignés pour meilleur espacement */}
      <div className="p-4 pt-0 space-y-3">
        <div className="grid grid-cols-2 gap-3">
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

        {/* Bouton de réponse */}
        <ActionButton
          icon={isReplying ? FaTimes : FaReply}
          label={isReplying ? "Annuler" : "Répondre"}
          color="bg-blue-500 hover:bg-blue-600"
          fullWidth={true}
          onClick={() => setIsReplying(!isReplying)}
        />

        {/* Section réponse avec animation */}
        <AnimatePresence>
          {isReplying && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="space-y-3 mt-3"
            >
              <textarea
                className="w-full p-3 rounded-lg bg-gray-50 dark:bg-gray-700
                border border-gray-200 dark:border-gray-600
                focus:ring-2 focus:ring-blue-500 focus:border-transparent
                text-gray-700 dark:text-gray-300 text-sm"
                placeholder="Votre réponse..."
                rows={4}
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
              />
              <ActionButton
                icon={FaPaperPlane}
                label="Envoyer"
                color="bg-blue-500 hover:bg-blue-600"
                fullWidth={true}
                onClick={() => handleAction('replied')}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Message de confirmation */}
      <AnimatePresence>
        {showConfirmation && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`absolute top-3 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-lg text-white shadow-lg ${
              confirmationType === 'accepted' ? 'bg-green-500' :
              confirmationType === 'rejected' ? 'bg-red-500' :
              'bg-blue-500'
            }`}
          >
            <div className="flex items-center space-x-2">
              <FaExclamationCircle className="w-4 h-4" />
              <span>
                {confirmationType === 'accepted' && "Email accepté !"}
                {confirmationType === 'rejected' && "Email refusé"}
                {confirmationType === 'replied' && "Réponse envoyée !"}
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default ActionItem;