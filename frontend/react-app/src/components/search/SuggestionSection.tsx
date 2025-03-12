import React from 'react';
import { motion } from 'framer-motion';
import { FaQuoteLeft } from 'react-icons/fa';

interface SuggestionSectionProps {
  suggestions: string[];
  onSuggestionClick: (suggestion: string) => void;
}

const SuggestionSection: React.FC<SuggestionSectionProps> = ({
  suggestions,
  onSuggestionClick
}) => {
  return (
  <div className="mb-6">
    <h2 className="text-lg font-medium mb-3 text-gray-800 dark:text-gray-200">Suggestions</h2>

    <div className="space-y-2">
      {suggestions.map((suggestion, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onSuggestionClick(suggestion)}
          className="bg-gray-200 dark:bg-gray-700 rounded-lg px-3 py-2 cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors w-1/4"
          // Padding réduit: px-4→px-3 et py-3→py-2
        >
          <div className="flex items-center">
            <span className="text-sm text-gray-800 dark:text-white">
              {suggestion}
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  </div>
);
};

export default SuggestionSection;