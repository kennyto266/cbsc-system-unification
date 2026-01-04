import React from 'react';
import { LucideIcon } from 'lucide-react';

// Page Props Interface
interface PageTemplateProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  headerActions?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

/**
 * PageTemplate Component
 * All pages unified wrapper with dark theme
 */
export const PageTemplate: React.FC<PageTemplateProps> = ({
  title,
  description,
  icon: Icon,
  headerActions,
  children,
  footer,
}) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 font-['Outfit']">
      {/* Custom animations */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fadeIn 0.4s ease-out;
        }
        .animate-fade-in-up {
          animation: fadeInUp 0.5s ease-out;
        }
        /* Custom scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        ::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.5);
        }
        ::-webkit-scrollbar-thumb {
          background: rgba(51, 65, 85, 0.8);
          border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: rgba(71, 85, 105, 0.9);
        }
      `}</style>

      {/* Page Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <header className="mb-8 animate-fade-in">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              {Icon && (
                <div className="p-3 bg-slate-900/50 border border-slate-800/50 rounded-xl">
                  <Icon className="w-6 h-6 text-cyan-400" />
                </div>
              )}
              <div>
                <h1 className="text-3xl font-bold text-slate-100">
                  {title}
                </h1>
                {description && (
                  <p className="mt-1 text-sm text-slate-400">
                    {description}
                  </p>
                )}
              </div>
            </div>
            {headerActions && (
              <div className="flex items-center gap-3">
                {headerActions}
              </div>
            )}
          </div>
        </header>

        {/* Content Section */}
        <main className="animate-fade-in-up">
          {children}
        </main>

        {/* Footer Section */}
        {footer && (
          <footer className="mt-8 pt-6 border-t border-slate-800/50 animate-fade-in">
            {footer}
          </footer>
        )}
      </div>
    </div>
  );
};

/**
 * Card Component
 * Unified card component with dark theme
 */
interface CardProps {
  title?: string;
  icon?: LucideIcon;
  className?: string;
  children: React.ReactNode;
  delay?: number;
}

export const Card: React.FC<CardProps> = ({
  title,
  icon: Icon,
  className = '',
  children,
  delay = 0,
}) => {
  return (
    <div
      className={`
        bg-slate-900/50 border border-slate-800/50
        rounded-xl p-6 backdrop-blur-sm
        hover:bg-slate-800/50 hover:border-slate-700/50
        transition-all duration-300 ease-out
        animate-fade-in-up
        ${className}
      `}
      style={{ animationDelay: `${delay}ms` }}
    >
      {(title || Icon) && (
        <div className="flex items-center gap-3 mb-4">
          {Icon && <Icon className="w-5 h-5 text-cyan-400" />}
          {title && (
            <h3 className="text-lg font-semibold text-slate-100">
              {title}
            </h3>
          )}
        </div>
      )}
      {children}
    </div>
  );
};

/**
 * StatCard Component
 * Data statistics card
 */
interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  suffix?: string;
  icon?: LucideIcon;
  delay?: number;
  colorClass?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  suffix = '',
  icon: Icon,
  delay = 0,
  colorClass = 'text-cyan-400',
}) => {
  const isPositive = change !== undefined && change > 0;
  const isNegative = change !== undefined && change < 0;

  return (
    <div
      className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300"
      style={{ animation: `fadeInUp 0.5s ease-out ${delay}ms both` }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={`text-3xl font-bold font-['JetBrains_Mono'] ${colorClass}`}>
            {value}{suffix}
          </p>
          {change !== undefined && (
            <div className={`mt-2 flex items-center gap-1 text-sm font-['JetBrains_Mono'] ${
              isPositive ? 'text-emerald-400' : isNegative ? 'text-rose-400' : 'text-slate-400'
            }`}>
              {isPositive && '↑'}
              {isNegative && '↓'}
              <span>{Math.abs(change)}%</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className={`p-4 rounded-xl bg-gradient-to-br ${
            isPositive ? 'from-emerald-500/20 to-emerald-600/20' :
            isNegative ? 'from-rose-500/20 to-rose-600/20' :
            'from-cyan-500/20 to-cyan-600/20'
          }`}>
            <Icon className={`w-6 h-6 ${
              isPositive ? 'text-emerald-400' :
              isNegative ? 'text-rose-400' :
              colorClass
            }`} />
          </div>
        )}
      </div>
    </div>
  );
};

export default PageTemplate;
