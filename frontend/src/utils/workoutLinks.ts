/**
 * Utility functions for detecting dates in text and converting them to workout page links
 */

const monthNames = [
  'january', 'february', 'march', 'april', 'may', 'june',
  'july', 'august', 'september', 'october', 'november', 'december'
];

const monthAbbreviations = [
  'jan', 'feb', 'mar', 'apr', 'may', 'jun',
  'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
];

/**
 * Convert various date formats to YYYY-MM-DD
 */
function normalizeDate(year: string, month: string, day: string): { year: string; month: string; day: string } | null {
  // Ensure year is 4 digits
  let normalizedYear = year;
  if (year.length === 2) {
    // Assume 20xx for years 00-30, 19xx for years 31-99
    const yearNum = parseInt(year);
    normalizedYear = yearNum <= 30 ? `20${year}` : `19${year}`;
  }

  // Normalize month (could be number or name)
  let normalizedMonth = month;
  if (isNaN(parseInt(month))) {
    // Month is a name, convert to number
    const monthLower = month.toLowerCase();
    let monthIndex = monthNames.indexOf(monthLower);
    if (monthIndex === -1) {
      monthIndex = monthAbbreviations.indexOf(monthLower);
    }
    if (monthIndex === -1) return null;
    normalizedMonth = (monthIndex + 1).toString();
  }

  // Pad month and day with zeros
  normalizedMonth = normalizedMonth.padStart(2, '0');
  const normalizedDay = day.padStart(2, '0');

  // Validate the date
  const yearNum = parseInt(normalizedYear);
  const monthNum = parseInt(normalizedMonth);
  const dayNum = parseInt(normalizedDay);

  if (yearNum < 1900 || yearNum > 2100) return null;
  if (monthNum < 1 || monthNum > 12) return null;
  if (dayNum < 1 || dayNum > 31) return null;

  return {
    year: normalizedYear,
    month: normalizedMonth,
    day: normalizedDay
  };
}

/**
 * Replace dates in text with markdown links to workout pages
 */
export function replaceDatesWithLinks(content: string): string {
  // Pattern collection for various date formats
  const patterns = [
    // "Month DD, YYYY" or "Month DDth, YYYY"
    {
      regex: /\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4}|\d{2})\b/gi,
      replacer: (match: string, month: string, day: string, year: string) => {
        const normalized = normalizeDate(year, month, day);
        if (!normalized) return match;
        return `[${match}](#/workouts/${normalized.year}/${normalized.month}/${normalized.day})`;
      }
    },
    // "DD Month YYYY" or "DDth Month YYYY" (European style)
    {
      regex: /\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4}|\d{2})\b/gi,
      replacer: (match: string, day: string, month: string, year: string) => {
        const normalized = normalizeDate(year, month, day);
        if (!normalized) return match;
        return `[${match}](#/workouts/${normalized.year}/${normalized.month}/${normalized.day})`;
      }
    },
    // "MM/DD/YYYY" or "MM-DD-YYYY"
    {
      regex: /\b(\d{1,2})[/-](\d{1,2})[/-](\d{4}|\d{2})\b/g,
      replacer: (match: string, month: string, day: string, year: string) => {
        const normalized = normalizeDate(year, month, day);
        if (!normalized) return match;
        return `[${match}](#/workouts/${normalized.year}/${normalized.month}/${normalized.day})`;
      }
    },
    // "YYYY-MM-DD" (ISO format)
    {
      regex: /\b(\d{4})-(\d{2})-(\d{2})\b/g,
      replacer: (match: string, year: string, month: string, day: string) => {
        // Check if this is already part of a markdown link
        const beforeMatch = content.substring(0, content.indexOf(match));
        if (beforeMatch.endsWith('(') || beforeMatch.endsWith('#/workouts/')) {
          return match; // Already in a link
        }
        return `[${match}](#/workouts/${year}/${month}/${day})`;
      }
    }
  ];

  let processedContent = content;

  // Apply patterns in order (most specific first)
  for (const pattern of patterns) {
    processedContent = processedContent.replace(pattern.regex, pattern.replacer as any);
  }

  return processedContent;
}