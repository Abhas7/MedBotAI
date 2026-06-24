import { getToken } from "./auth";

async function getHeaders(requireAuth = true): Promise<HeadersInit> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  
  if (requireAuth) {
    const token = getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  
  return headers;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  user_id: string;
}

export interface Source {
  page_number: number;
  snippet: string;
  score: number;
}

export interface Message {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  sources?: Source[];
}

export async function register(email: string, password: string, fullName: string) {
  const res = await fetch(`/auth/register`, {
    method: "POST",
    headers: await getHeaders(false),
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.message || "Registration failed");
  }
  return data;
}

export async function login(email: string, password: string) {
  const res = await fetch(`/auth/login`, {
    method: "POST",
    headers: await getHeaders(false),
    body: JSON.stringify({ email, password }),
  });
  
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.message || "Login failed");
  }
  return data;
}

export async function getMe() {
  const res = await fetch(`/auth/me`, {
    method: "GET",
    headers: await getHeaders(true),
  });
  
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.message || "Failed to fetch user profile");
  }
  return data;
}

export async function getSessions(): Promise<Session[]> {
  const res = await fetch(`/api/sessions`, {
    method: "GET",
    headers: await getHeaders(true),
  });
  
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.message || "Failed to fetch sessions");
  }
  return res.json();
}

export async function createSession(title: string): Promise<Session> {
  const res = await fetch(`/api/sessions`, {
    method: "POST",
    headers: await getHeaders(true),
    body: JSON.stringify({ title }),
  });
  
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.message || "Failed to create session");
  }
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`/api/sessions/${sessionId}`, {
    method: "DELETE",
    headers: await getHeaders(true),
  });
  
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.message || "Failed to delete session");
  }
}

export async function getSessionMessages(sessionId: string): Promise<Message[]> {
  const res = await fetch(`/api/sessions/${sessionId}/messages`, {
    method: "GET",
    headers: await getHeaders(true),
  });
  
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.message || "Failed to fetch messages");
  }
  return res.json();
}

export async function streamChat(
  sessionId: string,
  message: string,
  onToken: (token: string) => void,
  onDone: (sources: Source[]) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const headers = await getHeaders(true);
    const res = await fetch(`/api/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({ session_id: sessionId, message }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.message || "Failed to start chat stream");
    }

    if (!res.body) {
      throw new Error("No response body received from stream");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        if (trimmed.startsWith("data: ")) {
          const rawData = trimmed.slice(6);
          try {
            const parsed = JSON.parse(rawData);
            if (parsed.error) {
              onError(parsed.error);
            } else if (parsed.token) {
              onToken(parsed.token);
            } else if (parsed.done) {
              onDone(parsed.sources || []);
            }
          } catch (e) {
            console.error("Failed to parse SSE line:", trimmed, e);
          }
        }
      }
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Stream connection failed";
    onError(message);
  }
}
