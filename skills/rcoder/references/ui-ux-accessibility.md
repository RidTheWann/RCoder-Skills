# UI/UX and accessibility expert module

## Activate when
User-facing flows, screens, navigation, components, interaction, responsive layout, or accessibility changes.

## Mental model
A UI is a stateful interaction system; task completion, comprehension, accessibility, and design-system consistency outrank decoration.

## Procedure
1. Identify user, job, entry point, success condition, and highest-cost failure.
2. Map flow and hierarchy; inspect current design tokens, components, typography, and navigation.
3. Cover initial, empty, loading, partial, success, validation/system error, disabled, and offline states where relevant.
4. Define supported breakpoints; prevent overflow, lost actions, and inaccessible reordering.
5. Check WCAG 2.2 AA: semantics, keyboard, visible focus, contrast, labels, instructions, error identification, target size, and reduced motion.
6. Reuse design-system components; do not replace established visual language with generic gradients/cards/blur.
7. Verify automation where available, keyboard-only use, zoom/reflow, and screenshots at representative sizes.

## Quality checklist
Primary action and feedback are clear; focus order matches reading order; inputs are labeled; contrast, target size, zoom, responsive states, accessible names, and reduced motion are checked.

## Anti-patterns
Generic redesign; automated scan as sole proof; placeholder-only labels; success-only desktop screenshots.

## Verification
Use accessibility tree, keyboard walkthrough, contrast measurement, representative viewport screenshots, and tool/version notes.

## Output format
User flow · state coverage · design-system fit · WCAG findings by severity · responsive evidence · gaps.
