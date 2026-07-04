---
name: React hooks must precede early returns
description: All useState/useEffect calls must come before any conditional return — hook order must be identical across renders
type: learning
source: rrr — pops-clinic-oracle diagnostic drawer session
---

Placed `useState` and `useEffect` after `if (!mounted) return null` in PrototypeGuide.tsx. Caused "Rendered more hooks than during the previous render" crash — first render had 3 hooks (before early return), second render had 5 (after mount). React requires identical hook call order every render.

**Fix**: Move all hooks to the top of the component, before any early returns. Use the state values conditionally in the render output, not the hook calls themselves.

**Pattern**:
```tsx
// WRONG
const [mounted, setMounted] = useState(false);
if (!mounted) return null;
const [extra, setExtra] = useState(false); // hook after return = crash

// RIGHT
const [mounted, setMounted] = useState(false);
const [extra, setExtra] = useState(false); // all hooks first
if (!mounted) return null;
```
