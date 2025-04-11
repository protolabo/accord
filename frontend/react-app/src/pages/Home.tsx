import React, { useState, useEffect, useCallback, useRef } from "react";
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
import UserProfileModal from "../components/UserProfileModal";
import SearchPopup from "../components/search/SearchPopup";
import EmailLogin from "../components/EmailLogin";
import emailAPIService, {
  StandardizedEmail as EmailServiceEmail,
} from "../services/EmailService";
import {
  mockEmails,
  mockNotifications,
  mockPriorityLevels,
  mockEstimatedTimes,
  mockTopContacts,
} from "../data/mockData";
// Remove this import to avoid conflict
// import type { Email } from "../components/types";
import ResizeHandle from "../components/ResizeHandle";
import { useNavigate } from "react-router-dom";

// Define Email interface for the component
interface Email {
  "Message-ID": string;
  Subject: string;
  From: string;
  To: string;
  Cc: string;
  Date: string;
  "Content-Type": string;
  Body: string;
  IsRead: boolean;
  Attachments: {
    filename: string;
    contentType: string;
    size: number;
    contentId?: string;
    url?: string;
  }[];
  Categories: string[];
  Importance: "high" | "normal" | "low";
  ThreadId: string;
}

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
  isResizing: boolean;
  resizingIndex: number | null;
  startX: number;
  startSizes: { [key: string]: number };
  showComposePopup: boolean;
  recipientAvailability?: number;
  showSearchPopup: boolean;
  focusMode: {
    active: boolean;
    priority: "high" | "medium" | "low";
    timeBlock: number; // minutes
    endTime: Date | null;
  };
  isAuthenticated: boolean;
  emails: Email[];
  isLoading: boolean;
}

// Add type cast to ensure mockEmails matches our Email interface
const typedMockEmails = mockEmails as unknown as Email[];

const Home: React.FC = () => {
  // Initial state
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
    isResizing: false,
    resizingIndex: null,
    startX: 0,
    startSizes: {},
    showComposePopup: false,
    recipientAvailability: undefined,
    showSearchPopup: false,
    focusMode: {
      active: false,
      priority: "high",
      timeBlock: 25,
      endTime: null,
    },
    isAuthenticated: false,
    emails: [],
    isLoading: false,
  };
  const sectionRefs = useRef<Array<HTMLDivElement | null>>([]);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [state, setState] = useState<HomeState>(initialState);
  const navigate = useNavigate();

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      const isAuth = emailAPIService.isAuthenticated();
      setState((prev) => ({ ...prev, isAuthenticated: isAuth }));

      if (isAuth) {
        fetchEmails();
      }
    };

    checkAuth();
  }, []);

  // Fetch emails from the selected email service
  const fetchEmails = async () => {
    setState((prev) => ({ ...prev, isLoading: true }));

    try {
      if (emailAPIService.isAuthenticated()) {
        const serviceEmails = await emailAPIService.fetchEmails();

        // Convert service emails to the format expected by the app
        const convertedEmails: Email[] = serviceEmails.map((email) => ({
          "Message-ID": email.id,
          Subject: email.subject,
          From: email.from,
          To: email.to.join(", "),
          Cc: email.cc.join(", "),
          Date: email.date.toString(),
          "Content-Type":
            email.bodyType === "html" ? "text/html" : "text/plain",
          Body: email.body,
          IsRead: email.isRead,
          Attachments: email.attachments,
          Categories: email.categories,
          Importance: email.importance,
          ThreadId: email.threadId || email.id,
        }));

        setState((prev) => ({
          ...prev,
          emails: convertedEmails,
          isLoading: false,
        }));
      } else {
        // Fall back to mock data if not authenticated
        setState((prev) => ({
          ...prev,
          emails: typedMockEmails,
          isLoading: false,
        }));
      }
    } catch (error) {
      console.error("Error fetching emails:", error);
      // Fall back to mock data on error
      setState((prev) => ({
        ...prev,
        emails: typedMockEmails,
        isLoading: false,
      }));
    }
  };

  // Handle successful login
  const handleLoginSuccess = () => {
    setState((prev) => ({ ...prev, isAuthenticated: true }));
    fetchEmails();
  };

  // Effect for dark mode
  useEffect(() => {
    if (state.darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [state.darkMode]);

  // Filter emails
  const filteredEmails = state.emails.filter(
    (email) =>
      email.Subject.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
      email.From.toLowerCase().includes(state.searchTerm.toLowerCase())
  );

  // Group emails by category
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

  const groupedEmails = groupEmailsByCategory(state.emails);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setState((prev) => ({ ...prev, searchTerm: e.target.value }));
  };
  const handleSearchClick = () => {
    setState((prev) => ({ ...prev, showSearchPopup: true }));
  };

  const toggleDarkMode = () => {
    setState((prev) => ({ ...prev, darkMode: !prev.darkMode }));
  };

  const toggleAvailability = () => {
    setState((prev) => ({ ...prev, isAvailable: !prev.isAvailable }));
  };

  const toggleNotifications = () => {
    setState((prev) => ({
      ...prev,
      showNotifications: !prev.showNotifications,
    }));
  };

  const toggleProfileOptions = () => {
    setState((prev) => ({
      ...prev,
      showProfileOptions: !prev.showProfileOptions,
    }));
  };

  // resize section
  const handleSectionResize = (
    sectionName: string,
    action: "expand" | "collapse" | "reset"
  ) => {
    setState((prev) => {
      const newSizes = { ...prev.sectionSizes };

      if (action === "expand") {
        Object.keys(newSizes).forEach((key) => {
          if (key === sectionName) {
            newSizes[key] = 2;
          } else {
            newSizes[key] = 0.5;
          }
        });
      } else if (action === "collapse") {
        newSizes[sectionName] = 0.5;

        // Adjust other sections
        const otherSections = Object.keys(newSizes).filter(
          (k) => k !== sectionName
        );
        otherSections.forEach((key) => {
          newSizes[key] = 1.25;
        });
      } else {
        // Reset all sections to equal size
        Object.keys(newSizes).forEach((key) => {
          newSizes[key] = 1;
        });
      }

      return { ...prev, sectionSizes: newSizes };
    });
  };

  const handleThreadSelect = useCallback(async (email: Email) => {
    setState((prev) => ({
      ...prev,
      selectedThread: email,
      showThreadDetail: true,
    }));

    // Mark as read if using real email service
    if (emailAPIService.isAuthenticated() && email && !email.IsRead) {
      try {
        await emailAPIService.markAsRead(email["Message-ID"]);
        // Update the email in state to reflect it's now read
        setState((prev) => ({
          ...prev,
          emails: prev.emails.map((e) =>
            e["Message-ID"] === email["Message-ID"] ? { ...e, IsRead: true } : e
          ),
        }));
      } catch (error) {
        console.error("Error marking email as read:", error);
      }
    }
  }, []);

  const handleBackToList = () => {
    setState((prev) => ({
      ...prev,
      selectedThread: null,
      showThreadDetail: false,
    }));
  };

  // resize event handlers
  const handleResizeStart = useCallback(
    (index: number, clientX: number) => {
      const sectionSizes = { ...state.sectionSizes };

      setState((prev) => ({
        ...prev,
        isResizing: true,
        resizingIndex: index,
        startX: clientX,
        startSizes: { ...sectionSizes },
      }));
    },
    [state.sectionSizes]
  );

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!state.isResizing || state.resizingIndex === null) return;

      const deltaX = e.clientX - state.startX;

      if (Math.abs(deltaX) < 5) return;

      const containerWidth = containerRef.current?.offsetWidth || 1000;

      const deltaRatio = deltaX / containerWidth;

      const sectionKeys = Object.keys(state.sectionSizes);
      const leftSection = sectionKeys[state.resizingIndex];
      const rightSection = sectionKeys[state.resizingIndex + 1];

      if (!leftSection || !rightSection) return;

      // minimum size
      const MIN_SIZE = 0.15;
      const newSizes = { ...state.startSizes };

      const totalCurrentSize = newSizes[leftSection] + newSizes[rightSection];

      let newLeftSize = newSizes[leftSection] + deltaRatio * totalCurrentSize;
      let newRightSize = newSizes[rightSection] - deltaRatio * totalCurrentSize;

      if (newLeftSize < MIN_SIZE) {
        newLeftSize = MIN_SIZE;
        newRightSize = totalCurrentSize - MIN_SIZE;
      } else if (newRightSize < MIN_SIZE) {
        newRightSize = MIN_SIZE;
        newLeftSize = totalCurrentSize - MIN_SIZE;
      }

      newSizes[leftSection] = newLeftSize;
      newSizes[rightSection] = newRightSize;

      setState((prev) => ({
        ...prev,
        sectionSizes: newSizes,
      }));
    },
    [
      state.isResizing,
      state.resizingIndex,
      state.startX,
      state.startSizes,
      state.sectionSizes,
    ]
  );

  const handleMouseUp = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isResizing: false,
      resizingIndex: null,
    }));
  }, []);

  useEffect(() => {
    if (state.isResizing) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [state.isResizing, handleMouseMove, handleMouseUp]);

  // Calculate total width to normalize sizes
  const totalSize = Object.values(
    state.sectionSizes || {
      Actions: 1,
      Threads: 1,
      Informations: 1,
    }
  ).reduce((a, b) => a + b, 0);

  // Define available time in minutes (e.g., 8 hours = 480 minutes)
  const availableTime =
    480 - (new Date().getHours() * 60 + new Date().getMinutes());

  // Example data for total actions
  const totalActions = {
    Actions: 500,
    Threads: 300,
    Informations: 200,
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
            <div className="flex items-center space-x-6">
              <span className="text-2xl font-bold text-gray-800 dark:text-white">
                Accord
              </span>
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
                  value={state.searchTerm}
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
                {state.showProfileOptions && (
                  <UserProfileModal onClose={toggleProfileOptions} />
                )}
              </div>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main content */}
      <main className="container mx-auto p-4">
        {!state.isAuthenticated ? (
          <EmailLogin onLogin={handleLoginSuccess} />
        ) : state.showThreadDetail ? (
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
          // Home sections
          <div
            ref={containerRef}
            className="flex flex-col md:flex-row justify-center items-stretch gap-0 max-w-[85rem] mx-auto"
            style={{ cursor: state.isResizing ? "col-resize" : "default" }}
          >
            {(
              ["Actions", "Threads", "Informations"] as Array<
                keyof typeof totalActions
              >
            ).map((section, index) => {
              // Calculate the width percentage
              const sizePercent =
                (state.sectionSizes[section] / totalSize) * 100;
              const isExpanded = state.sectionSizes[section] > 1;

              return (
                <React.Fragment key={section}>
                  <motion.div
                    ref={(el) => {
                      sectionRefs.current[index] = el;
                    }}
                    layout
                    animate={{ width: `${sizePercent}%` }}
                    transition={{
                      type: state.isResizing ? "tween" : "spring",
                      duration: state.isResizing ? 0 : 0.3,
                      stiffness: 300,
                      damping: 30,
                    }}
                    className="w-full md:h-[calc(100vh-192px)] bg-white dark:bg-gray-800 shadow-lg rounded-xl
                  overflow-hidden flex flex-col select-none"
                    style={{ userSelect: state.isResizing ? "none" : "auto" }}
                  >
                    <AttentionGauge
                      level={mockPriorityLevels[section]}
                      previousLevel={null}
                      section={section}
                      estimatedTime={
                        mockEstimatedTimes[
                          section as keyof typeof mockEstimatedTimes
                        ]
                      }
                      totalActions={totalActions[section]}
                      availableTime={availableTime}
                    />

                    <div className="p-4 border-b dark:border-gray-700">
                      <div className="flex justify-between items-center">
                        <h2 className="text-xl font-bold dark:text-white">
                          {section}
                        </h2>
                        <div className="flex space-x-2">
                          {isExpanded ? (
                            <motion.button
                              whileHover={{ scale: 1.1 }}
                              whileTap={{ scale: 0.95 }}
                              onClick={() =>
                                handleSectionResize(section, "reset")
                              }
                              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                              title="Réinitialiser"
                            >
                              <FaCompress className="text-gray-500 dark:text-gray-400" />
                            </motion.button>
                          ) : (
                            <motion.button
                              whileHover={{ scale: 1.1 }}
                              whileTap={{ scale: 0.95 }}
                              onClick={() =>
                                handleSectionResize(section, "expand")
                              }
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
                      {state.isLoading ? (
                        <div className="flex justify-center items-center h-full">
                          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
                        </div>
                      ) : section === "Threads" ? (
                        <div className="h-full overflow-y-auto pr-2 scrollbar-thin space-y-2 min-w-0">
                          <ThreadSection
                            groupedEmails={groupedEmails}
                            onThreadSelect={handleThreadSelect}
                          />
                        </div>
                      ) : section === "Actions" ? (
                        <div className="h-full overflow-y-auto pr-2 scrollbar-thin space-y-2 min-w-0">
                          {filteredEmails.map((email, idx) => (
                            <ActionItem
                              key={email["Message-ID"]}
                              email={email}
                              actionNumber={idx + 1}
                              totalActions={filteredEmails.length}
                              totalProgress={`${idx + 1}/${Object.keys(
                                groupedEmails
                              ).reduce(
                                (acc, key) => acc + groupedEmails[key].length,
                                0
                              )}`}
                            />
                          ))}
                        </div>
                      ) : (
                        <div className="h-full overflow-y-auto pr-2 scrollbar-thin space-y-2 min-w-0">
                          {filteredEmails.map((email, idx) => (
                            <InfoItem
                              key={email["Message-ID"]}
                              email={email}
                              infoNumber={idx + 1}
                              totalInfo={filteredEmails.length}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>

                  {index <
                    ["Actions", "Threads", "Informations"].length - 1 && (
                    <ResizeHandle
                      index={index}
                      onResizeStart={handleResizeStart}
                    />
                  )}
                </React.Fragment>
              );
            })}
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="fixed bottom-6 right-6 w-14 h-14 bg-blue-500 hover:bg-blue-600 rounded-full shadow-lg flex items-center justify-center text-white text-2xl z-50"
              onClick={() =>
                setState((prev) => ({ ...prev, showComposePopup: true }))
              }
            >
              <span className="text-2xl font-bold">+</span>
            </motion.button>

            {/* Frequent contacts Panel */}
            <div className="fixed right-6 top-24 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 z-40">
              <h3 className="text-lg font-semibold mb-4 dark:text-white">
                Contacts fréquents
              </h3>
              <div className="space-y-4">
                {mockTopContacts.map((contact) => (
                  <div key={contact.id} className="flex flex-col">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium dark:text-white">
                        {contact.name}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {contact.availability}%
                      </span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${contact.availability}%` }}
                        transition={{ duration: 0.5 }}
                        className="h-full transition-all duration-300"
                        style={{
                          backgroundColor: `hsl(${contact.availability}, 70%, 50%)`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* Quick message Popup */}
            {state.showComposePopup && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="fixed bottom-24 right-6 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-xl z-50"
              >
                <div className="p-4">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold dark:text-white">
                      Nouveau message
                    </h3>
                    <button
                      onClick={() =>
                        setState((prev) => ({
                          ...prev,
                          showComposePopup: false,
                        }))
                      }
                      className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                    >
                      ×
                    </button>
                  </div>

                  <form
                    className="space-y-4"
                    onSubmit={async (e) => {
                      e.preventDefault();
                      if (!emailAPIService.isAuthenticated()) {
                        alert("Veuillez vous connecter pour envoyer un email");
                        return;
                      }

                      // Get form data
                      const formData = new FormData(e.currentTarget);
                      const to = (formData.get("to") as string)
                        .split(",")
                        .map((e) => e.trim());
                      const cc = (formData.get("cc") as string)
                        .split(",")
                        .map((e) => e.trim());
                      const subject = formData.get("subject") as string;
                      const body = formData.get("body") as string;

                      try {
                        const result = await emailAPIService.sendEmail({
                          subject,
                          from: "", // The API will use the authenticated user's email
                          to,
                          cc,
                          body,
                          bodyType: "text",
                          attachments: [],
                          categories: [],
                          importance: "normal",
                          isRead: true,
                        });

                        if (result.success) {
                          alert("Message envoyé avec succès!");
                          setState((prev) => ({
                            ...prev,
                            showComposePopup: false,
                          }));
                          // Refresh emails to include the sent message
                          fetchEmails();
                        } else {
                          alert(
                            "Échec de l'envoi du message. Veuillez réessayer."
                          );
                        }
                      } catch (error) {
                        console.error("Error sending email:", error);
                        alert(
                          "Une erreur s'est produite lors de l'envoi du message."
                        );
                      }
                    }}
                  >
                    <div>
                      <input
                        type="email"
                        name="to"
                        placeholder="À"
                        className="w-full px-3 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                        onChange={(e) => {
                          // Simulate recipient availability (we'll fetch this when we have the backend)
                          setState((prev) => ({
                            ...prev,
                            recipientAvailability: Math.random() * 100,
                          }));
                        }}
                        required
                      />
                    </div>

                    <div>
                      <input
                        type="email"
                        name="cc"
                        placeholder="Cc"
                        className="w-full px-3 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                      />
                    </div>

                    <div>
                      <input
                        type="text"
                        name="subject"
                        placeholder="Objet"
                        className="w-full px-3 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                        required
                      />
                    </div>

                    {state.recipientAvailability !== undefined && (
                      <div className="flex items-center space-x-2">
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Disponibilité du destinataire:
                        </div>
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full transition-all duration-300"
                            style={{
                              width: `${state.recipientAvailability}%`,
                              backgroundColor: `hsl(${state.recipientAvailability}, 70%, 50%)`,
                            }}
                          />
                        </div>
                      </div>
                    )}

                    <textarea
                      name="body"
                      placeholder="Message"
                      rows={4}
                      className="w-full px-3 py-2 border dark:border-gray-600 rounded-lg resize-none dark:bg-gray-700 dark:text-white"
                      required
                    />

                    <div className="flex justify-end">
                      <motion.button
                        type="submit"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                      >
                        Envoyer
                      </motion.button>
                    </div>
                  </form>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </main>
      <SearchPopup
        isOpen={state.showSearchPopup}
        onClose={() =>
          setState((prev) => ({ ...prev, showSearchPopup: false }))
        }
      />
    </div>
  );
};

export default Home;
