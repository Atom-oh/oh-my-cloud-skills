import React from 'react';

const paths: Record<string, React.ReactNode> = {
  slides: <><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21l4-4 4 4M8 8h8M8 12h5"/></>,
  diagram: <><rect x="9" y="3" width="6" height="5" rx="1"/><rect x="2" y="16" width="6" height="5" rx="1"/><rect x="16" y="16" width="6" height="5" rx="1"/><path d="M12 8v4H5v4m7-4h7v4"/></>,
  review: <><path d="M13 4H5a2 2 0 00-2 2v13a2 2 0 002 2h13a2 2 0 002-2v-8M8 9h3M8 14h7"/><path d="M15 5l2 2 4-4"/></>,
  project: <><path d="M3 7V5a2 2 0 012-2h5l2 3h7a2 2 0 012 2v11a2 2 0 01-2 2H5a2 2 0 01-2-2V7h18M8 12h8m-8 4h5"/></>,
  cloud: <><path d="M7 17H6a4 4 0 01-1-7.9 7 7 0 0113.4-1.6A4.8 4.8 0 0120 17h-3M9 14l3-3 3 3m-3-3v10"/></>,
  branches: <><circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M6 7v10M18 7v2a5 5 0 01-5 5H6"/></>,
  book: <><path d="M12 5C8 2 4 3 2 4v15c4-2 7-1 10 1 3-2 6-3 10-1V4c-2-1-6-2-10 1v15M6 8h2m-2 4h2m8-4h2m-2 4h2"/></>,
  layout: <><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 9v12"/></>,
  edit: <><path d="M15 4l5 5M5 14L16 3a2 2 0 013 3L8 17l-5 1 2-4M4 22h16"/></>,
  search: <><circle cx="10.5" cy="10.5" r="6.5"/><path d="M16 16l5 5"/></>,
  arrow: <path d="M5 12h14m-5-5l5 5-5 5"/>,
  back: <path d="M19 12H5m5-5l-5 5 5 5"/>,
  play: <path d="M8 5l11 7-11 7V5z"/>,
  check: <path d="M5 12l4 4L19 6"/>,
  close: <path d="M6 6l12 12M6 18L18 6"/>,
  copy: <><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V5a2 2 0 00-2-2H5a2 2 0 00-2 2v9a2 2 0 002 2h3"/></>,
  terminal: <><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 9l3 3-3 3m6 0h5"/></>,
  spark: <><path d="M12 3l2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3z"/></>,
};
export default function Icon({name, size = 20}: {name: string; size?: number}) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.book}</svg>;
}
