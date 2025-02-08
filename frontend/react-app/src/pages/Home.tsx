import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  FaBell,
  FaUser,
  FaAt,
  FaExpand,
  FaMoon,
  FaSun,
  FaSearch,
} from "react-icons/fa";
import { twMerge } from "tailwind-merge";

const Home = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [darkMode, setDarkMode] = useState(false);
  const [availability, setAvailability] = useState(50);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [isAvailable, setIsAvailable] = useState(true);

  const emails = [
    {
      id: 1,
      subject: "Nouvelle fonctionnalité",
      sender: "Jean Dupont",
      time: "10:30",
    },
    {
      id: 2,
      subject: "Réunion d'équipe",
      sender: "Marie Curie",
      time: "11:45",
    },
    {
      id: 3,
      subject: "Mise à jour système",
      sender: "IT Support",
      time: "13:15",
    },
    {
      id: 4,
      subject: "Facture mensuelle",
      sender: "Comptabilité",
      time: "14:20",
    },
    {
      id: 5,
      subject: "Planification du projet",
      sender: "Chef de projet",
      time: "15:00",
    },
  ];

  const filteredEmails = emails.filter(
    (email) =>
      email.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
      email.sender.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div
      className={twMerge(
        "flex flex-col min-h-screen",
        darkMode ? "bg-gray-900 text-white" : "bg-gray-100 text-black"
      )}
    >
      {/* Header amélioré */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="sticky top-0 z-50 bg-white dark:bg-gray-800 shadow-lg"
      >
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
            {/* Barre de recherche améliorée */}
            <div className="flex-1 max-w-xl">
              <div className="relative">
                <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Rechercher..."
                  className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 
                  rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 
                  dark:text-white transition-all"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>

            {/* Actions rapides */}
            <div className="flex items-center space-x-6">
              {/* Toggle mode sombre */}
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => setDarkMode(!darkMode)}
              >
                {darkMode ? (
                  <FaSun className="text-xl text-yellow-400" />
                ) : (
                  <FaMoon className="text-xl text-gray-500" />
                )}
              </motion.button>

              {/* Toggle disponibilité */}
              <div
                className="flex items-center bg-gray-100 dark:bg-gray-700 
              rounded-full px-4 py-2"
              >
                <span className="mr-3 text-sm font-medium">
                  {isAvailable ? "Disponible" : "Occupé"}
                </span>
                <label className="relative inline-flex cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAvailable}
                    onChange={() => setIsAvailable(!isAvailable)}
                    className="sr-only peer"
                  />
                  <div
                    className="w-12 h-6 bg-gray-300 peer-checked:bg-green-500 
                  rounded-full transition-all duration-300"
                  >
                    <div
                      className="absolute left-1 top-1 w-4 h-4 bg-white 
                    rounded-full transition-all duration-300 
                    peer-checked:translate-x-6"
                    />
                  </div>
                </label>
              </div>

              {/* Icônes d'action */}
              {[
                { icon: FaAt, title: "Threads" },
                { icon: FaBell, title: "Notifications" },
                { icon: FaUser, title: "Profil" },
              ].map(({ icon: Icon, title }) => (
                <motion.button
                  key={title}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-2 rounded-full hover:bg-gray-100 
                  dark:hover:bg-gray-700 tooltip"
                  title={title}
                >
                  <Icon className="text-xl text-gray-600 dark:text-gray-300" />
                </motion.button>
              ))}
            </div>
          </div>
        </div>
      </motion.header>

      {/* Contenu principal */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <div className="grid grid-cols-3 gap-6">
          {["Actions", "Threads", "Informations"].map((section) => (
            <motion.div
              key={section}
              layout
              className={twMerge(
                "bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden",
                expandedSection === section ? "col-span-3" : "col-span-1"
              )}
            >
              {/* En-tête de section */}
              <div className="p-6 border-b dark:border-gray-700">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-bold">{section}</h2>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() =>
                      setExpandedSection(
                        expandedSection === section ? null : section
                      )
                    }
                    className="p-2 rounded-full hover:bg-gray-100 
                    dark:hover:bg-gray-700"
                  >
                    <FaExpand className="text-gray-500 dark:text-gray-400" />
                  </motion.button>
                </div>
              </div>

              {/* Contenu de section */}
              <div className="p-6">
                {/* Barre de progression */}
                <div className="mb-6">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium">Progression</span>
                    <span className="text-sm font-medium">{availability}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${availability}%` }}
                      className="h-full bg-blue-500 rounded-full"
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </div>

                {/* Liste des emails */}
                <div className="space-y-4">
                  {filteredEmails.map((email) => (
                    <motion.div
                      key={email.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      whileHover={{ scale: 1.02 }}
                      className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg 
                      cursor-pointer hover:shadow-md transition-all"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-semibold mb-1">
                            {email.subject}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-300">
                            {email.sender}
                          </p>
                        </div>
                        <span className="text-xs text-gray-500">
                          {email.time}
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Home;
