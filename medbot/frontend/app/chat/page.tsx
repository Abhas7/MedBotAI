"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { removeToken } from "@/lib/auth";
import {
  getMe,
  getSessions,
  createSession,
  deleteSession,
  getSessionMessages,
  streamChat,
  Session,
  Message
} from "@/lib/api";
import {
  Stethoscope,
  LogOut,
  Loader2,
  Plus,
  Trash2,
  Send,
  User,
  Bot,
  Sparkles,
  BookOpen,
  ShieldCheck,
  AlertCircle,
  ChevronDown,
  ChevronUp
} from "lucide-react";

export default function ChatDashboard() {
  const router = useRouter();

  // Profile & UI Session states
  const [user, setUser] = useState<{ id: string; email: string; full_name: string } | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  
  // Input form & Streaming states
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState("");
  const [streamError, setStreamError] = useState<string | null>(null);

  // Active citation indices for accordion rendering
  const [expandedCitationIndex, setExpandedCitationIndex] = useState<number | null>(null);

  // Refs for scrolling and form textareas
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);

  // Initial loading setup
  useEffect(() => {
    async function initWorkspace() {
      try {
        const profile = await getMe();
        setUser(profile);
        
        const sessionList = await getSessions();
        setSessions(sessionList);
      } catch (err) {
        console.error("Session initialization failure:", err);
        // Purge token and redirect to login if profile fails
        removeToken();
        router.replace("/login");
      } finally {
        setLoading(false);
        setSessionsLoading(false);
      }
    }
    initWorkspace();
  }, [router]);

  // Load message logs when switching sessions
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }

    async function loadSessionData(sessionId: string) {
      setMessagesLoading(true);
      setStreamError(null);
      setExpandedCitationIndex(null);
      try {
        const messageLogs = await getSessionMessages(sessionId);
        setMessages(messageLogs);
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load message history.";
        setStreamError(errorMessage);
      } finally {
        setMessagesLoading(false);
      }
    }
    loadSessionData(activeSessionId);
  }, [activeSessionId]);

  // Trigger auto-scroll on token stream or message updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage]);

  const handleLogout = () => {
    removeToken();
    router.replace("/login");
  };

  const handleCreateSession = async (title = "New Chat") => {
    try {
      const newSession = await createSession(title);
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
    } catch (err) {
      console.error("Failed to create new session:", err);
    }
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Avoid selecting deleted session
    
    if (!confirm("Are you sure you want to delete this chat session?")) return;

    // Save original state for rollback on failure
    const originalSessions = [...sessions];
    const originalActiveId = activeSessionId;
    const originalMessages = [...messages];

    // Optimistically update state immediately for instant UI response
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (activeSessionId === sessionId) {
      setActiveSessionId(null);
      setMessages([]);
    }

    try {
      await deleteSession(sessionId);
    } catch (err) {
      console.error("Failed to delete session:", err);
      alert("Failed to delete session. Please check your connection and try again.");
      // Rollback to original state
      setSessions(originalSessions);
      setActiveSessionId(originalActiveId);
      setMessages(originalMessages);
    }
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isStreaming || !activeSessionId) return;

    const userQuery = input.trim();
    const sessionId = activeSessionId;
    setInput("");
    setStreamError(null);
    setExpandedCitationIndex(null);

    // Append temporary user message locally
    const userMsg: Message = {
      id: `temp-user-${Date.now()}`,
      session_id: sessionId,
      role: "user",
      content: userQuery,
      created_at: new Date().toISOString(),
      sources: []
    };
    setMessages((prev) => [...prev, userMsg]);

    setIsStreaming(true);
    setStreamingMessage("");

    try {
      await streamChat(
        sessionId,
        userQuery,
        (token) => {
          setStreamingMessage((prev) => prev + token);
        },
        async () => {
          // Sync complete messages list directly from database upon stream completion
          const finalMessages = await getSessionMessages(sessionId);
          setMessages(finalMessages);
          setIsStreaming(false);
          setStreamingMessage("");
        },
        (errorMsg) => {
          setStreamError(errorMsg);
          setIsStreaming(false);
        }
      );
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to transmit message.";
      setStreamError(errorMessage);
      setIsStreaming(false);
    }
  };

  const handlePromptStarter = async (starterPrompt: string) => {
    // Generate a title based on the starter prompt
    const cleanedTitle = starterPrompt.split(" ").slice(0, 3).join(" ") + "...";
    try {
      const newSession = await createSession(cleanedTitle);
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      
      // Auto-populate input and send
      setInput(starterPrompt);
      setTimeout(() => {
        const form = document.getElementById("chat-form") as HTMLFormElement;
        form?.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
      }, 100);
    } catch (err) {
      console.error("Prompt starter trigger failure:", err);
    }
  };

  // Keyboard shortcut: Enter sends message, Shift+Enter inputs newline
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-emerald-400">
        <Loader2 className="h-8 w-8 animate-spin" />
        <p className="mt-2 text-sm text-slate-400">Verifying Clinical Session credentials...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex overflow-hidden h-screen">
      {/* Sidebar - Sessions Logs */}
      <aside className="w-80 border-r border-slate-800 bg-slate-900/60 flex flex-col shrink-0 h-full">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center">
              <Stethoscope className="h-4.5 w-4.5 text-slate-950" />
            </div>
            <span className="font-bold tracking-wide text-md bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
              MedBot AI
            </span>
          </div>

          <button
            onClick={() => handleCreateSession()}
            className="p-1.5 rounded-lg border border-slate-700 hover:border-emerald-500/30 hover:bg-emerald-500/10 text-slate-400 hover:text-emerald-400 transition-all cursor-pointer"
            title="Create New Session"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <p className="text-[10px] font-bold tracking-wider text-slate-500 uppercase px-2 mb-2">
            Clinical Queries
          </p>

          {sessionsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-slate-500" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl p-4 m-2">
              No sessions logged. Click &quot;+&quot; above or use a prompt starter to begin.
            </div>
          ) : (
            sessions.map((session) => {
              const isActive = activeSessionId === session.id;
              return (
                <div
                  key={session.id}
                  onClick={() => setActiveSessionId(session.id)}
                  className={`group flex items-center justify-between px-3 py-2.5 rounded-xl text-sm transition-all cursor-pointer ${
                    isActive
                      ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-semibold"
                      : "hover:bg-slate-800/50 border border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <span className="truncate pr-2">{session.title}</span>
                  <button
                    onClick={(e) => handleDeleteSession(session.id, e)}
                    className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-500/10 hover:text-red-400 transition-all cursor-pointer shrink-0"
                    title="Delete Chat"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Bottom profile area */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between">
          <div className="flex items-center gap-3 truncate pr-2">
            <div className="h-9 w-9 rounded-full bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
              <User className="h-4.5 w-4.5 text-emerald-400" />
            </div>
            <div className="truncate text-left">
              <p className="text-xs font-semibold text-slate-200 truncate">{user?.full_name}</p>
              <p className="text-[10px] text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg border border-slate-800 hover:border-red-500/20 hover:bg-red-500/5 text-slate-500 hover:text-red-400 transition-all cursor-pointer shrink-0"
            title="Log Out"
          >
            <LogOut className="h-4.5 w-4.5" />
          </button>
        </div>
      </aside>

      {/* Main Panel - Conversation Area */}
      <section className="flex-1 flex flex-col h-full bg-slate-950 relative">
        {/* Background glow decoration */}
        <div className="absolute top-0 right-0 w-[400px] h-[400px] rounded-full bg-emerald-500/5 blur-[120px] pointer-events-none"></div>

        {activeSessionId ? (
          <>
            {/* Active Header */}
            <header className="h-16 border-b border-slate-900 px-6 flex items-center justify-between bg-slate-950/80 backdrop-blur-md z-10 shrink-0">
              <div>
                <h2 className="font-semibold text-slate-200 text-sm">
                  {sessions.find((s) => s.id === activeSessionId)?.title || "Workspace"}
                </h2>
                <p className="text-[10px] text-emerald-400 flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Gale Encyclopedia RAG Context active
                </p>
              </div>
            </header>

            {/* Message Thread Board */}
            <div
              ref={scrollContainerRef}
              className="flex-1 overflow-y-auto p-6 space-y-6"
            >
              {messagesLoading ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-400">
                  <Loader2 className="h-6 w-6 animate-spin text-emerald-500" />
                  <p className="mt-2 text-xs">Loading context logs...</p>
                </div>
              ) : messages.length === 0 && !isStreaming ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 max-w-md mx-auto text-center">
                  <BookOpen className="h-12 w-12 text-slate-700 mb-4 animate-bounce" />
                  <h3 className="font-semibold text-slate-300">Start the Consultation</h3>
                  <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                    Ask a medical question below. MedBot will search the vector encyclopedia and retrieve matching answers with page numbers.
                  </p>
                </div>
              ) : (
                <>
                  {messages.map((msg) => {
                    const isUser = msg.role === "user";
                    return (
                      <div
                        key={msg.id}
                        className={`flex gap-4 max-w-3xl ${
                          isUser ? "ml-auto flex-row-reverse" : "mr-auto"
                        }`}
                      >
                        {/* Avatar */}
                        <div
                          className={`h-9 w-9 rounded-full flex items-center justify-center border shrink-0 ${
                            isUser
                              ? "bg-slate-800 border-slate-700 text-emerald-400"
                              : "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                          }`}
                        >
                          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                        </div>

                        {/* Content Card */}
                        <div className="space-y-3">
                          <div
                            className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-line border shadow-lg ${
                              isUser
                                ? "bg-slate-900 border-slate-800 text-slate-200"
                                : "bg-slate-900/40 border-slate-900 text-slate-300"
                            }`}
                          >
                            {msg.content}
                          </div>

                          {/* Sources Accordion list */}
                          {!isUser && msg.sources && msg.sources.length > 0 && (
                            <div className="space-y-1.5">
                              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                                <BookOpen className="h-3 w-3" />
                                gale encyclopedia source citations
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {msg.sources.map((src, idx) => {
                                  const isExpanded = expandedCitationIndex === idx;
                                  return (
                                    <div key={idx} className="w-full">
                                      <button
                                        onClick={() =>
                                          setExpandedCitationIndex(isExpanded ? null : idx)
                                        }
                                        className="flex items-center justify-between w-full px-3 py-1.5 text-xs text-left rounded-lg bg-slate-900/30 border border-slate-800/80 hover:border-emerald-500/20 hover:bg-emerald-500/5 text-slate-400 hover:text-slate-300 transition-all cursor-pointer"
                                      >
                                        <span className="flex items-center gap-1.5">
                                          <span className="font-semibold text-emerald-400">Page {src.page_number}</span>
                                          <span className="text-[10px] text-slate-500">
                                            (Score: {Math.round(src.score * 100)}%)
                                          </span>
                                        </span>
                                        {isExpanded ? (
                                          <ChevronUp className="h-3 w-3" />
                                        ) : (
                                          <ChevronDown className="h-3 w-3" />
                                        )}
                                      </button>
                                      
                                      {/* Accordion content */}
                                      {isExpanded && (
                                        <div className="mt-1 p-3 rounded-lg border border-emerald-500/10 bg-emerald-500/5 text-[11px] text-slate-400 leading-relaxed italic whitespace-pre-line animate-fade-in">
                                          &ldquo;{src.snippet}&rdquo;
                                        </div>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}

                  {/* Token Streaming message placeholder */}
                  {isStreaming && streamingMessage && (
                    <div className="flex gap-4 max-w-3xl mr-auto">
                      <div className="h-9 w-9 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
                        <Bot className="h-4 w-4 animate-pulse" />
                      </div>
                      <div className="p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-line border bg-slate-900/40 border-slate-900 text-slate-300 shadow-lg relative">
                        {streamingMessage}
                        <span className="inline-block w-1.5 h-4 ml-1 bg-emerald-400 animate-pulse align-middle"></span>
                      </div>
                    </div>
                  )}
                  
                  {/* Ollama loading prefill delay placeholder */}
                  {isStreaming && !streamingMessage && (
                    <div className="flex gap-4 max-w-3xl mr-auto items-center">
                      <div className="h-9 w-9 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0 animate-spin">
                        <Loader2 className="h-4 w-4" />
                      </div>
                      <p className="text-xs text-slate-400 italic animate-pulse">
                        Retrieving vector logs and calculating response... (Ollama model warming up)
                      </p>
                    </div>
                  )}

                  {/* Stream Error Alert */}
                  {streamError && (
                    <div className="max-w-md mx-auto p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-xs text-red-400 flex items-center gap-2.5">
                      <AlertCircle className="h-4 w-4 shrink-0" />
                      <span>{streamError}</span>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Chat bottom Input Form container */}
            <div className="p-4 border-t border-slate-900 bg-slate-950/90 backdrop-blur-sm z-10 shrink-0">
              <form
                id="chat-form"
                onSubmit={handleSend}
                className="max-w-3xl mx-auto relative flex items-center bg-slate-900 border border-slate-800 rounded-xl focus-within:border-emerald-500/50 transition-all p-1.5"
              >
                <textarea
                  rows={1}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Query a medical topic (e.g. Symptoms of Hypertension)..."
                  disabled={isStreaming}
                  className="flex-1 max-h-32 bg-transparent border-0 outline-none text-sm text-slate-100 placeholder-slate-500 py-2.5 px-3 resize-none disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={isStreaming || !input.trim()}
                  className="h-9 w-9 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 flex items-center justify-center text-slate-950 transition-all hover:opacity-95 hover:shadow-lg disabled:opacity-30 disabled:pointer-events-none cursor-pointer shrink-0"
                >
                  <Send className="h-4 w-4 text-slate-950" />
                </button>
              </form>
              <p className="text-[10px] text-slate-500 text-center mt-2.5 max-w-xl mx-auto leading-normal">
                Liability Notice: MedBot outputs generated results from encyclopedia references. This bot is an AI assistant, not a replacement for professional clinical advice.
              </p>
            </div>
          </>
        ) : (
          /* Welcome Screen (When no session is active) */
          <div className="flex-1 overflow-y-auto p-8 flex flex-col justify-center max-w-4xl mx-auto relative z-10">
            <div className="text-center mb-10">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 shadow-lg shadow-emerald-500/20 mb-4 animate-pulse">
                <Stethoscope className="h-6 w-6 text-slate-950" />
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
                Medical Encylopedia Chat
              </h1>
              <p className="text-slate-400 text-sm mt-2 max-w-xl mx-auto leading-relaxed">
                Connect and consult the Gale Encyclopedia of Medicine instantly. Open an existing session or start a new clinical diagnosis context below.
              </p>
            </div>

            {/* Prompt Starter widgets */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl mx-auto w-full mb-8">
              <button
                onClick={() => handlePromptStarter("What is hypertension and what are its symptoms?")}
                className="flex items-start gap-3 p-4 rounded-xl border border-slate-800/80 bg-slate-900/30 hover:border-emerald-500/30 hover:bg-emerald-500/5 text-left transition-all group cursor-pointer"
              >
                <Sparkles className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-300 group-hover:text-emerald-400 transition-colors">
                    Explain Hypertension
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-1 leading-normal">
                    Queries diagnostic parameters and symptoms from reference files.
                  </p>
                </div>
              </button>

              <button
                onClick={() => handlePromptStarter("What are the diagnostic tests for pneumonia?")}
                className="flex items-start gap-3 p-4 rounded-xl border border-slate-800/80 bg-slate-900/30 hover:border-emerald-500/30 hover:bg-emerald-500/5 text-left transition-all group cursor-pointer"
              >
                <BookOpen className="h-5 w-5 text-teal-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-300 group-hover:text-teal-400 transition-colors">
                    Pneumonia Diagnosis
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-1 leading-normal">
                    Examines diagnostic testing models and radiology citations.
                  </p>
                </div>
              </button>

              <button
                onClick={() => handlePromptStarter("What are the common treatments and management options for asthma?")}
                className="flex items-start gap-3 p-4 rounded-xl border border-slate-800/80 bg-slate-900/30 hover:border-emerald-500/30 hover:bg-emerald-500/5 text-left transition-all group cursor-pointer"
              >
                <Stethoscope className="h-5 w-5 text-sky-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-300 group-hover:text-sky-400 transition-colors">
                    Asthma Treatment
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-1 leading-normal">
                    Details inhaled medications, triggers, and clinical therapies.
                  </p>
                </div>
              </button>

              <button
                onClick={() => handlePromptStarter("What are the symptoms and stages of a migraine headache?")}
                className="flex items-start gap-3 p-4 rounded-xl border border-slate-800/80 bg-slate-900/30 hover:border-emerald-500/30 hover:bg-emerald-500/5 text-left transition-all group cursor-pointer"
              >
                <AlertCircle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-300 group-hover:text-amber-400 transition-colors">
                    Migraine Symptoms
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-1 leading-normal">
                    Explores aura phases, sensory triggers, and pain descriptors.
                  </p>
                </div>
              </button>
            </div>

            {/* Medical compliance rules disclaimer card */}
            <div className="max-w-2xl mx-auto p-5 rounded-2xl border border-slate-900 bg-slate-900/10 text-xs text-slate-500 flex gap-4 leading-relaxed">
              <ShieldCheck className="h-6 w-6 text-emerald-400 shrink-0" />
              <div>
                <h5 className="font-bold text-slate-300 mb-1">Clinical Safety Protocols</h5>
                All queries are processed locally to ensure complete transmission privacy. Vector embeddings are matched using cosine similarities. Verify page references under answers to cross-check clinical details.
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
