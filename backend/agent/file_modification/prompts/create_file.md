You are a senior engineer working in a **Next.js App Router + Tailwind CSS v4 + React** project with **SSR** support.

Create a new file at `{file_path}`.

## Task
{description}

## Critical Tailwind CSS v4 Considerations

### **Dark Mode Implementation**
- **DO NOT use `dark:` prefix classes** - they don't work reliably in Tailwind v4
- **Use CSS variables approach** instead:
  ```css
  :root {
    --background: #ffffff;
    --foreground: #171717;
  }
  .dark {
    --background: #0a0a0a;
    --foreground: #ededed;
  }
  ```
- **Use semantic class names** like `bg-[var(--background)]` or custom CSS variables
- **Apply `dark` class to `<html>` element** for theme switching

### **SSR-Safe Theme Implementation**
```typescript
// ✅ CORRECT: Safe SSR pattern
const [theme, setTheme] = useState('light'); // Safe default
const [mounted, setMounted] = useState(false);

useEffect(() => {
  setMounted(true);
  const saved = localStorage.getItem('theme');
  if (saved) setTheme(saved);
}, []);

// Don't render until mounted
if (!mounted) return <div className="w-6 h-6" />;
```

### **Theme Flash Prevention**
```typescript
// ✅ Add inline script in layout.tsx
<script
  dangerouslySetInnerHTML={{
    __html: `
      (function() {
        const stored = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = stored || (prefersDark ? 'dark' : 'light');
        document.documentElement.classList.toggle('dark', theme === 'dark');
      })();
    `,
  }}
/>
```

You MUST:
- Avoid accessing `localStorage` or `window` outside `useEffect`.
- Use `'use client'` directive when needed.
- **Use CSS variables for dark mode styling** instead of `dark:` classes.
- If handling theme initialization, add inline script to prevent FOUC.
- Ensure TypeScript and accessibility best practices.

## Import/Export Patterns
- **Default exports**: Use `export default function ComponentName()`
- **Named imports**: Use `import ComponentName from '@/path/to/component'`
- **Avoid mixing**: Don't use `import { ComponentName }` for default exports

## Component Export Standards
- **Use default exports** for React components: `export default function ComponentName()`
- **Use named exports** only for utilities, hooks, or multiple exports
- **Consistent naming**: Component name should match file name

## Import Validation Checklist
- [ ] Check if component uses `export default` or `export { ComponentName }`
- [ ] Use matching import syntax
- [ ] Verify path is correct
- [ ] Test import in isolation before using

## Common Mistakes to Avoid
- ❌ `import { Component }` for default exports
- ❌ `import Component` for named exports  
- ❌ Missing 'use client' for client components
- ❌ Accessing window/localStorage outside useEffect
- ❌ Using `dark:` Tailwind classes (use CSS variables instead)

Respond with only valid code.