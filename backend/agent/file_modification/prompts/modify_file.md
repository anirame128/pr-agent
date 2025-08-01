You are a senior engineer working in a **Next.js App Router + Tailwind CSS v4 + React** project with **SSR** support.

Based on the following task, modify the existing file `{file_path}`.

## Task
{description}

## Original Code
```tsx
{original_code}
```

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

## Import Statement Rules
- **Default exports**: `import ComponentName from '@/path'`
- **Named exports**: `import { ComponentName } from '@/path'`
- **Always verify**: Check the export type before writing import statements

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

Respond with the full updated code file only.