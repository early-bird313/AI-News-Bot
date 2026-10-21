import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import HeroTrending from './components/HeroTrending';
import NewsCard from './components/NewsCard';
import { ChevronLeft, ChevronRight, Sparkles, Flame, Archive, ArrowRight } from 'lucide-react';

export default function App() {
  const [allNews, setAllNews] = useState([]);
  const [categories, setCategories] = useState([]);
  const [status, setStatus] = useState(null);
  
  // Navigation & Filter State
  const [currentView, setCurrentView] = useState('trending'); // 'trending' | 'archive'
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('');
  
  // Pagination State for Archive View
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;
  
  const [isLoading, setIsLoading] = useState(true);
  const [isFetching, setIsFetching] = useState(false);
  const [isSendingDigest, setIsSendingDigest] = useState(false);
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const showToast = (msg, duration = 4000) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), duration);
  };

  // Fetch status
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Failed to load status:', err);
    }
  }, []);

  // Fetch categories
  const fetchCategories = useCallback(async () => {
    try {
      const res = await fetch('/api/categories');
      if (res.ok) {
        const data = await res.json();
        setCategories(data);
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }, []);

  // Fetch all news
  const fetchNews = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('limit', '100');

      const res = await fetch(`/api/news?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setAllNews(data);
      }
    } catch (err) {
      console.error('Failed to load news:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchCategories();
    fetchNews();
  }, [fetchStatus, fetchCategories, fetchNews]);

  // Action: Trigger background crawler
  const handleFetchNow = async () => {
    setIsFetching(true);
    try {
      const res = await fetch('/api/fetch-now', { method: 'POST' });
      if (res.ok) {
        showToast('🚀 নতুন খবরের অনুসন্ধান চলছে...');
        setTimeout(() => {
          fetchNews();
          fetchStatus();
          setIsFetching(false);
        }, 4000);
      } else {
        showToast('⚠️ ক্রলার চালু করা যায়নি।');
        setIsFetching(false);
      }
    } catch (err) {
      showToast('⚠️ সার্ভারে সংযোগ ব্যর্থ।');
      setIsFetching(false);
    }
  };

  // Action: Trigger manual digest to Telegram
  const handleSendDigest = async () => {
    setIsSendingDigest(true);
    try {
      const res = await fetch('/api/send-digest', { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        showToast(`✅ টেলিগ্রামে ডাইজেস্ট পাঠানো হয়েছে! (${data.items_sent}টি খবর)`);
        fetchStatus();
      } else {
        const err = data.detail || data.error || 'ডাইজেস্ট পাঠানো ব্যর্থ হয়েছে';
        showToast(`⚠️ ${err}`);
      }
    } catch (err) {
      showToast('⚠️ ব্যাকএন্ড সার্ভারে সংযোগ ব্যর্থ।');
    } finally {
      setIsSendingDigest(false);
    }
  };

  // Action: Trigger manual HTML digest to Email
  const handleSendEmailDigest = async () => {
    setIsSendingEmail(true);
    try {
      const res = await fetch('/api/send-email-digest', { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        const recInfo = data.recipient_count > 1 ? ` (${data.recipient_count} জনের ইনবক্সে)` : '';
        showToast(`✅ ইমেইলে সফলভাবে AI ডাইজেস্ট পাঠানো হয়েছে!${recInfo} (${data.items_sent}টি খবর)`);
        fetchStatus();
      } else {
        const err = data.detail || data.error || 'ইমেইল পাঠানো যায়নি। .env ফাইলে EMAIL_USERNAME ও EMAIL_PASSWORD চেক করুন।';
        showToast(`⚠️ ${err}`, 6000);
      }
    } catch (err) {
      showToast('⚠️ ব্যাকএন্ড সার্ভারে সংযোগ ব্যর্থ।');
    } finally {
      setIsSendingEmail(false);
    }
  };

  // Filter news based on search query and category
  const filteredNews = allNews.filter((item) => {
    const matchesSearch = searchQuery.trim()
      ? (item.title_bn && item.title_bn.toLowerCase().includes(searchQuery.toLowerCase())) ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (item.raw_summary && item.raw_summary.toLowerCase().includes(searchQuery.toLowerCase()))
      : true;

    const matchesCat = activeCategory ? item.category === activeCategory : true;

    return matchesSearch && matchesCat;
  });

  // Separate Trending vs Archive
  // Top 10 items for the curated Trending view
  const trendingPool = filteredNews.filter(n => n.is_trending || n.impact_score >= 7.5);
  const trendingSelected = trendingPool.length >= 6 ? trendingPool : filteredNews.slice(0, 11);
  
  const featuredItem = trendingSelected[0];
  const sideTrending = trendingSelected.slice(1, 5);
  const extraTrendingCards = trendingSelected.slice(5, 11);

  // Archive items (everything else, sorted chronologically)
  const heroIds = new Set([featuredItem?.id, ...sideTrending.map(s => s.id), ...extraTrendingCards.map(s => s.id)].filter(Boolean));
  const archivePool = filteredNews.filter(n => !heroIds.has(n.id));

  // Pagination for Archive
  const totalArchivePages = Math.max(1, Math.ceil(archivePool.length / itemsPerPage));
  const paginatedArchiveItems = archivePool.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const isSearchActive = Boolean(searchQuery.trim());

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col font-sans">
      {/* Light Mode Yahoo Tech Header */}
      <Header
        status={status}
        isFetching={isFetching}
        onFetchNow={handleFetchNow}
        isSendingDigest={isSendingDigest}
        onSendDigest={handleSendDigest}
        isSendingEmail={isSendingEmail}
        onSendEmailDigest={handleSendEmailDigest}
        searchQuery={searchQuery}
        onSearchChange={(q) => {
          setSearchQuery(q);
          setCurrentPage(1);
        }}
        currentView={currentView}
        onViewChange={(v) => {
          setCurrentView(v);
          setCurrentPage(1);
        }}
        message={toastMessage}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6">
        {isLoading ? (
          <div className="space-y-6">
            <div className="h-64 bg-slate-200/70 rounded-2xl animate-pulse"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-56 bg-slate-200/70 rounded-xl animate-pulse"></div>
              ))}
            </div>
          </div>
        ) : isSearchActive ? (
          /* Search Results View */
          <div>
            <div className="mb-6 pb-2 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900">
                সার্চের ফলাফল: "{searchQuery}" ({filteredNews.length}টি পাওয়া গেছে)
              </h2>
              <button
                onClick={() => setSearchQuery('')}
                className="text-xs font-semibold text-indigo-600 hover:underline"
              >
                রিসেট
              </button>
            </div>
            {filteredNews.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {filteredNews.map(item => (
                  <NewsCard key={item.id || item.url} item={item} />
                ))}
              </div>
            ) : (
              <div className="text-center py-16 bg-white border border-slate-200 rounded-2xl p-8">
                <Sparkles className="w-10 h-10 text-slate-400 mx-auto mb-3" />
                <h3 className="text-base font-bold text-slate-800">কোনো ফলাফল পাওয়া যায়নি</h3>
                <p className="text-xs text-slate-500 mt-1">অন্য কোনো শব্দ দিয়ে সার্চ করে দেখুন।</p>
              </div>
            )}
          </div>
        ) : currentView === 'trending' ? (
          /* PAGE 1: TODAY'S TRENDING ONLY (Strictly Curated Few News) */
          <div>
            {featuredItem && (
              <HeroTrending
                featuredItem={featuredItem}
                sideItems={sideTrending}
              />
            )}

            {/* Curated Trending Grid (Only ~6 cards) */}
            {extraTrendingCards.length > 0 && (
              <div className="mt-8">
                <div className="mb-4 pb-2 border-b border-slate-200 flex items-center justify-between">
                  <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                    <Flame className="w-4 h-4 text-rose-500" />
                    আরও গুরুত্বপূর্ণ এআই আপডেট
                  </h3>
                  <span className="text-xs text-slate-400 font-medium">আজকের নির্বাচিত সংবাদ</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {extraTrendingCards.map(item => (
                    <NewsCard key={item.id || item.url} item={item} />
                  ))}
                </div>
              </div>
            )}

            {/* Switch to Archive CTA */}
            <div className="mt-12 text-center p-6 bg-white border border-slate-200 rounded-2xl shadow-xs">
              <h4 className="text-sm font-bold text-slate-800 mb-1">
                আগের দিনের আরও খবর দেখতে চান?
              </h4>
              <p className="text-xs text-slate-500 mb-4">
                হোমপেজ পরিচ্ছন্ন রাখতে পূর্বের সকল খবর আলাদা পাতায় সংরক্ষিত রয়েছে।
              </p>
              <button
                onClick={() => {
                  setCurrentView('archive');
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-sm transition"
              >
                <span>পূর্বের খবর ও আর্কাইভ দেখুন</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          /* PAGE 2: ARCHIVE / PREVIOUS POSTS (Clean Pagination) */
          <div>
            {/* Archive Header & Category Bar */}
            <div className="mb-6 pb-3 border-b border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-slate-900 flex items-center gap-2">
                  <Archive className="w-5 h-5 text-indigo-600" />
                  পূর্বের খবর ও আর্কাইভ
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  আগের দিনগুলোর সকল এআই সংবাদের সংকলন (মোট {archivePool.length}টি পোস্ট)
                </p>
              </div>

              {/* Category Pills */}
              <div className="flex items-center gap-1 overflow-x-auto w-full sm:w-auto scrollbar-none">
                {categories.map((cat) => {
                  const isSelected = activeCategory === cat || (cat === 'All' && !activeCategory);
                  return (
                    <button
                      key={cat}
                      onClick={() => {
                        setActiveCategory(cat === 'All' ? '' : cat);
                        setCurrentPage(1);
                      }}
                      className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition border ${
                        isSelected
                          ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      {cat}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Paginated Cards (8 per page) */}
            {paginatedArchiveItems.length > 0 ? (
              <div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {paginatedArchiveItems.map(item => (
                    <NewsCard key={item.id || item.url} item={item} />
                  ))}
                </div>

                {/* Pagination Controls */}
                <div className="mt-10 flex items-center justify-center gap-3">
                  <button
                    onClick={() => {
                      setCurrentPage(p => Math.max(1, p - 1));
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    disabled={currentPage === 1}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span>আগের পৃষ্ঠা</span>
                  </button>

                  <span className="text-xs font-medium text-slate-500 px-2">
                    পৃষ্ঠা <strong className="text-slate-800">{currentPage}</strong> এর <strong className="text-slate-800">{totalArchivePages}</strong>
                  </span>

                  <button
                    onClick={() => {
                      setCurrentPage(p => Math.min(totalArchivePages, p + 1));
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    disabled={currentPage === totalArchivePages}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition"
                  >
                    <span>পরের পৃষ্ঠা</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-16 bg-white border border-slate-200 rounded-2xl p-8">
                <Sparkles className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <h3 className="text-sm font-bold text-slate-800">কোনো আর্কাইভ খবর নেই</h3>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Clean Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        AI News & Daily Digest &bull; 100% Free & Localhost &bull; প্রতিদিন সকাল ১০:০০ | দুপুর ২:০০ | রাত ৯:০০
      </footer>
    </div>
  );
}
