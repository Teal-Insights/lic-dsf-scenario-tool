# Accessibility and platform status

This is a source preview. No WCAG conformance, assistive-technology acceptance, Windows acceptance or completed cross-platform release is claimed.

## Accessibility features and remaining work

The browser page has labelled controls, numbered navigation links, a visible keyboard-focus style, expandable help and a live status region. The input grid labels each field by economic input and workbook year. Comparison values appear in a table. Charts distinguish series using line styles and markers as well as colour, and retain units and years.

Those implementation choices need independent testing. Keyboard-only completion, screen-reader reading order and table associations, focus after validation errors, zoom/reflow, colour contrast, long labels and projected readability remain acceptance checks for the assembled release. Wide input tables require horizontal scrolling. The image alternative points to the numerical table; it does not narrate every series.

PNG is a raster image. PDF contains vector text and plots but is not certified as a tagged accessible PDF. JSON preserves full-precision data and assumptions but is not a substitute for usable nontechnical access. A release should provide an accessible table alongside charts and test it with its intended users.

## Platform evidence

| Area | Current status |
| --- | --- |
| Python requirement | Source declares Python 3.11 or later; dependency/platform compatibility still needs verification |
| Excel installation | Not required by the Python calculation route; exact Excel verification is a separate pending activity |
| Browser | Local HTML interface implemented; no complete accepted browser matrix |
| macOS | Development environment exists; this does not establish independent installation or analyst acceptance |
| Windows | Source includes platform-specific process/lock handling; no accepted real-Windows end-to-end test |
| Linux | No accepted end-to-end platform test |
| Offline runtime | No hosted service or remote runtime assets intended; measured offline/network-behaviour acceptance remains pending |
| Installation | Source package route documented; clean noneditable installation acceptance remains pending |
| Recovery | Durable records and recovery instructions exist; independent full-workspace restore acceptance remains pending |

Record the exact application/dependency versions, OS, browser, test steps and observed result when closing a gap. Do not infer platform acceptance from a simulated test, packaged files or source branches alone.
