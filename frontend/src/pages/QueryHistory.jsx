import React,{useEffect,useState} from 'react';
import {fetchHistory} from '../services/historyService';
export default function QueryHistory(){
 const [rows,setRows]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState('');
 useEffect(()=>{let active=true;fetchHistory().then(({data})=>{if(active)setRows(data);}).catch(()=>{if(active)setError('Unable to load history. Check the backend connection.');}).finally(()=>{if(active)setLoading(false);});return()=>{active=false;};},[]);
 return <main className="utility-page"><h1>Query History</h1><p>Shared query activity on this local demo.</p>{loading && <p role="status">Loading history...</p>}{error && <p role="alert" className="error-banner">{error}</p>}{!loading&&!error&&!rows.length&&<p>No queries yet. Generate your first query to start history.</p>}<div className="details-stack">{rows.map((row,index)=><article className="panel utility-card" key={index}><div className="detail-label">{row.execution_status} | {new Date(row.timestamp+'Z').toLocaleString()}</div>{row.nl_input&&<p>{row.nl_input}</p>}<pre className="sql-block">{row.sql_generated}</pre>{row.rows_returned!=null&&<p>{row.rows_returned} rows returned</p>}{row.risk_warning&&<p className="risk-note">{row.risk_warning}</p>}</article>)}</div></main>;
}
