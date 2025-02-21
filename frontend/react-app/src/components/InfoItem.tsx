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

// @ts-ignore
const InfoItem = ({ email, infoNumber, totalInfo }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);

  // format de date
  const formatDate = (dateString: string | number | Date) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden mb-4"
    >

      <div className="relative bg-gray-50 dark:bg-gray-700 p-4">
        <div className="absolute -left-3 top-4 bg-blue-500 text-white px-3 py-1 rounded-r-full text-sm font-semibold">
          #{infoNumber}/{totalInfo}
        </div>

        <div className="flex justify-between items-start ml-16">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
              {email.Subject}
            </h3>
            <div className="flex items-center space-x-4 mt-1">
              <span className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                <FaUser className="mr-1 w-4 h-4" />
                {email.From}
              </span>
              <span className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                <FaClock className="mr-1 w-4 h-4" />
                {formatDate(email.Date)}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setIsBookmarked(!isBookmarked)}
              className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              {isBookmarked ? (
                <FaBookmark className="w-5 h-5 text-blue-500" />
              ) : (
                <FaRegBookmark className="w-5 h-5 text-gray-400 dark:text-gray-500" />
              )}
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              {isExpanded ? (
                <FaChevronUp className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              ) : (
                <FaChevronDown className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              )}
            </motion.button>
          </div>
        </div>
      </div>

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
              <div className="flex items-center space-x-2 mb-3">
                <FaInfoCircle className="w-5 h-5 text-blue-500" />
                <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                  Information importante
                </span>
              </div>

              <div className="prose dark:prose-invert max-w-none">
                <p className="text-gray-700 dark:text-gray-300">
                  {email.Body}
                </p>
              </div>

              {/* Catégories */}
              <div className="mt-4 flex items-center space-x-2">
                <FaTags className="w-4 h-4 text-gray-400" />
                <div className="flex flex-wrap gap-2">
                  {email.Categories.map((category: string | number | bigint | boolean | React.ReactElement<unknown, string | React.JSXElementConstructor<any>> | Iterable<React.ReactNode> | React.ReactPortal | Promise<string | number | bigint | boolean | React.ReactPortal | React.ReactElement<unknown, string | React.JSXElementConstructor<any>> | Iterable<React.ReactNode> | null | undefined> | null | undefined, index: React.Key | null | undefined) => (
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
            </div>

            {/* Pied de message avec métadonnées */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 flex justify-between items-center">
              <div className="text-sm text-gray-500 dark:text-gray-400">
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