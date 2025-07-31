# Fortnite.gg Search Notes

## 🔍 Search URL Format
https://fortnite.gg/maps?search={query}

## 🧠 Behavior
- Search is **client-side only** — no public search API
- `search=` filters map titles in JavaScript on the frontend
- We must **scrape the HTML** from the search page and parse DOM manually

## 🧱 HTML Structure (using Cheerio or Regex)
Based on actual Fortnite.gg HTML structure:

### Map Card Container
- Each map card: `.island-detail`
- Main container with all map information

### Map Information
- **Title**: `h1` (direct child of `.island-detail`)
- **Creator**: `a` with `href="/creator?name={creator}"` 
- **Description**: `.island-desc` (contains full description)
- **Tags**: `.island-tags .island-tag` (array of tags)
- **Code**: `.copy-code` button with `data-code="{map_code}"`

### Map Details Table
- **Created In**: Table row with "Created In:" label
- **Release Date**: Table row with "Release Date:" label  
- **Last Update**: Table row with "Last Update:" label
- **Max Players**: Table row with "Max Players:" label
- **Age Rating**: Table row with "Age Rating:" label
- **XP Status**: Table row with "XP Status:" label

## 🔁 Fetch Strategy
- Use `fetch('https://fortnite.gg/maps?search=BOX')`
- Use Cheerio to extract `.island-detail` elements
- Parse each card for title, code, description, creator, tags
- Build response as JSON: `[ { name, code, description, creator, tags, maxPlayers, releaseDate } ]`

## ⚠️ Rate Limits
- No official API key
- No aggressive throttling detected
- Avoid rapid repeated queries to prevent IP ban

## ✅ Fallback
- If search page returns zero `.island-detail`, return empty result
- If page fails, log error and suggest fallback to manual map code entry

## 🛠️ Example Output
```json
[
  {
    "name": "STEAL THE BRAINROT",
    "code": "3225-0366-8885",
    "description": "🆕 NEW LUCKY ROTS AND BRAINROT CHARACTERS! Steal Brainrots from other players!",
    "creator": "ferins",
    "tags": ["simulator", "just for fun", "casual", "tycoon"],
    "maxPlayers": 8,
    "releaseDate": "Jul 5, 2025",
    "lastUpdate": "Jul 30, 2025"
  }
]
```

## 🔧 Implementation Notes
- Use `cheerio` for HTML parsing in Node.js
- Extract map code from `.copy-code` button's `data-code` attribute
- Parse tags from `.island-tag` elements
- Extract creator from the creator link
- Implement debouncing (300ms delay) to avoid excessive requests
- Cache results for 5 minutes to reduce API calls
- Handle network errors gracefully with user-friendly messages
- Consider implementing a fallback to manual map code entry if search fails 