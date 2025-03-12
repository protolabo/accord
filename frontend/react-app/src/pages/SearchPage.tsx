import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaSearch, FaArrowLeft, FaClock, FaShare } from 'react-icons/fa';

const SearchPage = () => {
  // Utilisez useNavigate si vous êtes dans le contexte Router
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');

  // Données simulées pour les catégories
  const categories = [
    { id: 'recent', title: 'Recently Viewed', icon: <FaClock /> },
    { id: 'shared', title: 'Recently Shared', icon: <FaShare /> }
  ];

  // Suggestions de recherche
  const suggestions = [
    "One Year Ago",
    "Pescadero in the Summer",
    "Scooter in 2024"
  ];

  const handleBackToHome = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 pt-6">
      {/* En-tête */}
      <div className="flex items-center justify-between px-4 py-2">
        <button
          onClick={handleBackToHome}
          className="text-blue-500 font-medium"
        >
          <FaArrowLeft className="inline mr-1" /> Retour
        </button>
        <h1 className="text-xl font-bold text-center flex-1">Search</h1>
        <button className="text-blue-500 font-medium">Done</button>
      </div>

      <div className="px-4 py-6">
        {/* Section des catégories */}
        <h2 className="text-lg font-semibold mb-3">Recents</h2>
        <div className="flex space-x-4 mb-6 overflow-x-auto pb-2">
          {categories.map(category => (
            <div key={category.id} className="flex-shrink-0">
              <div className="w-24 h-24 bg-gray-200 rounded-lg overflow-hidden">
                {/* Ici vous afficheriez une image */}
                <div className="w-full h-full flex items-center justify-center text-gray-500">
                  {category.icon}
                </div>
              </div>
              <p className="text-xs text-center mt-1">{category.title}</p>
            </div>
          ))}
        </div>

        {/* Section des suggestions */}
        <div className="space-y-2 mb-6">
          {suggestions.map((suggestion, index) => (
            <div
              key={index}
              className="bg-gray-200 dark:bg-gray-700 rounded-full px-4 py-2 inline-block mr-2 mb-2"
            >
              <span className="text-gray-800 dark:text-white">"{suggestion}"</span>
            </div>
          ))}
        </div>

        {/* Barre de recherche */}
        <div className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search your library..."
            className="w-full bg-gray-200 dark:bg-gray-700 rounded-full py-3 pl-10 pr-4
                     text-gray-800 dark:text-white placeholder-gray-500"
          />
          <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" />
        </div>
      </div>
    </div>
  );
};

export default SearchPage;