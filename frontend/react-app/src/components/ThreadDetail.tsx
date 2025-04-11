import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  FaArrowLeft,
  FaPaperclip,
  FaPaperPlane,
  FaImage,
  FaFile,
  FaTrash,
  FaLightbulb
} from 'react-icons/fa';
import { useNavigate, useLocation } from 'react-router';
import type { ThreadDetailProps, Email, Attachment } from '../components/types';

interface LocationState {
  threadCategory: string;
  emails: Email[];
  currentEmail: Email;
}

const ThreadDetail: React.FC<ThreadDetailProps> = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;

  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [replyText, setReplyText] = useState<string>('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(true);

  const suggestions: string[] = [
    "Je confirme la réception de votre message.",
    "Merci pour votre retour, je vais étudier votre proposition.",
    "Je vous recontacte dès que possible avec plus d'informations."
  ];

  const handleAttachment = (files: FileList | null) => {
    if (!files) return;

    const newAttachments: Attachment[] = Array.from(files).map(file => ({
      name: file.name,
      size: file.size,
      type: file.type
    }));

    setAttachments(prev => [...prev, ...newAttachments]);
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
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
            <h1 className="text-2xl font-bold dark:text-white">
              {state?.threadCategory || "Thread Detail"}
            </h1>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="flex gap-6">
          {/* Email List */}
          <div className="w-1/2 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Messages</h2>
            <div className="space-y-4">
              {state?.emails?.map((email) => (
                <motion.div
                  key={email["Message-ID"]}
                  whileHover={{ scale: 1.02 }}
                  className={`p-4 rounded-lg cursor-pointer transition-colors duration-200 ${
                    selectedEmail?.["Message-ID"] === email["Message-ID"]
                      ? 'bg-blue-50 dark:bg-blue-900'
                      : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600'
                  }`}
                  onClick={() => setSelectedEmail(email)}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold dark:text-white">{email.Subject}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                        {email.Body}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        De : {email.From}
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

          {/* Reply Section */}
          <div className="w-1/2 space-y-6">
            {selectedEmail ? (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-semibold mb-4 dark:text-white">Répondre</h2>

                {/* Suggestions */}
                {showSuggestions && (
                  <div className="mb-4 bg-blue-50 dark:bg-blue-900 p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center">
                        <FaLightbulb className="text-blue-500 mr-2" />
                        <span className="font-medium text-blue-700 dark:text-blue-300">
                          Suggestions de réponse
                        </span>
                      </div>
                      <button
                        onClick={() => setShowSuggestions(false)}
                        className="text-gray-500 hover:text-gray-700 dark:text-gray-400"
                      >
                        ×
                      </button>
                    </div>
                    <div className="space-y-2">
                      {suggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => setReplyText(suggestion)}
                          className="block w-full text-left p-2 rounded hover:bg-blue-100
                          dark:hover:bg-blue-800 text-sm text-gray-700 dark:text-gray-300"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reply Form */}
                <div className="space-y-4">
                  <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Votre réponse..."
                    className="w-full h-40 p-4 border rounded-lg bg-gray-50 dark:bg-gray-700
                    border-gray-200 dark:border-gray-600 focus:ring-2 focus:ring-blue-500
                    focus:border-transparent text-gray-700 dark:text-gray-300"
                  />

                  {/* Attachments */}
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <label className="flex items-center space-x-2 px-4 py-2 bg-gray-100
                      dark:bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-200
                      dark:hover:bg-gray-600">
                        <FaPaperclip className="text-gray-500 dark:text-gray-400" />
                        <span className="text-sm text-gray-600 dark:text-gray-300">
                          Ajouter des fichiers
                        </span>
                        <input
                          type="file"
                          multiple
                          className="hidden"
                          onChange={(e) => handleAttachment(e.target.files)}
                        />
                      </label>
                    </div>

                    {attachments.length > 0 && (
                      <div className="space-y-2">
                        {attachments.map((file, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between p-2 bg-gray-50
                            dark:bg-gray-700 rounded-lg"
                          >
                            <div className="flex items-center space-x-2">
                              {file.type.startsWith('image/') ? (
                                <FaImage className="text-gray-500" />
                              ) : (
                                <FaFile className="text-gray-500" />
                              )}
                              <span className="text-sm text-gray-600 dark:text-gray-300">
                                {file.name}
                              </span>
                            </div>
                            <button
                              onClick={() => removeAttachment(index)}
                              className="text-red-500 hover:text-red-600"
                            >
                              <FaTrash className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Send Button */}
                  <div className="flex justify-end">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="flex items-center space-x-2 px-6 py-2 bg-blue-500 text-white
                      rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      <FaPaperPlane className="w-4 h-4" />
                      <span>Envoyer</span>
                    </motion.button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                Sélectionnez un message pour répondre
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreadDetail;