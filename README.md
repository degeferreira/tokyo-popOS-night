<p align="center">
  <img src="docs/images/logo.png" alt="TokyoNight — Pop!_OS" width="640" />
</p>

# Tokyo Pop!_OS Night

[Português](#português) · [English](#english)

![Tokyo Night: Arquivos e Kitty / Files and Kitty](docs/images/desktop.png)

## Português

Azul profundo e lilás: **Tokyo Night** no COSMIC.

- Painel fino e flutuante, dock sempre visível.
- Iosevka Nerd Font e ícones TokyoNight-SE.
- Borda azul de 2 px e mosaico com espaçamento de 10 px.
- Transparência nativa e cores harmonizadas.

Wallpaper, atalhos e shell preservados. Estilo do terminal exclusivo do **Kitty**; outros terminais mantêm suas configurações. Se ausente, o instalador avisa e oferece instalação e uso como padrão, opcionalmente.

**Instalar:** Pop!_OS 24.04 com COSMIC e Python 3.12+. Execute sem `sudo`. Fontes/ícones baixados na primeira aplicação; backup automático.

```sh
git clone https://github.com/degeferreira/tokyo-popOS-night.git
cd tokyo-popOS-night
python3 theme.py apply
```

**Restaurar**, no projeto:

```sh
python3 theme.py restore
```

[Opções, compatibilidade e backups](docs/advanced.md)

## English

Deep blues and lilac. **Tokyo Night** meets COSMIC.

- Slim floating panel and an always-visible dock.
- Iosevka Nerd Font and TokyoNight-SE icons.
- Blue 2 px focus border and 10 px tiling gaps.
- Native transparency and matching colors.

Wallpaper, shortcuts, and shell preserved. Terminal styling is **Kitty-only**. Other terminals keep their settings. If missing, the installer warns and optionally offers installation and default-terminal setup.

**Install:** Pop!_OS 24.04 with COSMIC and Python 3.12+. Run the commands above without `sudo`. Fonts/icons download on first use; automatic backup.

**Restore:** run `python3 theme.py restore` from this folder.

[Advanced guide (Portuguese)](docs/advanced.md) · [Credits / Créditos](ATTRIBUTION.md) · [MIT](LICENSE)
