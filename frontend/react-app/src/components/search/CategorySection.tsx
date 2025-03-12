import React from 'react';
import { motion } from 'framer-motion';
import { FaClock, FaShare, FaTrash, FaBan } from 'react-icons/fa';

interface CategorySectionProps {
  selectedCategory: string | null;
  setSelectedCategory: (category: string | null) => void;
}

const CategorySection: React.FC<CategorySectionProps> = ({ selectedCategory, setSelectedCategory }) => {
  const categories = [
    { id: 'recent', title: 'Consulté récemment', icon: <FaClock className="text-blue-500" />, count: 25 },
    { id: 'shared', title: 'Envoyé', icon: <FaShare className="text-green-500" />, count: 45 },
    { id: 'corbeille', title: 'Corbeille', icon: <FaTrash className="text-gray-500" />, count: 20 },
    { id: 'spam', title: 'Spam', icon: <FaBan className="text-red-500" />, count: 30 },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 mb-6"
    >
      <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">Catégories</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {categories.map(category => (
          <motion.div
            key={category.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              if (selectedCategory === category.id) {
                setSelectedCategory(null); // Désélectionner si déjà sélectionné
              } else {
                setSelectedCategory(category.id);
              }
            }}
            className={`flex items-center justify-between p-4 rounded-xl cursor-pointer border-2 
              ${selectedCategory === category.id
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'}`}
          >
            <div className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center 
                ${selectedCategory === category.id ? 'bg-blue-100 dark:bg-blue-800' : 'bg-gray-100 dark:bg-gray-700'}`}>
                {category.icon}
              </div>
              <span className="ml-3 font-medium text-gray-800 dark:text-white">{category.title}</span>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium 
              ${selectedCategory === category.id
                ? 'bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}`}>
              {category.count}
            </span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default CategorySection;