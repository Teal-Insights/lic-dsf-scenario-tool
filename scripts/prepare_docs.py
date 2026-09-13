"""Prepare website pages from the same Markdown guides displayed on GitHub.

Only explicit public source documents are read. Runtime workspaces and repository
history are never documentation inputs. Run before ``great-docs build``.
"""
from pathlib import Path
import re


ROOT_PAGES = {
    "CONTRIBUTING.md": "contributing",
    "CODE_OF_CONDUCT.md": "conduct",
    "SECURITY.md": "security",
    "THIRD_PARTY.md": "third-party",
    "LICENSE": "license",
}


def rewrite_links(text, root_page=False):
    def replace(match):
        target = match.group(1)
        if ":" in target or target.startswith("#"):
            return match.group(0)
        path, separator, anchor = target.partition("#")
        basename = Path(path).name
        if basename in ROOT_PAGES:
            slug = ROOT_PAGES[basename]
        elif basename == "README.md":
            slug = "documentation-index" if path != "../README.md" else "getting-started"
        elif path.endswith(".md"):
            slug = Path(path).stem
        else:
            return match.group(0)
        prefix = "user-guide/" if root_page else ""
        return "(" + prefix + slug + ".qmd" + separator + anchor + ")"
    return re.sub(r"\(([^()\s]+)\)", replace, text)


def as_qmd(text, fallback):
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        title = lines.pop(0)[2:]
    else:
        title = fallback
    # JSON strings are valid YAML scalars and retain punctuation in titles.
    import json
    return "---\ntitle: " + json.dumps(title) + "\n---\n" + "\n".join(lines) + "\n"


def main():
    root = Path(__file__).resolve().parents[1]
    destination = root / "user_guide"
    destination.mkdir(exist_ok=True)
    documents = {p: ("documentation-index" if p.name == "README.md" else p.stem)
                 for p in sorted((root / "docs").glob("*.md"))}
    documents.update({root / name: slug for name, slug in ROOT_PAGES.items()})
    for path, slug in documents.items():
        if path.is_symlink():
            raise SystemExit("Documentation sources must be regular files.")
        text = path.read_text(encoding="utf-8")
        (destination / (slug + ".qmd")).write_text(
            as_qmd(rewrite_links(text), slug), encoding="utf-8")
    print(f"Prepared {len(documents)} website pages from public source documents.")


if __name__ == "__main__":
    main()
