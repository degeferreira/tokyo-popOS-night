import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('onlyoffice_theme', Path(__file__).parents[1] / 'onlyoffice/install.py')
oo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oo)


class OnlyofficeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.target = self.root / 'data/uithemes/tokyo-night-day.json'
        self.config = self.root / 'config/DesktopEditors.conf'
        self.config.parent.mkdir()
        self.original = '[General]\nUITheme=theme-light\nOther=value\n\n[Section]\nKeep=yes\n'
        self.config.write_text(self.original)
        for patcher in [patch.object(oo, 'locations', return_value=(self.target, self.config)), patch.object(oo, 'state_dir', return_value=self.root / 'state'), patch('sys.stdout', new_callable=io.StringIO)]:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_install_reapply_restore_preserves_other_preferences(self):
        oo.install('flatpak', True)
        self.assertEqual(oo.theme_value(self.config.read_text()), str(self.target.resolve()))
        latest = (self.root / 'state/latest').read_text()
        oo.install('flatpak', True)
        self.assertEqual((self.root / 'state/latest').read_text(), latest)
        self.config.write_text(self.config.read_text().replace('Other=value', 'Other=changed-later'))
        oo.restore()
        self.assertEqual(self.config.read_text(), self.original.replace('Other=value', 'Other=changed-later'))
        self.assertFalse(self.target.exists())

    def test_no_select_keeps_theme_and_existing_json_restores(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b'previous-json')
        oo.install('flatpak', False)
        self.assertEqual(self.config.read_text(), self.original)
        oo.restore()
        self.assertEqual(self.target.read_bytes(), b'previous-json')

    def test_later_selection_preserved(self):
        oo.install('native', True)
        self.config.write_text(oo.with_theme(self.config.read_text(), 'theme-dark'))
        oo.restore()
        self.assertEqual(oo.theme_value(self.config.read_text()), 'theme-dark')
        self.assertTrue(self.target.exists())

    def test_symlink_refused_before_changes(self):
        self.target.parent.mkdir(parents=True)
        real = self.root / 'real'; real.write_text('keep')
        self.target.symlink_to(real)
        with self.assertRaises(ValueError):
            oo.install('native', True)
        self.assertEqual(real.read_text(), 'keep')
        self.assertEqual(self.config.read_text(), self.original)

    def test_theme_is_light_with_readable_key_pairs(self):
        d = json.loads((oo.ROOT / oo.NAME).read_text())
        self.assertEqual(d['type'], 'light')
        self.assertEqual(d['colors']['canvas-content-background'], '#ffffff')
        def luminance(color):
            values = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            return sum(w * (v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4) for w, v in zip((.2126, .7152, .0722), values))
        for fg, bg in [('text-normal', 'background-normal'), ('text-secondary', 'background-normal'), ('text-inverse', 'background-primary-dialog-button'), ('text-toolbar-header', 'toolbar-header-document'), ('text-pretty', 'brand-word')]:
            a, b = sorted([luminance(d['colors'][fg]), luminance(d['colors'][bg])])
            self.assertGreaterEqual((b + .05) / (a + .05), 4.5, (fg, bg))

    def test_native_and_web_header_roles_agree(self):
        colors = json.loads((oo.ROOT / oo.NAME).read_text())['colors']
        for native, web in [('brand-word', 'toolbar-header-document'), ('brand-cell', 'toolbar-header-spreadsheet'), ('brand-slide', 'toolbar-header-presentation'), ('brand-pdf', 'toolbar-header-pdf'), ('brand-draw', 'toolbar-header-visio')]:
            self.assertEqual(colors[native], colors[web], (native, web))
        self.assertEqual(colors['text-pretty'], colors['text-toolbar-header'])

    def test_document_tab_labels_contrast_inactive_hover_and_active(self):
        c = json.loads((oo.ROOT / oo.NAME).read_text())['colors']
        def lum(h):
            v = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
            return sum(w * (x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4) for w, x in zip((.2126, .7152, .0722), v))
        # CTabBar 9.4 uses this text role for inactive tabs as well as light active tabs.
        for fg, bg in [('tab-simple-active-text', 'window-background'), ('tab-simple-active-text', 'tool-button-hover-background'), ('text-inverse', 'brand-word'), ('tab-simple-active-text', 'tab-simple-active-background')]:
            a,b = sorted((lum(c[fg]),lum(c[bg])))
            self.assertGreaterEqual((b+.05)/(a+.05),7,(fg,bg))
        self.assertEqual(c['tab-editor-theme-type'],'dark')
