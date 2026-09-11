# Privacy and publication boundary

The public software repository and users' analytical work are separate. Completed workbooks, analyst names and notes, saved collections, calculation caches, exports, logs and screenshots are local working material unless their owner deliberately reviews and shares a copy.

Do not attach workbooks or analytical records to public issues. A diagnostic should reveal only the minimum technical information needed, after review. A private full-workspace backup and a shareable chart/data export have different content. Backups include workbooks and private saved records; this preview has no internal-export button. Follow the [backup and recovery instructions](privacy-recovery.md). Neither a backup nor a shareable export makes economic data anonymous by itself.

Public releases are assembled from an explicit reviewed inventory, not a recursive copy of a working directory. File contents, names, symlinks, binary/embedded material, generated distributions and Git history must be checked. A deletion from the current tree does not remove historical disclosure. `.gitignore` is useful housekeeping but is not a publication security boundary.

Public admission requires known provenance, an appropriate rights basis, and review of the exact content being published. The release check must reject unknown or changed files and unexpected destinations. Changed content invalidates an earlier review. A public source link is not automatically a redistribution license for its downloaded asset.

Application code is MIT licensed. Required external template, dependency and font rights must be inventoried independently. Use the official template source record; do not silently substitute an unrelated workbook or a maintainer's edited copy.

## Shared content and release evidence

Deliberately shared driver explanations accompany comparison-v3 JSON and PDF annexes. Charts include shared labels and a workbook reference. An analyst can enter personal or confidential information in these fields. Field selection prevents automatic sharing of private journals; it cannot determine whether all remaining content is safe to disclose. Review the actual output.

The [release-control procedure](release-controls.md) distinguishes source admission, Git history, packaged files, local hooks and proposed hosted enforcement. Every materially changed source/documentation/package candidate needs fresh exact review. Reusing a version number, old approval or filename is insufficient.

The local preview has no public feed or automated content moderation. Project maintainers still need reporting and removal arrangements for public contributor/support surfaces. Any future hosted content feature must define operator responsibilities, retention and safe handling before launch. See the [DPG evidence register](dpg-evidence.md) and [security policy](../SECURITY.md).
