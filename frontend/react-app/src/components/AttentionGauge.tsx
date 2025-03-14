import React from "react";
import { motion } from "framer-motion";
import { FaExclamationCircle, FaArrowUp, FaArrowDown } from "react-icons/fa";

interface AttentionGaugeProps {
  level: number;
  previousLevel?: number | null;
  section: string;
  estimatedTime: string;
  totalActions: number;
  availableTime: number; // in minutes
}

const AttentionGauge: React.FC<AttentionGaugeProps> = ({
  level,
  previousLevel,
  section,
  estimatedTime,
  totalActions,
  availableTime,
}) => {
  // Calculer la différence si previousLevel existe
  const difference =
    previousLevel !== undefined && previousLevel !== null
      ? level - previousLevel
      : null;

  // Estimation du temps total nécessaire pour compléter toutes les actions
  const estimatedTimePerAction = parseInt(estimatedTime.split(" ")[0], 10);
  const totalEstimatedTime = totalActions * estimatedTimePerAction;

  // Calculer le pourcentage de temps disponible utilisé
  const timeUsagePercentage =
    availableTime > 0
      ? Math.max((totalEstimatedTime / availableTime) * 100, 0)
      : 0;

  const getStatus = (percentage: number) => {
    if (percentage >= 100) return { text: "Critique", color: "text-red-500" };
    if (percentage >= 75) return { text: "Élevé", color: "text-orange-500" };
    if (percentage >= 50) return { text: "Modéré", color: "text-yellow-500" };
    return { text: "Normal", color: "text-green-500" };
  };

  const getGradientColors = (percentage: number) => {
    if (percentage >= 100) return "from-red-500 via-red-400 to-red-300";
    if (percentage >= 75) return "from-orange-500 via-orange-400 to-orange-300";
    if (percentage >= 50) return "from-yellow-500 via-yellow-400 to-yellow-300";
    return "from-green-500 via-green-400 to-green-300";
  };

  const status = getStatus(timeUsagePercentage);

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-xl shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center space-x-2">
          <FaExclamationCircle className={`w-5 h-5 ${status.color}`} />
          <h3 className="text-lg font-semibold dark:text-white">{section}</h3>
        </div>
        <div className="flex items-center space-x-2">
          {difference !== null && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center space-x-1"
            >
              {difference > 0 ? (
                <FaArrowUp className="w-4 h-4 text-red-500" />
              ) : (
                <FaArrowDown className="w-4 h-4 text-green-500" />
              )}
              <span
                className={`text-sm ${
                  difference > 0 ? "text-red-500" : "text-green-500"
                }`}
              >
                {Math.abs(difference)}%
              </span>
            </motion.div>
          )}
          <span className={`text-sm font-medium ${status.color}`}>
            {status.text}
          </span>
        </div>
      </div>

      <div className="relative pt-1">
        <div className="flex justify-between mb-2">
          <span className="text-sm font-medium dark:text-white">
            Niveau d'attention
          </span>
          <span className="text-sm font-semibold dark:text-white">
            {timeUsagePercentage.toFixed(2)}%
          </span>
        </div>

        <div className="w-full h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full bg-gradient-to-r ${getGradientColors(
              timeUsagePercentage
            )}`}
            initial={{ width: 0 }}
            animate={{ width: `${timeUsagePercentage}%` }}
            transition={{
              duration: 1,
              ease: "easeOut",
            }}
          />
        </div>

        <div className="flex justify-between mt-1">
          <div className="w-px h-2 bg-gray-300 dark:bg-gray-600" />
          <div className="w-px h-2 bg-gray-300 dark:bg-gray-600" />
          <div className="w-px h-2 bg-gray-300 dark:bg-gray-600" />
          <div className="w-px h-2 bg-gray-300 dark:bg-gray-600" />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-500 dark:text-gray-400">0%</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">50%</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">100%</span>
        </div>
      </div>

      <div className="flex justify-between items-center mt-4">
        <span className="text-sm font-medium dark:text-white">
          Urgence : {timeUsagePercentage.toFixed(2)}%
        </span>
        <span className="text-sm font-medium dark:text-white">
          Temps estimé : {totalEstimatedTime} minutes
        </span>
      </div>
      <div className="mt-2 text-xs text-gray-600 dark:text-gray-300">
        {section === "Actions" &&
          "Priorité élevée, nécessite une attention immédiate."}
        {section === "Threads" &&
          "Priorité moyenne, nécessite une attention modérée."}
        {section === "Informations" &&
          "Priorité basse, nécessite une attention minimale."}
      </div>
    </div>
  );
};

export default AttentionGauge;
