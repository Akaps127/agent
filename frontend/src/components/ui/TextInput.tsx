import React from 'react';
import { clsx } from 'clsx';
import { Tooltip } from './Tooltip';

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    suffix?: string;
    helperText?: string;
    required?: boolean;
    tooltip?: string;
}

export const TextInput = React.forwardRef<HTMLInputElement, TextInputProps>(
    ({ label, error, suffix, helperText, className, required, tooltip, ...props }, ref) => {
        return (
            <div className={clsx("flex flex-col gap-1.5", className)}>
                {label && (
                    <div className="flex items-center gap-1.5">
                        <label className="text-sm font-semibold text-neutral-700">
                            {label}
                            {required && <span className="text-primary-600 ml-0.5" aria-label="필수">*</span>}
                        </label>
                        {tooltip && <Tooltip content={tooltip} />}
                    </div>
                )}

                <div className="relative flex items-center">
                    <input
                        ref={ref}
                        className={clsx(
                            "flex h-11 w-full rounded-xl border bg-white px-4 py-2 text-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-neutral-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50",
                            error
                                ? "border-red-300 focus-visible:ring-red-200 text-red-900 bg-red-50"
                                : "border-neutral-300 focus-visible:border-primary-500 focus-visible:ring-primary-100 text-neutral-900",
                            suffix && "pr-12"
                        )}
                        aria-invalid={!!error}
                        {...props}
                    />
                    {suffix && (
                        <div className="absolute right-4 flex items-center pointer-events-none text-neutral-500 text-sm font-medium">
                            {suffix}
                        </div>
                    )}
                </div>

                {error && <p className="text-xs font-medium text-red-600 animate-pulse">{error}</p>}
                {!error && helperText && <p className="text-xs text-neutral-500">{helperText}</p>}
            </div>
        );
    }
);

TextInput.displayName = "TextInput";
