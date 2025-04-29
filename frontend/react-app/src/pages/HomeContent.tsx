import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  FaExpand,
  FaCompress,
} from "react-icons/fa";
import AttentionGauge from "../components/AttentionGauge";
import ActionItem from "../components/ActionItem";
import InfoItem from "../components/InfoItem";
import ThreadSection from "./ThreadSection";
import ResizeHandle from "../components/ResizeHandle";
import { mockPriorityLevels, mockEstimatedTimes, mockTopContacts } from "../data/mockData";
import ComposePopup from "../components/ComposePopup";
import ContactsAdapter from "../components/ContactsAdapter";
import SearchPopup from "../components/search/SearchPopup";

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

interface HomeContentProps {
  isLoading: boolean;
  sectionSizes: {
    [key: string]: number;
  };
  isResizing: boolean;
  filteredEmails: Email[];
  handleSectionResize: (
    sectionName: string,
    action: "expand" | "collapse" | "reset"
  ) => void;
  handleResizeStart: (index: number, clientX: number) => void;
  handleThreadSelect: (email: Email) => void;
  groupedEmails: {
    [key: string]: Email[];
  };
  showSearchPopup: boolean;
  setShowSearchPopup: (show: boolean) => void;
  fetchEmails: () => Promise<void>;
}

const HomeContent: React.FC<HomeContentProps> = ({
  isLoading,
  sectionSizes,
  isResizing,
  filteredEmails,
  handleSectionResize,
  handleResizeStart,
  handleThreadSelect,
  groupedEmails,
  showSearchPopup,
  setShowSearchPopup,
  fetchEmails,
}) => {
  const sectionRefs = useRef<Array<HTMLDivElement | null>>([]);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [showComposePopup, setShowComposePopup] = useState(false);
  const [recipientAvailability, setRecipientAvailability] = useState<number | undefined>(undefined);

  // Calculate total width to normalize sizes
  const totalSize = Object.values(sectionSizes).reduce((a, b) => a + b, 0);

  // Define available time in minutes (e.g., 8 hours = 480 minutes)
  const availableTime = 480 - (new Date().getHours() * 60 + new Date().getMinutes());

  // Example data for total actions
  const totalActions = {
    Actions: 500,
    Threads: 300,
    Informations: 200,
  };

  return (
    <div
      ref={containerRef}
      className="flex flex-col md:flex-row justify-center items-stretch gap-0 max-w-[85rem] mx-auto"
      style={{ cursor: isResizing ? "col-resize" : "default" }}
    >
      {(
        ["Actions", "Threads", "Informations"] as Array<
          keyof typeof totalActions
        >
      ).map((section, index) => {
        // Calculate the width percentage
        const sizePercent = (sectionSizes[section] / totalSize) * 100;
        const isExpanded = sectionSizes[section] > 1;

        return (
          <React.Fragment key={section}>
            <motion.div
              ref={(el) => {
                sectionRefs.current[index] = el;
              }}
              layout
              animate={{ width: `${sizePercent}%` }}
              transition={{
                type: isResizing ? "tween" : "spring",
                duration: isResizing ? 0 : 0.3,
                stiffness: 300,
                damping: 30,
              }}
              className="w-full md:h-[calc(100vh-192px)] bg-white dark:bg-gray-800 shadow-lg rounded-xl
            overflow-hidden flex flex-col select-none"
              style={{ userSelect: isResizing ? "none" : "auto" }}
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
                        onClick={() => handleSectionResize(section, "reset")}
                        className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                        title="Réinitialiser"
                      >
                        <FaCompress className="text-gray-500 dark:text-gray-400" />
                      </motion.button>
                    ) : (
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleSectionResize(section, "expand")}
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
                {isLoading ? (
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

            {index < ["Actions", "Threads", "Informations"].length - 1 && (
              <ResizeHandle index={index} onResizeStart={handleResizeStart} />
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
        onClick={() => setShowComposePopup(true)}
      >
        <span className="text-2xl font-bold">+</span>
      </motion.button>

      {/* Frequent contacts Panel */}
      <ContactsAdapter contacts={mockTopContacts} />

      {/* Quick message Popup */}
      {showComposePopup && (
        <ComposePopup
          onClose={() => setShowComposePopup(false)}
          onSend={() => {
            setShowComposePopup(false);
            fetchEmails();
          }}
          onRecipientChange={() => setRecipientAvailability(Math.random() * 100)}
          recipientAvailability={recipientAvailability}
        />
      )}

      <SearchPopup
        isOpen={showSearchPopup}
        onClose={() => setShowSearchPopup(false)}
      />
    </div>
  );
};

export default HomeContent;