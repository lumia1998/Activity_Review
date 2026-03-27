const APPEARANCE_MAP = {
  idle: {
    fur: 'from-stone-50 via-white to-stone-200 dark:from-slate-100 dark:via-slate-50 dark:to-slate-200',
    belly: 'bg-white/88 dark:bg-white/92',
    innerEar: 'bg-rose-200/85 dark:bg-rose-200/90',
    accent: 'bg-slate-500',
    accentSoft: 'bg-slate-100/90 dark:bg-slate-200/95',
    desk: 'from-slate-300/90 via-slate-200/95 to-white dark:from-slate-700/90 dark:via-slate-600/95 dark:to-slate-500/95',
    glow: 'rgba(148,163,184,0.28)',
    badge: 'text-slate-700 dark:text-slate-200',
    outline: 'rgba(148,163,184,0.22)',
  },
  working: {
    fur: 'from-stone-50 via-white to-stone-200 dark:from-slate-100 dark:via-slate-50 dark:to-slate-200',
    belly: 'bg-white/88 dark:bg-white/92',
    innerEar: 'bg-rose-200/85 dark:bg-rose-200/90',
    accent: 'bg-sky-500',
    accentSoft: 'bg-sky-100/90 dark:bg-sky-200/95',
    desk: 'from-sky-300/85 via-cyan-200/90 to-white dark:from-sky-700/90 dark:via-sky-600/95 dark:to-slate-500/95',
    glow: 'rgba(14,165,233,0.28)',
    badge: 'text-sky-700 dark:text-sky-300',
    outline: 'rgba(14,165,233,0.22)',
  },
  reading: {
    fur: 'from-stone-50 via-white to-stone-200 dark:from-slate-100 dark:via-slate-50 dark:to-slate-200',
    belly: 'bg-white/88 dark:bg-white/92',
    innerEar: 'bg-rose-200/85 dark:bg-rose-200/90',
    accent: 'bg-amber-500',
    accentSoft: 'bg-amber-100/90 dark:bg-amber-200/95',
    desk: 'from-amber-300/85 via-amber-200/90 to-white dark:from-amber-700/90 dark:via-amber-600/95 dark:to-slate-500/95',
    glow: 'rgba(245,158,11,0.26)',
    badge: 'text-amber-700 dark:text-amber-300',
    outline: 'rgba(245,158,11,0.2)',
  },
  thinking: {
    fur: 'from-stone-50 via-white to-stone-200 dark:from-slate-100 dark:via-slate-50 dark:to-slate-200',
    belly: 'bg-white/88 dark:bg-white/92',
    innerEar: 'bg-rose-200/85 dark:bg-rose-200/90',
    accent: 'bg-emerald-500',
    accentSoft: 'bg-emerald-100/90 dark:bg-emerald-200/95',
    desk: 'from-emerald-300/85 via-lime-200/90 to-white dark:from-emerald-700/90 dark:via-emerald-600/95 dark:to-slate-500/95',
    glow: 'rgba(16,185,129,0.26)',
    badge: 'text-emerald-700 dark:text-emerald-300',
    outline: 'rgba(16,185,129,0.22)',
  },
};

export function getAvatarAppearance(mode) {
  return APPEARANCE_MAP[mode] || APPEARANCE_MAP.idle;
}
