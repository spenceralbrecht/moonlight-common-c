# Native security scanning

GitHub CodeQL default setup is the scanning source of record for this fork.
Keep its existing C/C++ scan enabled. The maintained
`moonshine-adaptive-bitrate` branch is protected from force pushes and deletion
so default setup includes pushes and same-repository pull requests targeting
that branch. Default setup excludes pull requests whose head is in a fork;
do not treat those pull requests as scanned without a separate analysis receipt.
`master` continues to receive its existing default-branch analysis.

An intentionally retained protected `security/consumed-6cc46f7` reference points
to the already-public commit `6cc46f722fa27c8722e5ed8cc8c82bfe46f4bb1f`.
It provides exact-source analysis without moving a downstream dependency or
merging newer native behavior. Preserve this verification reference; it is not
a redundant implementation branch.

Check the analysis commit and reference before treating a scan as release
coverage. A successful scan of `master` does not cover a different release
commit. Keep findings open until their callers, build selection and input
bounds establish the appropriate disposition; an alert count is not a
reachability assessment.

Default setup runs on qualifying pushes and pull requests. Weekly scanning
starts only after one of those events triggers an analysis and continues while
such activity occurred within the preceding 180 days. An initial setup scan or
configuration change alone does not establish ongoing weekly coverage. Read
the current Actions and code-scanning analysis records rather than assuming a
configured schedule has executed.

These controls use standard GitHub-hosted scanning of this public repository.
They do not require a native product build, credentials, a downstream private
checkout, a runtime deployment, or a change to existing scan queries.

References:
- [GitHub default setup behavior](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types)
- [Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
