# Kicker: faster search in the Application Dashboard

Five QML-only commits for `applets/kicker` in plasma-desktop that stop search from lagging while typing. Every keystroke used to rebuild every result tile, visible or not; now only the visible tiles are built, and each is cheaper. `REPORT.md` has the measurements and the reasoning for each change.

## Contents

| Path | What it is |
| --- | --- |
| `REPORT.md` | Before/after measurements, why each change is needed, what was tried and dropped, open questions. Usable as the merge request description. |
| `patches/0001-…0005-*.patch` | The five commits, from `git format-patch`, against plasma-desktop master at `083c7508e8`. |
| `kicker-search-perf.diff` | All five commits as one diff, for reading. |
| `modified-files/applets/kicker/` | The four changed QML files, as they are after the five commits. |
| `profiling/` | How to record a `qmlprofiler` trace of the dashboard, and the script that turns one into per-keystroke numbers. |

## Commits

1. `applets/kicker: only fetch actionList when opening the context menu`
2. `applets/kicker: use QQC2.Action for delegate actions`
3. `applets/kicker: create grid delegate tooltips on demand`
4. `applets/kicker: load grid delegate content asynchronously`
5. `applets/kicker: only create visible delegates in ItemMultiGridView`

Each commit builds on its own on master with no warnings. The changes were tested in daily use on a Plasma 6.8.1 build of the same patches.

## Submitting

KDE takes changes as merge requests on [invent.kde.org](https://invent.kde.org/plasma/plasma-desktop), not as patch files.

1. Log in to invent.kde.org with a KDE Identity account and fork `plasma/plasma-desktop`.
2. Apply the patches on a branch and push it to your fork:
   ```sh
   git checkout -b work/kicker-search-perf origin/master
   git am patches/*.patch
   git push <your-fork> work/kicker-search-perf
   ```
3. Open a merge request against `master`, with `REPORT.md` as the description.
