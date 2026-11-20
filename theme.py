#!/usr/bin/env python3
"""Portable COSMIC Tokyo Night preset installer (Python 3.12+, standard library)."""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent
SYSTEM_DATA = Path('/usr/share/cosmic')
START = '# BEGIN cosmic-tokyo-night'
END = '# END cosmic-tokyo-night'
FONT = 'Iosevka Nerd Font'
DEFAULT_ONLY = {'name', 'plugins_center', 'plugins_wings', 'keyboard_interactivity', 'layer'}


def xdg(name, fallback):
    value = os.environ.get(name)
    return Path(value).expanduser() if value else Path.home() / fallback


def locations():
    return {
        'config': xdg('XDG_CONFIG_HOME', '.config'),
        'data': xdg('XDG_DATA_HOME', '.local/share'),
        'state': xdg('XDG_STATE_HOME', '.local/state') / 'cosmic-tokyo-night',
        'cache': xdg('XDG_CACHE_HOME', '.cache') / 'cosmic-tokyo-night',
    }


def run(args):
    return subprocess.run(args, text=True, capture_output=True, timeout=30)


def snapshot(path):
    if path.is_symlink():
        return {'type': 'symlink', 'target': os.readlink(path)}
    if path.exists():
        if not path.is_file():
            raise RuntimeError(f'Esperado arquivo: {path}')
        return {'type': 'file', 'data': base64.b64encode(path.read_bytes()).decode(),
                'mode': path.stat().st_mode & 0o777}
    return None


def atomic(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.tokyo-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def put_state(path, state):
    if state is None:
        if path.is_file() or path.is_symlink():
            path.unlink()
    elif state['type'] == 'symlink':
        if path.is_file() or path.is_symlink():
            path.unlink()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(state['target'])
    else:
        atomic(path, base64.b64decode(state['data']), state['mode'])


def compatibility():
    for name, version in [('com.system76.CosmicTheme.Dark', 2),
                          ('com.system76.CosmicTheme.Dark.Builder', 2),
                          ('com.system76.CosmicPanel.Panel', 1)]:
        folder = SYSTEM_DATA / name
        versions = [int(p.name[1:]) for p in folder.glob('v[0-9]*')
                    if p.is_dir() and p.name[1:].isdigit()]
        if not versions or max(versions) != version:
            raise RuntimeError(f'Formato não suportado em {folder}: {versions}; esperado v{version}. '
                               'Nenhuma configuração foi aplicada. Consulte o README.')
    checksums = json.loads((ROOT / 'preset/checksums.json').read_text())
    for rel, digest in checksums.items():
        path = ROOT / 'preset' / rel
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f'Preset alterado/corrompido: {rel}')


def cached_asset(item, paths, offline=False):
    cache = paths['cache'] / (item['sha256'] + '-' + item['file'])
    if cache.is_file() and hashlib.sha256(cache.read_bytes()).hexdigest() == item['sha256']:
        return cache
    if offline:
        raise RuntimeError(f'Ativo ausente ou inválido no cache: {item["file"]}. Execute download-assets antes.')
    if not item['url'].startswith('https://'):
        raise RuntimeError('Apenas ativos HTTPS são aceitos.')
    paths['cache'].mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(item['url'], timeout=60) as response:
        data = response.read(130 * 1024 * 1024)
    if hashlib.sha256(data).hexdigest() != item['sha256']:
        raise RuntimeError(f'SHA-256 incorreto: {item["file"]}; download descartado.')
    atomic(cache, data)
    return cache


def extract_icons(archive, destination):
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        if len(members) > 60000 or sum(m.size for m in members) > 256 * 1024 * 1024:
            raise RuntimeError('Arquivo de ícones excede os limites esperados.')
        for member in members:
            parts = Path(member.name).parts
            if not parts or parts[0] != 'TokyoNight-SE' or '..' in parts or member.name.startswith('/'):
                raise RuntimeError(f'Caminho inseguro no arquivo: {member.name}')
        tar.extractall(destination, members=members, filter='data')


def assets(paths, offline=False):
    sources = json.loads((ROOT / 'assets/sources.json').read_text())
    icon_dir = paths['data'] / 'icons/TokyoNight-SE'
    font_dir = paths['data'] / 'fonts/cosmic-tokyo-night'
    font_found = False
    if shutil.which('fc-match'):
        match = run(['fc-match', '--format=%{family}', FONT])
        font_found = match.returncode == 0 and FONT in match.stdout.split(',')
    # Download and validate all required inputs before installing any asset.
    icon_source = None if (icon_dir / 'index.theme').is_file() else cached_asset(sources['icons'], paths, offline)
    font_sources = [] if font_found else [(item, cached_asset(item, paths, offline)) for item in sources['fonts']]
    installed = []
    if icon_source:
        if icon_dir.exists():
            raise RuntimeError(f'Diretório de ícones existente sem index.theme: {icon_dir}')
        icon_dir.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.tokyo-', dir=icon_dir.parent) as tmp:
            extract_icons(icon_source, Path(tmp))
            staged = Path(tmp) / 'TokyoNight-SE'
            index = staged / 'index.theme'
            text = index.read_text()
            text = re.sub(r'^Inherits=(.*)$', r'Inherits=Cosmic,\1', text, flags=re.M)
            index.write_text(text)
            staged.rename(icon_dir)
        installed.append(str(icon_dir))
        if shutil.which('gtk-update-icon-cache'):
            run(['gtk-update-icon-cache', '-f', '-t', str(icon_dir)])
    if font_sources:
        if font_dir.exists():
            if any(not (font_dir / item['file']).is_file() or
                   hashlib.sha256((font_dir / item['file']).read_bytes()).hexdigest() != item['sha256']
                   for item, _ in font_sources):
                raise RuntimeError(f'Fontes existentes diferentes: {font_dir}; nada será sobrescrito.')
        else:
            font_dir.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.tokyo-', dir=font_dir.parent) as tmp:
                staged = Path(tmp) / 'font'; staged.mkdir()
                for item, source in font_sources:
                    shutil.copy2(source, staged / item['file'])
                staged.rename(font_dir)
            installed.append(str(font_dir))
        if shutil.which('fc-cache'):
            run(['fc-cache', '-f', str(font_dir)])
    return installed


def panel_entries(text):
    # RON list of strings. Refuse unfamiliar syntax instead of discarding custom panels.
    clean = re.sub(r'//[^\n]*', '', text).strip()
    if not clean.startswith('[') or not clean.endswith(']'):
        raise RuntimeError('Lista de painéis desconhecida; preservada sem alteração.')
    tokens = re.findall(r'"(?:[^"\\]|\\.)*"', clean)
    remainder = re.sub(r'"(?:[^"\\]|\\.)*"', '', clean[1:-1])
    if remainder.strip(' ,\n\r\t'):
        raise RuntimeError('Formato da lista de painéis não reconhecido.')
    entries = [json.loads(t) for t in tokens]
    for name in ['Panel', 'Dock']:
        if name not in entries:
            entries.append(name)
    return json.dumps(entries) + '\n'


def kitty_available():
    return shutil.which('kitty') is not None


def terminal_setup(args):
    if kitty_available():
        return False
    print('Aviso: Kitty não encontrado. O tema do COSMIC será aplicado normalmente; '
          'cores, abas e transparência do terminal são exclusivas do Kitty. '
          'Outros terminais mantêm sua configuração.')
    if args.dry_run or args.offline or not sys.stdin.isatty() or not sys.stdout.isatty():
        print('Para usar o preset do terminal, instale Kitty e reaplique o tema: sudo apt install kitty')
        return False
    if input('Instalar Kitty pelo APT agora? / Install Kitty using APT? [s/y/N] ').strip().lower() not in ('s', 'y', 'sim', 'yes'):
        return False
    if not shutil.which('apt'):
        print('Aviso: APT indisponível. Instale Kitty manualmente; o tema continuará sem ele.')
        return False
    command = ['apt', 'install', 'kitty']
    if os.geteuid() != 0:
        if not shutil.which('sudo'):
            print('Aviso: sudo indisponível. Instale Kitty manualmente.')
            return False
        command.insert(0, 'sudo')
    try:
        result = subprocess.run(command, check=False)
    except OSError as error:
        print(f'Aviso: não foi possível instalar Kitty: {error}. Continuando com o tema.')
        return False
    if result.returncode or not kitty_available():
        print('Aviso: Kitty não foi instalado. Continuando com o tema do COSMIC.')
        return False
    return input('Usar Kitty como terminal padrão do COSMIC (Super+T)? / Set as COSMIC default? [s/y/N] ').strip().lower() in ('s', 'y', 'sim', 'yes')


def plan(paths, no_assets=False, default_terminal=False):
    planned = {}
    for source in sorted((ROOT / 'preset/cosmic').rglob('*')):
        if not source.is_file():
            continue
        rel = source.relative_to(ROOT / 'preset/cosmic')
        if no_assets and rel.parts[0] == 'com.system76.CosmicTk' and source.name != 'apply_theme_global':
            continue
        target = paths['config'] / 'cosmic' / rel
        if source.name in DEFAULT_ONLY and target.exists():
            continue
        if target.is_symlink():
            raise RuntimeError(f'Configuração vinculada: {target}; preserve/ajuste o link antes de aplicar.')
        planned[target] = source.read_bytes()
    entry = paths['config'] / 'cosmic/com.system76.CosmicPanel/v1/entries'
    planned[entry] = panel_entries(entry.read_text() if entry.exists() else '[]').encode()
    if default_terminal:
        action = paths['config'] / 'cosmic/com.system76.CosmicSettings.Shortcuts/v1/system_actions'
        if action.is_symlink():
            print('Aviso: terminal padrão preservado: configuração vinculada.')
        else:
            text = action.read_text() if action.exists() else '{}'
            pattern = r'(?m)^(\s*Terminal:\s*)"(?:[^"\\]|\\.)*"'
            if len(re.findall(pattern, text)) == 1:
                planned[action] = re.sub(pattern, lambda m: m[1] + '"kitty"', text).encode()
            elif 'Terminal:' not in text and text.strip().startswith('{') and text.strip().endswith('}'):
                end = text.rfind('}')
                prefix = text[:end].rstrip()
                if not prefix.endswith(('{', ',')):
                    prefix += ','
                planned[action] = (prefix + '\n    Terminal: "kitty",\n' + text[end:]).encode()
            else:
                print('Aviso: formato de terminal padrão desconhecido; preservado.')
    if not kitty_available():
        return planned
    kitty = paths['config'] / 'kitty'
    planned[kitty / 'cosmic-tokyo-night-colors.conf'] = (ROOT / 'preset/kitty/colors.conf').read_bytes()
    style = (ROOT / 'preset/kitty/style.conf').read_text()
    if no_assets:
        style = '\n'.join(l for l in style.splitlines() if not l.startswith('font_family')) + '\n'
    planned[kitty / 'cosmic-tokyo-night-style.conf'] = style.encode()
    config = kitty / 'kitty.conf'
    if config.is_symlink():
        raise RuntimeError('kitty.conf é um link simbólico; ajuste-o antes de aplicar.')
    text = config.read_text() if config.exists() else ''
    if (text.count(START) != text.count(END) or text.count(START) > 1
            or (START in text and text.index(START) > text.index(END))):
        raise RuntimeError('Bloco gerenciado do Kitty inválido; nenhuma alteração aplicada.')
    text = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n?', '', text, flags=re.S)
    block = START + '\ninclude ./cosmic-tokyo-night-colors.conf\ninclude ./cosmic-tokyo-night-style.conf\n' + END + '\n'
    planned[config] = (text.rstrip('\n') + '\n\n' + block).lstrip('\n').encode()
    return planned


def preferences(enabled):
    if not enabled or not shutil.which('gsettings'):
        return {}
    values = {'font-name': 'Iosevka Nerd Font 11', 'monospace-font-name': 'Iosevka Nerd Font 11',
              'icon-theme': 'TokyoNight-SE'}
    result = {}
    for key, value in values.items():
        current = run(['gsettings', 'get', 'org.gnome.desktop.interface', key])
        if current.returncode == 0:
            result[key] = {'before': current.stdout.strip(), 'desired': value}
    return result


def exports(paths):
    config = paths['config']
    return [config / p for p in ['gtk-3.0/gtk.css', 'gtk-4.0/gtk.css',
            'gtk-4.0/cosmic/dark.css', 'gtk-4.0/cosmic/light.css',
            'qt5ct/colors/CosmicDark.conf', 'qt6ct/colors/CosmicDark.conf',
            'qt5ct/qt5ct.conf', 'qt6ct/qt6ct.conf']]


def save_manifest(path, data):
    atomic(path, (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode(), 0o600)


def apply(args):
    compatibility()
    paths = locations()
    default_terminal = terminal_setup(args)
    planned = plan(paths, args.no_assets, default_terminal)
    prefs = preferences(not (args.no_gsettings or args.no_assets))
    if args.dry_run:
        print(f'Compatível. {len(planned)} arquivos previstos; {len(prefs)} preferências GTK. Nenhum arquivo alterado.')
        print('Fontes/ícones: ' + ('não selecionados (--no-assets).' if args.no_assets else 'reutilizados se presentes; download com SHA-256 se ausentes.'))
        return
    installed = [] if args.no_assets else assets(paths, args.offline)
    candidates = list(dict.fromkeys([*planned, *exports(paths)]))
    states = {str(p): snapshot(p) for p in candidates}
    ident = dt.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
    backup = paths['state'] / 'backups' / ident / 'manifest.json'
    record = {'version': 1, 'status': 'preparing', 'config_home': str(paths['config']),
              'files': [{'path': str(p), 'before': states[str(p)], 'after': None} for p in candidates],
              'gsettings': prefs, 'installed_assets': installed}
    # Back up before writing. Unchanged files are filtered after the native daemon settles.
    save_manifest(backup, record)
    try:
        for path, content in planned.items():
            before = states[str(path)]
            atomic(path, content, before.get('mode', 0o644) if before else 0o644)
        for key, item in prefs.items():
            response = run(['gsettings', 'set', 'org.gnome.desktop.interface', key, item['desired']])
            if response.returncode:
                raise RuntimeError(response.stderr.strip() or f'Falha ao gravar preferência {key}')
            item['after'] = run(['gsettings', 'get', 'org.gnome.desktop.interface', key]).stdout.strip()
        time.sleep(1)
        for path, content in planned.items():
            if path.read_bytes() != content:
                raise RuntimeError(f'Verificação após gravação falhou: {path}')
        record['status'] = 'applied'
    except Exception:
        # Roll back the transaction; downloaded assets may remain available but unselected.
        for path in reversed(candidates):
            put_state(path, states[str(path)])
        for key, item in prefs.items():
            run(['gsettings', 'set', 'org.gnome.desktop.interface', key, item['before']])
        record['status'] = 'rolled-back'
        save_manifest(backup, record)
        raise
    for item in record['files']:
        item['after'] = snapshot(Path(item['path']))
    record['files'] = [item for item in record['files'] if item['before'] != item['after']]
    record['gsettings'] = {k: v for k, v in prefs.items() if v['before'] != v.get('after')}
    save_manifest(backup, record)
    if not record['files'] and not record['gsettings']:
        print('Tema já aplicado; backup anterior preservado.')
        return
    atomic(paths['state'] / 'latest', str(backup).encode(), 0o600)
    print(f'Tema aplicado. Backup: {backup}')
    print('Cores são atualizadas pelo COSMIC. Aplicativos abertos podem precisar ser reabertos para carregar fontes.')


def restore(args):
    paths = locations()
    backup = Path(args.backup).expanduser() if args.backup else Path((paths['state'] / 'latest').read_text())
    record = json.loads(backup.read_text())
    if record.get('version') != 1 or record.get('status') != 'applied':
        raise RuntimeError('Backup inválido ou transação não concluída.')
    eligible, skipped = [], []
    for item in record['files']:
        now = snapshot(Path(item['path']))
        if now == item['before']:
            continue
        (eligible if now == item['after'] else skipped).append(item)
    prefs = []
    for key, item in record.get('gsettings', {}).items():
        current = run(['gsettings', 'get', 'org.gnome.desktop.interface', key])
        if current.returncode == 0 and current.stdout.strip() == item.get('after'):
            prefs.append((key, item['before']))
    print(f'{len(eligible)} arquivos e {len(prefs)} preferências para restaurar; {len(skipped)} edições posteriores preservadas.')
    for item in skipped:
        print('PRESERVADO:', item['path'])
    if args.dry_run:
        return
    # Restore config before files produced by the native export daemon.
    config_home = Path(record['config_home'])
    direct = [i for i in eligible if Path(i['path']).is_relative_to(config_home / 'cosmic')
              or Path(i['path']).is_relative_to(config_home / 'kitty')]
    direct.sort(key=lambda i: ('com.system76.CosmicTheme.Mode' in i['path'], i['path']))
    for item in direct:
        put_state(Path(item['path']), item['before'])
    for key, value in prefs:
        result = run(['gsettings', 'set', 'org.gnome.desktop.interface', key, value])
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
    time.sleep(1)
    for item in eligible:
        if item not in direct:
            put_state(Path(item['path']), item['before'])
    print('Restauração concluída. Fontes/ícones permanecem instalados, mas as seleções anteriores foram restauradas.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor', help='Verifica os formatos instalados, sem alterar configurações.')
    apply_parser = sub.add_parser('apply', help='Aplica o preset com backup automático.')
    for flag in ['dry-run', 'offline', 'no-assets', 'no-gsettings']:
        apply_parser.add_argument('--' + flag, action='store_true')
    restore_parser = sub.add_parser('restore', help='Restaura o último backup ou um backup informado.')
    restore_parser.add_argument('--backup')
    restore_parser.add_argument('--dry-run', action='store_true')
    download_parser = sub.add_parser('download-assets', help='Prepara o cache para instalação offline.')
    download_parser.add_argument('--offline', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'doctor':
            compatibility()
            print('Compatível: COSMIC Theme v2 / Panel v1. Preset íntegro.')
        elif args.command == 'apply':
            apply(args)
        elif args.command == 'restore':
            restore(args)
        else:
            paths = locations(); sources = json.loads((ROOT / 'assets/sources.json').read_text())
            for item in [sources['icons'], *sources['fonts']]:
                print(cached_asset(item, paths, args.offline))
    except (OSError, ValueError, RuntimeError, tarfile.TarError, subprocess.SubprocessError) as error:
        print(f'Erro: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
