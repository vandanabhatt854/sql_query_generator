import { useContext } from 'react';
import { QueryContext } from '../context/QueryContext';

export default function useQuery() {
  return useContext(QueryContext);
}
