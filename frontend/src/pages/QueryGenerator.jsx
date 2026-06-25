import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { generateQuery } from '../services/queryService';

export default function QueryGenerator() {
  const [queryText, setQueryText] = useState('');
  const [generatedSql, setGeneratedSql] = useState('');
  const [generatedExplanation, setGeneratedExplanation] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!queryText.trim()) return;
    setLoading(true);
    setError('');
    setGeneratedSql('');
    setGeneratedExplanation('');

    try {
      const response = await generateQuery({ nl_query: queryText });
      const candidate = response.data?.candidates?.[0];
      if (candidate) {
        setGeneratedSql(candidate.sql || 'No SQL generated');
        setGeneratedExplanation(candidate.explanation?.summary || 'No explanation available');
      } else {
        setError('No SQL query could be generated from that input.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to generate query.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      handleGenerate();
    }
  };

  return (
    <div className="page-container">
      <div className="page-header-card">
        <div>
          <h1 className="page-title">SQL Query Generator</h1>
          <p className="page-subtitle">Convert natural language to optimized SQL queries</p>
        </div>
      </div>

      <div className="query-card">
        <label className="query-label">Describe your query in plain English</label>
        <textarea
          className="query-textarea"
          placeholder="e.g., Show me all employees in the IT department with their salaries"
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button className="generate-button" onClick={handleGenerate} disabled={loading || !queryText.trim()}>
          {loading ? 'Generating...' : 'Generate SQL Query'}
        </button>
        <p className="tip-text">Tip: Press Ctrl+Enter to generate</p>
        {error && <p className="error-text">{error}</p>}
        {generatedSql && (
          <div className="response-card">
            <h2 className="response-title">Generated SQL</h2>
            <pre className="response-output">{generatedSql}</pre>
            {generatedExplanation && <p className="response-explanation">{generatedExplanation}</p>}
          </div>
        )}
      </div>
    </div>
  );
}
