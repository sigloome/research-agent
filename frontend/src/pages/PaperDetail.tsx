import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, BookOpen, Calendar, StickyNote, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import useSWR from 'swr';

// Fetcher for SWR
const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface Paper {
    id: string;
    title: string;
    authors: string;
    published_date: string;
    abstract: string;
    full_text?: string;
    url: string;
    tags?: string[];
    summary_main_ideas?: string;
    summary_methods?: string;
    summary_results?: string;
    summary_limitations?: string;
}

export default function PaperDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const { data: paper, error, mutate } = useSWR<Paper>(id ? `/api/paper/${id}` : null, fetcher);

    // Notes state
    const [isNotesOpen, setIsNotesOpen] = useState(false);
    const { data: notes, mutate: mutateNotes } = useSWR(id ? `/api/notes?paper_id=${id}` : null, fetcher);
    const [newNote, setNewNote] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const handleSaveNote = async () => {
        if (!newNote.trim() || !id) return;
        setIsSaving(true);
        try {
            await fetch('/api/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: newNote, paper_id: id })
            });
            setNewNote('');
            mutateNotes();
        } catch (e) {
            console.error("Failed to save note", e);
        } finally {
            setIsSaving(false);
        }
    };

    const handleAnalyze = async () => {
        if (!id) return;
        setIsAnalyzing(true);
        try {
            const res = await fetch(`/api/paper/${id}/analyze?force_update=true`, { method: 'POST' });
            if (res.ok) {
                mutate(); // Refresh paper data
            }
        } catch (e) {
            console.error("Analysis failed", e);
        } finally {
            setIsAnalyzing(false);
        }
    };

    // Highlight snippet from URL hash
    // Implementation of precise citation highlighting will go here later

    if (error) return <div className="p-8 text-red-500">Failed to load paper details.</div>;
    if (!paper) return <div className="p-8 text-warmstone-500">Loading paper...</div>;

    const hasAISummary = !!paper.summary_main_ideas;

    return (
        <div className="h-full flex flex-col bg-cream overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-warmstone-200 bg-cream-50 flex items-center gap-3">
                <button
                    onClick={() => navigate('/')}
                    className="p-2 hover:bg-warmstone-200 rounded-full transition-colors text-warmstone-600"
                    title="Back to Library"
                >
                    <ArrowLeft size={20} />
                </button>
                <div className="flex-1 min-w-0">
                    <h1 className="text-xl font-bold text-warmstone-900 truncate" title={paper.title}>
                        {paper.title}
                    </h1>
                    <div className="text-sm text-warmstone-500 flex items-center gap-2 truncate">
                        <span>{paper.authors}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                            <Calendar size={12} /> {new Date(paper.published_date).getFullYear()}
                        </span>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                    {/* Content Source Badge */}
                    <div className={`px-2 py-1 rounded-md text-xs font-medium border flex items-center gap-1 ${paper.full_text
                        ? (paper.full_text.includes("<html>") ? "bg-green-50 text-green-700 border-green-200" : "bg-orange-50 text-orange-700 border-orange-200")
                        : "bg-gray-50 text-gray-500 border-gray-200"
                        }`}>
                        {paper.full_text
                            ? (paper.full_text.includes("<html>") ? <span>HTML Content</span> : <span>PDF Content</span>)
                            : <span>Abstract Only</span>}
                    </div>

                    <button
                        onClick={handleAnalyze}
                        disabled={isAnalyzing}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${hasAISummary ? 'bg-purple-100 text-purple-700 hover:bg-purple-200' : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-sm hover:shadow-md'}`}
                        title="Force re-analysis of paper content"
                    >
                        <Sparkles size={16} className={isAnalyzing ? "animate-pulse" : ""} />
                        <span>{isAnalyzing ? "Analyzing..." : "Re-Analyze"}</span>
                    </button>
                    <button
                        onClick={() => setIsNotesOpen(!isNotesOpen)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${isNotesOpen ? 'bg-warmstone-800 text-white' : 'bg-warmstone-200 text-warmstone-800 hover:bg-warmstone-300'}`}
                    >
                        <StickyNote size={16} />
                        <span>Notes</span>
                    </button>
                    <a
                        href={paper.url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-2 px-3 py-1.5 border border-warmstone-300 text-warmstone-700 rounded-lg text-sm hover:bg-warmstone-100"
                    >
                        <BookOpen size={16} />
                        <span>Source</span>
                    </a>
                </div>
            </div>

            {/* Main Content + Notes Layout */}
            <div className="flex-1 flex overflow-hidden">
                {/* Article Content */}
                <div className="flex-1 overflow-y-auto p-8 scrollbar-thin scrollbar-thumb-warmstone-300">
                    <div className="max-w-4xl mx-auto space-y-8">

                        {/* AI Summary Section */}
                        {hasAISummary && (
                            <section className="bg-gradient-to-br from-white to-purple-50 p-6 rounded-xl shadow-sm border border-purple-100 ring-1 ring-purple-50">
                                <div className="flex items-center gap-2 mb-4 text-purple-700">
                                    <Sparkles size={18} />
                                    <h2 className="text-sm font-bold uppercase tracking-wider">AI Summary</h2>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-4">
                                        <div>
                                            <h3 className="text-xs font-bold text-warmstone-500 uppercase mb-1">Main Ideas</h3>
                                            <p className="text-sm text-warmstone-800 leading-relaxed font-medium">{paper.summary_main_ideas}</p>
                                        </div>
                                        <div>
                                            <h3 className="text-xs font-bold text-warmstone-500 uppercase mb-1">Methods</h3>
                                            <p className="text-sm text-warmstone-800 leading-relaxed">{paper.summary_methods}</p>
                                        </div>
                                    </div>
                                    <div className="space-y-4">
                                        <div>
                                            <h3 className="text-xs font-bold text-warmstone-500 uppercase mb-1">Results</h3>
                                            <p className="text-sm text-warmstone-800 leading-relaxed">{paper.summary_results}</p>
                                        </div>
                                        {paper.summary_limitations && (
                                            <div>
                                                <h3 className="text-xs font-bold text-warmstone-500 uppercase mb-1">Limitations</h3>
                                                <p className="text-sm text-warmstone-800 leading-relaxed">{paper.summary_limitations}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </section>
                        )}

                        {/* Abstract Section */}
                        <section className="bg-white p-6 rounded-xl shadow-sm border border-warmstone-100">
                            <h2 className="text-sm font-bold uppercase tracking-wider text-warmstone-400 mb-3">Abstract</h2>
                            <p className="leading-relaxed text-warmstone-800">
                                {paper.abstract}
                            </p>
                        </section>

                        {/* Full Text / Body */}
                        <section className="prose prose-warmstone max-w-none">
                            {paper.full_text ? (
                                <ReactMarkdown>{paper.full_text}</ReactMarkdown>
                            ) : (
                                <div className="p-12 text-center border-2 border-dashed border-warmstone-200 rounded-xl text-warmstone-500">
                                    <p>Full text content not available locally.</p>
                                    <a href={paper.url} target="_blank" className="text-blue-600 hover:underline">Read original source</a>
                                </div>
                            )}
                        </section>
                    </div>
                </div>

                {/* Right Sidebar: Notes */}
                {isNotesOpen && (
                    <div className="w-[350px] border-l border-warmstone-200 bg-white flex flex-col shadow-xl animate-in slide-in-from-right duration-200">
                        <div className="p-4 border-b border-warmstone-100 font-bold text-warmstone-900 flex items-center gap-2">
                            <StickyNote size={16} className="text-warmstone-500" />
                            Research Notes
                        </div>

                        <div className="flex-1 overflow-y-auto p-4 space-y-4">
                            {notes?.map((note: any) => (
                                <div key={note.id} className="bg-warmstone-50 p-3 rounded-lg border border-warmstone-100 text-sm">
                                    <div className="prose prose-sm max-w-none text-warmstone-800">
                                        <ReactMarkdown components={{
                                            a: ({ href, children }) => (
                                                <a
                                                    href={href}
                                                    onClick={(e) => {
                                                        if (href?.startsWith('/')) {
                                                            e.preventDefault();
                                                            navigate(href);
                                                        }
                                                    }}
                                                    className="text-blue-600 hover:underline cursor-pointer"
                                                >
                                                    {children}
                                                </a>
                                            )
                                        }}>
                                            {note.content}
                                        </ReactMarkdown>
                                    </div>
                                    <div className="mt-2 text-xs text-warmstone-400">
                                        {new Date(note.created_at).toLocaleDateString()}
                                    </div>
                                </div>
                            ))}
                            {(!notes || notes.length === 0) && (
                                <p className="text-sm text-warmstone-400 text-center py-4">No notes yet.</p>
                            )}
                        </div>

                        <div className="p-4 border-t border-warmstone-100 bg-warmstone-50">
                            <textarea
                                className="w-full p-3 border border-warmstone-200 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                rows={3}
                                placeholder="Add a note (indexed by AI)..."
                                value={newNote}
                                onChange={e => setNewNote(e.target.value)}
                                onKeyDown={e => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSaveNote();
                                    }
                                }}
                            />
                            <div className="mt-2 flex justify-end">
                                <button
                                    disabled={!newNote.trim() || isSaving}
                                    onClick={handleSaveNote}
                                    className="px-3 py-1.5 bg-blue-600 text-white text-xs font-bold rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                                >
                                    {isSaving ? 'Saving...' : 'Save Note'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
