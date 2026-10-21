import React from 'react';
import { ExternalLink } from 'lucide-react';

export default function NewsCard({ item }) {
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

  const summaryBullets = item.ai_summary_bn
    ? item.ai_summary_bn
        .split('\n')
        .filter(line => line.trim().length > 0)
        .slice(0, 2)
    : [];

  const defaultImg = item.image_url || "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=600&q=80";

  return (
    <div className="group bg-white border border-slate-200 hover:border-slate-300 rounded-xl overflow-hidden hover:shadow-md transition duration-200 flex flex-col justify-between">
      <div>
        {/* Card Thumbnail Image */}
        <div className="h-44 w-full bg-slate-100 overflow-hidden relative">
          <img
            src={defaultImg}
            alt={item.title}
            className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
            onError={(e) => {
              e.target.src = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=600&q=80";
            }}
          />
          <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-white/90 backdrop-blur-xs text-slate-800 shadow-xs border border-slate-200">
            {item.category}
          </span>
        </div>

        {/* Card Content */}
        <div className="p-4">
          {/* Metadata */}
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span className="font-bold text-indigo-600">{item.source}</span>
            <span>{formatRelativeTime(item.published_at)}</span>
          </div>

          {/* Clickable Bengali Headline */}
          <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition leading-snug line-clamp-2 mb-1">
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline"
            >
              {item.title_bn || item.title}
            </a>
          </h3>

          {/* Original English Title */}
          <p className="text-[11px] text-slate-400 mb-2 line-clamp-1 italic">
            {item.title}
          </p>

          {/* Summary */}
          {summaryBullets.length > 0 ? (
            <div className="space-y-1 text-xs text-slate-600 leading-relaxed">
              {summaryBullets.map((bullet, idx) => (
                <p key={idx} className="line-clamp-2">
                  {bullet}
                </p>
              ))}
            </div>
          ) : item.raw_summary ? (
            <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
              {item.raw_summary}
            </p>
          ) : null}
        </div>
      </div>

      {/* Footer Link */}
      <div className="px-4 pb-3 pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
        <span className="text-[11px] text-slate-400">
          {item.is_trending ? '🔥 ট্রেন্ডিং' : 'নিয়মিত আপডেট'}
        </span>
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 font-bold transition"
        >
          <span>মূল খবর</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </div>
  );
}
