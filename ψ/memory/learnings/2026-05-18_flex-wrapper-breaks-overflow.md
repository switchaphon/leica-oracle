# flex-1 min-h-0 chains break when a plain wrapper div is inserted

**Context**: OrderSummaryPane children rendered inside a `data-guide` wrapper div. The parent was `flex flex-col`, the child had `flex-1 min-h-0`, but the wrapper between them was a plain `<div>` with no flex properties.

**Symptom**: Right pane showed "รวม 4 รายการ" but only 3 items visible. 4th item existed in DOM but was clipped with no scrollbar hint.

**Root cause**: `maxHeight: calc(100% - 24px)` on a child of a non-flex wrapper resolves to `auto` height, clipping content. The flex chain was: `flex flex-col` parent → plain `<div data-guide>` → `flex-1 min-h-0` child. The plain div doesn't participate in flex layout, so `flex-1` on the grandchild has no effect.

**Fix**: Add `className='flex-1 min-h-0 flex flex-col'` to the wrapper div. Remove the `maxHeight` inline style (unnecessary once flex chain is intact).

**Rule**: Any div inserted into a flex overflow chain (parent has `flex flex-col`, child needs `flex-1 min-h-0`) must also carry those flex properties. This includes `data-guide`, `data-testid`, or any attribute-only wrapper divs.

**Applied to**: LabTestSelector, XRayStudySelector, UltrasoundStudySelector — all three had the same pattern.
