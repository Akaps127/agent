import React from 'react';

export const Tooltip = ({ content }: { content: string }) => {
    return (
        <div className="group relative flex items-center justify-center cursor-help">
            <div className="flex items-center justify-center w-5 h-5 rounded-full bg-neutral-100 text-neutral-500 text-xs font-bold border border-neutral-200 group-hover:bg-primary-50 group-hover:text-primary-600 group-hover:border-primary-200 transition-colors">
                ?
            </div>
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[200px] px-3 py-2 bg-neutral-800 text-white text-xs rounded-lg shadow-xl opacity-0 translate-y-2 pointer-events-none group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-200 z-50">
                {content}
                <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-neutral-800" />
            </div>
        </div>
    );
};
