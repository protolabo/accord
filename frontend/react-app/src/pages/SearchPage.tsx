import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaSearch, FaArrowLeft, FaClock, FaShare } from 'react-icons/fa';
import CategorySection from '../components/search/CategorySection';
import SuggestionSection from "../components/search/SuggestionSection";

const SearchPage = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
 const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Suggestions de recherche
  const suggestions = [
    '"Affiche mes mails du 19 janvier"',
    '"Mails de Paul concernant le projet marketing"',
    '"Factures du mois dernier"',
    '"Réunions planifiées pour demain"',
    '"Emails non lus cette semaine"'
  ];

  const handleBackToHome = () => {
    navigate('/');
  };
  // Fonction pour gérer le clic sur une suggestion
   const handleSuggestionClick = (suggestion: string) => {
    setSearchTerm(suggestion);
    // déclenche la recherche
    // handleSearch(suggestion);
  };
   // Fonction de recherche
  const handleSearch = () => {
    console.log(`Recherche pour: ${searchTerm}`);
  };

    return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 shadow-sm">
        <button
          onClick={handleBackToHome}
          className="text-blue-500 font-medium flex items-center"
        >
          <FaArrowLeft className="mr-1" />
          <span>Retour</span>
        </button>
        <h1 className="text-xl font-bold text-gray-800 dark:text-white flex-1 text-center">
          Recherche
        </h1>
      </div>

      <div className="p-4 space-y-6">

        <CategorySection
          selectedCategory={selectedCategory}
          setSelectedCategory={setSelectedCategory}
        />

        <SuggestionSection
          suggestions={suggestions}
          onSuggestionClick={handleSuggestionClick}
        />

        {/* Barre de recherche */}
        <div className="relative mt-6">
          <FaSearch
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500"
            onClick={handleSearch}
          />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Ecrivez quelque chose..."
            className="w-full bg-gray-200 dark:bg-gray-700 rounded-full py-3 pl-10 pr-4
                     text-gray-800 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch();
              }
            }}
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
            >
              ×
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchPage;