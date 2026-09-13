# Review the exact release before publishing

A release comprises source, Git history and metadata, generated packages and their contents, dependency notices, and the exact destination. Each needs review. A clean current tree or a passing text scan covers only part of that work. The application can run without the maintainer's private release controls; publishing a maintained release requires those controls to be provisioned separately.

## What is available in each environment

| Environment | Available evidence/control | Limit |
| --- | --- | --- |
| Fresh source clone | Public source, license, documentation, schemas and tests | The reviewed clone does not contain the maintainer's private admission gate, private policy/receipts or installed pre-push hook. The source includes hosted source-test and documentation-check workflows. They do not publish releases or replace confidential admission review. |
| Maintainer release environment | Separately provisioned admission inventory, policy, independent review records and local push hook | These are local controls. They must be checked after cloning or moving machines. A hook cannot govern unrelated API uploads or a privileged actor who disables it. |
| Hosted repository | Required reviews/checks, restricted release credentials, protected branches/tags and security reporting require separately verified repository configuration | Configuration and failed-attempt tests must be observed in the actual repository. This document does not assert they are enabled. |
| Built archive or deployment | Exact archive/image hash, full member inventory, provenance/rights evidence and separate review | A reviewed source tree does not automatically approve generated metadata, bundled dependencies, downloads or an image filesystem. |

Git documents [local hooks and pre-push behavior](https://git-scm.com/docs/githooks). Verify the installed hook and its referenced control files directly; do not infer installation from source documentation.

## Maintain the public source boundary

1. Start with the previously reviewed general source and explicitly select reusable files with known provenance. Never seed public history by copying a mixed working repository or data directory.
2. Inspect every new or changed file, including names and metadata. Record each admitted path, content hash and mode. Exclude analytical workspaces, logs, screenshots, exports and private provenance. Exceptions for intentionally public assets need separate content and rights review.
3. Check current files and the index independently. Confirm the intended publication commit has exactly the reviewed tree. Review all reachable commits, deleted historical files, ref names, author/committer metadata and annotated tags. Reject linked/shared/incomplete history and unexplained Git objects.
4. Bind an independent review to the manifest, policy, gate version and exact destination. Changing any binding makes the old review insufficient. Historical approval covers only unchanged historical content, never a replacement current file or a new release.
5. Exercise neutral synthetic failure cases: unknown ignored files, private-looking markers, user data, logs, images, exported results, symlinks, binary content, changed hashes, stale approvals, staged/disk differences, old commits and unexpected remotes. Include a valid new general change so the control also proves it can admit appropriate content.

The admission gate is read-only. A PASS states what the check accepted; it does not authorize an external write. Source-only review may inspect a directory without Git. A publication check must additionally require and validate the exact commit/history. If that distinction is not enforced by the installed gate, hold publication and repair/review the control.

## Inspect each generated artifact

Build in an isolated directory containing only admitted inputs. Pin build tools and resolved dependencies, retain acquisition URLs and hashes, and record the platform. Inspect wheels, source archives, application bundles, installer ZIPs, container layers and build logs independently for the formats actually offered.

Check the outer hash and the complete inner path/hash inventory. Reject unexpected members, duplicate or ambiguous paths, traversal, symlinks, unauthorized binary assets, archive comments or extended metadata containing local details, and unexplained generated files. Check wheel RECORD hashes where relevant, and reconcile licenses/notices for every bundled dependency, interpreter, native library and font. Rebuilds require new byte-level review even if their filenames and version strings are unchanged.

Never send private files or verification fixtures to an external scanner. A public-source dependency audit can use a reviewed list of public package names/versions. Record the tool, database date, exact input and result; a notice inventory is not a vulnerability scan.

## Before the first authorized publication

The release operator needs a new exact decision containing the final commit, source manifest, archive/image hashes, target and visibility, included release notes/docs, independent reviews and unresolved qualifications. Source code, binary distribution and hosting may require separate decisions. An older decision does not silently expand to changed content.

After exact authorization, provision and verify repository protections and private security reporting. Restrict release credentials to reviewed paths and scope. Exercise a denied unreviewed update. CI on a public repository can catch later mistakes, but it cannot undo a secret or private file already uploaded for the CI run. Keep first admission and confidential checks in the private release environment before any public upload.

Recheck exact bytes immediately before publishing, then verify the remote commit and downloaded artifacts against the approved hashes. Retain private operational receipts and publish only an independently reviewed safe evidence summary. A release rollback can change future distribution; it cannot guarantee deletion of copies already downloaded.

Formal DPG recognition is a separate process. See the [evidence register](dpg-evidence.md).
