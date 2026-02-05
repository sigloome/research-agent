
import { useState, useRef } from 'react'
import { mutate } from 'swr'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import clsx from 'clsx'
import ChatInterface, { ChatInterfaceHandle } from './components/ChatInterface'
import PaperList from './components/PaperList'
import PaperDetail from './pages/PaperDetail'
import NotesList from './pages/NotesList'
import NoteDetail from './pages/NoteDetail'

function App() {
  const [isChatExpanded, setIsChatExpanded] = useState(false)
  const [librarySearch, setLibrarySearch] = useState<string | undefined>(undefined)
  const chatRef = useRef<ChatInterfaceHandle>(null)

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
    <BrowserRouter>
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
    </BrowserRouter>
  )
}


export default App
