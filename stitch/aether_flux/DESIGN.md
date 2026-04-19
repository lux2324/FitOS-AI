# Design System Specification: The Kinetic HUD

## 1. Overview & Creative North Star
**Creative North Star: "The Tactical Biometric Interface"**

This design system moves away from the "neon-clutter" of typical cyberpunk tropes, leaning instead into a high-end, tactical HUD (Heads-Up Display) aesthetic. It is designed to feel like an advanced biometric OS—precise, cold, and performance-oriented. 

To achieve a signature editorial feel, we break the "template" look through **Intentional Asymmetry**. Dashboards should not be perfectly balanced; use oversized biometric data points offset against condensed, technical labels. We utilize **Tonal Depth** rather than structural lines to create a layout that feels like a holographic projection—layered, luminous, and deep.

---

## 2. Colors: Luminance & Atmosphere
The palette is built on a foundation of "void" space, punctuated by high-chroma light sources.

### Core Tones
*   **Surface Lowest (#0a0e1a):** The "Void." Used for the primary background. Apply a subtle 1px grid overlay or a horizontal scan-line texture at 3% opacity to ground the digital space.
*   **Primary (#71ffe8) / Container (#00e5cc):** The "Active Pulse." Used for critical biometric data, primary progress rings, and high-priority actions.
*   **Secondary (#d3fbff) / Container (#00eefc):** The "Glow." Reserved for hover states and secondary highlights.

### The "No-Line" Rule
Prohibit 1px solid borders for sectioning. In this system, boundaries are defined by:
1.  **Background Shifts:** Transitioning from `surface_container_lowest` to `surface_container_low`.
2.  **Luminous Fringes:** Instead of a border, use a 1px inner glow or a subtle "Ghost Border" using `outline_variant` at 15% opacity.

### The "Glass & Gradient" Rule
To escape a flat, static feel, all primary CTAs must use a linear gradient (Primary to Primary-Container) at a 135-degree angle. Floating modules should utilize `backdrop-filter: blur(12px)` combined with a semi-transparent `surface_container` color to simulate high-tech glass.

---

## 3. Typography: Technical Authority
We pair high-impact, condensed headings with hyper-legible body text to mimic military-grade hardware interfaces.

*   **Display & Headlines (Space Grotesk):** Use for "Big Data"—pulse rates, miles ran, or daily goals. Set to uppercase with -2% letter spacing to enhance the "tech" feel.
*   **Titles & Body (Inter):** The workhorse. Inter provides a clean, neutral balance to the aggressive headlines.
*   **Labels (Inter):** Used for micro-data (e.g., "BPM," "KCAL"). Always uppercase with +10% letter spacing for a tactical, "meter-readout" appearance.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are forbidden. Elevation is achieved through light emission and atmospheric stacking.

*   **The Layering Principle:** 
    *   **Level 0:** `surface_container_lowest` (Background with grid texture).
    *   **Level 1:** `surface_container` (Main content cards).
    *   **Level 2:** `surface_bright` (Floating action buttons or active modal states).
*   **Ambient Shadows:** When a card needs to "float," use an **Outer Glow** instead of a shadow. Apply a blur of 24px using the `primary` color at 8% opacity. This mimics light reflecting off a glass surface.
*   **Glassmorphism:** For overlays (Modals/Pop-overs), use `surface_container_high` at 70% opacity with a 20px background blur. This keeps the user grounded in their fitness data while focusing on the task.

---

## 5. Components

### Buttons: High-Energy Triggers
*   **Primary:** Gradient fill (`primary` to `primary_container`). Border-radius: `md`. Box-shadow: 0 0 15px `primary` at 30% opacity. Text must be `on_primary`, bold uppercase.
*   **Secondary (Outline):** 1px "Ghost Border" using `primary`. On hover, the border opacity increases to 100% with a subtle inner glow.
*   **Tertiary:** No background. Text color `primary`. 

### Cards: The HUD Modules
*   **Construction:** Use `surface_container` with `xl` (1.5rem) rounded corners.
*   **Edge Treatment:** A "Ghost Border" of `outline_variant` at 20% opacity. 
*   **Content:** Forbid divider lines. Separate "Current Set" from "Next Set" using vertical white space (24px) or a background shift to `surface_container_high`.

### Progress Rings: Biometric Gauges
*   **Track:** `surface_variant` at 30% opacity.
*   **Indicator:** Gradient of `primary` to `secondary`. 
*   **End-Cap:** Round. Use a "Glow Point" (a small 4px circle of pure white) at the leading edge of the progress bar to simulate a moving light source.

### Input Fields: Command Lines
*   **Style:** Minimalist. Only a bottom border (2px) using `outline_variant`. 
*   **Active State:** Bottom border transitions to `primary` with a subtle 4px vertical glow rising from the line.

---

## 6. Do’s and Don'ts

### Do:
*   **Do** use "Data Density." It’s okay to have a lot of small, technical information if the hierarchy clearly highlights the "Hero" metric.
*   **Do** use asymmetrical layouts. A large circular gauge on the left balanced by three small text modules on the right feels more "OS" than a centered stack.
*   **Do** use Success/Error colors sparingly. They should feel like "Alerts" in an aircraft cockpit—high contrast and immediate.

### Don't:
*   **Don't** use 100% opaque, high-contrast white text for everything. Use `on_surface_variant` for secondary labels to create depth.
*   **Don't** use standard 0.5px or 1px solid dividers. They break the holographic illusion. Use spacing or tonal shifts instead.
*   **Don't** use "Soft" imagery. Photos should be high-contrast, desaturated, or treated with a cool-toned duotone filter to match the system's atmosphere.