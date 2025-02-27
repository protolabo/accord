import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FaBell,
  FaUser,
  FaExpand,
  FaCompress,
  FaMoon,
  FaSun,
  FaSearch,
  FaArrowLeft,
} from "react-icons/fa";
import { twMerge } from "tailwind-merge";
import AttentionGauge from "../components/AttentionGauge";
import ActionItem from "../components/ActionItem";
import InfoItem from "../components/InfoItem";
import ThreadSection from "../pages/ThreadSection";
import ThreadDetail from "../components/ThreadDetail";
import { mockEmails, mockNotifications, mockPriorityLevels } from "../data/mockData";
import type { Email } from "../components/types";

interface HomeState {
  searchTerm: string;
  darkMode: boolean;
  availability: number;
  sectionSizes: {
    [key: string]: number;
  };
  isAvailable: boolean;
  showNotifications: boolean;
  showProfileOptions: boolean;
  selectedThread: Email | null;
  showThreadDetail: boolean;
}

const Home: React.FC = () => {
  // Etat initial
  const initialState: HomeState = {
    searchTerm: "",
    darkMode: false,
    availability: 50,
    sectionSizes: {
      Actions: 1,
      Threads: 1,
      Informations: 1,
    },
    isAvailable: true,
    showNotifications: false,
    showProfileOptions: false,
    selectedThread: null,
    showThreadDetail: false,
  };

  const [state, setState] = useState<HomeState>(initialState);

  // Effet pour le mode sombre
  useEffect(() => {
    if (state.darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [state.darkMode]);

  // Filtrer les emails
  const filteredEmails = mockEmails.filter(
      (email) =>
          email.Subject.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
          email.From.toLowerCase().includes(state.searchTerm.toLowerCase())
  );

  // Grouper les emails par catégorie
  const groupEmailsByCategory = (emails: Email[]) => {
    const grouped: { [key: string]: Email[] } = {};
    emails.forEach((email) => {
      email.Categories.forEach((category) => {
        if (!grouped[category]) {
          grouped[category] = [];
        }
        grouped[category].push(email);
      });
    });
    return grouped;
  };

  const groupedEmails = groupEmailsByCategory(mockEmails);

  // Gestionnaires d'événements
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setState((prev) => ({ ...prev, searchTerm: e.target.value }));
  };

  const toggleDarkMode = () => {
    setState((prev) => ({ ...prev, darkMode: !prev.darkMode }));
  };

  const toggleAvailability = () => {
    setState((prev) => ({ ...prev, isAvailable: !prev.isAvailable }));
  };

  const toggleNotifications = () => {
    setState((prev) => ({ ...prev, showNotifications: !prev.showNotifications }));
  };

  const toggleProfileOptions = () => {
    setState((prev) => ({ ...prev, showProfileOptions: !prev.showProfileOptions }));
  };

  // resize section
  const handleSectionResize = (sectionName: string, action: 'expand' | 'collapse' | 'reset') => {
    setState(prev => {
      const newSizes = { ...prev.sectionSizes };

      if (action === 'expand') {
        Object.keys(newSizes).forEach(key => {
          if (key === sectionName) {
            newSizes[key] = 2;
          } else {
            newSizes[key] = 0.5;
          }
        });
      } else if (action === 'collapse') {
        newSizes[sectionName] = 0.5;

        // Ajuster les autres sections
        const otherSections = Object.keys(newSizes).filter(k => k !== sectionName);
        otherSections.forEach(key => {
          newSizes[key] = 1.25;
        });
      } else {
        // Réinitialiser toutes les sections à taille égale
        Object.keys(newSizes).forEach(key => {
          newSizes[key] = 1;
        });
      }

      return { ...prev, sectionSizes: newSizes };
    });
  };

  // Gestion des threads
  const handleThreadSelect = (email: Email) => {
    setState(prev => ({
      ...prev,
      selectedThread: email,
      showThreadDetail: true
    }));
  };

  const handleBackToList = () => {
    setState(prev => ({
      ...prev,
      selectedThread: null,
      showThreadDetail: false
    }));
  };

  // Calcul de la largeur totale pour normaliser les tailles
  const totalSize = Object.values(state.sectionSizes || {
    Actions: 1,
    Threads: 1,
    Informations: 1
  }).reduce((a, b) => a + b, 0);

  return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors duration-200">
        <motion.header
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="sticky top-0 z-50 bg-white dark:bg-gray-800 shadow-lg"
        >
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex justify-between items-center">
              <div className="flex items-center">
                {state.showThreadDetail && (
                    <motion.button
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleBackToList}
                        className="mr-4 p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <FaArrowLeft className="text-xl text-gray-600 dark:text-gray-300" />
                    </motion.button>
                )}
                {/* Barre de recherche */}
                <div className="flex-1 max-w-xl">
                  <div className="relative">
                    <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Rechercher..."
                        className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg
                    focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white transition-all"
                        value={state.searchTerm}
                        onChange={handleSearchChange}
                    />
                  </div>
                </div>
              </div>


              <div className="flex items-center space-x-6">
                <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={toggleDarkMode}
                >
                  {state.darkMode ? (
                      <FaSun className="text-xl text-yellow-400" />
                  ) : (
                      <FaMoon className="text-xl text-gray-500" />
                  )}
                </motion.button>

                <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-full px-4 py-2">
                <span className="mr-3 text-sm font-medium dark:text-white">
                  {state.isAvailable ? "Disponible" : "Occupé"}
                </span>
                  <motion.div className="relative w-12 h-6 flex items-center">
                    <input
                        type="checkbox"
                        checked={state.isAvailable}
                        onChange={toggleAvailability}
                        className="hidden"
                    />
                    <motion.div
                        className={`absolute w-full h-full rounded-full cursor-pointer transition-colors duration-300 ${
                            state.isAvailable ? "bg-green-500" : "bg-red-500"
                        }`}
                    />
                    <motion.div
                        layout
                        className="absolute w-4 h-4 bg-white rounded-full"
                        animate={{
                          x: state.isAvailable ? 24 : 4,
                        }}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  </motion.div>
                </div>

                {/* Notifications*/}
                <div className="relative">
                  <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.95 }}
                      className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 tooltip"
                      title="Notifications"
                      onClick={toggleNotifications}
                  >
                    <FaBell className="text-xl text-gray-600 dark:text-gray-300" />
                  </motion.button>
                  {state.showNotifications && (
                      <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 shadow-lg rounded-lg p-4">
                        <h3 className="text-lg font-semibold dark:text-white">
                          Notifications
                        </h3>
                        <ul className="mt-2 space-y-2">
                          {mockNotifications.map((notification) => (
                              <li
                                  key={notification.id}
                                  className="text-sm text-gray-600 dark:text-gray-300"
                              >
                                {notification.text}
                              </li>
                          ))}
                        </ul>
                      </div>
                  )}
                </div>

                {/* Profil*/}
                <div className="relative">
                  <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.95 }}
                      className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 tooltip"
                      title="Profil"
                      onClick={toggleProfileOptions}
                  >
                    <FaUser className="text-xl text-gray-600 dark:text-gray-300" />
                  </motion.button>
                  {state.showProfileOptions && (
                      <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 shadow-lg rounded-lg p-4">
                        <h3 className="text-lg font-semibold dark:text-white">
                          Profil
                        </h3>
                        <ul className="mt-2 space-y-2">
                          <li className="text-sm text-gray-600 dark:text-gray-300 cursor-pointer">
                            Settings
                          </li>
                          <li className="text-sm text-red-600 dark:text-red-400 cursor-pointer">
                            Déconnexion
                          </li>
                        </ul>
                      </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </motion.header>

        {/* Contenu principal */}
        <main className="container mx-auto p-4">
          {state.showThreadDetail ? (
              <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
              >
                <ThreadDetail
                    thread={state.selectedThread}
                    onBack={handleBackToList}
                />
              </motion.div>
          ) : (
              // sections Home
              <div className="flex flex-col md:flex-row justify-center items-start gap-4 max-w-7xl mx-auto">
                {["Actions", "Threads", "Informations"].map((section) => {
                  // Calculer le pourcentage de largeur
                  const sizePercent = (state.sectionSizes[section] / totalSize) * 100;
                  const isExpanded = state.sectionSizes[section] > 1;

                  return (
                      <motion.div
                          key={section}
                          layout
                          animate={{ width: `${sizePercent}%` }}
                          transition={{ type: "spring", stiffness: 300, damping: 30 }}
                          className="w-full md:h-[calc(100vh-160px)] bg-white dark:bg-gray-800 shadow-lg rounded-xl overflow-hidden flex flex-col"
                      >
                        <AttentionGauge
                            level={mockPriorityLevels[section]}
                            previousLevel={75}
                            section={section}
                        />

                        <div className="p-4 border-b dark:border-gray-700">
                          <div className="flex justify-between items-center">
                            <h2 className="text-xl font-bold dark:text-white">{section}</h2>
                            <div className="flex space-x-2">
                              {isExpanded ? (
                                  <motion.button
                                      whileHover={{ scale: 1.1 }}
                                      whileTap={{ scale: 0.95 }}
                                      onClick={() => handleSectionResize(section, 'reset')}
                                      className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                                      title="Réinitialiser"
                                  >
                                    <FaCompress className="text-gray-500 dark:text-gray-400" />
                                  </motion.button>
                              ) : (
                                  <motion.button
                                      whileHover={{ scale: 1.1 }}
                                      whileTap={{ scale: 0.95 }}
                                      onClick={() => handleSectionResize(section, 'expand')}
                                      className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                                      title="Agrandir"
                                  >
                                    <FaExpand className="text-gray-500 dark:text-gray-400" />
                                  </motion.button>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="p-4 flex-grow overflow-auto">
                          {section === "Threads" ? (
                              <div className="h-full overflow-y-auto pr-2 scrollbar-thin">
                                <ThreadSection
                                    groupedEmails={groupedEmails}
                                    onThreadSelect={handleThreadSelect}
                                />
                              </div>
                          ) : section === "Actions" ? (
                              <div className="h-full overflow-y-auto pr-2 scrollbar-thin">
                                {filteredEmails.map((email, index) => (
                                    <ActionItem
                                        key={email["Message-ID"]}
                                        email={email}
                                        actionNumber={index + 1}
                                        totalActions={filteredEmails.length}
                                        totalProgress={`${index + 1}/${
                                            Object.keys(groupedEmails).reduce(
                                                (acc, key) => acc + groupedEmails[key].length,
                                                0
                                            )
                                        }`}
                                    />
                                ))}
                              </div>
                          ) : (
                              <div className="h-full overflow-y-auto pr-2 scrollbar-thin">
                                {filteredEmails.map((email, index) => (
                                    <InfoItem
                                        key={email["Message-ID"]}
                                        email={email}
                                        infoNumber={index + 1}
                                        totalInfo={filteredEmails.length}
                                    />
                                ))}
                              </div>
                          )}
                        </div>
                      </motion.div>
                  );
                })}
              </div>
          )}
        </main>
      </div>
  );
};

export default Home;