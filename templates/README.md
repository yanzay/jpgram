# Japanese Grammar Anki Templates

Premium HTML+CSS card templates for the Japanese Grammar deck, optimized for desktop, AnkiMobile, AnkiDroid, and AnkiWeb.

## Overview

This directory contains templates for 4 note types, each with a pedagogically-designed hierarchy to maximize learning clarity:

- **Recognition**: JP → EN translation (identify meaning from kanji/kana)
- **Production**: EN → JP production (generate correct form from English prompt)
- **Cloze**: Fill-in-the-blank (context-dependent learning)
- **Contrast**: Choose correct form (A/B discrimination, common confusions)

Each note type has:
- `{NoteName}.front.html` — question side
- `{NoteName}.back.html` — answer side
- `{NoteName}.style.css` — type-specific styling
- `_common.css` — shared base styles, color palette, dark mode

## File Structure

```
templates/
├── _common.css
├── Recognition.front.html
├── Recognition.back.html
├── Recognition.style.css
├── Production.front.html
├── Production.back.html
├── Production.style.css
├── Cloze.front.html
├── Cloze.back.html
├── Cloze.style.css
├── Contrast.front.html
├── Contrast.back.html
├── Contrast.style.css
└── README.md (this file)
```

## Design Principles

### Pedagogical Hierarchy

Each card type follows a **signal-to-noise** hierarchy:

#### Recognition (JP → EN)
- **Front**: Large JP text, audio button (no answers)
- **Back**: Reading (furigana), EN gloss, Label, Formula, MainUse, QuickCue (accent box), Contrast (warning box), audio replay

#### Production (EN → JP)
- **Front**: Large EN prompt, small Target form hint, optional audio
- **Back**: Sample JP (big), Reading, Target form box, Why explanation, audio replay

#### Cloze (Fill-in-the-blank)
- **Front**: Cloze-marked text (`[...]`), subtle Hint below
- **Back**: Cloze text with answer revealed, Reading, Hint box, audio button

#### Contrast (A/B choice)
- **Front**: JP with blank (`___`), Option A and B as side-by-side boxes (visual only), audio button
- **Back**: Both options displayed, correct answer highlighted (green), Why reasoning, Tip warning, audio replay

### Typography

- **Japanese text**: `'Noto Sans JP', 'Hiragino Sans', 'Yu Gothic', sans-serif`
  - Main body JP: **2.4em** (large for easy reading)
  - Metadata JP: **0.9em**
  - Ruby (furigana): **0.55em** relative to base, 0.8 opacity

- **English text**: `system-ui, -apple-system, 'Segoe UI', sans-serif`
  - Main body EN: **1.1em–1.4em**
  - Metadata: **0.9em**

- **Code/Formula**: `'Courier New', 'Monaco', monospace`
  - Used for grammar patterns, formula syntax

### Color Palette

#### Light Mode (Default)
- **Background**: `white`
- **Foreground**: `#222`
- **Accent** (Info boxes, Quick Cue): `#4f46e5` (indigo)
- **Warning** (Contrast boxes, Tips): `#d97706` (amber)
- **Success** (Correct answer highlight): `#059669` (emerald)
- **Muted** (Hints, metadata): `#6b7280` (gray)

#### Dark Mode (`@media (prefers-color-scheme: dark)`)
Automatically applies when system preference is dark:
- **Background**: `#1a1a1a`
- **Foreground**: `#e8e8e8`
- **Accent**: `#818cf8` (lighter indigo)
- **Warning**: `#fbbf24` (lighter amber)
- **Success**: `#34d399` (lighter emerald)
- **Muted**: `#9ca3af` (lighter gray)

#### Anki's `.night_mode` Class
Anki adds a `.night_mode` class to `<body>` when in dark mode. The templates override all CSS variables accordingly.

### Component Styles

#### Info Box
```html
<div class="info-box">
  <div class="metadata-row">
    <span class="label">Label:</span>
    <span>Value</span>
  </div>
</div>
```
Used for: Label, Formula, MainUse, Why, Target explanations
- Background: soft accent color
- Left border: solid accent color
- Padding: 0.75em 1em
- Box shadow: subtle depth on all platforms

#### Warning Box
```html
<div class="warning-box">
  <strong>⚠ Title:</strong> Content
</div>
```
Used for: Contrast (common confusion), Tip (gotchas)
- Background: soft warning color (amber)
- Left border: solid warning color
- Same padding & shadow as info-box

#### Success Box
```html
<div class="success-box">
  ✓ Correct Answer
</div>
```
Used for: Highlighting correct choice in Contrast cards
- Background: soft success color (emerald)
- Left border: solid success color

#### Quick Cue Box
```html
<div class="quick-cue">
  💡 <strong>Quick Cue:</strong> Mnemonic or recall aid
</div>
```
Used for: Quick mnemonic in Recognition cards
- Gradient background (accent → transparent)
- Border: accent color
- Font style: italic

#### Audio Button
```html
<button class="audio-button" onclick="...">
  {{Audio}}
</button>
```
- Custom ▶ play icon (CSS `::before`)
- Background: accent color
- Hover effect: lift + shadow
- Min height: **44px** (mobile touch target)
- Icon color: white

### Mobile Responsiveness

All templates are optimized for **360px–720px viewports**:

- **Max width**: 720px on desktop, full-width on mobile
- **Padding**: 1.5em on desktop, 1em on mobile
- **Font sizes**: Scale down on mobile (< 480px)
- **Touch targets**: All buttons ≥ 44px height (WCAG AA)
- **Flex layout**: Option boxes (Contrast) stack vertically on mobile

Media query breakpoint: `@media (max-width: 480px)`

## Features

### Ruby (Furigana) Support

Reading fields support HTML `<ruby>` tags:

```html
<ruby>感<rt>かん</rt></ruby><ruby>情<rt>じょう</rt></ruby>
```

CSS automatically styles:
- `rt` font-size: 0.55em relative to base
- `rt` opacity: 0.8 for subtle appearance
- Proper alignment with `ruby-align: space-around`

### Tags Display

Every **back card** automatically shows a tags row at the bottom:

```html
<div class="tags">
  {{Tags}}
</div>
```

- Small gray text
- Hashtag prefix (`#`) auto-generated by CSS
- Bordered top separator
- Wraps on mobile

### Pitch Accent Enhancement (Optional)

The Recognition.back.html includes a comment describing how to add **pitch accent overlays** via JavaScript:

```html
<!-- Example hook for pitch accent visualization -->
<span class="pitch" data-word="ばし">ばし</span>
```

CSS provides two accent classes:
- `.pitch-accent-high` — highlights high-pitch accent pattern
- `.pitch-accent-low` — highlights low-pitch accent pattern

To enable pitch overlay:

1. **Install a third-party add-on** (e.g., via AnkiWeb community) or write a custom script
2. **Hook into `ankiConnected` events** to inject JS that:
   - Fetches pitch data from an API (e.g., NHK Accent Database)
   - Wraps Reading words in `<span class="pitch" data-word="word">word</span>`
   - Adds `.pitch-accent-high` or `.pitch-accent-low` classes
3. **Example snippet** (would be in a separate JS file):

```javascript
// Pseudo-code: inject via AnkiConnect or browser console
document.querySelectorAll('.pitch').forEach(el => {
  const word = el.dataset.word;
  const accentInfo = await fetchPitchData(word);
  if (accentInfo.isHigh) {
    el.classList.add('pitch-accent-high');
  }
});
```

### Dark Mode Behavior

Dark mode is automatically applied when:
1. System preference is set to dark mode (`@media (prefers-color-scheme: dark)`)
2. Anki is running in dark mode (Anki adds `.night_mode` to `<body>`)

**All colors, backgrounds, and shadows adapt smoothly** to maintain readability and reduce eye strain. No manual toggling required.

## Print Styles

When cards are printed:
- Audio buttons are hidden (`display: none`)
- Cards have a visible border and padding for clear separation
- Backgrounds are preserved (enable "background graphics" in printer dialog)

## Deployment

1. **Copy all files from `templates/`** into your Anki add-on or collection:
   - On **desktop Anki**: `~/Library/Application Support/Anki2/addons21/{addon_id}/templates/`
   - On **AnkiWeb**: Upload via web interface
   - On **AnkiMobile/AnkiDroid**: Sync from desktop or AnkiWeb

2. **Link templates in Anki**:
   - Open your deck/note type
   - Go to **Tools → Manage Note Types**
   - For each note type, set Front/Back/CSS to the corresponding HTML/CSS files
   - Ensure field order matches `NOTE_TYPES` in `build_anki_package.py`

3. **Verify on all platforms**:
   - Desktop Anki (Linux/macOS/Windows)
   - AnkiMobile (iOS)
   - AnkiDroid (Android)
   - AnkiWeb (browser)

## Accessibility

- **Color contrast**: All text meets WCAG AA standards (4.5:1 for normal text)
- **Touch targets**: All interactive elements ≥ 44px (WCAG AA Mobile)
- **Font sizes**: Minimum 0.9em on desktop, scale on mobile
- **Semantic HTML**: Proper use of `<ruby>`, `<button>`, semantic `<div>` classes
- **Dark mode**: Full support with high contrast

## Browser & Platform Compatibility

- **Anki Desktop** (2.1.50+): Full support
- **AnkiMobile** (iOS 13+): Full support (requires AnkiMobile 2.0.70+)
- **AnkiDroid** (Android 5.0+): Full support
- **AnkiWeb**: Full support (browser-based)

Note: Some older Anki versions may not support CSS custom properties (`--color-name`). If needed, define colors inline in each template.

## Customization

### Change Accent Color

Edit `_common.css`:

```css
:root {
  --accent: #4f46e5;        /* Change this */
  --accent-light: #eef2ff;  /* And this */
}

@media (prefers-color-scheme: dark) {
  :root {
    --accent: #818cf8;       /* Dark mode version */
  }
}
```

### Adjust Font Size

For larger/smaller text, modify the `.jp-large`, `.en-large`, `.reading-display` sizes in `_common.css`:

```css
.jp-large {
  font-size: 2.4em;  /* Increase to 2.8em for very large, or 2.0em for smaller */
}
```

### Modify Box Styling

Edit the `.info-box`, `.warning-box`, `.quick-cue` classes in `_common.css` or type-specific CSS files.

## Troubleshooting

### Audio Button Not Working
- Ensure the `Audio` field is populated with a valid audio file reference
- Check that Anki can find the audio file in the media folder
- On mobile, confirm that the device has speakers/headphones enabled

### Ruby/Furigana Not Displaying
- Verify the Reading field contains proper HTML `<ruby>` tags
- Check that the font-size for `rt` is visible (try increasing from 0.55em)
- Ensure Anki's font stack includes Japanese font support

### Dark Mode Colors Wrong
- Clear Anki's cache: **Tools → Check Database**
- Re-import the templates
- On AnkiMobile/AnkiDroid, close and reopen the app

### Mobile Layout Broken
- Check that max-width and padding in `.card` are set in `_common.css`
- Verify media query breakpoints match your device width
- Test on multiple device sizes (360px, 480px, 720px)

## License

These templates are part of the Japanese Grammar Anki deck. See the root `LICENSE.md` for terms.

## Contributing

To improve these templates:
1. Test changes on desktop, AnkiMobile, AnkiDroid, and AnkiWeb
2. Maintain pedagogical hierarchy (front/back signal-to-noise)
3. Keep dark mode support working
4. Verify mobile responsiveness (< 480px viewport)
5. Submit pull request with test results

---

**Version**: 0.1.0  
**Last Updated**: 2026-05-16  
**Maintainer**: jpgram project
