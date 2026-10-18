const STORAGE_PREFIX = 'notlanken-notes:';

/** @typedef {'bug'|'onske'|'note'} NoteType */

/**
 * @typedef {Object} SessionNote
 * @property {string} id
 * @property {NoteType} type
 * @property {number} time seconds
 * @property {string} text
 * @property {number} created
 */

export function loadNotes(songFile) {
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + songFile);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveNotes(songFile, notes) {
  localStorage.setItem(STORAGE_PREFIX + songFile, JSON.stringify(notes));
}

export function noteTypeLabel(type) {
  if (type === 'bug') return 'BUG/FEL';
  if (type === 'onske') return 'ÖNSKEMÅL';
  return 'ANTECKNING';
}

export function noteTypeShort(type) {
  if (type === 'bug') return 'B';
  if (type === 'onske') return 'Ö';
  return 'N';
}
