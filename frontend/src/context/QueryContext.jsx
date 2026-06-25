import React, { createContext, useState } from 'react';

export const QueryContext = createContext(null);

export function QueryProvider({ children }) {
  const [queryHistory, setQueryHistory] = useState([]);
  const [currentQuery, setCurrentQuery] = useState('');

  return (
    <QueryContext.Provider value={{ queryHistory, setQueryHistory, currentQuery, setCurrentQuery }}>
      {children}
    </QueryContext.Provider>
  );
}
