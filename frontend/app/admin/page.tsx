"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  adminDeleteKB,
  adminGetPrompt,
  adminListKB,
  adminListUsers,
  adminResetPassword,
  adminSessionMessages,
  adminSetRole,
  adminUpdatePrompt,
  adminUserSessions,
  fetchCurrentUser,
  type CurrentUser,
  type KBEntry,
  type SessionSummary,
  type StoredMessage,
} from "@/lib/api";

const ROLES = ["basic", "trainer", "admin"];

export default function AdminPage() {
  const router = useRouter();
  const [authorized, setAuthorized] = useState<boolean | undefined>(undefined);

  const [users, setUsers] = useState<CurrentUser[]>([]);
  const [prompt, setPrompt] = useState("");
  const [promptSaved, setPromptSaved] = useState(false);
  const [kbEntries, setKbEntries] = useState<KBEntry[]>([]);

  const [viewedUserId, setViewedUserId] = useState("");
  const [userSessions, setUserSessions] = useState<SessionSummary[]>([]);
  const [conversation, setConversation] = useState<StoredMessage[]>([]);

  const loadUsers = useCallback(async () => {
    setUsers(await adminListUsers());
  }, []);

  const loadKB = useCallback(async () => {
    setKbEntries(await adminListKB());
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
      const promptResponse = await adminGetPrompt();
      setPrompt(promptResponse.prompt);
    })();
  }, [router, loadUsers, loadKB]);

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
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {viewedUserId && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium">Conversations</h2>
          <div className="flex flex-wrap gap-2">
            {userSessions.map((session) => (
              <Button
                key={session.session_id}
                variant="outline"
                size="sm"
                onClick={() => viewConversation(viewedUserId, session.session_id)}
              >
                {session.title}
              </Button>
            ))}
          </div>
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
                  <td className="p-2">{entry.filename || entry.source_label}</td>
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
