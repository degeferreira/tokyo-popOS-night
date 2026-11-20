# Tokyo Pop!_OS Night

Preset pessoal para **Pop!_OS 24.04 / COSMIC**, inspirado no Tokyo Night: painel superior fino e flutuante, dock inferior visível, mosaico com gaps de 10 px, contorno azul na janela ativa, fonte Iosevka Nerd Font e ícones TokyoNight-SE.

O pacote aplica as configurações do usuário com backup automático. Não exige `sudo`, Rust, Waybar, PPAs ou outro compositor. Fontes e ícones são obtidos dos projetos originais, com versões fixadas e verificação SHA-256; nenhum instalador remoto é executado.

## Aplicar após reinstalar

1. Instale normalmente o Pop!_OS com COSMIC e entre na sessão.
2. Clone este repositório ou baixe e extraia seu ZIP.
3. Para clonar e aplicar, execute (se já extraiu o ZIP, use apenas os dois comandos `python3` dentro da pasta extraída):

```sh
git clone https://github.com/degeferreira/tokyo-popOS-night.git
cd tokyo-popOS-night
python3 theme.py doctor
python3 theme.py apply
```

Requisitos: **Python 3.12 ou superior**, COSMIC com **Theme v2 e Panel v1**; esses são os formatos verificados pelo instalador. A validação recusa versões de formato desconhecidas antes de alterar configurações. `fc-cache`/`fc-match` e `gsettings`, normalmente disponíveis no Pop!_OS, permitem atualizar o cache das fontes e integrar preferências GTK. A personalização do Kitty será utilizada se/quando ele estiver instalado; o instalador não muda o terminal padrão.

A primeira aplicação pode baixar aproximadamente **75 MB** de fontes e ícones. Ativos já disponíveis no usuário são reaproveitados. O restante do pacote é pequeno e não contém binários compilados. Aplicação, backup e restauração devem ser executados como seu usuário, **sem sudo**.

Para conferir o que será feito, sem gravar arquivos ou baixar ativos:

```sh
python3 theme.py apply --dry-run
```

O tema é recarregado pelos mecanismos nativos do COSMIC. Aplicativos já abertos podem precisar ser reabertos para carregar fontes novas. O instalador não reinicia o painel, o computador nem encerra a sessão. Se a fonte do painel permanecer em cache, entre novamente na sessão quando for conveniente.

## O que está incluído

| Componente | Configuração |
|---|---|
| Aparência | Tokyo Night escuro fixo; fundo `#1a1b26`, superfícies azul-marinho e texto azul-lilás |
| Janela ativa | Borda azul `#7aa2f7`, 2 px; cantos suavemente arredondados |
| Tiling | Ativado por área de trabalho; espaçamento interno 10 px |
| Painel superior | XS, cerca de 32 px a 100% de escala; margem 10 px, raio 12 px, opacidade 96% |
| Dock inferior | Sempre visível, centralizado e flutuante; margem 10 px, raio 14 px, tamanho S |
| Fontes | Iosevka Nerd Font na interface e terminal; Kitty a 11 pt |
| Ícones | TokyoNight-SE com fallback para ícones específicos do COSMIC |
| Kitty | Cores Tokyo Night, fundo opaco e margem interna de 10 px |
| GTK/Qt | Exportação das cores pelo próprio daemon COSMIC |

A lista de painéis mantém entradas adicionais e garante a presença de `Panel` e `Dock`. Ambos são configurados para **todas as telas**, sem nomes de monitores ou identificadores EDID. A disposição dos indicadores existentes é preservada; os indicadores padrão deste preset são usados somente onde a configuração ainda não existe.

**Não são exportados:** papel de parede, atalhos, aplicativos favoritos, teclado, shell, sessões, contas, monitores, histórico, capturas ou dados pessoais. O tema não altera as cores internas de páginas web nem aplicativos que imponham uma aparência própria. Indicadores com cores individuais e bordas em gradiente da Waybar/Hyprland não são reproduzidos por este preset nativo.

## Usar somente a aparência

Para aplicar cores, painel, dock e estilo do terminal sem baixar/selecionar fontes e ícones:

```sh
python3 theme.py apply --no-assets
```

Para não modificar preferências GTK via GSettings:

```sh
python3 theme.py apply --no-gsettings
```

Também existe **`tokyo-night.ron`**, para importar apenas a aparência no menu de importação de temas do COSMIC compatível. Ele não configura painel, dock, tiling, fontes ou ícones; para o conjunto completo, use `theme.py apply`.

## Instalação sem internet

Antes de ficar offline, prepare o cache:

```sh
python3 theme.py download-assets
```

O cache fica em `${XDG_CACHE_HOME:-~/.cache}/cosmic-tokyo-night/`. Guarde essa pasta junto do backup da reinstalação. Depois, restaure-a no mesmo local do novo usuário e execute:

```sh
python3 theme.py apply --offline
```

A opção offline nunca tenta baixar arquivos. Se um ativo obrigatório não estiver instalado nem no cache com o hash correto, o instalador para antes de gravar configurações. Os ícones/fontes continuam sujeitos às licenças de seus projetos; o repositório não redistribui esses ativos.

## Restaurar

Cada aplicação que efetivamente muda configurações cria um manifesto privado em:

```text
${XDG_STATE_HOME:-~/.local/state}/cosmic-tokyo-night/backups/<data-id>/manifest.json
```

O manifesto contém os originais, modos e links simbólicos, além dos valores de GSettings alterados. Não publique essa pasta: os originais podem conter suas preferências pessoais.

```sh
python3 theme.py restore --dry-run
python3 theme.py restore
```

Para escolher outra aplicação:

```sh
python3 theme.py restore --backup /caminho/do/manifest.json
```

A restauração compara o estado atual com o aplicado: arquivos editados depois são preservados e seus caminhos são informados. Arquivos novos deste preset são removidos; originais são restaurados. Fontes e ícones continuam instalados, mas deixam de ser selecionados. Configurações já restauradas são ignoradas. Uma reaplicação sem mudanças mantém o apontamento para o backup útil anterior.

Em caso de falha durante a gravação, o instalador tenta desfazer a transação imediatamente. Se o processo for interrompido abruptamente (por exemplo, falta de energia), os originais permanecem no manifesto `preparing`; nesse caso, inspecione esse manifesto antes de fazer recuperação manual. A restauração automática aceita somente transações concluídas.

## Publicar no GitHub

Publique **somente os arquivos desta pasta**, incluindo `preset/`, `assets/sources.json`, documentação, testes e `theme.py`. Não publique a pasta maior `cosmic-personalizacao/`, nem seus backups/capturas.

O repositório pode receber qualquer nome. Depois de cloná-lo, a aplicação continua sendo apenas `python3 theme.py apply`; nenhum caminho de usuário ou URL do seu futuro repositório está fixado no código.

Não é necessário incluir as fontes, o arquivo de ícones ou o cache no Git. O instalador os baixa diretamente dos autores. Nenhum repositório remoto é criado ou publicado automaticamente.

## Testes e compatibilidade

```sh
python3 -m unittest discover -s tests -v
```

Os testes usam diretórios XDG temporários e não modificam sua sessão. Cobrem aplicação/restauração, reaplicação, preservação de preferências, backups, links, formatos incompatíveis, downloads corrompidos, extração insegura, modo offline e falhas parciais. O GitHub Actions executa os testes em Python 3.12.

O preset foi extraído de Pop!_OS 24.04 com `cosmic-settings`/`cosmic-panel` 1.9.0, Theme v2 e Panel v1. A validação foi feita nos formatos instalados e em um ambiente temporário que simula uma instalação nova; não foi realizada uma reinstalação real do sistema. Futuras versões do COSMIC podem exigir atualização do preset. Veja [os créditos e as fontes](ATTRIBUTION.md).
