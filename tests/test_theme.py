import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('theme', Path(__file__).parents[1] / 'theme.py')
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        env = {f'XDG_{n}_HOME': str(self.root / n.lower()) for n in ['CONFIG', 'DATA', 'STATE', 'CACHE']}
        self.env = patch.dict(os.environ, env); self.env.start()
        self.system = self.root / 'system'
        for ns, version in [('com.system76.CosmicTheme.Dark', 2), ('com.system76.CosmicTheme.Dark.Builder', 2), ('com.system76.CosmicPanel.Panel', 1)]:
            (self.system / ns / f'v{version}').mkdir(parents=True)
        self.system_patch = patch.object(theme, 'SYSTEM_DATA', self.system); self.system_patch.start()
        self.sleep = patch.object(theme.time, 'sleep'); self.sleep.start()
        self.config = self.root / 'config'

    def tearDown(self):
        self.sleep.stop(); self.system_patch.stop(); self.env.stop(); self.tmp.cleanup()

    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return theme.main(list(args))

    def write(self, rel, text):
        p = self.config / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
        return p

    def test_fresh_apply_reapply_and_restore(self):
        kitty = self.write('kitty/kitty.conf', '# own settings\nfont_size 14\n')
        shortcut = self.write('cosmic/com.system76.CosmicSettings.Shortcuts/v1/custom', 'private-shortcuts')
        favorites = self.write('cosmic/com.system76.CosmicAppList/v1/favorites', '["personal-app"]')
        entries = self.write('cosmic/com.system76.CosmicPanel/v1/entries', '["OtherPanel"]')
        layout = self.write('cosmic/com.system76.CosmicPanel.Panel/v1/plugins_center', 'Some(["custom-applet"])')
        css = self.write('gtk-4.0/cosmic/dark.css', 'original-css')
        link = self.config / 'gtk-4.0/gtk.css'; link.symlink_to(css)
        self.assertEqual(self.call('apply', '--no-assets', '--no-gsettings'), 0)
        latest = theme.locations()['state'] / 'latest'; first = latest.read_text()
        self.assertEqual(kitty.read_text().count(theme.START), 1)
        self.assertEqual(json.loads(entries.read_text()), ['OtherPanel', 'Panel', 'Dock'])
        self.assertEqual(layout.read_text(), 'Some(["custom-applet"])')
        self.assertEqual(shortcut.read_text(), 'private-shortcuts')
        self.assertEqual(favorites.read_text(), '["personal-app"]')
        self.assertEqual(self.call('apply', '--no-assets', '--no-gsettings'), 0)
        self.assertEqual(latest.read_text(), first, 'no-op must not hide the useful backup')
        self.assertEqual(self.call('restore'), 0)
        self.assertEqual(kitty.read_text(), '# own settings\nfont_size 14\n')
        self.assertEqual(entries.read_text(), '["OtherPanel"]')
        self.assertTrue(link.is_symlink())
        self.assertEqual(css.read_text(), 'original-css')
        self.assertFalse((self.config / 'cosmic/com.system76.CosmicTheme.Dark/v2/accent').exists())

    def test_restore_preserves_later_edits(self):
        self.assertEqual(self.call('apply', '--no-assets', '--no-gsettings'), 0)
        kitty = self.config / 'kitty/kitty.conf'; kitty.write_text('later user changes')
        self.assertEqual(self.call('restore'), 0)
        self.assertEqual(kitty.read_text(), 'later user changes')

    def test_dry_run_has_no_writes_or_network(self):
        with patch.object(theme, 'assets', side_effect=AssertionError('network/install must not run')):
            self.assertEqual(self.call('apply', '--dry-run', '--no-gsettings'), 0)
        self.assertFalse(self.config.exists())
        self.assertFalse(theme.locations()['state'].exists())

    def test_rejects_incompatible_version_before_writing(self):
        (self.system / 'com.system76.CosmicTheme.Dark/v3').mkdir()
        self.assertEqual(self.call('apply', '--no-assets', '--no-gsettings'), 1)
        self.assertFalse(self.config.exists())

    def test_rejects_unsafe_tar(self):
        archive = self.root / 'bad.tar'
        with tarfile.open(archive, 'w') as stream:
            item = tarfile.TarInfo('../outside'); item.size = 3
            stream.addfile(item, io.BytesIO(b'bad'))
        with self.assertRaises(RuntimeError):
            theme.extract_icons(archive, self.root / 'extract')
        self.assertFalse((self.root / 'outside').exists())

    def test_bad_download_hash_never_installed(self):
        item = {'file': 'test.bin', 'sha256': '0' * 64, 'url': 'https://example.invalid/test'}
        with patch.object(theme.urllib.request, 'urlopen', return_value=io.BytesIO(b'wrong')):
            with self.assertRaises(RuntimeError):
                theme.cached_asset(item, theme.locations())
        self.assertEqual(list(theme.locations()['cache'].glob('*')), [])

    def test_offline_missing_cache_leaves_config_untouched(self):
        self.assertEqual(self.call('apply', '--offline', '--no-gsettings'), 1)
        self.assertFalse(self.config.exists())

    def test_symlink_kitty_not_overwritten(self):
        target = self.root / 'real-kitty'; target.write_text('keep-me')
        (self.config / 'kitty').mkdir(parents=True)
        (self.config / 'kitty/kitty.conf').symlink_to(target)
        self.assertEqual(self.call('apply', '--no-assets', '--no-gsettings'), 1)
        self.assertEqual(target.read_text(), 'keep-me')

    def test_partial_write_failure_rolls_back(self):
        kitty = self.write('kitty/kitty.conf', 'original\n')
        real = theme.atomic
        fired = False
        def failing(path, data, mode=0o644):
            nonlocal fired
            if str(path).endswith('CosmicTheme.Dark/v2/background') and not fired:
                fired = True
                raise OSError('simulated failure')
            return real(path, data, mode)
        with patch.object(theme, 'atomic', side_effect=failing):
            self.assertEqual(self.call('apply', '--no-assets', '--no-gsettings'), 1)
        self.assertTrue(fired)
        self.assertEqual(kitty.read_text(), 'original\n')
        self.assertFalse((self.config / 'cosmic/com.system76.CosmicTheme.Dark/v2/accent').exists())

    def test_preferences_failure_rolls_back(self):
        kitty = self.write('kitty/kitty.conf', 'original preferences\n')
        prefs = {'font-name': {'before': "'Old Font 11'", 'desired': 'Iosevka Nerd Font 11'}}
        def fake_run(args):
            if args[:2] == ['gsettings', 'set'] and args[-1] == 'Iosevka Nerd Font 11':
                return theme.subprocess.CompletedProcess(args, 1, '', 'simulated preference failure')
            return theme.subprocess.CompletedProcess(args, 0, "'Old Font 11'\n", '')
        with patch.object(theme, 'preferences', return_value=prefs), patch.object(theme, 'run', side_effect=fake_run) as runner:
            self.assertEqual(self.call('apply', '--no-assets'), 1)
        self.assertEqual(kitty.read_text(), 'original preferences\n')
        self.assertTrue(any(call.args[0][-1] == "'Old Font 11'" for call in runner.call_args_list))

    def test_offline_assets_install_from_verified_cache(self):
        # Small fixtures exercise the installer/extractor, without network or desktop changes.
        fake_root = self.root / 'package'; (fake_root / 'assets').mkdir(parents=True)
        archive = self.root / 'icons.tar'
        content = b'[Icon Theme]\nName=Tokyo Night\nInherits=breeze,hicolor\n'
        with tarfile.open(archive, 'w') as stream:
            item = tarfile.TarInfo('TokyoNight-SE/index.theme'); item.size = len(content)
            stream.addfile(item, io.BytesIO(content))
        blobs = [('icons.tar', archive.read_bytes()), ('font.ttf', b'font fixture')]
        items = []
        paths = theme.locations(); paths['cache'].mkdir(parents=True)
        for name, data in blobs:
            digest = theme.hashlib.sha256(data).hexdigest()
            item = {'file': name, 'sha256': digest, 'url': 'https://example.invalid/' + name}
            (paths['cache'] / (digest + '-' + name)).write_bytes(data); items.append(item)
        (fake_root / 'assets/sources.json').write_text(json.dumps({'icons': items[0], 'fonts': [items[1]]}))
        def fake_run(args):
            return theme.subprocess.CompletedProcess(args, 0, 'Other Font', '')
        with patch.object(theme, 'ROOT', fake_root), patch.object(theme, 'run', side_effect=fake_run), patch.object(theme.urllib.request, 'urlopen', side_effect=AssertionError('offline network')):
            installed = theme.assets(paths, offline=True)
        self.assertEqual(len(installed), 2)
        self.assertIn('Inherits=Cosmic,breeze,hicolor', (paths['data'] / 'icons/TokyoNight-SE/index.theme').read_text())
        self.assertEqual((paths['data'] / 'fonts/cosmic-tokyo-night/font.ttf').read_bytes(), b'font fixture')

    def test_reversed_kitty_markers_do_not_write(self):
        kitty = self.write('kitty/kitty.conf', theme.END + '\n' + theme.START + '\n')
        old = kitty.read_text()
        self.assertEqual(self.call('apply', '--no-assets', '--no-gsettings'), 1)
        self.assertEqual(kitty.read_text(), old)
        self.assertFalse((self.config / 'cosmic/com.system76.CosmicTheme.Dark/v2/accent').exists())

    def test_malformed_panel_list_does_not_write(self):
        self.write('cosmic/com.system76.CosmicPanel/v1/entries', 'unexpected-format')
        self.assertEqual(self.call('apply', '--no-assets', '--no-gsettings'), 1)
        self.assertFalse((self.config / 'kitty').exists())


if __name__ == '__main__':
    unittest.main()
