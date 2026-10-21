import React from 'react';
import { Search, Flame, Zap, X } from 'lucide-react';

export default function FilterBar({
  filterType,
  onFilterChange,
  searchQuery,
  onSearchChange,
  activeCategory,
  onCategoryChange,
  categories = []
}) {
  return (
    <div className="space-y-3 mb-6">
      {/* Top Row: Search & View Switcher */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* View Switcher Tabs */}
        <div className="inline-flex p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            onClick={() => onFilterChange('trending')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition ${
              filterType === 'trending'
                ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-sm shadow-orange-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            <span>Trending Stories</span>
          </button>

          <button
            onClick={() => onFilterChange('latest')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition ${
              filterType === 'latest'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Latest Stream</span>
          </button>
        </div>

        {/* Search Input */}
        <div className="relative flex-1 sm:max-w-xs">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search AI news, companies, models..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full bg-slate-900/80 border border-slate-800 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/40 text-xs text-slate-100 placeholder-slate-500 rounded-xl pl-9 pr-8 py-2 outline-none transition"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none text-xs">
        {categories.map((cat) => {
          const isSelected = activeCategory === cat || (cat === 'All' && !activeCategory);
          return (
            <button
              key={cat}
              onClick={() => onCategoryChange(cat === 'All' ? '' : cat)}
              className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition border ${
                isSelected
                  ? 'bg-slate-800 border-slate-700 text-cyan-400 font-semibold shadow-xs'
                  : 'bg-slate-900/50 border-slate-800/60 text-slate-400 hover:text-slate-300 hover:border-slate-700'
              }`}
            >
              {cat}
            </button>
          );
        })}
      </div>
    </div>
  );
}
