import React, { HTMLAttributes } from 'react';
import clsx from 'clsx';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined' | 'elevated';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export function Card({
  children,
  variant = 'default',
  padding = 'md',
  className,
  ...props
}: CardProps) {
  const variants = {
    default: 'bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border',
    outlined: 'bg-transparent border-2 border-gray-300 dark:border-gray-600',
    elevated: 'bg-white dark:bg-dark-card shadow-lg',
  };

  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  return (
    <div
      className={clsx('rounded-lg', variants[variant], paddings[padding], className)}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('mb-4', className)}>{children}</div>;
}

export function CardTitle({ children, className }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={clsx('text-lg font-semibold text-gray-900 dark:text-white', className)}>
      {children}
    </h3>
  );
}

export function CardContent({ children, className }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx(className)}>{children}</div>;
}

export function CardFooter({ children, className }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('mt-4 pt-4 border-t dark:border-dark-border', className)}>{children}</div>;
}
