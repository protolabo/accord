import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FaBell,
  FaUser,
  FaExpand,
  FaMoon,
  FaSun,
  FaSearch,
  FaArrowRight,
} from "react-icons/fa";
import { twMerge } from "tailwind-merge";
import ActionBox from "../components/ActionBox.tsx";

const Home = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [darkMode, setDarkMode] = useState(false);
  const [availability, setAvailability] = useState(50);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [expandedThread, setExpandedThread] = useState<string | null>(null);
  const [isAvailable, setIsAvailable] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileOptions, setShowProfileOptions] = useState(false);

  // Effet pour le mode sombre
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  const priorityLevels = {
    Actions: 90, // Haute priorité
    Threads: 60, // Moyenne priorité
    Informations: 30, // Basse priorité
  };

  const getGradient = (priority: number) => {
    if (priority > 80) return "bg-gradient-to-r from-red-500 to-yellow-400";
    if (priority > 50) return "bg-gradient-to-r from-yellow-400 to-green-500";
    return "bg-gradient-to-r from-green-500 to-green-300";
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
  const filteredEmails = emails.filter(
    (email) =>
      email.Subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
      email.From.toLowerCase().includes(searchTerm.toLowerCase())
  );
  const groupEmailsByCategory = (emails) => {
    const grouped = {};
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

              <div className="relative">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 tooltip"
                  title="Notifications"
                  onClick={() => setShowNotifications(!showNotifications)}
                >
                  <FaBell className="text-xl text-gray-600 dark:text-gray-300" />
                </motion.button>
                {showNotifications && (
                  <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 shadow-lg rounded-lg p-4">
                    <h3 className="text-lg font-semibold dark:text-white">
                      Notifications
                    </h3>
                    <ul className="mt-2 space-y-2">
                      <li className="text-sm text-gray-600 dark:text-gray-300">
                        Notification 1
                      </li>
                      <li className="text-sm text-gray-600 dark:text-gray-300">
                        Notification 2
                      </li>
                      <li className="text-sm text-gray-600 dark:text-gray-300">
                        Notification 3
                      </li>
                    </ul>
                  </div>
                )}
              </div>

              <div className="relative">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 tooltip"
                  title="Profil"
                  onClick={() => setShowProfileOptions(!showProfileOptions)}
                >
                  <FaUser className="text-xl text-gray-600 dark:text-gray-300" />
                </motion.button>
                {showProfileOptions && (
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

      <main className="container mx-auto p-4">
        <div className="flex flex-col md:flex-row justify-center items-center gap-4 max-w-7xl mx-auto">
          {["Actions", "Threads", "Informations"].map((section) => (
            <motion.div
              key={section}
              layout
              className={twMerge(
                "w-full md:w-1/3 max-w-md bg-white dark:bg-gray-800 shadow-lg rounded-xl overflow-hidden transition-all duration-300",
                expandedSection === section ? "md:w-1/2" : "md:w-1/3"
              )}
            >
              {/* Jauge d'Attention */}
              <div className="p-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium dark:text-white">
                    Attention Requise : {priorityLevels[section]}%
                  </span>
                </div>
                <div className="w-full h-2 rounded-full mt-2">
                  <motion.div
                    className={`h-full rounded-full ${getGradient(
                      priorityLevels[section]
                    )}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${priorityLevels[section]}%` }}
                    transition={{ duration: 1 }}
                  />
                </div>
              </div>

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
                {section === "Threads" ? (
                  <div className="max-h-[calc(100vh-300px)] overflow-y-auto pr-2">
                    {Object.keys(groupedEmails).map((category) => (
                      <motion.div
                        key={category}
                        className="mb-6 p-4 bg-gray-200 dark:bg-gray-700 rounded-lg"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() =>
                          setExpandedSection(
                            expandedSection === category ? null : category
                          )
                        }
                      >
                        <div className="flex justify-between items-center">
                          <h2 className="text-xl font-semibold mb-2">
                            {category}
                          </h2>
                          <FaArrowRight
                            className="text-gray-500 dark:text-gray-400 cursor-pointer"
                            onClick={() =>
                              setExpandedThread(
                                expandedThread === category ? null : category
                              )
                            }
                          />
                        </div>
                        {expandedSection === category && (
                          <ul className="list-disc pl-6 space-y-2">
                            {groupedEmails[category].map((email) => (
                              <motion.li
                                key={email["Message-ID"]}
                                className="bg-gray-50 dark:bg-gray-800 p-4 rounded-md hover:shadow-lg cursor-pointer"
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() =>
                                  alert(`Email sélectionné : ${email.Subject}`)
                                }
                              >
                                <strong className="text-lg">
                                  {email.Subject}
                                </strong>{" "}
                                -{" "}
                                <span className="text-sm text-gray-600 dark:text-gray-300">
                                  {email.Body}
                                </span>{" "}
                                <em className="text-sm text-gray-500 dark:text-gray-400">
                                  (from: {email.From})
                                </em>
                              </motion.li>
                            ))}
                          </ul>
                        )}
                      </motion.div>
                    ))}
                  </div>
                ) : section === "Actions" ? (
                  <div className="max-h-[calc(100vh-300px)] overflow-y-auto pr-2">
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
                              {email.Subject}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-300">
                              {email.From}
                            </p>
                          </div>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {email.Date}
                          </span>
                        </div>
                        <div className="mt-4 space-y-2">
                          <ActionBox title="Accepter">
                            <button className="w-full bg-green-500 text-white py-2 rounded-lg hover:bg-green-600 transition-all">
                              Accepter
                            </button>
                          </ActionBox>
                          <ActionBox title="Répondre">
                            <button className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 transition-all">
                              Répondre
                            </button>
                            <textarea
                              className="w-full mt-2 p-2 bg-gray-100 dark:bg-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
                              placeholder="Réponse rapide..."
                            />
                          </ActionBox>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="max-h-[calc(100vh-300px)] overflow-y-auto pr-2">
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
                              {email.Subject}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-300">
                              {email.From}
                            </p>
                          </div>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {email.Date}
                          </span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {expandedThread && (
          <div className="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg max-w-3xl w-full">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold dark:text-white">
                  {expandedThread}
                </h2>
                <button
                  onClick={() => setExpandedThread(null)}
                  className="text-gray-500 dark:text-gray-400"
                >
                  Close
                </button>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-1 space-y-4">
                  {groupedEmails[expandedThread].map((email) => (
                    <div
                      key={email["Message-ID"]}
                      className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                    >
                      <h3 className="font-semibold mb-1 dark:text-white">
                        {email.Subject}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-300">
                        {email.Body}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        From: {email.From}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Date: {email.Date}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="col-span-2 space-y-4">
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <h3 className="font-semibold mb-1 dark:text-white">
                      Meetings
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      Placeholder for meetings related to the thread.
                    </p>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <h3 className="font-semibold mb-1 dark:text-white">
                      AI-Generated Summary
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      Placeholder for AI-generated summary about the project
                      advancement.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Home;
