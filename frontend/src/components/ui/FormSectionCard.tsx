import React from 'react';
import { clsx } from 'clsx';

interface FormSectionCardProps {
    title: string;
    description?: string;
    children: React.ReactNode;
    className?: string;
}

export const FormSectionCard = ({ title, description, children, className }: FormSectionCardProps) => {
    return (
        <section className={clsx("bg-white rounded-[20px] shadow-soft border border-neutral-100 p-8 hover:shadow-medium transition-shadow duration-300", className)}>
            <div className="mb-6 pb-4 border-b border-neutral-100/80">
                <h3 className="text-xl font-bold text-neutral-800 flex items-center gap-2">
                    <span className="w-1.5 h-6 bg-primary-500 rounded-full" />
                    {title}
                </h3>
                {description && <p className="text-sm text-neutral-500 mt-2 pl-4 ml-0.5">{description}</p>}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6 pl-1">
                {children}
            </div>
        </section>
    );
};
