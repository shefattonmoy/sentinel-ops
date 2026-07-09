// src/context/ThemeContext.tsx
import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

type ThemeMode = 'light' | 'dark';

interface ThemeModeContextType {
  mode: ThemeMode;
  toggleColorMode: () => void;
}

const ThemeModeContext = createContext<ThemeModeContextType>({
  mode: 'dark',
  toggleColorMode: () => {},
});

export const ThemeModeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [mode, setMode] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem('theme_mode');
    return (saved === 'light' || saved === 'dark') ? saved : 'dark';
  });

  const toggleColorMode = useCallback(() => {
    setMode((prev) => {
      const next = prev === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme_mode', next);
      return next;
    });
  }, []);

  return (
    <ThemeModeContext.Provider value={{ mode, toggleColorMode }}>
      {children}
    </ThemeModeContext.Provider>
  );
};

export const useThemeMode = () => useContext(ThemeModeContext);