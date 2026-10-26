# Measuring search lag in the dashboard

The numbers in `REPORT.md` come from `qmlprofiler` traces of the Application Dashboard, typing the same words in each build (`firefox`, delete it, `settings`).

## Record a trace

Build the applet (`cmake --build build --target org.kde.plasma.kicker`), then run the dashboard with that build ahead of the installed one. `--interactive` lets you save the trace while the window is still open, because closing it can end the process before the data is sent.

```sh
mkfifo ctl
QT_PLUGIN_PATH=$PWD/build/bin bash -c 'exec 3<>ctl; exec qmlprofiler --interactive -o trace.qtd \
    plasmoidviewer -a org.kde.plasma.kickerdash -l bottomedge -f horizontal <&3' &
# open the dashboard from the launcher icon and type
echo f > ctl   # stop recording and write trace.qtd
echo q > ctl   # quit
```

Leave out `QT_PLUGIN_PATH` to profile the installed (stock) applet.

## Analyse it

```sh
python3 analyze_keystrokes.py trace.qtd
```

It prints, per key press, the time until the next key, the QML time spent in between and the number of grid delegates created, then a summary. A key that arrives less than 1 ms after the previous one was queued while the UI thread was blocked.

`qmlprofiler` only sees QML and JavaScript. Time spent in C++ (the runner queries, icon loading, layout) shows up only as a longer gap between keys.
