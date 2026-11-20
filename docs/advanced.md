# Guia de uso

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
| Painel superior | XS, cerca de 32 px a 100% de escala; margem 10 px, raio 12 px, opacidade 92% |
| Dock inferior | Sempre visível, centralizado e flutuante; margem 10 px, raio 14 px, tamanho S |
| Fontes | Iosevka Nerd Font na interface e terminal; Kitty a 11 pt |
| Ícones | TokyoNight-SE com fallback para ícones específicos do COSMIC |
| Kitty | Cores Tokyo Night, opacidade 92% e margem interna de 10 px |
| GTK/Qt | Exportação das cores pelo próprio daemon COSMIC |

A lista de painéis mantém entradas adicionais e garante a presença de `Panel` e `Dock`. Ambos são configurados para **todas as telas**, sem nomes de monitores ou identificadores EDID. A disposição dos indicadores existentes é preservada; os indicadores padrão deste preset são usados somente onde a configuração ainda não existe.

**Não são exportados:** papel de parede, atalhos, aplicativos favoritos, teclado, shell, sessões, contas, monitores, histórico, capturas pessoais ou dados pessoais. O tema não altera as cores internas de páginas web nem aplicativos que imponham uma aparência própria. Indicadores com cores individuais e bordas em gradiente da Waybar/Hyprland não são reproduzidos por este preset nativo.

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

## Testes e compatibilidade

```sh
python3 -m unittest discover -s tests -v
```

Os testes usam diretórios XDG temporários e não modificam sua sessão. Cobrem aplicação/restauração, reaplicação, preservação de preferências, backups, links, formatos incompatíveis, downloads corrompidos, extração insegura, modo offline e falhas parciais. O GitHub Actions executa os testes em Python 3.12.

O preset foi extraído de Pop!_OS 24.04 com `cosmic-settings`/`cosmic-panel` 1.9.0, Theme v2 e Panel v1. A validação foi feita nos formatos instalados e em um ambiente temporário que simula uma instalação nova; não foi realizada uma reinstalação real do sistema. Futuras versões do COSMIC podem exigir atualização do preset. Veja [os créditos e as fontes](../ATTRIBUTION.md).

## Cores e importação nativa

O arquivo `tokyo-night.ron` contém a definição-base ThemeBuilder v2. A importação isolada deixa o COSMIC gerar os estados dos componentes; ela não reproduz todos os ajustes de listas, seleção, divisórias, texto secundário e botões do preset completo. O comando `theme.py apply` aplica também esses papéis nativos em `preset/cosmic/com.system76.CosmicTheme.Dark/v2/`, além das abas do Kitty. Alterar ou reimportar o tema nas Configurações pode regenerar esses papéis; reaplique o pacote para recuperá-los. GTK/Qt continuam usando a exportação do próprio COSMIC, sem CSS manual. Aplicativos podem escolher quais papéis nativos utilizam ou desenhar seus próprios controles.

A paleta usa texto principal `#c0caf5`, secundário `#a9b1d6`, divisórias `#3b4261`, hover `#292e42` e seleção `#283457`. Botões azuis usam texto `#1a1b26`. As transparências originais dos estados desativados e dos controles transparentes são mantidas; cores semânticas de erro, aviso e sucesso continuam distintas.

Alguns controles do Arquivos usam diretamente o destaque azul para a seleção, em vez do papel geral `selected`. Nesses casos, o azul e o texto escuro seguem a implementação nativa; o preset não injeta CSS nem altera o aplicativo.

## Transparência e terminais

O preset ativa `frosted_windows`, `frosted_maximized_apps`, `frosted_system_interface`, `frosted_panel` e `frosted_applets` no Theme v2, com intensidade nativa `ExtremelyLow`. Superfícies transparentes ficam em aproximadamente 92% de opacidade; painel/dock em 92% e Kitty em 92%. O Arquivos e outros aplicativos libcosmic que respeitam esses papéis podem usar o efeito; aplicativos com superfícies próprias podem permanecer opacos. O desfoque depende do compositor e do aplicativo, sem efeitos externos. GTK/Qt não recebem transparência forçada.

A configuração de terminal deste pacote é exclusiva do Kitty. O tema do COSMIC, fontes e ícones funcionam independentemente do terminal escolhido. Sem Kitty, a instalação continua e não grava arquivos dele. Em terminal interativo com acesso online, oferece instalar `kitty` pelo APT (pode solicitar senha via sudo e confirmação do próprio APT), e depois pergunta separadamente se deve defini-lo como terminal padrão do COSMIC/Super+T. As respostas padrão são Não. Sem interação, em `--offline` ou em `--dry-run`, apenas avisa e sugere `sudo apt install kitty`; depois de instalar, reaplique o tema.

A seleção de terminal padrão é salva no backup e pode ser restaurada. A restauração não desinstala pacotes APT. Se a instalação do Kitty for recusada ou falhar, o tema continua normalmente com o terminal atual. Não há configuração automática para Alacritty, WezTerm, GNOME Terminal ou outros terminais.
