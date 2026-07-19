# RetailPulse Design Guidelines

## Brand Direction
- The report should feel like an executive retail command center, not a generic dashboard.
- Use crisp spacing, clear hierarchy, and restrained accent colors.
- Keep every page readable in presentation mode and in exported PDF form.

## Typography
- Use `Segoe UI Semibold` for titles and `Segoe UI` for body text.
- Suggested sizes:
  - Page title: 28 to 32 pt
  - Section heading: 16 to 18 pt
  - KPI label: 11 to 12 pt
  - Table body: 10 to 11 pt
- Avoid decorative typefaces and avoid mixing too many font weights on the same page.

## Color Palette

### Dark Variant
| Token | Hex | Use |
| --- | --- | --- |
| Background | `#0B1220` | Report canvas |
| Surface | `#111827` | Cards and panels |
| Primary | `#2D6CDF` | Main actions and highlights |
| Secondary | `#14B8A6` | Supportive signals |
| Warning | `#F59E0B` | Attention states |
| Danger | `#EF4444` | Critical risk and churn |
| Success | `#22C55E` | Healthy performance |
| Text | `#E5EEF8` | Primary typography |

### Light Variant
| Token | Hex | Use |
| --- | --- | --- |
| Background | `#F5F7FA` | Report canvas |
| Surface | `#FFFFFF` | Cards and panels |
| Primary | `#1D4ED8` | Main actions and highlights |
| Secondary | `#0F766E` | Supportive signals |
| Warning | `#D97706` | Attention states |
| Danger | `#DC2626` | Critical risk and churn |
| Success | `#15803D` | Healthy performance |
| Text | `#0F172A` | Primary typography |

## Spacing And Layout
- Use an 8 px grid with 16 px minimum padding inside cards.
- Keep 24 px between major sections and 32 px between major visual groups.
- Align cards to a consistent baseline across the page.
- Prefer 16:9 canvases and avoid full-width clutter.

## Visual Styling
- Use rounded cards with subtle borders instead of heavy shadows.
- Keep axes, gridlines, and legends minimal.
- Use one accent color per page family and reserve red for exceptions.
- Avoid rainbow category palettes unless the chart needs categorical separation.

## Icons And Shapes
- Use line icons for navigation and category callouts.
- Keep icons small and consistent in stroke weight.
- Use shape containers to create visual grouping only when the grouping improves comprehension.

## Accessibility
- Keep contrast high enough for projector and laptop viewing.
- Do not rely on color alone to signal risk or status.
- Use clear labels and short annotations on key visuals.
- Test all pages with dark and light themes before final sign-off.

## Theme Files
- `theme.json` is the default dark enterprise theme.
- `theme-light.json` is the companion light theme for report variants or print-friendly presentations.
