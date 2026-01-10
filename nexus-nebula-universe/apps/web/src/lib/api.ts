export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL!;

export async function authedFetch(path: string, accessToken: string, init?: RequestInit) {
  return fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers || {}),
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json"
    }
  });
}
