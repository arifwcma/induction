"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  adminDeleteKB,
  adminDeleteSession,
  adminDeleteUser,
  adminGetPrompt,
  adminListGaps,
  adminListKB,
  adminListUsers,
  adminResetPassword,
  adminSessionMessages,
  adminSetGapStatus,
  adminSetRole,
  adminUpdatePrompt,
  adminUserSessions,
  fetchCurrentUser,
  kbDownloadUrl,
  type CurrentUser,
  type Gap,
  type KBEntry,
  type SessionSummary,
  type StoredMessage,
} from "@/lib/api";

const ROLES = ["basic", "trainer", "admin"];
const GAP_STATUSES = ["open", "reviewed", "dismissed"];

export default function AdminPage() {
  const router = useRouter();
  const [authorized, setAuthorized] = useState<boolean | undefined>(undefined);

  const [users, setUsers] = useState<CurrentUser[]>([]);
  const [prompt, setPrompt] = useState("");
  const [promptSaved, setPromptSaved] = useState(false);
  const [kbEntries, setKbEntries] = useState<KBEntry[]>([]);
  const [gaps, setGaps] = useState<Gap[]>([]);

  const [viewedUserId, setViewedUserId] = useState("");
  const [userSessions, setUserSessions] = useState<SessionSummary[]>([]);
  const [conversation, setConversation] = useState<StoredMessage[]>([]);

  const loadUsers = useCallback(async () => {
    setUsers(await adminListUsers());
  }, []);

  const loadKB = useCallback(async () => {
    setKbEntries(await adminListKB());
  }, []);

  const loadGaps = useCallback(async () => {
    setGaps(await adminListGaps());
  }, []);

  useEffect(() => {
    (async () => {
      const currentUser = await fetchCurrentUser();
      if (!currentUser || currentUser.role !== "admin") {
        setAuthorized(false);
        router.replace("/");
        return;
      }
      setAuthorized(true);
      await loadUsers();
      await loadKB();
      await loadGaps();
      const promptResponse = await adminGetPrompt();
      setPrompt(promptResponse.prompt);
    })();
  }, [router, loadUsers, loadKB, loadGaps]);

  async function changeRole(userId: string, role: string) {
    await adminSetRole(userId, role);
    await loadUsers();
  }

  async function resetPassword(userId: string) {
    const newPassword = window.prompt("New password for this user:");
    if (!newPassword) {
      return;
    }
    await adminResetPassword(userId, newPassword);
    alert("Password reset.");
  }

  async function deleteUser(userId: string, email: string) {
    if (!window.confirm(`Delete ${email} and all of their chat history? This cannot be undone.`)) {
      return;
    }
    try {
      await adminDeleteUser(userId);
    } catch (error) {
      alert(error instanceof Error ? error.message : "Could not delete this user.");
      return;
    }
    if (viewedUserId === userId) {
      setViewedUserId("");
      setUserSessions([]);
      setConversation([]);
    }
    await loadUsers();
    await loadGaps();
  }

  async function updateGapStatus(gapId: string, status: string) {
    await adminSetGapStatus(gapId, status);
    await loadGaps();
  }

  async function viewGapConversation(gap: Gap) {
    if (!gap.user_id || !gap.session_key) {
      alert("This gap is not linked to a viewable conversation.");
      return;
    }
    setViewedUserId(gap.user_id);
    setUserSessions(await adminUserSessions(gap.user_id));
    setConversation(await adminSessionMessages(gap.user_id, gap.session_key));
  }

  async function savePrompt() {
    await adminUpdatePrompt(prompt);
    setPromptSaved(true);
    setTimeout(() => setPromptSaved(false), 2000);
  }

  async function deleteEntry(entryId: string) {
    if (!window.confirm("Remove this knowledge base entry?")) {
      return;
    }
    await adminDeleteKB(entryId);
    await loadKB();
  }

  async function viewUserConversations(userId: string) {
    setViewedUserId(userId);
    setConversation([]);
    setUserSessions(await adminUserSessions(userId));
  }

  async function viewConversation(userId: string, sessionId: string) {
    setConversation(await adminSessionMessages(userId, sessionId));
  }

  async function deleteConversation(sessionId: string, title: string) {
    if (!window.confirm(`Delete the conversation "${title}"? This cannot be undone.`)) {
      return;
    }
    try {
      await adminDeleteSession(viewedUserId, sessionId);
    } catch (error) {
      alert(error instanceof Error ? error.message : "Could not delete this conversation.");
      return;
    }
    setConversation([]);
    setUserSessions(await adminUserSessions(viewedUserId));
  }

  if (authorized === undefined) {
    return <div className="p-8 text-muted-foreground">Loading...</div>;
  }
  if (!authorized) {
    return null;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-10 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Admin panel</h1>
        <a className="text-sm underline" href="/">
          Back to chat
        </a>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Users</h2>
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left">
              <tr>
                <th className="p-2">Email</th>
                <th className="p-2">Name</th>
                <th className="p-2">Role</th>
                <th className="p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-t">
                  <td className="p-2">{user.email}</td>
                  <td className="p-2">{user.full_name}</td>
                  <td className="p-2">
                    <select
                      className="rounded-md border bg-background px-2 py-1"
                      value={user.role}
                      onChange={(event) => changeRole(user.id, event.target.value)}
                    >
                      {ROLES.map((role) => (
                        <option key={role} value={role}>
                          {role}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="p-2">
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => resetPassword(user.id)}>
                        Reset password
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => viewUserConversations(user.id)}
                      >
                        View chats
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => deleteUser(user.id, user.email)}
                      >
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Knowledge gaps</h2>
        <p className="text-sm text-muted-foreground">
          Questions our documents could not answer. Each one is logged for management to review and
          add to the induction material.
        </p>
        {gaps.length === 0 ? (
          <p className="text-sm text-muted-foreground">No gaps logged yet.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left">
                <tr>
                  <th className="p-2">Topic</th>
                  <th className="p-2">Question</th>
                  <th className="p-2">Asked by</th>
                  <th className="p-2">Status</th>
                  <th className="p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {gaps.map((gap) => (
                  <tr key={gap.id} className="border-t">
                    <td className="p-2">{gap.topic}</td>
                    <td className="p-2">{gap.question}</td>
                    <td className="p-2">{gap.user_email || "(unknown)"}</td>
                    <td className="p-2">
                      <select
                        className="rounded-md border bg-background px-2 py-1"
                        value={gap.status}
                        onChange={(event) => updateGapStatus(gap.id, event.target.value)}
                      >
                        {GAP_STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="p-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => viewGapConversation(gap)}
                      >
                        View chat
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {viewedUserId && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium">Conversations</h2>
          {userSessions.length === 0 ? (
            <p className="text-sm text-muted-foreground">This user has no saved conversations.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {userSessions.map((session) => (
                <div
                  key={session.session_id}
                  className="flex items-center overflow-hidden rounded-md border"
                >
                  <button
                    type="button"
                    className="px-3 py-1.5 text-sm hover:bg-muted"
                    onClick={() => viewConversation(viewedUserId, session.session_id)}
                  >
                    {session.title}
                  </button>
                  <button
                    type="button"
                    aria-label="Delete conversation"
                    title="Delete conversation"
                    className="border-l px-2 py-1.5 text-sm text-muted-foreground hover:bg-muted hover:text-destructive"
                    onClick={() => deleteConversation(session.session_id, session.title)}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="space-y-2 rounded-lg border p-3">
            {conversation.map((message, index) => (
              <div key={index} className="text-sm">
                <span className="font-medium">{message.role}: </span>
                <span className="whitespace-pre-wrap">{message.content}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-medium">System prompt</h2>
        <textarea
          className="h-64 w-full rounded-lg border bg-background p-3 font-mono text-sm"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
        />
        <Button onClick={savePrompt}>{promptSaved ? "Saved" : "Save prompt"}</Button>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Trainer knowledge base entries</h2>
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left">
              <tr>
                <th className="p-2">Source</th>
                <th className="p-2">Kind</th>
                <th className="p-2">Trainer</th>
                <th className="p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {kbEntries.map((entry) => (
                <tr key={entry.id} className="border-t">
                  <td className="p-2">
                    {entry.downloadable ? (
                      <a
                        href={kbDownloadUrl(entry.id)}
                        className="text-primary underline underline-offset-2 hover:opacity-80"
                        download
                      >
                        {entry.filename || entry.source_label}
                      </a>
                    ) : (
                      entry.filename || entry.source_label
                    )}
                  </td>
                  <td className="p-2">{entry.kind}</td>
                  <td className="p-2">{entry.trainer_name}</td>
                  <td className="p-2">
                    <Button variant="outline" size="sm" onClick={() => deleteEntry(entry.id)}>
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
