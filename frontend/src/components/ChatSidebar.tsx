import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Plus, MessageSquare, Trash2, Menu } from 'lucide-react';

interface Chat {
  id: string;
  title: string;
  created_at: string;
}

interface ChatSidebarProps {
  currentChatId: string;
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

export function ChatSidebar({ currentChatId, onSelectChat, onNewChat, isOpen, setIsOpen }: ChatSidebarProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [filterText, setFilterText] = useState('');
  const activeChatRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    fetchChats();
  }, [currentChatId]); // Refetch when chat changes (e.g. after new chat)

  useEffect(() => {
    activeChatRef.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [currentChatId, isOpen, chats.length]);

  const fetchChats = async () => {
    try {
      const res = await fetch('/api/chats');
      if (res.ok) {
        const data = await res.json();
        setChats(data);
      }
    } catch (e) {
      console.error("Failed to fetch chats", e);
    }
  };

  const deleteChat = async (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    if (!confirm("Delete this chat?")) return;

    try {
      const res = await fetch(`/api/chats/${chatId}`, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.text();
        alert("Failed to delete chat: " + err);
        return;
      }
      fetchChats();
      if (chatId === currentChatId) {
        onNewChat();
      }
    } catch (e) {
      console.error("Failed to delete chat", e);
      alert("Network error deleting chat");
    }
  };

  const visibleChats = useMemo(() => {
    const normalized = filterText.trim().toLowerCase();
    if (!normalized) return chats;
    return chats.filter(chat => (chat.title || 'New Chat').toLowerCase().includes(normalized));
  }, [chats, filterText]);

  return (
    <>
      {/* Backdrop for mobile/overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/20 backdrop-blur-sm md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      <div className={`
                absolute inset-y-0 left-0 z-40 w-64 bg-cream-50 border-r border-warmstone-200 
                transform transition-transform duration-300 ease-in-out shadow-xl
                ${isOpen ? 'translate-x-0' : '-translate-x-full'}
            `}>
        <div className="flex flex-col h-full">
          <div className="p-4 flex items-center justify-between border-b border-warmstone-200 bg-cream">
            <h2 className="font-semibold text-warmstone-800">History</h2>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 text-warmstone-500 hover:bg-warmstone-100 rounded"
              title="Close History"
            >
              <Menu size={18} />
            </button>
          </div>

          <div className="shrink-0 border-b border-warmstone-100 bg-cream-50/95 px-3 pb-3 backdrop-blur">
            <button
              onClick={() => {
                onNewChat();
                setIsOpen(false); // Auto-close on new chat? Maybe.
              }}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-warmstone-800 hover:bg-warmstone-700 text-white rounded-lg transition-colors shadow-sm"
            >
              <Plus size={16} />
              <span className="text-sm font-medium">New Chat</span>
            </button>

            <input
              type="text"
              value={filterText}
              onChange={e => setFilterText(e.target.value)}
              placeholder="Filter chats..."
              className="mt-3 w-full rounded-lg border border-warmstone-200 bg-white px-3 py-2 text-sm text-warmstone-700 outline-none transition-colors placeholder:text-warmstone-400 focus:border-blue-300"
            />
          </div>

          <div className="flex-1 overflow-y-auto px-2 space-y-1 pb-4">
            {visibleChats.map(chat => (
              <div
                key={chat.id}
                ref={chat.id === currentChatId ? activeChatRef : null}
                onClick={() => {
                  onSelectChat(chat.id);
                  if (window.innerWidth < 768) setIsOpen(false); // Close on mobile select
                }}
                className={`
                                    group flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-all
                                    ${chat.id === currentChatId
                    ? 'bg-white border border-warmstone-200 shadow-sm text-warmstone-900 font-medium'
                    : 'text-warmstone-600 hover:bg-warmstone-100 hover:text-warmstone-900 border border-transparent'}
                                `}
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <MessageSquare size={14} className={chat.id === currentChatId ? "text-blue-600" : "text-warmstone-400"} />
                  <span className="truncate text-sm">{chat.title || "New Chat"}</span>
                </div>

                <button
                  onClick={(e) => deleteChat(e, chat.id)}
                  className={`p-1.5 text-warmstone-400 hover:text-red-600 hover:bg-red-50 rounded transition-all ${
                    chat.id === currentChatId ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                  }`}
                  title="Delete chat"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
            {visibleChats.length === 0 && (
              <div className="px-3 py-6 text-center text-sm text-warmstone-400">
                No chats match this filter.
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
