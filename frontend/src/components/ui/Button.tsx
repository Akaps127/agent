import React from 'react';
import { clsx } from 'clsx'; // Assuming clsx is available since it was in package.json

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'outline';
    size?: 'sm' | 'md' | 'lg';
    fullWidth?: boolean;
}

export const Button = ({
    className,
    variant = 'primary',
    size = 'md',
    fullWidth = false,
    children,
    ...props
}: ButtonProps) => {
    const baseStyles = "inline-flex items-center justify-center rounded-full font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 disabled:pointer-events-none disabled:opacity-50 active:scale-95 transition-transform duration-75";

    const variants = {
        primary: "bg-primary-600 text-white hover:bg-primary-700 shadow-soft hover:shadow-medium",
        secondary: "bg-eco-500 text-white hover:bg-eco-600 shadow-soft hover:shadow-medium",
        outline: "border border-neutral-300 bg-white text-neutral-700 hover:bg-neutral-50 hover:text-primary-600 hover:border-primary-200",
        ghost: "bg-transparent text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900",
    };

    const sizes = {
        sm: "h-8 px-3 text-xs",
        md: "h-11 px-6 text-sm",
        lg: "h-12 px-8 text-base",
    };

    return (
        <button
            className={clsx(
                baseStyles,
                variants[variant],
                sizes[size],
                fullWidth && "w-full",
                className
            )}
            {...props}
        >
            {children}
        </button>
    );
};
