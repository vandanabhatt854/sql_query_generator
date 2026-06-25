import { useEffect } from 'react';
import { fetchSchema } from '../services/schemaService';

export default function useSchema(setSchema) {
  useEffect(() => {
    fetchSchema().then((res) => setSchema(res.data)).catch(() => {});
  }, [setSchema]);
}
