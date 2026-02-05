
import useSWR, { mutate } from 'swr'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ExternalLink, Users, BookOpen, Library, MessageCircle, Plus, X, FolderOpen, StickyNote, FileText, Trash2 } from 'lucide-react'
import { type ColumnDef } from '@tanstack/react-table'
import { DataTable } from './DataTable'
import clsx from 'clsx'

// Types
interface Paper {
    id: string;
    title: string;
    url?: string;
    published_date?: string;
    authors: string[];
    summary_main_ideas?: string;
    abstract?: string;
    tags?: string[];
    citation_count?: number;
    source_id?: number;
    source_name?: string;
    source_icon?: string;
}

interface Note {
    id: number;
    title?: string;
    content: string;
    note_type: 'note' | 'annotation' | 'summary';
    created_at: string;
    updated_at?: string;
    tags?: string[];
    paper_id?: string; // Links
}

type LibraryItem =
    | (Paper & { itemType: 'paper' })
    | (Note & { itemType: 'note' });

interface Source {
    id: number;
    name: string;
    source_type: string;
    config: Record<string, any>;
    description?: string;
    icon: string;
    enabled: boolean;
    paper_count: number;
    created_at: string;
}

interface PaperListProps {
    onAskAboutPaper?: (paperId: string, paperTitle: string) => void;
    searchQuery?: string;
}

const fetcher = (url: string) => fetch(url).then(r => r.json())

// Column Helper
function createColumns(onAskAboutPaper?: (id: string, title: string) => void): ColumnDef<LibraryItem, any>[] {
    return [
        {
            accessorKey: 'title', // Functions as ID for sorting, but we use cell for content
            header: 'Resource',
            cell: ({ row }) => {
                const item = row.original;

                if (item.itemType === 'paper') {
                    return (
                        <div className="flex items-start gap-3 max-w-lg py-1">
                            <div className="mt-1 p-1 bg-blue-50 text-blue-600 rounded shrink-0" title="Paper">
                                <FileText size={16} />
                            </div>
                            <div className="flex flex-col gap-1">
                                <Link
                                    to={`/paper/${item.id}`}
                                    className="font-medium text-warmstone-800 line-clamp-2 leading-snug hover:text-blue-600 hover:underline"
                                >
                                    {item.title}
                                </Link>
                                <div className="flex items-center gap-3 text-xs text-warmstone-500">
                                    <span className="flex items-center gap-1">
                                        <Users size={11} className="text-warmstone-400" />
                                        {item.authors.slice(0, 2).join(", ")}{item.authors.length > 2 ? " et al." : ""}
                                    </span>
                                    {item.source_name && (
                                        <span className="flex items-center gap-1 text-warmstone-400">
                                            <span>{item.source_icon || '📄'}</span>
                                            <span>{item.source_name}</span>
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                } else {
                    // Note
                    const typeColor =
                        item.note_type === 'summary' ? 'text-green-600 bg-green-50' :
                            item.note_type === 'annotation' ? 'text-blue-600 bg-blue-50' :
                                'text-yellow-600 bg-yellow-50';

                    return (
                        <div className="flex items-start gap-3 max-w-lg py-1">
                            <div className={clsx("mt-1 p-1 rounded shrink-0", typeColor)} title={item.note_type}>
                                <StickyNote size={16} />
                            </div>
                            <div className="flex flex-col gap-1">
                                <Link
                                    to={`/notes/${item.id}`} // Link to specific note detail
                                    className="font-medium text-warmstone-800 line-clamp-2 leading-snug hover:text-blue-600 hover:underline"
                                >
                                    {item.title || item.content.substring(0, 50) + "..."}
                                </Link>
                                <div className="flex items-center gap-3 text-xs text-warmstone-500">
                                    <span className="capitalize text-warmstone-400">
                                        {item.note_type}
                                    </span>
                                </div>
                            </div>
                        </div>
                    );
                }
            },
            sortingFn: (rowA, rowB) => {
                const a = rowA.original;
                const b = rowB.original;
                const titleA = a.itemType === 'paper' ? a.title : (a.title || a.content);
                const titleB = b.itemType === 'paper' ? b.title : (b.title || b.content);
                return titleA.localeCompare(titleB);
            }
        },
        {
            accessorKey: 'date', // Virtual accessor
            header: 'Date',
            cell: ({ row }) => {
                const item = row.original;
                const date = item.itemType === 'paper' ? item.published_date : item.created_at;
                return (
                    <span className="text-warmstone-600 text-sm">
                        {date ? new Date(date).getFullYear() : '—'}
                    </span>
                );
            },
            sortingFn: (rowA, rowB) => {
                const a = rowA.original;
                const b = rowB.original;
                const dateA = a.itemType === 'paper' ? a.published_date : a.created_at;
                const dateB = b.itemType === 'paper' ? b.published_date : b.created_at;
                return (dateA || '').localeCompare(dateB || '');
            }
        },
        {
            accessorKey: 'tags',
            header: 'Topics',
            cell: ({ row }) => {
                const tags = row.original.tags;
                if (!tags?.length) return <span className="text-warmstone-400">—</span>;
                return (
                    <div className="flex flex-wrap gap-1.5">
                        {tags.slice(0, 2).map((tag, i) => (
                            <span
                                key={i}
                                className={clsx(
                                    "text-[10px] px-2 py-0.5 rounded-md border",
                                    i === 0
                                        ? "bg-warmstone-100 text-warmstone-700 border-warmstone-200"
                                        : "bg-warmstone-50 text-warmstone-500 border-warmstone-200"
                                )}
                            >
                                {tag}
                            </span>
                        ))}
                        {tags.length > 2 && (
                            <span className="text-[10px] text-warmstone-400 self-center">+{tags.length - 2}</span>
                        )}
                    </div>
                );
            },
            enableSorting: false,
        },
        {
            id: 'actions',
            header: '',
            cell: ({ row }) => {
                const item = row.original;

                if (item.itemType === 'note') {
                    return (
                        <div className="flex items-center gap-1">
                            <button
                                onClick={async (e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    if (confirm('Delete this note?')) {
                                        try {
                                            await fetch(`/api/notes/${item.id}`, { method: 'DELETE' });
                                            mutate('/api/notes'); // Refresh list
                                        } catch (err) {
                                            console.error('Failed to delete', err);
                                        }
                                    }
                                }}
                                className="p-2 text-warmstone-400 hover:text-red-600 transition-all rounded-lg hover:bg-red-50 inline-flex"
                                title="Delete note"
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    );
                }

                return (
                    <div className="flex items-center gap-1">
                        {onAskAboutPaper && (
                            <button
                                onClick={() => onAskAboutPaper(item.id, item.title)}
                                className="p-2 text-blue-500 hover:text-blue-700 transition-all rounded-lg hover:bg-blue-50 inline-flex"
                                title="Ask about this paper"
                            >
                                <MessageCircle size={14} />
                            </button>
                        )}
                        {item.url && (
                            <a
                                href={item.url}
                                target="_blank"
                                rel="noreferrer"
                                className="p-2 text-warmstone-400 hover:text-warmstone-700 transition-all rounded-lg hover:bg-warmstone-100 inline-flex"
                                title="View source"
                            >
                                <ExternalLink size={14} />
                            </a>
                        )}
                    </div>
                );
            },
            enableSorting: false,
        },
    ];
}

// Source type options for creating new sources
const SOURCE_TYPES = [
    { value: 'arxiv', label: 'ArXiv', icon: '📄', description: 'ArXiv preprint server' },
    { value: 'url', label: 'URL/RSS', icon: '🔗', description: 'Papers from a URL or RSS feed' },
    { value: 'local_file', label: 'Local Files', icon: '📁', description: 'Papers from local PDF files' },
    { value: 'bibtex', label: 'BibTeX', icon: '📚', description: 'Import from BibTeX file' },
    { value: 'custom', label: 'Custom', icon: '⚙️', description: 'Custom paper source' },
];

function AddSourceModal({ isOpen, onClose, onAdd }: { isOpen: boolean; onClose: () => void; onAdd: () => void }) {
    const [name, setName] = useState('');
    const [sourceType, setSourceType] = useState('url');
    const [description, setDescription] = useState('');
    const [configUrl, setConfigUrl] = useState('');
    const [configPath, setConfigPath] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;

        setIsSubmitting(true);
        try {
            const config: Record<string, string> = {};
            if (sourceType === 'url') config.url = configUrl;
            if (sourceType === 'local_file') config.path = configPath;

            const selectedType = SOURCE_TYPES.find(t => t.value === sourceType);

            await fetch('/api/sources', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name.trim(),
                    source_type: sourceType,
                    config,
                    description: description.trim() || undefined,
                    icon: selectedType?.icon || '📁'
                })
            });

            setName('');
            setDescription('');
            setConfigUrl('');
            setConfigPath('');
            onAdd();
            onClose();
        } catch (error) {
            console.error('Failed to create source:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b border-warmstone-200">
                    <h3 className="text-lg font-semibold text-warmstone-800">Add Library Source</h3>
                    <button onClick={onClose} className="p-1 hover:bg-warmstone-100 rounded-lg">
                        <X size={20} className="text-warmstone-500" />
                    </button>
                </div>
                <form onSubmit={handleSubmit} className="p-4 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-warmstone-700 mb-1">Source Name</label>
                        <input
                            type="text"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            placeholder="e.g., My Research Papers"
                            className="w-full px-3 py-2 border border-warmstone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-warmstone-300"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-warmstone-700 mb-1">Source Type</label>
                        <div className="grid grid-cols-2 gap-2">
                            {SOURCE_TYPES.map(type => (
                                <button
                                    key={type.value}
                                    type="button"
                                    onClick={() => setSourceType(type.value)}
                                    className={clsx(
                                        "p-3 rounded-lg border text-left transition-all",
                                        sourceType === type.value
                                            ? "border-warmstone-400 bg-warmstone-50"
                                            : "border-warmstone-200 hover:border-warmstone-300"
                                    )}
                                >
                                    <span className="text-lg">{type.icon}</span>
                                    <span className="block text-sm font-medium text-warmstone-800">{type.label}</span>
                                    <span className="block text-xs text-warmstone-500">{type.description}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {sourceType === 'url' && (
                        <div>
                            <label className="block text-sm font-medium text-warmstone-700 mb-1">URL / RSS Feed</label>
                            <input
                                type="url"
                                value={configUrl}
                                onChange={e => setConfigUrl(e.target.value)}
                                placeholder="https://example.com/papers.rss"
                                className="w-full px-3 py-2 border border-warmstone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-warmstone-300"
                            />
                        </div>
                    )}

                    {sourceType === 'local_file' && (
                        <div>
                            <label className="block text-sm font-medium text-warmstone-700 mb-1">Folder Path</label>
                            <input
                                type="text"
                                value={configPath}
                                onChange={e => setConfigPath(e.target.value)}
                                placeholder="/path/to/papers"
                                className="w-full px-3 py-2 border border-warmstone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-warmstone-300"
                            />
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-warmstone-700 mb-1">Description (optional)</label>
                        <input
                            type="text"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            placeholder="A brief description..."
                            className="w-full px-3 py-2 border border-warmstone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-warmstone-300"
                        />
                    </div>

                    <div className="flex gap-2 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2 border border-warmstone-200 text-warmstone-700 rounded-lg hover:bg-warmstone-50"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting || !name.trim()}
                            className="flex-1 px-4 py-2 bg-warmstone-800 text-white rounded-lg hover:bg-warmstone-700 disabled:opacity-50"
                        >
                            {isSubmitting ? 'Adding...' : 'Add Source'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default function PaperList({ onAskAboutPaper, searchQuery }: PaperListProps) {
    const [selectedSourceId, setSelectedSourceId] = useState<string | number>('arxiv');
    const [showAddSource, setShowAddSource] = useState(false);
    const [sortBy, setSortBy] = useState('recency');

    // Fetch sources
    const { data: sources } = useSWR<Source[]>('/api/sources', fetcher);

    // Fetch papers: Only fetch if NOT filtering by 'notes'
    // If selectedSourceId is 'notes', we don't need papers.
    // If 'all', we need everything.
    const shouldFetchPapers = selectedSourceId !== 'notes';
    const paperUrl = shouldFetchPapers
        ? (selectedSourceId !== 'all'
            ? (typeof selectedSourceId === 'number'
                ? `/api/papers?sort=${sortBy}&source_id=${selectedSourceId}`
                : `/api/papers?sort=${sortBy}&source_type=${selectedSourceId}`)
            : `/api/papers?sort=${sortBy}`)
        : null;

    const { data: papers, isLoading: papersLoading, error: papersError } = useSWR<Paper[]>(
        paperUrl,
        fetcher,
        { revalidateOnFocus: false }
    );

    // Fetch notes: Fetch if 'notes' or 'all' is selected
    const shouldFetchNotes = selectedSourceId === 'all' || selectedSourceId === 'notes';
    const { data: notes, isLoading: notesLoading } = useSWR<Note[]>(
        shouldFetchNotes ? '/api/notes' : null,
        fetcher,
        { revalidateOnFocus: false }
    );

    const mergedData: LibraryItem[] = useMemo(() => {
        const items: LibraryItem[] = [];

        if (Array.isArray(papers)) {
            items.push(...papers.map(p => ({ ...p, itemType: 'paper' as const })));
        }

        // Show notes if no source filter is active or if we decide notes belong to all sources
        // If a note is linked to a paper in the filtered source, we could show it.
        // For simplicity, let's show notes only when "All Sources" is selected or if we explicitly toggle them.
        if (Array.isArray(notes) && shouldFetchNotes) {
            items.push(...notes.map(n => ({ ...n, itemType: 'note' as const })));
        }

        // Sort merged data by date (recency)
        return items.sort((a, b) => {
            const dateA = a.itemType === 'paper' ? a.published_date : a.created_at;
            const dateB = b.itemType === 'paper' ? b.published_date : b.created_at;
            // Descending
            return (dateB || '').localeCompare(dateA || '');
        });

    }, [papers, notes, selectedSourceId, shouldFetchPapers, shouldFetchNotes]);

    const columns = useMemo(() => createColumns(onAskAboutPaper), [onAskAboutPaper]);

    const allTags = useMemo(() => {
        const tags = new Set<string>();
        if (Array.isArray(papers)) papers.forEach(p => p.tags?.forEach(t => tags.add(t)));
        if (Array.isArray(notes)) notes.forEach(n => n.tags?.forEach(t => tags.add(t)));
        return Array.from(tags).sort();
    }, [papers, notes]);

    // Check for number (source_id) or string (source_type)
    const handleSourceAdded = () => {
        mutate('/api/sources');
        mutate(paperUrl);
    };

    const isLoading = papersLoading || notesLoading;
    const error = papersError; // Note error usually less critical

    if (isLoading && !papers && !notes) {
        return (
            <div className="flex h-full items-center justify-center bg-cream">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 rounded-full border-2 border-warmstone-300 border-t-warmstone-600 animate-spin"></div>
                    <span className="text-sm text-warmstone-500">Loading library...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-full items-center justify-center p-8 bg-cream">
                <div className="text-red-600 text-sm bg-red-50 px-6 py-4 rounded-xl border border-red-200 shadow-card">
                    <p className="font-medium">Connection Error</p>
                    <p className="text-red-500 text-xs mt-1">Failed to load library. Please try again.</p>
                </div>
            </div>
        );
    }

    if (!mergedData.length && selectedSourceId === 'all') {
        return (
            <div className="flex flex-col h-full items-center justify-center text-center p-8 bg-cream">
                <div className="w-16 h-16 bg-warmstone-100 rounded-2xl flex items-center justify-center mb-4 border border-warmstone-200 shadow-card">
                    <BookOpen size={28} className="text-warmstone-400" />
                </div>
                <h3 className="text-lg font-semibold text-warmstone-800 mb-2">Library Empty</h3>
                <p className="text-warmstone-500 text-sm max-w-xs mb-4">
                    Ask the assistant to find and save papers to build your research collection.
                </p>
                <div className="flex gap-2">
                    <button
                        onClick={() => setShowAddSource(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-warmstone-800 text-white rounded-lg hover:bg-warmstone-700"
                    >
                        <Plus size={16} />
                        Add Source
                    </button>
                    <Link
                        to="/notes"
                        className="flex items-center gap-2 px-4 py-2 bg-white border border-warmstone-200 text-warmstone-700 rounded-lg hover:bg-warmstone-50"
                    >
                        <StickyNote size={16} />
                        View Notes
                    </Link>
                </div>
                <AddSourceModal
                    isOpen={showAddSource}
                    onClose={() => setShowAddSource(false)}
                    onAdd={handleSourceAdded}
                />
            </div>
        );
    }

    return (
        <div className="h-full bg-cream flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-warmstone-200 bg-cream-50">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-warmstone-100 flex items-center justify-center border border-warmstone-200 shadow-card">
                            <Library size={18} className="text-warmstone-600" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-warmstone-800">
                                Library
                                <span className="ml-2 text-sm font-normal text-warmstone-500">
                                    {(papers?.length || 0) + (notes?.length || 0)} items
                                </span>
                            </h2>
                            <p className="text-xs text-warmstone-500">Your curated research collection</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* Source Filter Dropdown */}
                        <div className="relative">
                            <select
                                value={selectedSourceId ?? ''}
                                onChange={e => {
                                    const val = e.target.value;
                                    // If val is a number string, convert to number, otherwise keep as string
                                    const isNum = !isNaN(Number(val));
                                    setSelectedSourceId(val === 'all' || val === 'notes' ? val : (isNum ? Number(val) : val));
                                }}
                                className="appearance-none bg-white border border-warmstone-200 rounded-lg px-3 py-1.5 pr-8 text-sm text-warmstone-700 focus:outline-none focus:border-warmstone-300 cursor-pointer"
                            >
                                <option value="all">All Sources</option>
                                <optgroup label="Personal">
                                    <option value="notes">Notes</option>
                                </optgroup>
                                <optgroup label="Research">
                                    <option value="arxiv">ArXiv</option>
                                    <option value="url">Websites</option>
                                    {sources?.map(source => (
                                        <option key={source.id} value={source.id}>
                                            {source.name} ({source.paper_count})
                                        </option>
                                    ))}
                                </optgroup>
                            </select>
                            <FolderOpen size={14} className="absolute right-2 top-1/2 -translate-y-1/2 text-warmstone-400 pointer-events-none" />
                        </div>



                        {/* Add Source Button */}
                        <button
                            onClick={() => setShowAddSource(true)}
                            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-warmstone-800 text-white rounded-lg hover:bg-warmstone-700"
                            title="Add Source"
                        >
                            <Plus size={14} />
                            <span className="hidden sm:inline">Add Source</span>
                        </button>
                    </div>
                </div>

                {/* Source Pills (Removed) */}
            </div>

            <div className="flex-1 overflow-hidden">
                <DataTable
                    data={mergedData}
                    columns={columns}
                    searchPlaceholder="Search papers, notes, authors..."
                    filterableColumns={[{ id: 'tags', title: 'Topics', options: allTags }]}
                    externalSearch={searchQuery}
                />
            </div>

            <AddSourceModal
                isOpen={showAddSource}
                onClose={() => setShowAddSource(false)}
                onAdd={handleSourceAdded}
            />
        </div>
    );
}

