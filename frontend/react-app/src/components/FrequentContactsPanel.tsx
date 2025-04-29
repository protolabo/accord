import React from "react";
import { motion } from "framer-motion";

interface Contact {
  id: string;
  name: string;
  email: string;
  availability: number;
  lastContact ?: string;
}

interface FrequentContactsPanelProps {
  contacts: Contact[];
}

const FrequentContactsPanel: React.FC<FrequentContactsPanelProps> = ({ contacts }) => {
  return (
    <div className="fixed right-6 top-24 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 z-40">
      <h3 className="text-lg font-semibold mb-4 dark:text-white">
        Contacts fréquents
      </h3>
      <div className="space-y-4">
        {contacts.map((contact) => (
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
  );
};

export default FrequentContactsPanel;