import React from "react";

const ActionBox = ({ title, children }) => {
  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg shadow-md">
      <h3 className="font-semibold mb-2 dark:text-white">{title}</h3>
      <div>{children}</div>
    </div>
  );
};

export default ActionBox;
