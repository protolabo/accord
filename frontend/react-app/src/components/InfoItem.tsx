import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FaInfoCircle,
  FaClock,
  FaUser,
  FaTags,
  FaChevronDown,
  FaChevronUp,
  FaBookmark,
  FaRegBookmark
} from 'react-icons/fa';

interface InfoItemProps {
  email: {
    "Message-ID": string;
    Subject: string;
    From: string;
    Date: string;
    Body: string | { plain?: string; html?: string };
    Categories: string[];
    accord_sub_classes?: Array<[string, number]>;
  };
  infoNumber: number;
  totalInfo: number;
}

const InfoItem: React.FC<InfoItemProps> = ({ email, infoNumber, totalInfo }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);

  // Format de date amélioré
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);

    const isToday = date.toDateString() === now.toDateString();
    const isYesterday = date.toDateString() === yesterday.toDateString();

    const timeFormat = new Intl.DateTimeFormat('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);

    const dateFormat = new Intl.DateTimeFormat('fr-FR', {
      day: '2-digit',
      month: 'short'
    }).format(date);

    if (isToday) {
      return `Aujourd'hui, ${timeFormat}`;
    } else if (isYesterday) {
      return `Hier, ${timeFormat}`;
    } else {
      return `${dateFormat}, ${timeFormat}`;
    }
  };

  // Préparation du contenu du corps du message
  const getEmailBody = () => {
    if (typeof email.Body === 'string') {
      return email.Body;
    } else if (email.Body) {
      return email.Body.plain || email.Body.html || "";
    }
    return "";
  };

  // Extraction du nom d'utilisateur à partir de l'adresse email
  const extractName = (emailAddress: string) => {
    if (emailAddress.includes('@')) {
      const namePart = emailAddress.split('@')[0];
      return namePart
        .split(/[._]/)
        .map(part => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
    }
    return emailAddress;
  };

  // Prendre les 3 premières sous-catégories avec les scores les plus élevés
  const topSubCategories = email.accord_sub_classes
    ? [...email.accord_sub_classes]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
    : [];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden mb-4"
    >
      {/* Section principale qui est toujours visible */}
      <div className="p-4 relative">
        <div className="absolute left-0 top-0 bg-blue-500 text-white px-3 py-1 rounded-br-lg text-sm font-semibold">
          {infoNumber}/{totalInfo}
        </div>

        <div className="ml-20 mr-16">
          {/* Sujet de l'email */}
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-2 line-clamp-2">
            {email.Subject}
          </h3>

          {/* Affichage des sous-catégories */}
          {topSubCategories.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {topSubCategories.map(([category, score], index) => (
                <span
                  key={index}
                  className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full"
                  title={`Score: ${Math.round(score * 100)}%`}
                >
                  {category}
                </span>
              ))}
            </div>
          )}

          {/* Informations sur l'expéditeur et la date */}
          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
            <div className="flex items-center space-x-1">
              <FaUser className="w-3.5 h-3.5" />
              <span title={email.From}>{extractName(email.From)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <FaClock className="w-3.5 h-3.5" />
              <span>{formatDate(email.Date)}</span>
            </div>
          </div>
        </div>

        {/* Boutons d'action */}
        <div className="absolute right-4 top-4 flex flex-col space-y-2">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsBookmarked(!isBookmarked)}
            className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600"
            title={isBookmarked ? "Retirer le signet" : "Ajouter un signet"}
          >
            {isBookmarked ? (
              <FaBookmark className="w-4 h-4 text-blue-500" />
            ) : (
              <FaRegBookmark className="w-4 h-4 text-gray-400 dark:text-gray-500" />
            )}
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600"
            title={isExpanded ? "Réduire" : "Développer"}
          >
            {isExpanded ? (
              <FaChevronUp className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            ) : (
              <FaChevronDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            )}
          </motion.button>
        </div>
      </div>

      {/* Contenu détaillé qui s'affiche lorsque l'élément est développé */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-gray-100 dark:border-gray-700"
          >
            <div className="p-4">
              {/* En-tête d'information */}
              <div className="flex items-center space-x-2 mb-3">
                <FaInfoCircle className="w-5 h-5 text-blue-500" />
                <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                  Information importante
                </span>
              </div>

              {/* Corps du message */}
              <div className="prose dark:prose-invert max-w-none">
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">
                  {getEmailBody()}
                </p>
              </div>

              {/* Catégories */}
              {email.Categories && email.Categories.length > 0 && (
                <div className="mt-4 flex items-start gap-2">
                  <FaTags className="w-4 h-4 text-gray-400 mt-1" />
                  <div className="flex flex-wrap gap-2">
                    {email.Categories.map((category, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-gray-100 dark:bg-gray-700
                        text-gray-600 dark:text-gray-300 rounded-full text-sm"
                      >
                        {category}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Pied de message avec métadonnées */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 text-sm text-gray-500 dark:text-gray-400">
              <div className="truncate">
                Message ID: {email["Message-ID"]}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default InfoItem;