"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ThreadMessageLike,
} from "@assistant-ui/react";
import { Thread } from "@/components/thread";
import { Button } from "@/components/ui/button";
import { TrainerProvider } from "@/lib/trainer-context";
import {
  API_URL,
  deleteSession,
  fetchCurrentUser,
  getSessionMessages,
  listSessions,
  logout,
  saveTrainerFile,
  summariseKBFromSession,
  uploadDocumentToKB,
  type CurrentUser,
  type SessionSummary,
} from "@/lib/api";

const WELCOME_MESSAGE =
  "Hi there, and welcome to Wimmera CMA! I'm your induction assistant. " +
  "Ask me anything about our organisational policies and procedures — or, if you'd prefer, " +
  "I can walk you through them with a short guided tour. Where would you like to start?";

const WELCOME_THREAD: ThreadMessageLike[] = [
  { role: "assistant", content: WELCOME_MESSAGE },
];

function toThreadMessages(stored: { role: string; content: string }[]): ThreadMessageLike[] {
  if (stored.length === 0) {
    return WELCOME_THREAD;
  }
  return stored.map((message) => ({
    role: message.role === "user" ? "user" : "assistant",
    content: message.content,
  }));
}

function createBackendAdapter(sessionId: string, onTurnComplete: () => void): ChatModelAdapter {
  return {
    async *run({ messages, abortSignal }) {
      const lastMessage = messages[messages.length - 1];

      let userText = "";
      for (const part of lastMessage.content) {
        if (part.type === "text") {
          userText += part.text;
        }
      }

      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: userText }),
        signal: abortSignal,
      });

      const reader = response.body?.getReader();
      if (!reader) {
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let answer = "";
      let liveDraft = "";
      const steps: string[] = [];

      // The "thinking" trace (progress steps + the current unverified draft) is
      // shown in the muted, collapsible reasoning area; only the verified answer
      // lands in the normal-weight text part. A draft that fails verification is
      // dropped from the live trace rather than mistaken for the final answer.
      const thinking = () => {
        const trace = [...steps];
        if (liveDraft) {
          trace.push(liveDraft);
        }
        return trace.join("\n\n");
      };

      const display = () => {
        const parts: { type: "reasoning" | "text"; text: string }[] = [];
        const trace = thinking();
        if (trace) {
          parts.push({ type: "reasoning", text: trace });
        }
        parts.push({ type: "text", text: answer });
        return parts;
      };

      const handleFrame = (line: string) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return;
        }
        let frame: { t: string; v?: string };
        try {
          frame = JSON.parse(trimmed);
        } catch {
          // Tolerate any non-JSON line by treating it as answer text.
          answer += trimmed;
          return;
        }
        switch (frame.t) {
          case "status":
            if (frame.v && steps[steps.length - 1] !== frame.v) {
              steps.push(frame.v);
            }
            liveDraft = "";
            break;
          case "delta":
            liveDraft += frame.v ?? "";
            break;
          case "reset":
            liveDraft = "";
            break;
          case "final":
            answer = frame.v ?? answer;
            liveDraft = "";
            break;
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        let newlineIndex: number;
        while ((newlineIndex = buffer.indexOf("\n")) !== -1) {
          const line = buffer.slice(0, newlineIndex);
          buffer = buffer.slice(newlineIndex + 1);
          handleFrame(line);
        }
        yield { content: display() };
      }

      if (buffer.trim()) {
        handleFrame(buffer);
      }
      yield { content: display() };

      onTurnComplete();
    },
  };
}

function ChatPane({
  sessionId,
  initialMessages,
  onTurnComplete,
}: {
  sessionId: string;
  initialMessages: ThreadMessageLike[];
  onTurnComplete: () => void;
}) {
  const runtime = useLocalRuntime(createBackendAdapter(sessionId, onTurnComplete), {
    initialMessages,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="flex-1 overflow-hidden">
        <Thread />
      </div>
    </AssistantRuntimeProvider>
  );
}

export const Assistant = () => {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null | undefined>(undefined);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [initialMessages, setInitialMessages] = useState<ThreadMessageLike[]>(WELCOME_THREAD);
  const [kbOpen, setKbOpen] = useState(false);
  const [kbLoading, setKbLoading] = useState(false);
  const [kbDraft, setKbDraft] = useState("");
  const [kbNoKnowledge, setKbNoKnowledge] = useState(false);
  const [kbSaving, setKbSaving] = useState(false);
  const uploadInputRef = useRef<HTMLInputElement>(null);

  const refreshSessions = useCallback(async () => {
    try {
      setSessions(await listSessions());
    } catch {
      setSessions([]);
    }
  }, []);

  useEffect(() => {
    (async () => {
      const currentUser = await fetchCurrentUser();
      if (!currentUser) {
        router.replace("/login");
        return;
      }
      setUser(currentUser);
      await refreshSessions();
    })();
  }, [router, refreshSessions]);

  async function openSession(selectedId: string) {
    const stored = await getSessionMessages(selectedId);
    setInitialMessages(toThreadMessages(stored));
    setSessionId(selectedId);
  }

  function startNewChat() {
    setInitialMessages(WELCOME_THREAD);
    setSessionId(crypto.randomUUID());
  }

  async function handleDeleteSession(targetId: string) {
    if (!window.confirm("Delete this chat? This can't be undone.")) {
      return;
    }
    try {
      await deleteSession(targetId);
    } catch (error) {
      alert(error instanceof Error ? error.message : "Could not delete this chat.");
      return;
    }
    if (targetId === sessionId) {
      startNewChat();
    }
    await refreshSessions();
  }

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    try {
      await uploadDocumentToKB(file);
      alert(`"${file.name}" was added. It becomes searchable in a few seconds.`);
    } catch (uploadError) {
      alert(uploadError instanceof Error ? uploadError.message : "Upload failed.");
    } finally {
      if (uploadInputRef.current) {
        uploadInputRef.current.value = "";
      }
    }
  }

  const openAddToKb = useCallback(async () => {
    setKbOpen(true);
    setKbLoading(true);
    setKbNoKnowledge(false);
    setKbDraft("");
    try {
      const result = await summariseKBFromSession(sessionId);
      if (result.empty || !result.summary) {
        setKbNoKnowledge(true);
      } else {
        setKbDraft(result.summary);
      }
    } catch {
      setKbOpen(false);
      alert("Could not read this conversation to extract knowledge.");
    } finally {
      setKbLoading(false);
    }
  }, [sessionId]);

  function closeKb() {
    setKbOpen(false);
    setKbDraft("");
    setKbNoKnowledge(false);
  }

  async function handleSaveKb() {
    if (!kbDraft.trim()) {
      return;
    }
    setKbSaving(true);
    try {
      await saveTrainerFile(kbDraft);
      closeKb();
    } catch {
      alert("Could not save this knowledge.");
    } finally {
      setKbSaving(false);
    }
  }

  if (user === undefined) {
    return <div className="flex h-dvh items-center justify-center text-muted-foreground">Loading...</div>;
  }
  if (user === null) {
    return null;
  }

  const canTrain = user.role === "trainer" || user.role === "admin";

  return (
    <TrainerProvider canTrain={canTrain} sessionId={sessionId} openAddToKb={openAddToKb}>
      <div className="flex h-dvh w-full">
        <aside className="flex w-72 flex-col border-r bg-sidebar">
          <div className="border-b p-3">
            <span className="text-sm font-semibold">Induction Bot</span>
          </div>
          <div className="p-3">
            <Button className="w-full" onClick={startNewChat}>
              New chat
            </Button>
          </div>
          <nav className="flex-1 overflow-y-auto px-2">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className="group relative mb-1 flex items-center rounded-md hover:bg-muted aria-[current=true]:bg-muted"
                aria-current={session.session_id === sessionId}
              >
                <button
                  type="button"
                  onClick={() => openSession(session.session_id)}
                  className="min-w-0 flex-1 truncate px-3 py-2 text-left text-sm"
                  title={session.title}
                >
                  {session.title}
                </button>
                <button
                  type="button"
                  aria-label="Delete chat"
                  title="Delete chat"
                  onClick={() => handleDeleteSession(session.session_id)}
                  className="mr-1 hidden shrink-0 rounded-md p-1.5 text-muted-foreground hover:bg-background hover:text-destructive group-hover:block"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            ))}
          </nav>
          {canTrain && (
            <div className="flex flex-col gap-2 border-t p-3">
              <input
                ref={uploadInputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                className="hidden"
                onChange={handleUpload}
              />
              <Button
                variant="outline"
                className="w-full"
                onClick={() => uploadInputRef.current?.click()}
              >
                Upload document to KB
              </Button>
            </div>
          )}
          <div className="flex items-center justify-between gap-2 border-t p-3 text-xs">
            <span className="truncate" title={user.email}>
              {user.email}
            </span>
            <div className="flex shrink-0 gap-2">
              {user.role === "admin" && (
                <a className="underline" href="/admin">
                  Admin
                </a>
              )}
              <button type="button" className="underline" onClick={handleLogout}>
                Sign out
              </button>
            </div>
          </div>
        </aside>

        <div className="flex flex-1 flex-col">
          <header className="flex h-14 shrink-0 items-center border-b px-4 font-medium">
            Wimmera CMA Induction Assistant
          </header>
          <ChatPane
            key={sessionId}
            sessionId={sessionId}
            initialMessages={initialMessages}
            onTurnComplete={refreshSessions}
          />
        </div>
      </div>

      {kbOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={closeKb}
        >
          <div
            className="w-full max-w-lg rounded-lg border bg-background p-6 shadow-xl"
            onClick={(event) => event.stopPropagation()}
          >
            {kbLoading ? (
              <p className="text-base text-muted-foreground">Reading the conversation…</p>
            ) : kbNoKnowledge ? (
              <>
                <h2 className="mb-2 text-lg font-semibold">Nothing to add</h2>
                <p className="mb-5 text-base text-foreground">
                  I could not detect any knowledge from this conversation.
                </p>
                <div className="flex justify-end">
                  <Button onClick={closeKb}>Close</Button>
                </div>
              </>
            ) : (
              <>
                <h2 className="mb-1 text-lg font-semibold">Add to knowledge base</h2>
                <p className="mb-3 text-sm text-muted-foreground">
                  Review and edit the knowledge below. It becomes part of the knowledge base when
                  you click &ldquo;Apply pending&rdquo; in the sidebar.
                </p>
                <textarea
                  value={kbDraft}
                  onChange={(event) => setKbDraft(event.target.value)}
                  rows={8}
                  className="mb-4 w-full resize-y rounded-md border bg-background p-2 text-sm"
                />
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={closeKb} disabled={kbSaving}>
                    Cancel
                  </Button>
                  <Button onClick={handleSaveKb} disabled={kbSaving || !kbDraft.trim()}>
                    {kbSaving ? "Saving…" : "Save"}
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </TrainerProvider>
  );
};
