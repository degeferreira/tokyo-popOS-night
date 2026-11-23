# Tokyo Night Claro para ONLYOFFICE

[English](README.en.md) · [Voltar ao tema COSMIC](../README.md)

Um complemento opcional: superfícies claras em azul e lavanda, texto azul-acinzentado, azul profundo nos botões e lilás nos destaques. A página continua branca; o tema não muda fontes, estilos, cores ou conteúdo dos documentos.

Não faz parte de `theme.py apply`. Não altera o tema do sistema, o terminal ou as associações de arquivos.

## Instalar

Requisitos: ONLYOFFICE Desktop Editors com suporte a temas locais (8.0+), Linux e Python 3.12+. Configuração verificada no Flatpak 9.4.0; instalações nativas usam o mesmo formato, mas não foram verificadas visualmente.

Salve seus documentos e feche normalmente o ONLYOFFICE antes de instalar. Na raiz deste repositório, sem `sudo`:

```sh
python3 onlyoffice/install.py install
```

Abra novamente o ONLYOFFICE. O tema **Tokyo Night Claro / Tokyo Night Day** estará selecionado. O instalador detecta o perfil Flatpak primeiro; para escolher explicitamente:

```sh
python3 onlyoffice/install.py install --target flatpak
# ou, para pacote nativo/AppImage:
python3 onlyoffice/install.py install --target native
```

O JSON vai para `onlyoffice/desktopeditors/uithemes/` dentro dos dados do usuário; a seleção usa a chave `UITheme` do arquivo `onlyoffice/DesktopEditors.conf`. O Flatpak guarda ambos sob `~/.var/app/org.onlyoffice.desktopeditors/`. Nenhum arquivo interno do aplicativo é modificado, nem é necessário liberar permissões adicionais ao Flatpak.

## Importação manual

Em **Configurações → Geral → Tema da interface → Adicionar tema local**, escolha [tokyo-night-day.json](tokyo-night-day.json). Também pode selecioná-lo em **Exibir → Tema da interface**. Os nomes dos menus variam com o idioma/versão. Para copiar sem selecionar automaticamente:

```sh
python3 onlyoffice/install.py install --no-select
```

## Restaurar

Feche normalmente o ONLYOFFICE e execute:

```sh
python3 onlyoffice/install.py restore
```

Reabra o aplicativo. O backup fica em `${XDG_STATE_HOME:-~/.local/state}/tokyo-night-onlyoffice/backups/`. Apenas o JSON do tema e a seleção anterior são recuperados; outras preferências são preservadas. Se o JSON ou a seleção tiverem sido alterados depois, o instalador preserva essas edições. A restauração não muda associações de arquivos.

## Abrir DOCX e DOC por padrão (opcional)

Para a versão Flatpak, se desejar:

```sh
xdg-mime default org.onlyoffice.desktopeditors.desktop application/vnd.openxmlformats-officedocument.wordprocessingml.document
xdg-mime default org.onlyoffice.desktopeditors.desktop application/msword
```

Para pacote nativo, use o identificador `.desktop` instalado pela sua distribuição. Esse passo é independente do tema.

## Referências e limites

Formato baseado na [documentação oficial de temas](https://api.onlyoffice.com/docs/desktop-editors/usage-api/customizing-themes/) e no carregador nativo [CThemes](https://github.com/ONLYOFFICE/desktop-apps/blob/master/win-linux/src/cthemes.cpp). A [importação local](https://helpcenter.onlyoffice.com/desktop/getting-started) é oferecida pelo próprio aplicativo. Paleta própria inspirada no [Tokyo Night Day](https://github.com/folke/tokyonight.nvim), sem copiar o código dos projetos. Mantém a licença MIT do repositório; ONLYOFFICE conserva seus próprios termos e marcas.

O tema cobre a interface nativa e os editores que respeitam os papéis oficiais de cores. Plugins, diálogos do sistema e futuras versões podem usar cores próprias. Não altera páginas impressas/exportadas, nem oferece transparência para documentos.
