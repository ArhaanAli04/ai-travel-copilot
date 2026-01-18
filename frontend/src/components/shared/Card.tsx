import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'glass' | 'alert';
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className = '', 
  variant = 'glass',
  onClick 
}) => {
  const baseStyles = "rounded-xl p-6 transition-all duration-300";
  
  const variantStyles = {
    default: "bg-[#1a1d24] border border-[rgba(148,163,184,0.2)]",
    glass: "bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] shadow-lg",
    alert: "bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/30 backdrop-blur-xl"
  };

  const hoverStyles = onClick ? "cursor-pointer hover:scale-[1.02] hover:border-[rgba(148,163,184,0.4)]" : "";

  return (
    <div 
      className={`${baseStyles} ${variantStyles[variant]} ${hoverStyles} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export default Card;
