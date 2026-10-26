# Kicker search performance report

Search in the Application Dashboard (and, to a lesser degree, Application Menu) lagged because every keystroke rebuilt every result tile, visible or not. Five QML-only changes cut the work per keystroke by about 60% and stopped keystrokes from queueing up behind freezes.

## Results

With all changes, only 3% of keystrokes arrived queued behind a freeze, down from 36%, and the worst keystroke spent 222 ms in QML instead of 558 ms.

| Build | Keys queued behind a freeze | Tiles built per keystroke (avg / worst) | QML time per keystroke (avg / worst) |
| --- | --- | --- | --- |
| Stock 6.8.1 | 36% | 85 / 214 | 200 ms / 558 ms |
| + lazy tooltip, lighter Action | 23% | 186 / 467 | 298 ms / 840 ms |
| + async tile contents | 25% | 112 / 405 | 177 ms / 675 ms |
| + only build visible tiles | 3% | 59 / 157 | 82 ms / 222 ms |

Each row is one session of the dashboard run in `plasmoidviewer` under `qmlprofiler`, built from the v6.8.1 tag against an installed Plasma 6.8.1 (Arch Linux, Qt 6.12.0, Wayland). A key counts as queued when it reached QML less than 1 ms after the previous key, meaning the UI thread was blocked while it was typed. The middle rows built more tiles than stock because more was typed in those sessions; per tile, the QML cost fell from 2.8 ms to 1.7 ms.

First letters were the worst case, since they match the most results. On the stock build, typing `S` built 200 tiles, and the next five keys (`ettin`) arrived in the same millisecond 925 ms later. With all changes, `S` builds about 41 tiles and the next key arrives 110–215 ms later, at normal typing pace.

`profiling/` has the script that produced these numbers and the steps to record a trace.

## Changes and why

The biggest win is building only the tiles on screen; the others make each remaining tile cheaper or keep its cost off the input path. All five changes are QML-only and keep existing behaviour.

| Change | File | Why it was slow | Effect |
| --- | --- | --- | --- |
| Only build tiles scrolled into view | `ItemMultiGridView.qml`, `ItemGridView.qml` | Each result category is a `GridView` as tall as its content inside an outer `Flickable`, so the view treats every tile as visible and creates all of them. Negative `displayMarginBeginning` / `displayMarginEnd` shrink the fill range to the part inside the outer viewport. | Tiles per keystroke 112 → 59 avg, 405 → 157 worst; queued keys 25% → 3% |
| Load tile icon and label asynchronously | `ItemGridDelegate.qml`, `ItemGridView.qml` | Icon, label and layout were created synchronously with each tile, and large icons load on the GUI thread. The content now sits in a `Loader { asynchronous: true }`, so it is incubated between frames and dropped if the results change first. Only grids without drag-and-drop use it, so favorites load as before. | Moves content creation off the keystroke; tiles fill in a frame or two later |
| Fetch `actionList` only when the context menu opens | `ItemAbstractDelegate.qml` | Commit d5648c1929 made `actionList` a `required` property, so every row computed its jump list, recent documents and AppStream actions on creation. `code/tools.js` already warned this is costly. It is now read from `model.actionList` in `openActionMenu()`. | Removes the per-row action list cost in both Menu and Dashboard; menu content unchanged |
| Create the tooltip only on hover | `ItemGridDelegate.qml` | Every tile instantiated its own `PlasmaComponents3.ToolTip` popup with frame and label up front. It is now in a `Loader` active while the tile is hovered. | About 13% of per-tile QML cost |
| Use `QQC2.Action` instead of `Kirigami.Action` | `ItemAbstractDelegate.qml` | `Kirigami.Action` adds a `Shortcut` and a `Connections` object per delegate. Only `onTriggered` and `trigger()` are used, which `QQC2.Action` provides. | Together with the tooltip change, per-tile QML cost fell from 2.8 ms to 1.7 ms |

## Commits

One commit per change, in this order; each builds on its own on current master.

1. `applets/kicker: only fetch actionList when opening the context menu`
2. `applets/kicker: use QQC2.Action for delegate actions`
3. `applets/kicker: create grid delegate tooltips on demand`
4. `applets/kicker: load grid delegate content asynchronously`
5. `applets/kicker: only create visible delegates in ItemMultiGridView`

## Tried and dropped

Delegate reuse (`reuseItems: true` on the result grids) was dropped because it crashed on teardown. The idea was to re-point existing tiles at new results instead of recreating them on each keystroke.

The viewer crashed with SIGSEGV when it exited, inside `QQmlDelegateModelItem::destroyObjectLater()`, called from `~QQmlDelegateModel` while the nested result grids were being destroyed. In plasmashell, the same path would run when the widget is removed or the session ends, so the change was reverted before measuring it. Building only the visible tiles achieved the same goal without touching Qt's reuse pool.

## Limits and open questions

About 80 ms of QML work per keystroke remains, plus the search itself in plasma-workspace's C++ `RunnerModel`, which `qmlprofiler` cannot see.

- **Negative display margins are not documented.** Qt 6's `QQuickItemView` uses `displayMarginBeginning` / `displayMarginEnd` unclamped in `refill()`, which is what makes this work. A future Qt that clamps them would silently bring back the old cost, not break anything.
- **Tiles are still rebuilt on every result update.** The `RunnerModel` delivers results several times per keystroke and the grids rebuild their visible tiles each time. Batching those updates would have to happen in plasma-workspace.
- **The Menu view was not profiled.** The `actionList` fix applies to it, but the numbers above are from the Dashboard only.
- **Tested on 6.8.1, built on master.** The changes were tested in daily use on a 6.8.1 build. The five commits build cleanly on master, but were not run there, since master needs a newer plasma-workspace.

To check by hand: type in the Dashboard, then confirm tooltips on hover, right-click menus (including jump-list and recent-document entries), the "New!" badge, arrow-key navigation with scroll-into-view, and mouse-wheel scrolling with no blank tiles.
