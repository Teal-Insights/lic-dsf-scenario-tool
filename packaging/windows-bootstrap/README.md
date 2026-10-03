# Unsigned Windows bootstrap build preparation

The manual native build job compiles only the general C bootstrap source with the runner's existing x64 MSVC/SDK, records compiler/header/dependency evidence and proposes an unsigned PE for review. It uses a fixed bundled runtime interpreter and script at actual launch; it does not bundle or execute them here. The original CMD launchers and third-party runtime remain separate, preserved assets.

Source preparation and portable planner checks do not establish native compatibility, UTF-16, cancellation, first launch, signing, Windows11 or Excel acceptance. The native source/build recipe must still run successfully on its exact admitted commit, and its output must be reviewed before any later assembler/signing workflow. No current release asset or manifest is overwritten by this job.
