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
  const patterns = [
    // YYYY-MM-DD
    {
      regex: /(\d{4})-(\d{2})-(\d{2})/g,
      replacer: (match: string, year: string, month: string, day: string) => {
        return `[${match}](#/workouts/${year}/${month}/${day})`;
      }
    },
    // "Month Day, Year"
    {
      regex: /\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b/gi,
      replacer: (match: string, month: string, day: string, year: string) => {
        const normalized = normalizeDate(year, month, day);
        if (!normalized) return match;
        return `[${match}](#/workouts/${normalized.year}/${normalized.month}/${normalized.day})`;
      }
    },
    // YYMMDD
    {
      regex: /\b(\d{6})\b/g,
      replacer: (match: string, yymmdd: string) => {
        const year = yymmdd.slice(0, 2);
        const month = yymmdd.slice(2, 4);
        const day = yymmdd.slice(4, 6);
        const normalized = normalizeDate(year, month, day);
        if (!normalized) return match;
        return `[${match}](#/workouts/${normalized.year}/${normalized.month}/${normalized.day})`;
      }
    }
  ];

  let processedContent = content;

  for (const pattern of patterns) {
    processedContent = processedContent.replace(pattern.regex, pattern.replacer as any);
  }

  return processedContent;
}