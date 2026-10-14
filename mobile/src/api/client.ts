import { config } from "../config";
import { supabase } from '../lib/supabase';

const API_URL = process.env.EXPO_PUBLIC_API_URL;

const TIMEOUT_MS = 10_000;

export class ApiError extends Error {
  constructor(
    public readonly status: number | null,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function messageFor(status: number): string {
  if (status === 401 || status === 403) return "Not authorized.";
  if (status === 404) return "Element not found.";
  if (status === 422) return "Invalid data.";
  if (status === 429) return "Too many request, try again later.";
  if (status >= 500) return "Server error, try again later.";
  return "Request failed.";
}

type RequestOptions = { method?: string; body?: unknown };

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  const hasBody = options.body !== undefined;

  try {
    const res = await fetch(`${config.apiUrl}${path}`, {
      method: options.method ?? "GET",
      headers: {
        "X-API-Key": config.apiKey,
        ...(hasBody && { "Content-Type": "application/json" }),
      },
      body: hasBody ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    });

    if (!res.ok) throw new ApiError(res.status, messageFor(res.status));
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    throw new ApiError(null, "Connessione non riuscita.");
  } finally {
    clearTimeout(timer);
  }
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const { data } = await supabase.auth.getSession();
  if (!data.session) {
    throw new Error('NOT_AUTHENTICATED');
  }

  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${data.session.access_token}`);

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });

  if (res.status === 401) {
    await supabase.auth.signOut();
    throw new Error('SESSION_EXPIRED');
  }
  return res;
}