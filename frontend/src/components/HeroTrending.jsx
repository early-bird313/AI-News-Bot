import React from 'react';
import { Flame, ExternalLink, Sparkles, Clock } from 'lucide-react';

export default function HeroTrending({ featuredItem, sideItems = [] }) {
  if (!featuredItem) return null;

  const formatRelativeTime = (isoString) => {
    if (!isoString) return '';
    try {
      const now = new Date();
      const past = new Date(isoString);
      const diffMinutes = Math.floor((now - past) / 60000);
      if (diffMinutes < 60) return `${diffMinutes} মিনিট আগে`;
      const diffHours = Math.floor(diffMinutes / 60);
      if (diffHours < 24) return `${diffHours} ঘণ্টা আগে`;
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays} দিন আগে`;
    } catch {
      return '';
    }
  };

  const defaultImg =
    featuredItem.image_url ||
    'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80';

  const summaryBullets = featuredItem.ai_summary_bn
    ? featuredItem.ai_summary_bn
        .split('\n')
        .filter((line) => line.trim().length > 0)
        .slice(0, 3)
    : [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
      {/* Main Featured Story (Left / 7 cols) */}
      <div className="lg:col-span-7 bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs hover:shadow-md transition duration-300 flex flex-col justify-between group">
        <div>
          {/* Main Hero Image */}
          <div className="h-64 sm:h-72 w-full bg-slate-100 overflow-hidden relative">
            <img
              src={defaultImg}
              alt={featuredItem.title}
              className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
              onError={(e) => {
                e.target.src =
                  'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80';
              }}
            />
            <div className="absolute top-3 left-3 flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-white/95 backdrop-blur-xs text-slate-800 shadow-xs border border-slate-200">
                {featuredItem.category || 'AI News'}
              </span>
              <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-500 text-white shadow-xs flex items-center gap-1">
                <Flame className="w-3.5 h-3.5 fill-current" />
                শীর্ষ ট্রেন্ডিং
              </span>
            </div>
            {featuredItem.impact_score && (
              <div className="absolute top-3 right-3 px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-900/85 backdrop-blur-xs text-amber-400 shadow-xs border border-slate-700 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" />
                <span>স্কোর: {featuredItem.impact_score}/10</span>
              </div>
            )}
          </div>

          {/* Hero Content */}
          <div className="p-5 sm:p-6">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-bold text-indigo-600 text-sm">{featuredItem.source}</span>
              <span className="flex items-center gap-1 text-slate-500">
                <Clock className="w-3.5 h-3.5" />
                {formatRelativeTime(featuredItem.published_at)}
              </span>
            </div>

            <h2 className="text-xl sm:text-2xl font-black text-slate-900 group-hover:text-indigo-600 transition leading-snug mb-2">
              <a
                href={featuredItem.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline"
              >
                {featuredItem.title_bn || featuredItem.title}
              </a>
            </h2>

            <p className="text-xs text-slate-400 mb-4 italic line-clamp-1">
              {featuredItem.title}
            </p>

            {summaryBullets.length > 0 ? (
              <div className="space-y-2 bg-slate-50 p-4 rounded-xl border border-slate-100 text-xs sm:text-sm text-slate-700 leading-relaxed">
                {summaryBullets.map((bullet, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-2 shrink-0"></span>
                    <p>{bullet}</p>
                  </div>
                ))}
              </div>
            ) : featuredItem.raw_summary ? (
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
                {featuredItem.raw_summary}
              </p>
            ) : null}
          </div>
        </div>

        {/* Hero Footer */}
        <div className="px-5 sm:px-6 py-3 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500">
            গুগল জেমিনাই এআই দ্বারা বিশ্লেষিত
          </span>
          <a
            href={featuredItem.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-bold text-indigo-600 hover:text-indigo-800 transition"
          >
            <span>মূল উৎস পড়ুন</span>
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* Side Trending Highlights (Right / 5 cols) */}
      <div className="lg:col-span-5 flex flex-col justify-between gap-3">
        <div className="space-y-3">
          <div className="flex items-center justify-between pb-1 border-b border-slate-200">
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
              <Flame className="w-4 h-4 text-orange-500" />
              ট্রেন্ডিং বাছাই সংবাদ
            </h3>
            <span className="text-[11px] text-slate-400">সর্বশেষ আপডেট</span>
          </div>

          {sideItems.map((item) => {
            const sideImg =
              item.image_url ||
              'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=400&q=80';
            return (
              <div
                key={item.id || item.url}
                className="group bg-white border border-slate-200 hover:border-indigo-300 rounded-xl p-3 shadow-xs hover:shadow-sm transition flex gap-3 items-center"
              >
                <div className="w-20 h-20 rounded-lg bg-slate-100 overflow-hidden shrink-0 relative">
                  <img
                    src={sideImg}
                    alt={item.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                    onError={(e) => {
                      e.target.src =
                        'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=400&q=80';
                    }}
                  />
                  {item.impact_score && (
                    <span className="absolute bottom-1 right-1 px-1 rounded text-[9px] font-bold bg-slate-900/80 text-amber-300">
                      ★ {item.impact_score}
                    </span>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                    <span className="font-bold text-indigo-600 truncate max-w-[120px]">
                      {item.source}
                    </span>
                    <span>{formatRelativeTime(item.published_at)}</span>
                  </div>

                  <h4 className="text-xs sm:text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition leading-snug line-clamp-2 mb-1">
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline"
                    >
                      {item.title_bn || item.title}
                    </a>
                  </h4>

                  <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600">
                    {item.category || 'AI'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
