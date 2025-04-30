import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FaInbox,
  FaChevronRight,
  FaClock,
  FaUser,
  FaTag,
  FaArchive,
  FaStar,
  FaRegStar
} from 'react-icons/fa';
import type { Email } from './types';

interface ThreadCategoryProps {
  category: string;
  emails: Email[];
  expanded: boolean;
  onToggle: () => void;
  index: number;
  totalCategories: number;
  onThreadSelect: (email: Email) => void;
}

interface ThreadStatus {
  color: string;
  text: string;
}

const ThreadCategory: React.FC<ThreadCategoryProps> = ({
  category,
  emails,
  expanded,
  onToggle,
  index,
  totalCategories,
  onThreadSelect
}) => {
  const [starredThreads, setStarredThreads] = useState<Set<string>>(new Set());

  const toggleStar = (emailId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newStarred = new Set(starredThreads);
    if (starredThreads.has(emailId)) {
      newStarred.delete(emailId);
    } else {
      newStarred.add(emailId);
    }
    setStarredThreads(newStarred);
  };

  const getThreadStatus = (date: string): ThreadStatus => {
    const now = new Date();
    const emailDate = new Date(date);
    const diffDays = Math.round((now.getTime() - emailDate.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 1) return { color: 'bg-green-500', text: 'Nouveau' };
    if (diffDays < 3) return { color: 'bg-yellow-500', text: 'Récent' };
    if (diffDays < 7) return { color: 'bg-orange-500', text: 'Cette semaine' };
    return { color: 'bg-gray-500', text: 'Plus ancien' };
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden mb-4"
    >
      {/* Header de la catégorie */}
      <motion.div
        onClick={onToggle}
        className="flex items-center justify-between p-4 cursor-pointer
        bg-gray-50 dark:bg-gray-700 border-b dark:border-gray-600"
      >
        <div className="flex items-center space-x-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900">
            <FaInbox className="w-4 h-4 text-blue-500 dark:text-blue-300" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
              {category}
            </h3>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {emails.length} messages • Catégorie {index + 1}/{totalCategories}
            </span>
          </div>
        </div>
        <motion.div
          animate={{ rotate: expanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <FaChevronRight className="w-5 h-5 text-gray-400" />
        </motion.div>
      </motion.div>

      {/* Liste des emails */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {emails.map((email) => {
                const status = getThreadStatus(email.Date);
                return (
                  <motion.div
                    key={email["Message-ID"]}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700
                    transition-colors duration-200 cursor-pointer"
                    onClick={() => onThreadSelect(email)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={(e) => toggleStar(email["Message-ID"], e)}
                            className="text-gray-400 hover:text-yellow-400
                            dark:text-gray-500 dark:hover:text-yellow-400"
                          >
                            {starredThreads.has(email["Message-ID"]) ? (
                              <FaStar className="w-5 h-5 text-yellow-400" />
                            ) : (
                              <FaRegStar className="w-5 h-5" />
                            )}
                          </motion.button>
                          <div className={`flex-shrink-0 w-2 h-2 rounded-full ${status.color}`} />
                          <h4 className="font-medium text-gray-900 dark:text-white truncate">
                            {email.Subject}
                          </h4>
                        </div>
                        <div className="mt-1 flex items-center space-x-4">
                          <span className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                            <FaUser className="w-4 h-4 mr-1" />
                            {email.From}
                          </span>
                          <span className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                            <FaClock className="w-4 h-4 mr-1" />
                            {new Date(email.Date).toLocaleDateString()}
                          </span>
                          <span className="text-xs px-2 py-1 rounded-full bg-gray-100
                          dark:bg-gray-600 text-gray-600 dark:text-gray-300">
                            {status.text}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
                          {typeof email.Body === 'string'
                              ? email.Body
                              : (email.Body?.plain || email.Body?.html || "")}
                        </p>
                      </div>

                      <div className="ml-4 flex-shrink-0 flex flex-col items-end space-y-2">
                        <motion.button
                            whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          className="p-2 rounded-full hover:bg-gray-100
                          dark:hover:bg-gray-600 text-gray-400 dark:text-gray-500"
                        >
                          <FaArchive className="w-4 h-4" />
                        </motion.button>
                        <div className="flex flex-wrap gap-1">
                          {email.Categories.map((cat, idx) => (
                            <div
                              key={idx}
                              className="flex items-center text-xs px-2 py-1
                              rounded-full bg-blue-100 dark:bg-blue-900
                              text-blue-600 dark:text-blue-300"
                            >
                              <FaTag className="w-3 h-3 mr-1" />
                              {cat}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default ThreadCategory;