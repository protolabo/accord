import React from "react";
import { motion } from "framer-motion";
import { FaArrowLeft, FaCalendar, FaRobot } from "react-icons/fa";
import { useNavigate, useParams } from "react-router-dom";

interface ThreadDetailProps {
  category: string;
  emails: any[]; // Remplacer par le bon type
}

const ThreadDetail: React.FC = () => {
  const navigate = useNavigate();

  const { category } = useParams();

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-lg p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate(-1)}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <FaArrowLeft className="text-xl text-gray-600 dark:text-gray-300" />
            </motion.button>
            <h1 className="text-2xl font-bold dark:text-white">{category}</h1>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex gap-6">
          {/* Left Side - Email List */}
          <div className="w-1/2 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">
              Emails
            </h2>
            <div className="space-y-4">
              {emails.map((email) => (
                <motion.div
                  key={email["Message-ID"]}
                  whileHover={{ scale: 1.02 }}
                  className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold dark:text-white">
                        {email.Subject}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                        {email.Body}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        From: {email.From}
                      </p>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(email.Date).toLocaleDateString()}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Right Side */}
          <div className="w-1/2 space-y-6">
            {/* Upcoming Meetings */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold dark:text-white">
                  Upcoming Meetings
                </h2>
                <FaCalendar className="text-gray-500 dark:text-gray-400" />
              </div>
              <div className="space-y-3">
                {/* Placeholder pour les réunions */}
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="font-medium dark:text-white">Project Review</p>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    Tomorrow, 10:00 AM
                  </p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="font-medium dark:text-white">Team Sync</p>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    Friday, 2:00 PM
                  </p>
                </div>
              </div>
            </div>

            {/* AI Summary */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold dark:text-white">
                  AI Summary
                </h2>
                <FaRobot className="text-gray-500 dark:text-gray-400" />
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-gray-700 dark:text-gray-300">
                  Project progress: 75% complete. Key milestones achieved in the
                  last week. Next steps include team coordination and final
                  review.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreadDetail;
