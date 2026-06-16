"use client";

import { useState } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";
import { Thread } from "@/components/thread";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { ThreadListSidebar } from "@/components/threadlist-sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function createBackendAdapter(sessionId: string): ChatModelAdapter {
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: userText }),
        signal: abortSignal,
      });

      const reader = response.body?.getReader();
      if (!reader) {
        return;
      }

      const decoder = new TextDecoder();
      let answer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        answer += decoder.decode(value, { stream: true });
        yield { content: [{ type: "text", text: answer }] };
      }
    },
  };
}

export const Assistant = () => {
  const [sessionId] = useState(() => crypto.randomUUID());
  const runtime = useLocalRuntime(createBackendAdapter(sessionId));

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <SidebarProvider>
        <div className="flex h-dvh w-full pr-0.5">
          <ThreadListSidebar />
          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
              <SidebarTrigger />
              <Separator orientation="vertical" className="mr-2 h-4" />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem>
                    <BreadcrumbPage>Wimmera CMA Induction Assistant</BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </header>
            <div className="flex-1 overflow-hidden">
              <Thread />
            </div>
          </SidebarInset>
        </div>
      </SidebarProvider>
    </AssistantRuntimeProvider>
  );
};
