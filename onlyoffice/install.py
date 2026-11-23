#!/usr/bin/env python3
"""Optional ONLYOFFICE interface theme. Independent of the COSMIC installer."""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent
NAME = 'tokyo-night-day.json'
APP = 'org.onlyoffice.desktopeditors'


def atomic(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError(f'Link simbólico preservado: {path}')
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def theme_value(text):
    section = None
    for line in text.splitlines():
        if line.strip().startswith('['):
            section = line.strip()
        elif section == '[General]' and line.startswith('UITheme='):
            return line.split('=', 1)[1]
    return None


def with_theme(text, value):
    # Only this QSettings key changes; unrelated settings and comments survive.
    lines = text.splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if l.strip() == '[General]'), None)
    if start is None:
        return text + ('\n' if text and not text.endswith('\n') else '') + ('[General]\nUITheme=' + value + '\n' if value is not None else '')
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip().startswith('[')), len(lines))
    found = [i for i in range(start + 1, end) if lines[i].startswith('UITheme=')]
    if len(found) > 1:
        raise ValueError('UITheme duplicado; preferências preservadas.')
    if found:
        lines[found[0]] = 'UITheme=' + value + '\n' if value is not None else ''
    elif value is not None:
        lines.insert(start + 1, 'UITheme=' + value + '\n')
    return ''.join(lines)


def locations(target):
    flat = Path.home() / '.var/app' / APP
    if target == 'auto':
        target = 'flatpak' if flat.exists() else 'native'
    if target == 'flatpak':
        if not flat.exists():
            raise ValueError('Perfil Flatpak ausente. Abra ONLYOFFICE uma vez ou escolha --target native.')
        data, config = flat / 'data', flat / 'config'
    else:
        data = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
        config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    return data / 'onlyoffice/desktopeditors/uithemes' / NAME, config / 'onlyoffice/DesktopEditors.conf'


def state_dir():
    return Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'tokyo-night-onlyoffice'


def install(target, select):
    source = (ROOT / NAME).read_bytes()
    theme = json.loads(source)
    if theme.get('id') != 'theme-tokyo-night-day' or theme.get('type') != 'light' or not theme.get('colors'):
        raise ValueError('Tema inválido.')
    path, config = locations(target)
    if path.is_symlink() or config.is_symlink():
        raise ValueError('Configuração vinculada; nenhum arquivo alterado.')
    text = config.read_text() if config.exists() else ''
    selection = str(path.resolve())
    updated = with_theme(text, selection) if select else text
    if path.exists() and path.read_bytes() == source and updated == text:
        print('Tema já instalado; backup anterior preservado.')
        return
    record = {'theme_path': str(path), 'config_path': str(config),
              'theme_before': base64.b64encode(path.read_bytes()).decode() if path.exists() else None,
              'theme_mode': path.stat().st_mode & 0o777 if path.exists() else 0o644,
              'theme_after': hashlib.sha256(source).hexdigest(), 'selected': select,
              'selection_before': theme_value(text), 'selection_after': selection, 'status': 'preparing'}
    backup = state_dir() / 'backups' / (dt.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]) / 'manifest.json'
    atomic(backup, json.dumps(record, indent=2).encode())
    try:
        atomic(path, source, record['theme_mode'])
        if updated != text:
            atomic(config, updated.encode(), config.stat().st_mode & 0o777 if config.exists() else 0o600)
    except Exception:
        if record['theme_before'] is None:
            path.unlink(missing_ok=True)
        else:
            atomic(path, base64.b64decode(record['theme_before']), record['theme_mode'])
        raise
    record['status'] = 'applied'
    atomic(backup, json.dumps(record, indent=2).encode())
    atomic(state_dir() / 'latest', str(backup).encode())
    print(f'Tema instalado: {path}\nBackup: {backup}')
    print('Preferência nativa gravada pelo caminho absoluto; isso não comprova a aplicação das cores no editor.' if select else 'Tema copiado sem alterar a preferência nativa.')
    print('No ONLYOFFICE: Configurações > Geral > Tema da interface. Selecione Claro e depois Tokyo Night Claro.')
    print('Nenhum documento foi fechado ou modificado. Associações de arquivos não são alteradas por este instalador.')


def restore():
    backup = Path((state_dir() / 'latest').read_text())
    r = json.loads(backup.read_text())
    if r.get('status') != 'applied':
        raise ValueError('Backup incompleto; inspecione antes de restaurar.')
    path, config = Path(r['theme_path']), Path(r['config_path'])
    text = config.read_text() if config.exists() else ''
    if r['selected']:
        value = theme_value(text)
        if value == r['selection_after']:
            atomic(config, with_theme(text, r['selection_before']).encode())
        elif value != r['selection_before']:
            print('Tema selecionado mudou depois; seleção atual preservada.')
            return
    if path.exists() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == r['theme_after']:
        if r['theme_before'] is None:
            path.unlink()
        else:
            atomic(path, base64.b64decode(r['theme_before']), r['theme_mode'])
    elif path.exists():
        print('JSON editado depois; arquivo atual preservado.')
    print('Restauração concluída. Reabra ONLYOFFICE normalmente.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'restore'])
    parser.add_argument('--target', choices=['auto', 'flatpak', 'native'], default='auto')
    parser.add_argument('--no-select', action='store_true', help='Copia somente o tema, sem mudar a seleção.')
    args = parser.parse_args()
    try:
        restore() if args.action == 'restore' else install(args.target, not args.no_select)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Erro: {error}\n')


if __name__ == '__main__':
    main()
