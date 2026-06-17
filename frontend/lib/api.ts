export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type CurrentUser = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
};

export type SessionSummary = {
  session_id: string;
  title: string;
  updated_at: string;
};

export type StoredMessage = {
  role: string;
  content: string;
};

export type KBEntry = {
  id: string;
  kind: string;
  source_label: string;
  filename: string;
  trainer_name: string;
  created_at: string;
};

async function request(path: string, options: RequestInit = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export async function fetchCurrentUser(): Promise<CurrentUser | null> {
  const response = await fetch(`${API_URL}/users/me`, { credentials: "include" });
  if (!response.ok) {
    return null;
  }
  return response.json();
}

export async function login(email: string, password: string): Promise<void> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);

  const response = await fetch(`${API_URL}/auth/jwt/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!response.ok) {
    throw new Error("Login failed. Check your email and password.");
  }
}

export async function register(
  email: string,
  password: string,
  fullName: string,
): Promise<void> {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Registration failed.");
  }
}

export async function logout(): Promise<void> {
  await fetch(`${API_URL}/auth/jwt/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export async function listSessions(): Promise<SessionSummary[]> {
  return request("/sessions");
}

export async function getSessionMessages(sessionId: string): Promise<StoredMessage[]> {
  return request(`/sessions/${encodeURIComponent(sessionId)}/messages`);
}

export async function addTextToKB(content: string): Promise<void> {
  await request("/kb/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

export async function uploadDocumentToKB(file: File): Promise<void> {
  const form = new FormData();
  form.set("file", file);
  await request("/kb/document", { method: "POST", body: form });
}

export async function adminListUsers(): Promise<CurrentUser[]> {
  return request("/admin/users");
}

export async function adminSetRole(userId: string, role: string): Promise<void> {
  await request(`/admin/users/${userId}/role`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
}

export async function adminResetPassword(userId: string, newPassword: string): Promise<void> {
  await request(`/admin/users/${userId}/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ new_password: newPassword }),
  });
}

export async function adminUserSessions(userId: string): Promise<SessionSummary[]> {
  return request(`/admin/users/${userId}/sessions`);
}

export async function adminSessionMessages(
  userId: string,
  sessionId: string,
): Promise<StoredMessage[]> {
  return request(`/admin/users/${userId}/sessions/${encodeURIComponent(sessionId)}/messages`);
}

export async function adminGetPrompt(): Promise<{ prompt: string }> {
  return request("/admin/prompt");
}

export async function adminUpdatePrompt(prompt: string): Promise<void> {
  await request("/admin/prompt", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
}

export async function adminListKB(): Promise<KBEntry[]> {
  return request("/admin/kb");
}

export async function adminDeleteKB(entryId: string): Promise<void> {
  await request(`/admin/kb/${entryId}`, { method: "DELETE" });
}
