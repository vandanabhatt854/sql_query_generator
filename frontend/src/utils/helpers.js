export function formatDate(timestamp) {
  return new Date(timestamp).toLocaleString();
}

export function truncate(text, length = 100) {
  return text.length > length ? `${text.slice(0, length)}...` : text;
}
