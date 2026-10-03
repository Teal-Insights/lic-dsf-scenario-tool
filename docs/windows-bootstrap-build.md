# Build an unsigned Windows launcher

This maintainer workflow builds the general C launcher with the existing x64
MSVC and Windows SDK on a GitHub-hosted Windows Server 2022 runner. It does not
build the application package or execute the resulting launcher. A successful
run establishes only the compilation and PE inspection recorded for that commit.

## Run the build

After the exact source and Git history have been reviewed and the workflow is
admitted to main, select **Reviewed unsigned Windows bootstrap build** in
GitHub Actions and run it on main. The job refuses other repositories, private
copies and other branches. Checkout uses the dispatch commit with no persisted
credentials. Actions are pinned to full commit identifiers.

The build uses the runner's installed x64 MSVC and SDK, refuses unexpected
compiler options, and checks the four pinned source files before and after the
build. Its output directory must be new. Compilation uses C17, warnings as
errors and the static C runtime. The recipe inspects the x64 console PE header
and refuses a pre-existing signature.

The run has a 15-minute limit and stores these separate artifacts for seven days:

- `unsigned-bootstrap-<commit>-<run>-<attempt>` contains `Start LIC-DSF.exe` only,
  after a successful build.
- `bootstrap-build-evidence-<commit>-<run>-<attempt>` contains any available
  compiler, dependency and header logs, `unsigned-build-receipt.json` and
  `runner-toolchain.json`. Failure diagnostics may be incomplete; inspect the
  job result and actual artifact inventory.

Download the exact run's artifacts and review the executable, complete member
inventory, hashes, compiler and SDK evidence before any later package assembly.
Build logs are technical working material and need separate review before
being forwarded or attached to a release. Artifact upload is not a release.

## Evidence still required

The workflow does not run the PE, sign it, assemble a package or publish a
download. It uses no Azure login, OIDC signing permission or signing service.
Windows 11 standard-user launch, UTF-16 paths, cancellation, package integrity
and Excel acceptance require their own observed checks on the exact package.
The existing CMD launcher and bundled interpreter are preserved separately.
No numerical method, teaching case or comparison tolerance changes here.

The optional signing-preparation files validate supplied artifact/signature
facts locally. Their presence does not create a signing account, grant access,
sign a file or establish trust. Signing and release authorization remain
separate from this unsigned build.
