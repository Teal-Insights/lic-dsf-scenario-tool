# Third-party notices for the documentation website

The LIC-DSF Scenario Analysis Tool's documentation includes third-party code and fonts. The application's MIT license does not replace these components' licenses. The complete notice and license texts listed below accompany this document in `../licenses/`; original notices in distributed assets are also retained.

| Component | Distributed use | License and notice |
|---|---|---|
| [Great Docs 0.17.0](https://github.com/posit-dev/great-docs/tree/v0.17.0) | Documentation styling, navigation, widgets, lightbox and terminal display scripts | [MIT; Posit Software, PBC](../licenses/great-docs-LICENSE.txt) |
| [Quarto 1.8.27 web resources](https://github.com/quarto-dev/quarto-cli/tree/v1.8.27/src/resources) | Navigation, search integration, tabsets, HTML behavior and generated styles | [MIT; Posit Software, PBC](../licenses/quarto-LICENSE.txt) |
| [Bootstrap 5.3.1](https://github.com/twbs/bootstrap/tree/v5.3.1) | Styles and JavaScript | [MIT; The Bootstrap Authors](../licenses/bootstrap-LICENSE.txt) |
| [Bootstrap Icons 1.13.1](https://github.com/twbs/icons/tree/v1.13.1) | Icon CSS and WOFF font | [MIT; The Bootstrap Authors](../licenses/bootstrap-icons-LICENSE.txt) |
| [Clipboard.js 2.0.11](https://github.com/zenorocha/clipboard.js/tree/v2.0.11) | Clipboard helper | [MIT; Zeno Rocha](../licenses/clipboard-LICENSE.txt) |
| [AnchorJS 5.0.0](https://github.com/bryanbraun/anchorjs/tree/5.0.0) | Heading links | [MIT; Bryan Braun](../licenses/anchorjs-LICENSE.txt) |
| [Popper 2.11.7](https://github.com/floating-ui/floating-ui/tree/v2.11.7) | Tooltip positioning | [MIT; Federico Zivolo](../licenses/popper-LICENSE.txt) |
| [Tippy.js 6.3.7](https://github.com/atomiks/tippyjs/tree/v6.3.7) | Tooltip script and styles | [MIT; atomiks](../licenses/tippy-LICENSE.txt) |
| [Headroom.js 0.12.0](https://github.com/WickyNilliams/headroom.js/tree/v0.12.0) | Navigation behavior | [MIT; Nick Williams](../licenses/headroom-LICENSE.txt) |
| [Algolia Autocomplete 1.19.1](https://github.com/algolia/autocomplete/tree/v1.19.1) | Search interface, including its shared/core/preset/insights helper code | [MIT; Algolia, Inc. and contributors](../licenses/autocomplete-LICENSE.txt) |
| [Preact](https://github.com/preactjs/preact) | Embedded in the Autocomplete bundle | [MIT; Jason Miller](../licenses/preact-LICENSE.txt) |
| [htm](https://github.com/developit/htm) | Embedded in the Autocomplete bundle | [Apache 2.0; Google Inc.](../licenses/htm-LICENSE.txt) |
| [Fuse.js 6.6.2](https://github.com/krisk/Fuse/tree/v6.6.2) | Local documentation search | [Apache 2.0; Kirollos Risk](../licenses/fuse-LICENSE.txt) |
| [Lucide](https://github.com/lucide-icons/lucide) | Keyboard icon included by Great Docs | [ISC, with the upstream Feather/MIT notices retained](../licenses/lucide-LICENSE.txt) |
| [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) | Regular and Bold WOFF2 subsets supplied by Great Docs | [SIL OFL 1.1; The JetBrains Mono Project Authors](../licenses/jetbrains-mono-LICENSE.txt) |
| [Inter](https://github.com/rsms/inter) | Regular and SemiBold documentation fonts | [SIL OFL 1.1](../licenses/OFL-Inter.txt) |
| [IBM Plex Serif](https://github.com/IBM/plex) | SemiBold documentation font | [SIL OFL 1.1](../licenses/OFL-Plex.txt) |

The documentation build customizes Great Docs styling and scripts. Quarto's copy of Algolia Autocomplete includes an accessible-label adjustment, and its bundled minified assets omit source-map references. Font subset files supplied by Great Docs are redistributed without further font modifications. These notices also cover component copyright years retained in the bundled source headers, including AnchorJS (2023), Headroom.js (2020) and Fuse.js (2022).

Tool versions identify the documentation build inputs. The exact embedded Preact/htm patch versions and JetBrains Mono source-font version are not separately asserted; their distributed bytes are supplied by the identified Autocomplete and Great Docs versions. This website does not redistribute the Quarto command-line executable or the Great Docs Python build environment.
