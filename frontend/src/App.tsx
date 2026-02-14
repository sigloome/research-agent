
import { useState, useRef, useEffect } from 'react'
import { mutate } from 'swr'
import { useLocation, BrowserRouter, Routes, Route } from 'react-router-dom'
import clsx from 'clsx'
import ChatInterface, { ChatInterfaceHandle } from './components/ChatInterface'
import PaperList from './components/PaperList'
import PaperDetail from './pages/PaperDetail'
import NotesList from './pages/NotesList'
import NoteDetail from './pages/NoteDetail'


// Wrapper to use useLocation
function AppContent() {
  const [isChatExpanded, setIsChatExpanded] = useState(false)
  const [librarySearch, setLibrarySearch] = useState<string | undefined>(undefined)
  const chatRef = useRef<ChatInterfaceHandle>(null)
  const location = useLocation()

  // Handle initial message from navigation state (e.g. from PaperDetail fetch request)
  useEffect(() => {
    const state = location.state as { initialMessage?: string } | null;
    if (state?.initialMessage) {
      // Expand chat
      setIsChatExpanded(true);
      // Send message after a brief delay to ensure mounted
      setTimeout(() => {
        chatRef.current?.sendMessage(state.initialMessage!);
        // Clear state to prevent re-sending on refresh? 
        // Actually router state persists, but we only want to trigger once.
        // Helper to clear state would be good, but for now this is okay.
        window.history.replaceState({}, document.title)
      }, 500);
    }
  }, [location.state]);

  const handlePaperAction = () => {
    // Re-fetch papers list with new sort
    mutate('/api/papers?sort=recency')
  }

  const handleAskAboutPaper = (paperId: string, paperTitle: string) => {
    // Prepare question with template and suggestions - don't send immediately
    chatRef.current?.prepareQuestionAboutPaper(paperId, paperTitle)
    // Expand chat if collapsed
    if (!isChatExpanded) {
      setIsChatExpanded(true)
    }
  }

  const handleLibrarySearch = (query: string) => {
    setLibrarySearch(query);
    // If on mobile/collapsed view and chat is covering everything, we might want to collapse chat
    // But for now, we assume side-by-side or user manages layout.
    // If chat is expanded to full width, we should collapse it to show the library
    if (isChatExpanded) {
      setIsChatExpanded(false);
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-cream text-warmstone-800 font-sans">
      {/* Sidebar / Chat */}
      <div className={clsx(
        "flex flex-col border-r border-warmstone-200 shadow-xl z-10 transition-all duration-300 ease-in-out bg-cream overflow-hidden",
        isChatExpanded ? "w-full" : "w-1/3 min-w-[350px] max-w-[500px]"
      )}>
        <ChatInterface
          ref={chatRef}
          onPaperAction={handlePaperAction}
          onLibrarySearch={handleLibrarySearch}
          isExpanded={isChatExpanded}
          onToggleExpand={() => setIsChatExpanded(!isChatExpanded)}
        />
      </div>

      {/* Main Content / Routes */}
      <div className={clsx(
        "flex-1 overflow-hidden bg-cream scrollbar-thin scrollbar-thumb-warmstone-300 transition-all duration-300",
        isChatExpanded ? "hidden" : "block"
      )}>
        <Routes>
          <Route path="/" element={<PaperList onAskAboutPaper={handleAskAboutPaper} searchQuery={librarySearch} />} />
          <Route path="/paper/:id" element={<PaperDetail />} />
          <Route path="/notes" element={<NotesList />} />
          <Route path="/notes/:id" element={<NoteDetail />} />
        </Routes>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}


export default App
