import React from 'react';
import { Search, RefreshCw, Send, Mail, Radio, X, Flame, Archive } from 'lucide-react';

export default function Header({
  status,
  isFetching,
  onFetchNow,
  isSendingDigest,
  onSendDigest,
  isSendingEmail,
  onSendEmailDigest,
  searchQuery,
  onSearchChange,
  currentView,
  onViewChange,
  message
}) {
  const formatTime = (isoString) => {
    if (!isoString) return '১০:০০ AM';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '১০:০০ AM';
    }
  };

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-40 shadow-xs">
      {/* Top Navbar */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Brand */}
        <div className="flex items-center justify-between w-full md:w-auto">
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => onViewChange('trending')}>
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm shadow-indigo-200">
              <Radio className="w-4 h-4" />
            </div>
            <div>
              <span className="text-lg font-black tracking-tight text-slate-900">AI News</span>
              <span className="text-xs font-bold text-indigo-600 ml-1 px-1.5 py-0.5 bg-indigo-50 rounded">Live</span>
            </div>
          </div>

          {/* Mobile Actions */}
          <div className="flex items-center gap-1.5 md:hidden">
            <button
              onClick={onFetchNow}
              disabled={isFetching}
              title="নতুন খবর খুঁজুন"
              className="p-1.5 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-indigo-600' : ''}`} />
            </button>
            <button
              onClick={onSendDigest}
              disabled={isSendingDigest}
              title="টেলিগ্রামে পাঠান"
              className="p-1.5 rounded-lg bg-indigo-600 text-white shadow-xs"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onSendEmailDigest}
              disabled={isSendingEmail}
              title="ইমেইলে পাঠান"
              className="p-1.5 rounded-lg bg-emerald-600 text-white shadow-xs"
            >
              <Mail className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Center: Search Box (Yahoo Tech clean style) */}
        <div className="relative w-full md:max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="এআই খবর, কোম্পানি বা মডেল সার্চ করুন..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full bg-slate-50 hover:bg-slate-100/80 focus:bg-white border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 text-xs text-slate-800 placeholder-slate-400 rounded-full pl-9 pr-8 py-2 outline-none transition duration-150"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Right Desktop: Digest info & Controls */}
        <div className="hidden md:flex items-center gap-3">
          <div className="text-right">
            <div className="text-[11px] text-slate-500 font-medium">পরবর্তী টেলিগ্রাম ডাইজেস্ট:</div>
            <div className="text-xs font-bold text-indigo-600">
              {formatTime(status?.next_digest_time)}
            </div>
          </div>

          <div className="h-6 w-px bg-slate-200"></div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={onFetchNow}
              disabled={isFetching}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition"
              title="নতুন খবর খুঁজুন"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-indigo-600' : ''}`} />
              <span className="hidden lg:inline">{isFetching ? 'খোঁজা হচ্ছে...' : 'Fetch'}</span>
            </button>

            <button
              onClick={onSendDigest}
              disabled={isSendingDigest}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition"
              title="এখনই টেলিগ্রামে টেস্ট পাঠান"
            >
              <Send className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">টেলিগ্রাম টেস্ট</span>
            </button>

            <button
              onClick={onSendEmailDigest}
              disabled={isSendingEmail}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition"
              title="এখনই ইমেইলে টেস্ট পাঠান"
            >
              <Mail className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">{isSendingEmail ? 'পাঠানো হচ্ছে...' : 'ইমেইল টেস্ট'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Sub-Navigation Bar: Page Switcher */}
      <div className="bg-slate-50/80 border-t border-slate-200/80">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between">
          <div className="flex items-center gap-1">
            <button
              onClick={() => onViewChange('trending')}
              className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-bold border-b-2 transition ${
                currentView === 'trending'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <Flame className="w-3.5 h-3.5 text-rose-500" />
              <span>আজকের শীর্ষ ট্রেন্ডিং</span>
            </button>

            <button
              onClick={() => onViewChange('archive')}
              className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-bold border-b-2 transition ${
                currentView === 'archive'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <Archive className="w-3.5 h-3.5 text-slate-500" />
              <span>পূর্বের খবর ও আর্কাইভ</span>
            </button>
          </div>

          <span className="text-[11px] text-slate-400 hidden sm:inline">
            প্রতিদিন সকাল ১০:০০ • দুপুর ২:০০ • রাত ৯:০০
          </span>
        </div>
      </div>

      {/* Toast message */}
      {message && (
        <div className="bg-indigo-50 border-t border-indigo-100 px-4 py-1.5 text-center text-xs font-medium text-indigo-700">
          {message}
        </div>
      )}
    </header>
  );
}
