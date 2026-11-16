import React, { useEffect, useRef, useState } from 'react';
import { executeQuery, generateQuery, getGenerationStatus } from '../services/queryService';

const EXAMPLES = ['Show me all employees from the sales department', 'Show me all employees hired between 2020 and 2022', 'Count how many employees are in each department', 'Calculate total salary', 'Show all employees whose salary is greater than 50,000', 'Maximum salary', 'Who earns the most?', 'Show employees who joined last year', 'What is the average salary in each department?', 'Get all students enrolled in Computer Science'];
const errorMessage = (error, fallback) => {
  const detail = error.response?.data?.detail;
  return typeof detail === 'string' ? detail : detail?.message || fallback;
};

export default function QueryGenerator() {
  const [queryText, setQueryText] = useState('');
  const [generated, setGenerated] = useState(null);
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [executionMessage, setExecutionMessage] = useState('');
  const [status, setStatus] = useState(null);
  const detailsRef = useRef(null);
  const busy = loading || executing;
  const explanation = generated?.explanation || {};
  const tips = explanation.optimization_tips || [];

  useEffect(() => {
    let active = true;
    getGenerationStatus().then(({ data }) => { if (active) setStatus(data); }).catch(() => {});
    return () => { active = false; };
  }, []);

  async function generate(input = queryText) {
    if (busy || !input.trim()) return;
    setLoading(true); setError(''); setGenerated(null); setRows([]); setExecutionMessage('');
    try {
      const { data } = await generateQuery({ nl_query: input.trim() });
      if (!data.candidates?.[0]) throw new Error('No candidate');
      setGenerated(data.candidates[0]);
    } catch (err) {
      setError(errorMessage(err, 'Unable to generate SQL. Please try again.'));
    } finally { setLoading(false); }
  }

  async function execute() {
    if (!generated?.sql || busy) return;
    setExecuting(true); setError(''); setRows([]); setExecutionMessage('');
    try {
      const { data } = await executeQuery(generated.sql);
      if (data.success === false || data.error) throw new Error(data.error || 'Execution failed');
      setRows(data.rows || []);
      setExecutionMessage(data.simulated ? `Write preview only. ${data.rows_affected == null ? 'Affected-row count is unavailable' : `${data.rows_affected} rows would be affected`}; no data changed.` : data.rows?.length ? `${data.rows.length} rows returned.` : 'Query completed. No matching rows returned.');
    } catch (err) { setError(errorMessage(err, err.message || 'Unable to execute query.')); }
    finally { setExecuting(false); }
  }

  async function copy() {
    try { await navigator.clipboard.writeText(generated.sql); setCopied(true); setTimeout(() => setCopied(false), 2000); }
    catch { setError('Unable to copy. Please select and copy the SQL manually.'); }
  }

  return <div className="generator-shell">
    <header className="generator-header"><span className="generator-mark" aria-hidden="true">◦</span><div><h1>SQL Query Generator</h1><p>Convert natural language to optimized SQL queries</p></div></header>
    <div className="generator-grid">
      <section className="panel panel-compose">
        <label className="compose-label" htmlFor="query-input">Describe your query in natural language</label>
        <textarea id="query-input" className="compose-input" maxLength={500} placeholder="e.g., What is the average salary in each department?" value={queryText} disabled={busy} onChange={e => setQueryText(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); generate(); } }} />
        <p className="compose-hint">Press Enter to generate. Shift+Enter for new line</p>
        {status && <p className="generation-status" role="status">{status.message}</p>}
        <button className="primary-button" onClick={() => generate()} disabled={busy || !queryText.trim()}>{loading ? 'Generating...' : 'Generate SQL Query'}</button>
        {error && <div className="error-banner" role="alert">{error}</div>}
      </section>
      <section className="panel panel-result"><div className="panel-header"><h2 className="panel-title">Generated SQL Query</h2><button className="icon-button" onClick={copy} disabled={!generated?.sql} aria-label={copied ? 'SQL copied' : 'Copy SQL'} title={copied ? 'Copied!' : 'Copy SQL'}>{copied ? '✓' : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><rect x="9" y="9" width="11" height="12" rx="1"/><path d="M15 9V3H4v12h5"/></svg>}</button></div><pre className="sql-block">{generated?.sql || 'Your SQL output will appear here.'}</pre></section>
      <section className="panel panel-examples"><h2 className="panel-title">Example Queries</h2><div className="example-list">{EXAMPLES.map(example => <button key={example} disabled={busy} className={`example-item ${queryText === example ? 'is-active' : ''}`} onClick={() => { setQueryText(example); generate(example); }}>{example}</button>)}</div></section>
      <section className="panel panel-actions"><button className="secondary-button" disabled={busy || !generated?.sql} onClick={execute}>{executing ? 'Executing...' : '▶ Execute Query'}</button><button className="secondary-button secondary-button-light" disabled={!generated} onClick={() => detailsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })}>✧ Explain</button></section>
      <section className="panel panel-details" ref={detailsRef}><h2 className="panel-title">Query Details</h2><div className="details-stack">
        {generated ? <>
          {[['SQL CONCEPT', explanation.sql_concept || 'Generated SQL'], ['QUERY EXPLANATION', explanation.query_explanation || explanation.summary], ['EXPECTED OUTPUT', explanation.expected_output]].map(([label, value]) => <div className="detail-block" key={label}><div className="detail-label">{label}</div><div className="detail-value">{value || 'Generate the query again to load its details.'}</div></div>)}
          <div className="detail-block"><div className="detail-label">OPTIMIZATION TIPS</div><div className="detail-value">{tips.length ? <ul className="tips-list">{tips.map(tip => <li key={tip}>{tip}</li>)}</ul> : generated.optimization_suggestion || 'No additional optimization required for this query.'}</div></div>
          {generated.risk_warning && <div className="risk-note">{generated.risk_warning}</div>}
        </> : <p className="detail-value">Generate a query to see its explanation and optimization tips.</p>}
        {executionMessage && <p className="detail-value" role="status">{executionMessage}</p>}
        {rows.length > 0 && <div className="results-block"><div className="detail-label">QUERY OUTPUT</div><div className="results-table-wrap"><table className="results-table"><thead><tr>{Object.keys(rows[0]).map(col => <th key={col}>{col}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{Object.values(row).map((value, i) => <td key={i}>{value === null ? 'NULL' : String(value)}</td>)}</tr>)}</tbody></table></div></div>}
      </div></section>
    </div>
  </div>;
}
