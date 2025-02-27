import React from 'react';

export interface ResizeHandleProps {
    index: number;
    onResizeStart: (index: number, clientX: number) => void;
}

const ResizeHandle: React.FC<ResizeHandleProps> = ({ index, onResizeStart }) => {
    return (
        <div
            className="relative z-10 w-1 mx-1 cursor-col-resize group"
            onMouseDown={(e) => onResizeStart(index, e.clientX)}
        >
            <div className="absolute inset-0 w-4 -left-1.5 group-hover:bg-blue-500/10 transition-colors duration-200"></div>
            <div className="h-full w-full bg-gray-200 dark:bg-gray-600 group-hover:bg-blue-500 transition-colors duration-200"></div>
        </div>
    );
};

export default ResizeHandle;