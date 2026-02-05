
import { useState, useMemo, useEffect } from 'react'
import {
    flexRender,
    getCoreRowModel,
    getFilteredRowModel,
    getSortedRowModel,
    getPaginationRowModel,
    useReactTable,

    type ColumnDef,
    type SortingState,
    type ColumnFiltersState,
} from '@tanstack/react-table'
import { ChevronUp, ChevronDown, ChevronsUpDown, Search, X, Filter, SlidersHorizontal, ChevronLeft, ChevronRight } from 'lucide-react'

import clsx from 'clsx'

interface DataTableProps<T> {
    data: T[];
    columns: ColumnDef<T, any>[];
    searchPlaceholder?: string;
    filterableColumns?: { id: string; title: string; options: string[] }[];
    externalSearch?: string;
}

function DebouncedInput({
    value: initialValue,
    onChange,
    debounce = 300,
    ...props
}: {
    value: string;
    onChange: (value: string) => void;
    debounce?: number;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'>) {
    const [value, setValue] = useState(initialValue);

    // Sync with external value changes
    useEffect(() => {
        setValue(initialValue);
    }, [initialValue]);

    // Debounce the onChange callback
    useEffect(() => {
        const timeout = setTimeout(() => {
            if (value !== initialValue) {
                onChange(value);
            }
        }, debounce);
        return () => clearTimeout(timeout);
    }, [value, debounce, onChange, initialValue]);

    return <input {...props} value={value} onChange={(e) => setValue(e.target.value)} />;
}

export function DataTable<T extends object>({
    data,
    columns,
    searchPlaceholder = "Search...",
    filterableColumns = [],
    externalSearch
}: DataTableProps<T>) {
    const [sorting, setSorting] = useState<SortingState>([])
    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
    const [globalFilter, setGlobalFilter] = useState(externalSearch || '')
    const [activeFilters, setActiveFilters] = useState<Record<string, string[]>>({})
    const [showFilters, setShowFilters] = useState(false)

    // Sync external search
    useEffect(() => {
        if (externalSearch !== undefined) {
            setGlobalFilter(externalSearch);
        }
    }, [externalSearch]);

    const filteredData = useMemo(() => {
        if (Object.keys(activeFilters).length === 0) return data;
        return data.filter((row: any) => {
            return Object.entries(activeFilters).every(([columnId, values]) => {
                if (values.length === 0) return true;
                const cellValue = row[columnId];
                if (Array.isArray(cellValue)) return values.some(v => cellValue.includes(v));
                return values.includes(cellValue);
            });
        });
    }, [data, activeFilters]);

    const table = useReactTable({
        data: filteredData,
        columns,
        state: { sorting, columnFilters, globalFilter },
        onSortingChange: setSorting,
        onColumnFiltersChange: setColumnFilters,
        onGlobalFilterChange: setGlobalFilter,
        getCoreRowModel: getCoreRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        initialState: {
            pagination: {
                pageSize: 10,
            },
        },
    });

    const toggleFilter = (columnId: string, value: string) => {
        setActiveFilters(prev => {
            const current = prev[columnId] || [];
            const updated = current.includes(value) ? current.filter(v => v !== value) : [...current, value];
            return { ...prev, [columnId]: updated };
        });
    };

    const clearFilters = () => { setActiveFilters({}); setGlobalFilter(''); };
    const hasActiveFilters = Object.values(activeFilters).some(v => v.length > 0) || globalFilter;
    const activeFilterCount = Object.values(activeFilters).reduce((sum, arr) => sum + arr.length, 0);

    return (
        <div className="flex flex-col h-full bg-cream">
            {/* Toolbar */}
            <div className="flex items-center gap-4 p-4 border-b border-warmstone-200 bg-cream-50">
                {/* Search */}
                <div className="relative flex-1 max-w-md">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-warmstone-400" />
                    <DebouncedInput
                        value={globalFilter}
                        onChange={setGlobalFilter}
                        className="w-full bg-white border border-warmstone-200 rounded-lg py-2 pl-10 pr-4 text-sm text-warmstone-700 placeholder-warmstone-400 focus:outline-none focus:border-warmstone-300 focus:ring-1 focus:ring-warmstone-200 transition-all shadow-card"
                        placeholder={searchPlaceholder}
                    />
                </div>

                {/* Filter toggle button */}
                {filterableColumns.length > 0 && (
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={clsx(
                            "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all border shadow-card",
                            showFilters || activeFilterCount > 0
                                ? "bg-warmstone-100 text-warmstone-800 border-warmstone-300"
                                : "bg-white text-warmstone-600 border-warmstone-200 hover:border-warmstone-300"
                        )}
                    >
                        <SlidersHorizontal size={16} />
                        Filters
                        {activeFilterCount > 0 && (
                            <span className="bg-warmstone-800 text-white text-xs px-1.5 py-0.5 rounded-full min-w-[18px]">
                                {activeFilterCount}
                            </span>
                        )}
                    </button>
                )}

                {hasActiveFilters && (
                    <button onClick={clearFilters} className="flex items-center gap-1 text-xs text-warmstone-500 hover:text-warmstone-700 transition-colors">
                        <X size={14} /> Clear all
                    </button>
                )}

                {/* Results count */}
                <div className="text-sm ml-auto text-warmstone-600">
                    <span className="font-semibold text-warmstone-800">{table.getRowModel().rows.length}</span>
                    <span className="ml-1">results</span>
                </div>
            </div>

            {/* Expandable filter panel */}
            {showFilters && filterableColumns.length > 0 && (
                <div className="bg-cream-200 border-b border-warmstone-200 p-4">
                    <div className="flex flex-wrap gap-6">
                        {filterableColumns.map(filter => (
                            <div key={filter.id} className="space-y-2">
                                <h4 className="text-xs font-semibold text-warmstone-500 uppercase tracking-wider flex items-center gap-1.5">
                                    <Filter size={10} /> {filter.title}
                                </h4>
                                <div className="flex flex-wrap gap-1.5 max-w-lg">
                                    {filter.options.slice(0, 15).map(option => (
                                        <button
                                            key={option}
                                            onClick={() => toggleFilter(filter.id, option)}
                                            className={clsx(
                                                "text-xs px-2.5 py-1 rounded-md transition-all duration-200 border",
                                                activeFilters[filter.id]?.includes(option)
                                                    ? "bg-warmstone-800 text-white border-warmstone-800"
                                                    : "bg-white text-warmstone-600 border-warmstone-200 hover:border-warmstone-300 shadow-sm"
                                            )}
                                        >
                                            {option}
                                        </button>
                                    ))}
                                    {filter.options.length > 15 && (
                                        <span className="text-xs text-warmstone-400 self-center">+{filter.options.length - 15} more</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Table */}
            <div className="flex-1 overflow-auto bg-cream">
                <table className="w-full">
                    <thead className="sticky top-0 bg-cream-50 z-10 border-b border-warmstone-200">
                        {table.getHeaderGroups().map(headerGroup => (
                            <tr key={headerGroup.id}>
                                {headerGroup.headers.map(header => (
                                    <th key={header.id} className="text-left text-xs font-semibold text-warmstone-500 uppercase tracking-wider px-4 py-3">
                                        {header.isPlaceholder ? null : (
                                            <div
                                                className={clsx(
                                                    "flex items-center gap-1.5",
                                                    header.column.getCanSort() && "cursor-pointer select-none hover:text-warmstone-700 transition-colors"
                                                )}
                                                onClick={header.column.getToggleSortingHandler()}
                                            >
                                                {flexRender(header.column.columnDef.header, header.getContext())}
                                                {header.column.getCanSort() && (
                                                    <span>
                                                        {{
                                                            asc: <ChevronUp size={14} className="text-warmstone-700" />,
                                                            desc: <ChevronDown size={14} className="text-warmstone-700" />,
                                                        }[header.column.getIsSorted() as string] ?? <ChevronsUpDown size={14} className="text-warmstone-400" />}
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </th>
                                ))}
                            </tr>
                        ))}
                    </thead>
                    <tbody>
                        {table.getRowModel().rows.length === 0 ? (
                            <tr>
                                <td colSpan={columns.length} className="text-center py-16 text-warmstone-500">
                                    <div className="flex flex-col items-center gap-2">
                                        <Search size={24} className="text-warmstone-400" />
                                        <span>No results found</span>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            table.getRowModel().rows.map((row) => (
                                <tr
                                    key={row.id}
                                    className="group border-b border-warmstone-100 hover:bg-cream-200 transition-colors"
                                >
                                    {row.getVisibleCells().map(cell => (
                                        <td key={cell.id} className="px-4 py-3 text-sm text-warmstone-700">
                                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                        </td>
                                    ))}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between p-4 border-t border-warmstone-200 bg-cream-50">
                {/* Left side: Total count and page size */}
                <div className="flex items-center gap-4 text-sm text-warmstone-600">
                    <span className="text-warmstone-500">
                        Total: <span className="font-semibold text-warmstone-800">{filteredData.length}</span> papers
                    </span>
                    <span className="text-warmstone-300">|</span>
                    <select
                        value={table.getState().pagination.pageSize}
                        onChange={e => {
                            table.setPageSize(Number(e.target.value))
                        }}
                        className="bg-white border border-warmstone-200 rounded-md px-2 py-1 text-warmstone-800 font-medium focus:outline-none focus:border-warmstone-300 cursor-pointer"
                    >
                        {[10, 20, 30, 40, 50, 100].map(pageSize => (
                            <option key={pageSize} value={pageSize}>
                                Show {pageSize}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Center: Page navigation */}
                <div className="flex items-center gap-2">
                    <button
                        className="p-1.5 rounded-lg border border-warmstone-200 text-warmstone-600 hover:bg-white hover:text-warmstone-800 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        onClick={() => table.setPageIndex(0)}
                        disabled={!table.getCanPreviousPage()}
                        title="First page"
                    >
                        <ChevronsUpDown size={16} className="rotate-90" />
                    </button>
                    <button
                        className="p-1.5 rounded-lg border border-warmstone-200 text-warmstone-600 hover:bg-white hover:text-warmstone-800 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        onClick={() => table.previousPage()}
                        disabled={!table.getCanPreviousPage()}
                        title="Previous page"
                    >
                        <ChevronLeft size={16} />
                    </button>

                    {/* Page number input */}
                    <div className="flex items-center gap-2 text-sm">
                        <span className="text-warmstone-500">Page</span>
                        <input
                            type="number"
                            min={1}
                            max={table.getPageCount()}
                            value={table.getState().pagination.pageIndex + 1}
                            onChange={e => {
                                const page = e.target.value ? Number(e.target.value) - 1 : 0;
                                table.setPageIndex(Math.min(Math.max(0, page), table.getPageCount() - 1));
                            }}
                            className="w-14 text-center bg-white border border-warmstone-200 rounded-md px-2 py-1 text-warmstone-800 font-medium focus:outline-none focus:border-warmstone-400"
                        />
                        <span className="text-warmstone-500">of <span className="font-medium text-warmstone-800">{table.getPageCount()}</span></span>
                    </div>

                    <button
                        className="p-1.5 rounded-lg border border-warmstone-200 text-warmstone-600 hover:bg-white hover:text-warmstone-800 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        onClick={() => table.nextPage()}
                        disabled={!table.getCanNextPage()}
                        title="Next page"
                    >
                        <ChevronRight size={16} />
                    </button>
                    <button
                        className="p-1.5 rounded-lg border border-warmstone-200 text-warmstone-600 hover:bg-white hover:text-warmstone-800 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                        disabled={!table.getCanNextPage()}
                        title="Last page"
                    >
                        <ChevronsUpDown size={16} className="rotate-90" />
                    </button>
                </div>

                {/* Right side: Showing range */}
                <div className="text-sm text-warmstone-500">
                    Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}-
                    {Math.min((table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize, filteredData.length)} of {filteredData.length}
                </div>
            </div>
        </div>

    );
}

export default DataTable;
