import React from "react";
import { motion } from "framer-motion";
import {
  FaArrowLeft,
  FaBell,
  FaMoon,
  FaSearch,
  FaSun,
  FaUser,
} from "react-icons/fa";
import UserProfileModal from "./UserProfileModal";

interface HeaderProps {
  showThreadDetail: boolean;
  handleBackToList: () => void;
  searchTerm: string;
  handleSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleSearchClick: () => void;
  darkMode: boolean;
  toggleDarkMode: () => void;
  isAvailable: boolean;
  toggleAvailability: () => void;
  showNotifications: boolean;
  toggleNotifications: () => void;
  notifications: Array<{ id: string; text: string }>;
  showProfileOptions: boolean;
  toggleProfileOptions: () => void;
}

const Header: React.FC<HeaderProps> = ({
  showThreadDetail,
  handleBackToList,
  searchTerm,
  handleSearchChange,
  handleSearchClick,
  darkMode,
  toggleDarkMode,
  isAvailable,
  toggleAvailability,
  showNotifications,
  toggleNotifications,
  notifications,
  showProfileOptions,
  toggleProfileOptions,
}) => {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="sticky top-0 z-50 bg-white dark:bg-gray-800 shadow-lg"
    >
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-6">
            <span className="text-2xl font-bold text-gray-800 dark:text-white">
              Accord
            </span>
            {showThreadDetail && (
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
          </div>
          {/* Search bar */}
          <div className="flex-1 max-w-xl mx-auto">
            <div className="relative">
              <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher..."
                className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg
                focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white transition-all cursor-pointer"
                value={searchTerm}
                onChange={handleSearchChange}
                onClick={handleSearchClick}
                readOnly
              />
            </div>
          </div>

          <div className="flex items-center space-x-6">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
              onClick={toggleDarkMode}
            >
              {darkMode ? (
                <FaSun className="text-xl text-yellow-400" />
              ) : (
                <FaMoon className="text-xl text-gray-500" />
              )}
            </motion.button>

            <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-full px-4 py-2">
              <span className="mr-3 text-sm font-medium dark:text-white">
                {isAvailable ? "Disponible" : "Occupé"}
              </span>
              <motion.div className="relative w-12 h-6 flex items-center">
                <input
                  type="checkbox"
                  checked={isAvailable}
                  onChange={toggleAvailability}
                  className="hidden"
                />
                <motion.div
                  className={`absolute w-full h-full rounded-full cursor-pointer transition-colors duration-300 ${
                    isAvailable ? "bg-green-500" : "bg-red-500"
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
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 shadow-lg rounded-lg p-4">
                  <h3 className="text-lg font-semibold dark:text-white">
                    Notifications
                  </h3>
                  <ul className="mt-2 space-y-2">
                    {notifications.map((notification) => (
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

            {/* Profile*/}
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
              {showProfileOptions && (
                <UserProfileModal onClose={toggleProfileOptions} />
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.header>
  );
};

export default Header;