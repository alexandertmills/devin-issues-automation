import React from 'react';
import { Bell } from 'lucide-react';

interface CowbellIconProps {
  isAnimated?: boolean;
  size?: number;
  className?: string;
  onClick?: () => void;
}

export const CowbellIcon: React.FC<CowbellIconProps> = ({ 
  isAnimated = false, 
  size = 20,
  className = "",
  onClick
}) => {
  const animationClass = isAnimated ? 'animate-bounce' : '';
  
  return (
    <div 
      className={`inline-flex items-center ${className}`}
      onClick={onClick}
    >
      <Bell 
        size={size} 
        className={`text-yellow-600 ${animationClass}`}
        style={{ 
          filter: 'drop-shadow(0 0 4px rgba(251, 191, 36, 0.5))'
        }}
      />
      <span className="ml-1 text-xs font-bold text-yellow-600">
        🔔
      </span>
    </div>
  );
};
