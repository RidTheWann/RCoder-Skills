# UI/UX and accessibility expert module

## Activate when
User-facing flows, screens, navigation, components, interaction, responsive layout, or accessibility changes. Use frontend-engineering for implementation structure and web-platform-engineering for browser runtime behavior.

## Mission and expertise
Own task completion, comprehension, accessibility, and design-system consistency. Verify keyboard, screen-reader, zoom, and responsive behavior with evidence rather than automated scans alone.

## Mental model
A UI is a stateful interaction system; task completion, comprehension, accessibility, and design-system consistency outrank decoration. Accessibility is a functional requirement, not a final polish step.

## Prerequisites and reconnaissance
1. Identify user, job, entry point, success condition, and highest-cost failure.
2. Map the flow and hierarchy; inspect current design tokens, components, typography, and navigation.
3. Determine supported breakpoints, input methods, and assistive-technology expectations.
4. Check whether an accessibility audit or design-system specification already exists.

## Procedure
1. Identify user, job, entry point, success condition, and highest-cost failure.
2. Map flow and hierarchy; inspect current design tokens, components, typography, and navigation.
3. Cover initial, empty, loading, partial, success, validation/system error, disabled, and offline states where relevant.
4. Define supported breakpoints; prevent overflow, lost actions, and inaccessible reordering.
5. Check WCAG 2.2 AA: semantics, keyboard, visible focus, contrast, labels, instructions, error identification, target size, and reduced motion.
6. Reuse design-system components; do not replace established visual language with generic gradients/cards/blur.
7. Verify automation where available, keyboard-only use, zoom/reflow, and screenshots at representative sizes.

## Decision tree
- Action only reachable by pointer → add a keyboard path and visible focus.
- Error shown only visually → associate it programmatically with the input and announce it.
- Content breaks at narrow widths → fix layout and reflow; do not hide primary actions.
- Custom control needed → implement full keyboard and accessibility-tree semantics or use a native element.
- Automated scan is clean → still perform a manual keyboard and screen-reader walkthrough.
- Motion causes discomfort → respect reduced-motion preferences.
- Design-system component exists → use it; deviations require an explicit accessibility review.

## Tool strategy
Use accessibility-tree inspection, keyboard walkthroughs, contrast measurement, representative viewport screenshots, and automated checks where available. Verify tool versions and browser engines. Use synthetic content that reflects real data shapes without personal data.

## Advanced techniques
- **State matrix:** enumerate initial, loading, empty, partial, error, success, disabled, and offline states per screen.
- **Focus-order audit:** verify focus follows reading order and returns to a sensible place after dialogs close.
- **Error recovery:** give specific, programmatic error messages with correction guidance.
- **Reflow testing:** verify at 200% zoom and narrow widths that nothing is lost or overlaps.
- **Task-based validation:** measure whether a user can complete the primary job with keyboard only.

## Failure modes
- **Generic redesign** → lost consistency → reuse design-system components.
- **Automated scan as sole proof** → missed barriers → add manual keyboard and screen-reader checks.
- **Placeholder-only labels** → unusable forms → provide persistent labels and instructions.
- **Success-only desktop screenshots** → hidden failures → test all states and breakpoints.
- **Invisible focus** → keyboard users lost → keep a visible focus indicator.

## Quality checklist
Primary action and feedback are clear; focus order matches reading order; inputs are labeled; contrast, target size, zoom, responsive states, accessible names, and reduced motion are checked.

## Anti-patterns
Clickable divs without roles or keyboard handlers; color-only status; auto-playing motion without a control; truncating labels at narrow widths; claiming WCAG compliance from a single automated scan.

## Verification
Use accessibility tree, keyboard walkthrough, contrast measurement, representative viewport screenshots, and tool/version notes. Record what was tested and mark untested assistive technologies NOT VERIFIED.

## Output format
User flow · state coverage · design-system fit · WCAG findings by severity · responsive evidence · gaps.
