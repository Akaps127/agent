import React, { useId } from 'react';
import { clsx } from 'clsx';

interface Option {
    label: string;
    value: string;
}

interface SegmentedControlProps {
    options: Option[];
    value: string;
    onChange: (value: string) => void;
    label?: string;
    type?: 'tabs' | 'pills'; // tabs for text-only underline/segment style, pills for boxed toggle
    className?: string;
}

export const SegmentedControl = ({
    options,
    value,
    onChange,
    label,
    type = 'pills',
    className,
}: SegmentedControlProps) => {
    const name = useId();

    return (
        <div className={clsx("flex flex-col gap-2", className)}>
            {label && <span className="text-sm font-semibold text-neutral-700">{label}</span>}

            <div
                className={clsx(
                    "flex overflow-hidden",
                    type === 'pills' ? "flex-wrap gap-2" : "bg-neutral-100 p-1 rounded-lg gap-1"
                )}
                role="radiogroup"
                aria-label={label}
            >
                {options.map((opt) => {
                    const isSelected = value === opt.value;
                    return (
                        <button
                            key={opt.value}
                            type="button"
                            role="radio"
                            aria-checked={isSelected}
                            onClick={() => onChange(opt.value)}
                            className={clsx(
                                "relative flex items-center justify-center transition-all duration-200 ease-out focus-visible:ring-2 focus-visible:ring-primary-500 focus:outline-none",
                                type === 'pills'
                                    ? [
                                        "h-10 px-5 rounded-full border text-sm font-medium",
                                        isSelected
                                            ? "bg-primary-50 border-primary-500 text-primary-700 shadow-sm font-bold ring-1 ring-primary-500"
                                            : "bg-white border-neutral-300 text-neutral-600 hover:bg-neutral-50 hover:border-neutral-400"
                                    ]
                                    : [
                                        "flex-1 h-9 rounded-md text-sm font-medium",
                                        isSelected
                                            ? "bg-white text-primary-700 shadow-sm font-bold"
                                            : "text-neutral-500 hover:text-neutral-700 hover:bg-neutral-200/50"
                                    ]
                            )}
                        >
                            {isSelected && type === 'pills' && (
                                <div className="absolute inset-0 rounded-full bg-primary-500/5 pointer-events-none animate-pulse" />
                            )}
                            {opt.label}
                        </button>
                    );
                })}
            </div>
        </div>
    );
};
