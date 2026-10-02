export function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

export function formatTime(date: Date): string {
  const time = date.toTimeString();
  return time.split(' ')[0];
}
