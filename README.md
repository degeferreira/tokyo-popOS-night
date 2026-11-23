<p align="center">
  <img src="docs/images/logo.png" alt="TokyoNight — Pop!_OS" width="640" />
</p>

# Tokyo Pop!_OS Night

[English](README.en.md)

![Arquivos e Kitty com Tokyo Night](docs/images/desktop.png)

Azul profundo e lilás: **Tokyo Night** no COSMIC.

- Painel fino e flutuante, dock sempre visível.
- Iosevka Nerd Font e ícones TokyoNight-SE.
- Borda azul de 2 px e mosaico com espaçamento de 10 px.
- Transparência nativa e cores harmonizadas.

Papel de parede, atalhos e shell preservados. Estilo do terminal exclusivo do **Kitty**; outros terminais mantêm suas configurações. Se ausente, o instalador avisa e oferece instalação e uso como padrão, opcionalmente.

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

[Opções, compatibilidade e backups](docs/advanced.md) · [Créditos](ATTRIBUTION.md) · [MIT](LICENSE)

Opcional: [Tokyo Night Claro para ONLYOFFICE](onlyoffice/README.md), com instalação separada.
