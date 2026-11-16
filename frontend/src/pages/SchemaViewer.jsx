import React,{useEffect,useState} from 'react';
import {fetchSchema} from '../services/schemaService';
export default function SchemaViewer(){
 const [schema,setSchema]=useState({}),[loading,setLoading]=useState(true),[error,setError]=useState('');
 useEffect(()=>{let active=true;fetchSchema().then(({data})=>{if(active)setSchema(data);}).catch(()=>{if(active)setError('Unable to load the database schema. Try again shortly.');}).finally(()=>{if(active)setLoading(false);});return()=>{active=false;};},[]);
 return <main className="utility-page"><h1>Database Schema</h1><p>Use these tables and fields in your English requests.</p>{loading&&<p role="status">Loading schema...</p>}{error&&<p className="error-banner" role="alert">{error}</p>}<div className="schema-grid">{Object.entries(schema).map(([name,meta])=><section className="panel utility-card" key={name}><h2>{name}</h2><div className="results-table-wrap"><table className="results-table"><thead><tr><th>Column</th><th>Type</th><th>Nullable</th></tr></thead><tbody>{meta.columns.map(col=><tr key={col.name}><td>{col.name}</td><td>{col.type}</td><td>{col.nullable?'Yes':'No'}</td></tr>)}</tbody></table></div>{meta.relationships?.map((r,i)=><p key={i}>{r.columns.join(', ')} references {r.referred_table} ({r.referred_columns.join(', ')})</p>)}</section>)}</div></main>;
}
