/**
 * API client utilities.
 *
 * All requests go through the Next.js API route handlers (/api/*)
 * which proxy to the Python backend. This avoids CORS issues and
 * keeps the backend URL server-side only.
 */

export async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(endpoint, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export function createSSEStream(endpoint: string): EventSource {
  return new EventSource(endpoint);
}
