# Tokyo Night Day for ONLYOFFICE

[Português](README.md) · [Back to the COSMIC theme](../README.en.md)

An optional light interface with blue/lavender surfaces, slate text, deep blue buttons and purple accents. Document pages remain white. Fonts, document formatting and content stay unchanged.

This add-on is **not** included in `theme.py apply`. It does not modify the system theme, terminal or default file associations.

## Install

Requires Linux, Python 3.12+ and ONLYOFFICE Desktop Editors with local theme support (8.0+). Configuration checked with Flatpak 9.4.0; native installations share the format but were not visually tested.

Save your work and close ONLYOFFICE normally. From the repository root, without `sudo`:

```sh
python3 onlyoffice/install.py install
```

Reopen ONLYOFFICE. **Tokyo Night Day** will be selected. Flatpak profiles are detected first. Select a target explicitly if needed:

```sh
python3 onlyoffice/install.py install --target flatpak
python3 onlyoffice/install.py install --target native
```

The JSON is copied into the user's `onlyoffice/desktopeditors/uithemes/` data folder. Selection changes only `UITheme` in `onlyoffice/DesktopEditors.conf`. Flatpak stores these below `~/.var/app/org.onlyoffice.desktopeditors/`. Application files and Flatpak permissions remain untouched.

## Manual import

Choose **Settings → General → Interface theme → Add local theme** and select [tokyo-night-day.json](tokyo-night-day.json). It can also be selected under **View → Interface Theme**. Menu names depend on version/language. To copy the JSON without selecting it:

```sh
python3 onlyoffice/install.py install --no-select
```

## Restore

Close ONLYOFFICE normally, then run:

```sh
python3 onlyoffice/install.py restore
```

Reopen the app. Backups are stored in `${XDG_STATE_HOME:-~/.local/state}/tokyo-night-onlyoffice/backups/`. Only the theme JSON and selection are restored; other preferences survive. Later edits to the JSON or selection are preserved. File associations are unaffected.

## Default DOCX/DOC app (optional)

For Flatpak:

```sh
xdg-mime default org.onlyoffice.desktopeditors.desktop application/vnd.openxmlformats-officedocument.wordprocessingml.document
xdg-mime default org.onlyoffice.desktopeditors.desktop application/msword
```

Native packages require their installed `.desktop` identifier. This step is independent of theme installation.

## Sources and scope

Uses the [official theme format](https://api.onlyoffice.com/docs/desktop-editors/usage-api/customizing-themes/), [local theme import](https://helpcenter.onlyoffice.com/desktop/getting-started), and native [CThemes loader](https://github.com/ONLYOFFICE/desktop-apps/blob/master/win-linux/src/cthemes.cpp). Original palette inspired by [Tokyo Night Day](https://github.com/folke/tokyonight.nvim); no upstream source code is bundled. The repository's MIT license applies to this add-on; ONLYOFFICE retains its own license and trademarks.

Plugins, OS dialogs and future versions may use their own colors. Printed/exported document colors are not changed. Document transparency is not provided.
