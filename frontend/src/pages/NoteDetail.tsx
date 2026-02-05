
import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import useSWR, { mutate } from 'swr'
import { ArrowLeft, Save, Trash2, Calendar, Tag, FileText, Link2, StickyNote, Edit3, X, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'

const fetcher = (url: string) => fetch(url).then(r => r.json())

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

const NOTE_TYPE_STYLES = {
    note: { bg: 'bg-yellow-50', border: 'border-yellow-200', icon: 'text-yellow-600', label: 'Note' },
    annotation: { bg: 'bg-blue-50', border: 'border-blue-200', icon: 'text-blue-600', label: 'Annotation' },
    summary: { bg: 'bg-green-50', border: 'border-green-200', icon: 'text-green-600', label: 'Summary' },
}

export default function NoteDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [isEditing, setIsEditing] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    // Form state
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [noteType, setNoteType] = useState<string>('note');
    const [tags, setTags] = useState<string[]>([]);
    const [tagInput, setTagInput] = useState('');

    const { data: note, error, isLoading } = useSWR<Note>(
        id ? `/api/notes/${id}` : null,
        fetcher,
        {
            onSuccess: (data) => {
                if (!isEditing) {
                    setTitle(data.title || '');
                    setContent(data.content);
                    setNoteType(data.note_type);
                    setTags(data.tags || []);
                }
            }
        }
    );

    const handleSave = async () => {
        if (!id) return;
        try {
            await fetch(`/api/notes/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title,
                    content,
                    note_type: noteType,
                    tags
                })
            });
            await mutate(`/api/notes/${id}`);
            mutate('/api/notes'); // Refresh list
            setIsEditing(false);
        } catch (e) {
            console.error('Failed to update note:', e);
            alert('Failed to save changes');
        }
    };

    const handleDelete = async () => {
        // if (!confirm('Are you sure you want to delete this note?')) return;
        try {
            await fetch(`/api/notes/${id}`, { method: 'DELETE' });
            await mutate('/api/notes'); // Ensure cache is invalidated
            navigate('/', { replace: true }); // Use replace to prevent back navigation
        } catch (e) {
            console.error('Failed to delete note:', e);
            alert('Failed to delete note');
        }
    };

    const handleAddTag = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && tagInput.trim()) {
            e.preventDefault();
            if (!tags.includes(tagInput.trim())) {
                setTags([...tags, tagInput.trim()]);
            }
            setTagInput('');
        }
    };

    const removeTag = (tagToRemove: string) => {
        setTags(tags.filter(t => t !== tagToRemove));
    };

    if (isLoading) {
        return (
            <div className="flex h-full items-center justify-center bg-cream">
                <div className="w-8 h-8 rounded-full border-2 border-warmstone-300 border-t-warmstone-600 animate-spin"></div>
            </div>
        );
    }

    if (error || !note) {
        return (
            <div className="flex flex-col h-full items-center justify-center bg-cream text-warmstone-500">
                <p>Note not found</p>
                <Link to="/" className="mt-2 text-blue-600 hover:underline">Return to Library</Link>
            </div>
        );
    }

    const typeStyle = NOTE_TYPE_STYLES[note.note_type as keyof typeof NOTE_TYPE_STYLES] || NOTE_TYPE_STYLES.note;

    return (
        <div className="h-full bg-cream flex flex-col overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-warmstone-200 bg-cream-50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/')}
                        className="p-1.5 text-warmstone-500 hover:text-warmstone-800 hover:bg-warmstone-100 rounded-lg transition-colors"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    {!isEditing && (
                        <div className="flex items-center gap-2">
                            <div className={clsx("w-8 h-8 rounded-lg flex items-center justify-center border", typeStyle.bg, typeStyle.border)}>
                                <StickyNote size={18} className={typeStyle.icon} />
                            </div>
                            <div>
                                <h1 className="text-lg font-semibold text-warmstone-800 line-clamp-1 max-w-md">
                                    {note.title || 'Untitled Note'}
                                </h1>
                                <span className="text-xs text-warmstone-500 capitalize">{note.note_type}</span>
                            </div>
                        </div>
                    )}
                    {isEditing && <h1 className="text-lg font-semibold text-warmstone-800">Edit Note</h1>}
                </div>

                <div className="flex items-center gap-2">
                    {isEditing ? (
                        <>
                            <button
                                onClick={() => setIsEditing(false)}
                                className="px-3 py-1.5 text-sm bg-warmstone-100 text-warmstone-700 rounded-lg hover:bg-warmstone-200"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSave}
                                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-warmstone-800 text-white rounded-lg hover:bg-warmstone-700"
                            >
                                <Save size={14} />
                                Save
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                onClick={() => setIsEditing(true)}
                                className="p-2 text-warmstone-500 hover:text-warmstone-800 hover:bg-warmstone-100 rounded-lg transition-colors"
                                title="Edit note"
                            >
                                <Edit3 size={18} />
                            </button>

                            {showDeleteConfirm ? (
                                <div className="flex items-center gap-1 bg-red-50 p-1 rounded-lg border border-red-100">
                                    <button
                                        onClick={handleDelete}
                                        className="p-1.5 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                                        title="Confirm delete"
                                    >
                                        <Check size={16} />
                                    </button>
                                    <button
                                        onClick={() => setShowDeleteConfirm(false)}
                                        className="p-1.5 text-red-500 hover:bg-red-100 rounded transition-colors"
                                        title="Cancel delete"
                                    >
                                        <X size={16} />
                                    </button>
                                </div>
                            ) : (
                                <button
                                    onClick={() => setShowDeleteConfirm(true)}
                                    className="p-2 text-warmstone-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                    title="Delete note"
                                >
                                    <Trash2 size={18} />
                                </button>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8">
                <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-sm border border-warmstone-200 min-h-[500px]">
                    {isEditing ? (
                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-warmstone-700 mb-1">Title</label>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={e => setTitle(e.target.value)}
                                    className="w-full px-3 py-2 border border-warmstone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-warmstone-300"
                                    placeholder="Note Title"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-warmstone-700 mb-1">Type</label>
                                    <select
                                        value={noteType}
                                        onChange={e => setNoteType(e.target.value)}
                                        className="w-full px-3 py-2 border border-warmstone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-warmstone-300"
                                    >
                                        <option value="note">Note</option>
                                        <option value="annotation">Annotation</option>
                                        <option value="summary">Summary</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-warmstone-700 mb-1">Tags</label>
                                    <div className="flex flex-wrap gap-2 p-2 border border-warmstone-200 rounded-lg min-h-[42px]">
                                        {tags.map(tag => (
                                            <span key={tag} className="flex items-center gap-1 bg-warmstone-100 text-xs px-2 py-1 rounded text-warmstone-700">
                                                #{tag}
                                                <button onClick={() => removeTag(tag)} className="hover:text-red-500"><X size={12} /></button>
                                            </span>
                                        ))}
                                        <input
                                            type="text"
                                            value={tagInput}
                                            onChange={e => setTagInput(e.target.value)}
                                            onKeyDown={handleAddTag}
                                            className="flex-1 min-w-[60px] text-sm focus:outline-none bg-transparent"
                                            placeholder={tags.length === 0 ? "Add tags..." : ""}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-warmstone-700 mb-1">Content (Markdown)</label>
                                <textarea
                                    value={content}
                                    onChange={e => setContent(e.target.value)}
                                    className="w-full h-[400px] px-3 py-2 border border-warmstone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-warmstone-300 font-mono text-sm"
                                    placeholder="# Write your note here..."
                                />
                            </div>
                        </div>
                    ) : (
                        <div className="p-8">
                            {/* Metadata */}
                            <div className="flex flex-wrap gap-4 mb-6 pb-6 border-b border-warmstone-100 text-sm text-warmstone-500">
                                <div className="flex items-center gap-1.5">
                                    <Calendar size={14} />
                                    <span>Created {new Date(note.created_at).toLocaleDateString()}</span>
                                </div>
                                {note.updated_at && (
                                    <div className="flex items-center gap-1.5">
                                        <Edit3 size={14} />
                                        <span>Updated {new Date(note.updated_at).toLocaleDateString()}</span>
                                    </div>
                                )}
                                {note.tags && note.tags.length > 0 && (
                                    <div className="flex items-center gap-1.5">
                                        <Tag size={14} />
                                        <div className="flex gap-1">
                                            {note.tags.map(tag => (
                                                <span key={tag} className="bg-warmstone-100 px-1.5 py-0.5 rounded text-warmstone-600">
                                                    #{tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Rendered Content */}
                            <div className="prose prose-warmstone max-w-none">
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

                            {/* Linked Items */}
                            {note.links && note.links.length > 0 && (
                                <div className="mt-8 pt-6 border-t border-warmstone-100">
                                    <h3 className="text-sm font-semibold text-warmstone-800 mb-3 flex items-center gap-2">
                                        <Link2 size={16} />
                                        Linked Resources
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {note.links.map(link => (
                                            <Link
                                                key={link.id}
                                                to={link.linked_type === 'paper' ? `/paper/${link.linked_id}` : `/notes/${link.linked_id}`}
                                                className="flex items-center gap-2 bg-white border border-warmstone-200 px-3 py-1.5 rounded-lg hover:bg-warmstone-50 hover:border-warmstone-300 transition-colors group"
                                            >
                                                {link.linked_type === 'paper' ? (
                                                    <FileText size={14} className="text-blue-500" />
                                                ) : (
                                                    <StickyNote size={14} className="text-yellow-500" />
                                                )}
                                                <span className="text-sm text-warmstone-700 group-hover:text-blue-600">
                                                    {link.linked_title || link.linked_id}
                                                </span>
                                            </Link>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
