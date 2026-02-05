
import { useState, useCallback } from 'react'
import useSWR from 'swr'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, FileText, Calendar, StickyNote, Search, X, Tag, Link2, Filter, Plus, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'

interface NoteLink {
    id: number;
    linked_type: 'paper' | 'note';
    linked_id: string;
    linked_title?: string;
    link_type: string;
}

interface Note {
    id: number;
    title?: string;
    content: string;
    note_type: 'note' | 'annotation' | 'summary';
    created_at: string;
    updated_at?: string;
    tags?: string[];
    links?: NoteLink[];
}

const fetcher = (url: string) => fetch(url).then(r => r.json())

const NOTE_TYPE_STYLES = {
    note: { bg: 'bg-yellow-50', border: 'border-yellow-200', icon: 'text-yellow-600', label: 'Note' },
    annotation: { bg: 'bg-blue-50', border: 'border-blue-200', icon: 'text-blue-600', label: 'Annotation' },
    summary: { bg: 'bg-green-50', border: 'border-green-200', icon: 'text-green-600', label: 'Summary' },
}

export default function NotesList() {
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedType, setSelectedType] = useState<string>('');
    const [debouncedSearch, setDebouncedSearch] = useState('');

    // Debounce search
    const handleSearchChange = useCallback((value: string) => {
        setSearchQuery(value);
        const timeout = setTimeout(() => setDebouncedSearch(value), 300);
        return () => clearTimeout(timeout);
    }, []);

    // Build API URL with filters
    const apiUrl = `/api/notes${debouncedSearch || selectedType ? '?' : ''}${debouncedSearch ? `search=${encodeURIComponent(debouncedSearch)}` : ''
        }${debouncedSearch && selectedType ? '&' : ''}${selectedType ? `note_type=${selectedType}` : ''
        }`;

    const { data: notes, error, isLoading, mutate } = useSWR<Note[]>(apiUrl, fetcher);

    const handleDeleteNote = async (noteId: number) => {
        if (!confirm('Delete this note?')) return;
        try {
            await fetch(`/api/notes/${noteId}`, { method: 'DELETE' });
            mutate();
        } catch (e) {
            console.error('Failed to delete note:', e);
        }
    };

    // Group notes by linked paper (for notes with paper links) or as standalone
    const groupedNotes = (notes || []).reduce((acc, note) => {
        const paperLink = note.links?.find(l => l.linked_type === 'paper');
        const groupKey = paperLink?.linked_title || paperLink?.linked_id || '__standalone__';
        if (!acc[groupKey]) {
            acc[groupKey] = { paperId: paperLink?.linked_id, notes: [] };
        }
        acc[groupKey].notes.push(note);
        return acc;
    }, {} as Record<string, { paperId?: string; notes: Note[] }>);

    // Sort groups: standalone first, then by paper title
    const sortedGroups = Object.entries(groupedNotes).sort(([a], [b]) => {
        if (a === '__standalone__') return -1;
        if (b === '__standalone__') return 1;
        return a.localeCompare(b);
    });

    return (
        <div className="h-full bg-cream flex flex-col overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-warmstone-200 bg-cream-50">
                <div className="flex items-center gap-3 mb-4">
                    <button
                        onClick={() => navigate('/')}
                        className="p-1.5 text-warmstone-500 hover:text-warmstone-800 hover:bg-warmstone-100 rounded-lg transition-colors"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-yellow-100 flex items-center justify-center border border-yellow-200">
                            <StickyNote size={18} className="text-yellow-600" />
                        </div>
                        <h1 className="text-lg font-semibold text-warmstone-800">My Notes</h1>
                    </div>
                    <span className="ml-auto text-sm text-warmstone-500">
                        {notes?.length || 0} notes
                    </span>
                </div>

                {/* Search & Filter Bar */}
                <div className="flex gap-2">
                    <div className="flex-1 relative">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-warmstone-400" />
                        <input
                            type="text"
                            placeholder="Search notes..."
                            value={searchQuery}
                            onChange={(e) => handleSearchChange(e.target.value)}
                            className="w-full pl-9 pr-8 py-2 bg-white border border-warmstone-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-warmstone-300"
                        />
                        {searchQuery && (
                            <button
                                onClick={() => { setSearchQuery(''); setDebouncedSearch(''); }}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-warmstone-400 hover:text-warmstone-600"
                            >
                                <X size={14} />
                            </button>
                        )}
                    </div>
                    <div className="relative">
                        <select
                            value={selectedType}
                            onChange={(e) => setSelectedType(e.target.value)}
                            className="appearance-none pl-8 pr-6 py-2 bg-white border border-warmstone-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-warmstone-300 cursor-pointer"
                        >
                            <option value="">All Types</option>
                            <option value="note">Notes</option>
                            <option value="annotation">Annotations</option>
                            <option value="summary">Summaries</option>
                        </select>
                        <Filter size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-warmstone-400 pointer-events-none" />
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8">
                {isLoading ? (
                    <div className="flex justify-center p-12">
                        <div className="w-8 h-8 rounded-full border-2 border-warmstone-300 border-t-warmstone-600 animate-spin"></div>
                    </div>
                ) : error ? (
                    <div className="text-center p-12 text-red-500">Failed to load notes.</div>
                ) : !notes?.length ? (
                    <div className="text-center p-12 text-warmstone-500">
                        <StickyNote size={48} className="mx-auto mb-4 text-warmstone-300" />
                        <p>{searchQuery ? 'No notes match your search.' : 'No notes yet. Save notes from chat or while reading papers!'}</p>
                        <Link to="/" className="mt-4 inline-block text-blue-600 hover:underline">Go to Chat</Link>
                    </div>
                ) : (
                    <div className="max-w-4xl mx-auto space-y-6">
                        {sortedGroups.map(([groupKey, { paperId, notes: groupNotes }]) => (
                            <div key={groupKey} className="bg-white rounded-xl shadow-sm border border-warmstone-200 overflow-hidden">
                                {/* Group Header */}
                                {groupKey !== '__standalone__' ? (
                                    <div className="bg-warmstone-50 px-4 py-3 border-b border-warmstone-100 flex items-center gap-2">
                                        <FileText size={16} className="text-warmstone-400" />
                                        <h2 className="font-medium text-warmstone-800 truncate flex-1">{groupKey}</h2>
                                        {paperId && (
                                            <Link
                                                to={`/paper/${paperId}`}
                                                className="text-xs text-blue-600 hover:underline shrink-0"
                                            >
                                                View Paper
                                            </Link>
                                        )}
                                    </div>
                                ) : (
                                    <div className="bg-warmstone-50 px-4 py-3 border-b border-warmstone-100 flex items-center gap-2">
                                        <StickyNote size={16} className="text-warmstone-400" />
                                        <h2 className="font-medium text-warmstone-700">Standalone Notes</h2>
                                    </div>
                                )}

                                {/* Notes in Group */}
                                <div className="divide-y divide-warmstone-100">
                                    {groupNotes.map(note => {
                                        const typeStyle = NOTE_TYPE_STYLES[note.note_type] || NOTE_TYPE_STYLES.note;
                                        return (
                                            <div key={note.id} className="p-4 hover:bg-warmstone-50/50 transition-colors group">
                                                {/* Note Header */}
                                                <div className="flex items-start gap-2 mb-2">
                                                    <span className={clsx(
                                                        'text-[10px] font-medium px-1.5 py-0.5 rounded',
                                                        typeStyle.bg, typeStyle.border, 'border'
                                                    )}>
                                                        {typeStyle.label}
                                                    </span>
                                                    {note.title && (
                                                        <h3 className="font-medium text-warmstone-800 flex-1">{note.title}</h3>
                                                    )}
                                                    <button
                                                        onClick={() => handleDeleteNote(note.id)}
                                                        className="opacity-0 group-hover:opacity-100 p-1 text-warmstone-400 hover:text-red-500 transition-all"
                                                        title="Delete note"
                                                    >
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>

                                                {/* Note Content */}
                                                <div className="prose prose-sm prose-warmstone max-w-none text-warmstone-700 mb-3">
                                                    <ReactMarkdown
                                                        components={{
                                                            a: ({ href, children }) => {
                                                                const isPaperLink = href?.startsWith('/paper/');
                                                                return (
                                                                    <Link
                                                                        to={href || '#'}
                                                                        className="text-blue-600 hover:underline font-medium"
                                                                        onClick={(e) => {
                                                                            if (isPaperLink && href) {
                                                                                e.preventDefault();
                                                                                navigate(href);
                                                                            }
                                                                        }}
                                                                    >
                                                                        {children}
                                                                    </Link>
                                                                );
                                                            }
                                                        }}
                                                    >
                                                        {note.content}
                                                    </ReactMarkdown>
                                                </div>

                                                {/* Note Footer: Links, Tags, Date */}
                                                <div className="flex flex-wrap items-center gap-2 text-xs text-warmstone-400">
                                                    {/* Linked Items */}
                                                    {note.links && note.links.length > 0 && (
                                                        <div className="flex items-center gap-1">
                                                            <Link2 size={12} />
                                                            {note.links.slice(0, 3).map(link => (
                                                                <Link
                                                                    key={link.id}
                                                                    to={link.linked_type === 'paper' ? `/paper/${link.linked_id}` : '#'}
                                                                    className="bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded hover:bg-blue-100 truncate max-w-[120px]"
                                                                    title={link.linked_title || link.linked_id}
                                                                >
                                                                    {link.linked_title?.slice(0, 20) || link.linked_id.slice(0, 10)}...
                                                                </Link>
                                                            ))}
                                                            {note.links.length > 3 && (
                                                                <span className="text-warmstone-400">+{note.links.length - 3}</span>
                                                            )}
                                                        </div>
                                                    )}

                                                    {/* Tags */}
                                                    {note.tags && note.tags.length > 0 && (
                                                        <div className="flex items-center gap-1">
                                                            <Tag size={12} />
                                                            {note.tags.map(tag => (
                                                                <span key={tag} className="bg-warmstone-100 px-1.5 py-0.5 rounded text-warmstone-600">
                                                                    #{tag}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}

                                                    {/* Date */}
                                                    <div className="flex items-center gap-1 ml-auto">
                                                        <Calendar size={12} />
                                                        <span>{new Date(note.updated_at || note.created_at).toLocaleDateString()}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
