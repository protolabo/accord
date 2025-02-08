import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FaBell,
  FaUser,
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

  // Effet pour le mode sombre
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

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
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors duration-200">
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="sticky top-0 z-50 bg-white dark:bg-gray-800 shadow-lg"
      >
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
            <div className="flex-1 max-w-xl">
              <div className="relative">
                <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Rechercher..."
                  className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg 
                  focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white transition-all"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>

            <div className="flex items-center space-x-6">
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

              {/* Slider de disponibilité amélioré */}
              <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-full px-4 py-2">
                <span className="mr-3 text-sm font-medium dark:text-white">
                  {isAvailable ? "Disponible" : "Occupé"}
                </span>
                <motion.div className="relative w-12 h-6 flex items-center">
                  <input
                    type="checkbox"
                    checked={isAvailable}
                    onChange={() => setIsAvailable(!isAvailable)}
                    className="hidden"
                  />
                  <motion.div
                    className={`absolute w-full h-full rounded-full cursor-pointer transition-colors duration-300 ${
                      isAvailable ? "bg-green-500" : "bg-gray-400"
                    }`}
                  />
                  <motion.div
                    layout
                    className="absolute w-4 h-4 bg-white rounded-full"
                    animate={{
                      x: isAvailable ? 24 : 4,
                    }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                </motion.div>
              </div>

              {[
                { icon: FaBell, title: "Notifications" },
                { icon: FaUser, title: "Profil" },
              ].map(({ icon: Icon, title }) => (
                <motion.button
                  key={title}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 tooltip"
                  title={title}
                >
                  <Icon className="text-xl text-gray-600 dark:text-gray-300" />
                </motion.button>
              ))}
            </div>
          </div>
        </div>
      </motion.header>

      <main className="container mx-auto p-4">
        <div className="flex space-x-4 overflow-x-auto">
          {["Actions", "Threads", "Informations"].map((section) => (
            <motion.div
              key={section}
              layout
              className={twMerge(
                "flex-shrink-0 bg-white dark:bg-gray-800 shadow-lg rounded-xl overflow-hidden transition-all duration-300",
                expandedSection === section ? "w-[45%]" : "w-[30%]"
              )}
            >
              <div className="p-6 border-b dark:border-gray-700">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-bold dark:text-white">
                    {section}
                  </h2>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() =>
                      setExpandedSection(
                        expandedSection === section ? null : section
                      )
                    }
                    className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <FaExpand className="text-gray-500 dark:text-gray-400" />
                  </motion.button>
                </div>
              </div>

              <div className="p-6">
                <div className="mb-6">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium dark:text-white">
                      Progression
                    </span>
                    <span className="text-sm font-medium dark:text-white">
                      {availability}%
                    </span>
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

                <div className="space-y-4 overflow-y-auto max-h-[calc(100vh-400px)]">
                  {filteredEmails.map((email) => (
                    <motion.div
                      key={email.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      whileHover={{ scale: 1.02 }}
                      className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg cursor-pointer 
                      hover:shadow-md transition-all"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-semibold mb-1 dark:text-white">
                            {email.subject}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-300">
                            {email.sender}
                          </p>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
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
      </main>
    </div>
  );
};

export default Home;
