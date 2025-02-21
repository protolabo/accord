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
import AttentionGauge from "../components/AttentionGauge";
import ActionItem from "../components/ActionItem";
import InfoItem from "../components/InfoItem";
import ThreadSection from "../pages/ThreadSection";
import type { Email } from "../components/types";

interface Notification {
  id: string;
  text: string;
}

interface PriorityLevels {
  [key: string]: number;
}

interface HomeState {
  searchTerm: string;
  darkMode: boolean;
  availability: number;
  expandedSection: string | null;
  isAvailable: boolean;
  showNotifications: boolean;
  showProfileOptions: boolean;
  selectedThread: Email | null;
  showThreadDetail: boolean;
}

const Home: React.FC = () => {

  const initialState: HomeState = {
    searchTerm: "",
    darkMode: false,
    availability: 50,
    expandedSection: null,
    isAvailable: true,
    showNotifications: false,
    showProfileOptions: false,
    selectedThread: null,
    showThreadDetail: false,
  };

  const [state, setState] = useState<HomeState>(initialState);

  const notifications: Notification[] = [
    { id: "1", text: "Notification 1" },
    { id: "2", text: "Notification 2" },
    { id: "3", text: "Notification 3" },
  ];


  const priorityLevels: PriorityLevels = {
    Actions: 90,
    Threads: 60,
    Informations: 30,
  };

  const emails = [
    {
      "Message-ID": "<18782981.1075855378110.JavaMail.evans@thyme>",
      Date: "Mon, 14 May 2001 16:39:00 -0700",
      From: "phillip.allen@enron.com",
      To: "tim.belden@enron.com",
      Subject: "Here is our forecast",
      Body: "Here is our forecast for the upcoming quarter.",
      Categories: ["Other"],
    },
    {
      "Message-ID": "<15464986.1075855378456.JavaMail.evans@thyme>",
      Date: "Fri, 04 May 2001 13:51:00 -0700",
      From: "phillip.allen@enron.com",
      To: "john.lavorato@enron.com",
      Subject: "Re: Business trip",
      Body: "Traveling to have a business meeting takes the fun out of the trip...",
      Categories: ["Meeting Scheduling", "Business Discussion"],
    },
    {
      "Message-ID": "<24216240.1075855687451.JavaMail.evans@thyme>",
      Date: "Wed, 18 Oct 2000 03:00:00 -0700",
      From: "phillip.allen@enron.com",
      To: "leah.arsdall@enron.com",
      Subject: "Re: test",
      Body: "Test successful. Way to go!!!",
      Categories: ["System Testing & IT", "Information Distribution"],
    },
    {
      "Message-ID": "<13505866.1075863688222.JavaMail.evans@thyme>",
      Date: "Mon, 23 Oct 2000 06:13:00 -0700",
      From: "phillip.allen@enron.com",
      To: "randall.gay@enron.com",
      Subject: "Salary and schedule",
      Body: "Can you send me a schedule of the salary and level of everyone...",
      Categories: ["Meeting Scheduling", "Salary & Promotion"],
    },
    {
      "Message-ID": "<30922949.1075863688243.JavaMail.evans@thyme>",
      Date: "Thu, 31 Aug 2000 05:07:00 -0700",
      From: "phillip.allen@enron.com",
      To: "greg.piper@enron.com",
      Subject: "Re: Hello",
      Body: "Let's shoot for Tuesday at 11:45.",
      Categories: ["Scheduling Coordination"],
    },
    {
      "Message-ID": "<30965995.1075863688265.JavaMail.evans@thyme>",
      Date: "Thu, 31 Aug 2000 04:17:00 -0700",
      From: "phillip.allen@enron.com",
      To: "greg.piper@enron.com",
      Subject: "Re: Hello again",
      Body: "How about either next Tuesday or Thursday?",
      Categories: ["Scheduling Coordination"],
    },
    {
      "Message-ID": "<16254169.1075863688286.JavaMail.evans@thyme>",
      Date: "Tue, 22 Aug 2000 07:44:00 -0700",
      From: "phillip.allen@enron.com",
      To: "david.l.johnson@enron.com, john.shafer@enron.com",
      Subject: "Update distribution list",
      Body: "Please cc the following distribution list with updates...",
      Categories: ["System Updates", "Information Distribution"],
    },
    {
      "Message-ID": "<17189699.1075863688308.JavaMail.evans@thyme>",
      Date: "Fri, 14 Jul 2000 06:59:00 -0700",
      From: "phillip.allen@enron.com",
      To: "joyce.teixeira@enron.com",
      Subject: "Re: PRC review",
      Body: "Any morning between 10 and 11:30.",
      Categories: ["Other"],
    },
    {
      "Message-ID": "<18782982.1075855378111.JavaMail.evans@thyme>",
      Date: "Tue, 15 May 2001 10:39:00 -0700",
      From: "phillip.allen@enron.com",
      To: "tim.belden@enron.com",
      Subject: "Follow-up forecast",
      Body: "Here is an updated forecast.",
      Categories: ["Other"],
    },
    {
      "Message-ID": "<13505867.1075863688223.JavaMail.evans@thyme>",
      Date: "Tue, 24 Oct 2000 07:13:00 -0700",
      From: "phillip.allen@enron.com",
      To: "randall.gay@enron.com",
      Subject: "Promotion changes",
      Body: "Thoughts on changes for next quarter.",
      Categories: ["Salary & Promotion"],
    },
  ];


  useEffect(() => {
    if (state.darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [state.darkMode]);

  // Filtrer les emails en fonction du terme de recherche
  const filteredEmails = emails.filter(
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

  const groupedEmails = groupEmailsByCategory(emails);

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

  const toggleSection = (section: string) => {
    setState((prev) => ({
      ...prev,
      expandedSection: prev.expandedSection === section ? null : section,
    }));
  };


  const handleThreadSelect = (thread: Email) => {
    setState((prev) => ({
      ...prev,
      selectedThread: thread,
      showThreadDetail: true,
    }));
  };

  //revenir à la vue principale
  const handleBackToMain = () => {
    setState((prev) => ({
      ...prev,
      selectedThread: null,
      showThreadDetail: false,
    }));
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors duration-200">
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="sticky top-0 z-50 bg-white dark:bg-gray-800 shadow-lg"
      >
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
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

            {/* Actions rapides */}
            <div className="flex items-center space-x-6">
              {/* Toggle mode sombre */}
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

              {/* Toggle disponibilité */}
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

              {/* Notifications */}
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

              {/* Profil */}
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
        <div className="flex flex-col md:flex-row justify-center items-start gap-4 max-w-7xl mx-auto">
          {["Actions", "Threads", "Informations"].map((section) => (
            <motion.div
              key={section}
              layout
              className={twMerge(
                "w-full md:w-1/3 bg-white dark:bg-gray-800 shadow-lg rounded-xl overflow-hidden transition-all duration-300",
                state.expandedSection === section ? "md:w-1/2" : "md:w-1/3"
              )}
            >
              <AttentionGauge
                level={priorityLevels[section]}
                previousLevel={75}
                section={section}
              />

              <div className="p-6 border-b dark:border-gray-700">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-bold dark:text-white">{section}</h2>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => toggleSection(section)}
                    className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <FaExpand className="text-gray-500 dark:text-gray-400" />
                  </motion.button>
                </div>
              </div>

              <div className="p-6">
                {section === "Threads" ? (
                  <div className="max-h-[calc(100vh-300px)] overflow-y-auto pr-2">
                    <ThreadSection
                      groupedEmails={groupedEmails}
                      onThreadSelect={handleThreadSelect}
                    />
                  </div>
                ) : section === "Actions" ? (
                  <div className="max-h-[calc(100vh-300px)] overflow-y-auto pr-2">
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
                  <div className="max-h-[calc(100vh-300px)] overflow-y-auto pr-2">
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
          ))}
        </div>
      </main>
    </div>
  );
};

export default Home;