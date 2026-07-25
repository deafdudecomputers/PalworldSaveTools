<div align="center">

![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)

# PalworldSaveTools

**A comprehensive save file editing toolkit for Palworld**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md) | [Português (Brasil)](README.pt_BR.md) | [Português (Portugal)](README.pt_PT.md)

---

### **Download the standalone version from [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** 

---

</div>
<div align="center">

## Visão geral

<img src="https://readme-typing-svg.demolab.com?lines=O+que+exatamente+%C3%A9+isso%3F;Sua+economia%2C+do+seu+jeito;Uma+ferramenta+para+governar+todos+eles&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) é um aplicativo de desktop rápido e completo para inspecionar e editar arquivos salvos do Palworld. Construído com Python e PySide6, ele lê e grava diretamente o formato de salvamento compactado do jogo - sem necessidade de mods de jogo.

Se você precisa gerenciar um servidor dedicado, migrar entre servidores cooperativos e dedicados, limpar dados abandonados ou ajustar Pals individual, o PST fornece uma interface unificada para tudo isso.

### Destaques

- **Plataforma cruzada** — Binários pré-criados para **Windows**, **Linux** e **macOS**.
- **Análise nativa rápida** — Um dos leitores de arquivos salvos mais rápidos disponíveis, equipado com o mecanismo [`palsav`](src/palsav).
- **Mapa visual** — Mapa mundial interativo com marcadores de base/jogador, zonas de exclusão e calibração de coordenadas.
- **Edição profunda de Pal** — Controle total sobre estatísticas, IVs, almas, habilidades, passives, adequações de trabalho, classificação e sinalizadores de aparência.
- **Ferramentas de nível de servidor** — Exclusão em massa, limpeza, conversão e transferência de caracteres criadas para administradores.
- **Backups automáticos** — Cada operação de salvamento cria um backup antes de gravar.
- **9 idiomas** — UI localizada, guias no aplicativo e documentação.





---





## Table of Contents

- [Visão geral](#visão-geral)
- [Recursos](#recursos)
- [Instalação](#instalação)
- [Início rápido](#início-rápido)
- [Guias](#guias)
- [Solução de problemas](#solução-de-problemas)
- [Construindo a partir da fonte](#construindo-a-partir-da-fonte)
- [Contribuindo](#contribuindo)
- [Isenção de responsabilidade](#isenção-de-responsabilidade)
- [Suporte](#suporte)
- [Licença](#licença)
- [A Equipe Palworld](#a-equipe-palworld)
- [Agradecimentos](#agradecimentos)





---




<div align="center">

## Recursos

<img src="https://readme-typing-svg.demolab.com?lines=As+coisas+boas;Confira;Embalado+com+ferramentas&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

| Categoria | O que você pode fazer |
|---|---|
| **Gerenciamento de jogadores** | Edite nomes, níveis, estatísticas, pontos técnicos. Gerenciar itens em massa, pals, tecnologia entre jogadores. Limpe jogadores inativos ou duplicados. |
| **Pal Editor** | Alterar estatísticas, IVs, almas, classificação, habilidades, passives, adequação ao trabalho, chefe / bandeiras de sorte. Exportar/importar pals. Detecte e corrija pals ilegal. Modo de trapaça para edição ilimitada. |
| **Gerenciamento de Guilda** | Renomeie guildas, mude líderes, defina níveis. Desbloqueie pesquisas de laboratório. Mova jogadores entre guildas. Exclua guildas vazias ou inativas. |
| **Ferramentas do acampamento base** | Veja todas as bases com informações da guilda. Exportar/importar projetos. Clone bases para outras guildas. Reposicione as bases no mapa. Ajuste o raio. Exclua bases inativas. |
| **Visualizador de mapa** | Mapa mundial interativo com marcadores de base e de jogador. Desenhe zonas de exclusão. Modo de calibração. Visualizações do mapa mundial e do mapa em árvore. Zoom, panorâmica, fly-to. |
| **Gerenciamento de estoque** | Edite itens de jogadores, itens principais e slots de equipamentos. Desbloqueie todos os pontos de viagem rápida. Navegue e edite inventários básicos e contêineres em todas as guildas. Gerenciar trabalhador base pals. |
| **Exclusões** | Proteja jogadores, guildas e bases contra limpeza com listas de exclusão persistentes. Adicione entradas de menus de contexto. |
| **Salvar ferramentas** | Converta salvamentos entre SAV e JSON. Converta GamePass em Steam. Transferir personagens entre mundos. Corrija os salvamentos do host. Restaure o progresso do mapa. Expanda os slots do palbox. |
| **Limpeza e utilitários** | Exclua guildas vazias, bases/jogadores inativos, dados não referenciados. Remova itens/pals/estruturas inválidos. Reinicialize masmorras, plataforma de petróleo, quedas de suprimentos. Corrigir carimbos de data/hora. |

### Gerenciamento de jogadores

- Visualize e pesquise todos os jogadores por nome, nível, contagem de pal, UID, guilda e hora da última visualização.
- Edite nomes de jogadores, níveis, estatísticas e pontos de tecnologia.
- **Aba Estatísticas** — Estatísticas do herói (Saúde, Vigor, Ataque, Defesa, Velocidade de Trabalho, Peso) com valores corretos computados no jogo; Habilidades de relíquia com alternadores e giradores.
- **Max All Stats** — Limite instantaneamente todas as estatísticas ao máximo (50 pontos).
- **Operações em massa** entre vários jogadores: gerenciamento de itens, gerenciamento pal e desbloqueio de tecnologia.
- Excluir jogadores inativos por limite de tempo; remova duplicatas.

### Pal Editor

Uma interface de edição profunda para qualquer Pal de propriedade de qualquer jogador. Pals são organizados por **Party** (esquadrão ativo) e **Palbox** (armazenamento).

- **Estatísticas e IVs** — HP, Ataque, Defesa (IV 0–100), Nível (1–80), Classificação de Confiança (0–10).
- **Almas** — HP, Ataque, Defesa, Velocidade de Criação (0–20).
- **Habilidades** — Seletor de habilidades ativo; aprenda todos os movimentos; habilidades de sincronização em massa em Pals.
- **Passive Traits** — Seletor passivo com dados completos do jogo.
- **Adequação para o trabalho** — Defina níveis individuais de adequação para o trabalho (0–10).
- **Bandeiras de Aparência** — Alternar Boss/Alpha, Lucky/Shiny, Predator, Awakened e Imported/DNA.
- **Classificação e bloqueio** — Defina a classificação e o nível de bloqueio favorito (0–3).
- **Cheat Mode** — Alterne para expandir todos os limites: nível, IVs, almas, classificação do condensador para 255; desbloquear habilidades ativas/passivas ilimitadas com duplicatas permitidas.
- **Exportar/Importar** — Clique com o botão direito em qualquer pal para exportar como `.pstpal` (compactado) ou `.json`. Importe para slots vazios em party, palbox, DPS ou trabalhadores de base. Funciona em salvamentos e jogadores.
- **Max All Pals** — Maximize todas as estatísticas (IVs, almas, classificação, nível) para todos os pals no grupo, todas as páginas palbox ou todos os trabalhadores da base — respeita os limites do modo de trapaça.
- **Consertar Illegal Pals** — Detecte e limite pals com estatísticas, habilidades ou características ilegais por jogador.
- **Bulk Clone/Delete** — Diálogo de seleção de espécies com controles de quantidade e alternadores de origem (Party/Palbox/DPS) para operações em lote.
- Adicione novo Pals ou exclua rapidamente com clique duplo.

### Gerenciamento de Guilda

Visualização em dois painéis: lista de guildas no topo, lista de membros abaixo.

- Renomear guildas, mudar líderes, definir nível de guilda, nível máximo de guilda.
- Desbloqueie todas as pesquisas de laboratório; reconstruir todas as guildas.
- Mover jogadores entre guildas; exclua guildas vazias ou inativas.

### Ferramentas do acampamento base

- Veja todos os acampamentos base com associação de guilda.
- **Exportar** projetos básicos para `.json`; **importar** (arquivo único ou múltiplo) para qualquer guilda.
- **Clone** bases para outras guildas com posicionamento deslocado.
- **Alterar Coordenadas** — Clique com o botão direito em um marcador de base no mapa, escolha "Alterar Coordenadas" e clique em qualquer local para teletransportar a base.
- **Deslocamento de base** — Desloque uma base em deslocamentos X/Y/Z exatos para corrigir o corte ou a flutuação do solo.
- **Ajustar o raio da base** (50%–1000%).
- Excluir bases inativas e objetos do mapa não base.

### Visualizador de mapa

Visualização interativa de todo o seu mundo.

- Marcadores de base (ícone de casa) e marcadores de jogador (ícone de pessoa) com painéis de detalhes.
- Alternar sobreposições: Bases, Jogadores, Anéis de Raio, Zonas de Exclusão.
- **Desenho de zona** — Desenhe zonas de exclusão retangulares ou poligonais diretamente no mapa.
- **Modo de calibração** — Alinhe com precisão o mapa com as coordenadas do jogo.
- Visualizações do mapa mundial e do mapa em árvore; filtre por guilda ou nome do jogador.
- Zoom (1,0x–30,0x), panorâmica, clique duas vezes para voar até um marcador.
- Marcadores de clique com o botão direito e espaço vazio para ações de gerenciamento.

### Gerenciamento de estoque

**Inventário de jogadores** — Três subguias:
- *Inventário* — Todos os itens e equipamentos da sacola principal; editar quantidade, adicionar, remover.
- *Itens Principais* — Itens de missão, efígies e tecnologia; adicione em massa todas as efígies/itens principais.
- *Estatísticas* — Nível, HP, Vigor, Ataque, Defesa, Velocidade de Trabalho, Peso.
- Painel de equipamentos para armas, acessórios, alimentos, armaduras, escudos, planadores e slots de módulos.
- Desbloqueie todos os mapas + pontos de viagem rápida com um clique.

**Inventário Base** — Navegue e gerencie itens e trabalhe Pals em todas as bases:
- Visualizar/editar itens em containers; recipientes transparentes; modificar slots de contêiner.
- Operações de itens entre guildas (encontrar/remover itens em todas as guildas).
- Exclusão de estrutura entre guildas.
- Subguia **Base Pals** — Gerencie o Pals de trabalho atribuído a cada base com menus de contexto completos do editor pal.

### Exclusões

Listas de proteção que protegem jogadores, guildas e bases de operações de limpeza.

- Três painéis lado a lado: UIDs de jogadores, IDs de guilda e IDs de base excluídos.
- Adicione entradas através dos menus de contexto do botão direito nas guias Jogadores, Guildas ou Bases.
- Salve e carregue listas de exclusão de forma persistente.
- Crie sua lista **antes** de executar a limpeza em massa.

### Salvar ferramentas

Acessível na guia **Ferramentas** como cartões clicáveis:

| Ferramenta | Descrição |
|------|-------------|
| **Conversão salva** | Converter entre os formatos SAV e JSON |
| **Converter GamePass → Steam** | Converter salvamentos do Xbox/GamePass para o formato Steam |
| **Converter SteamID** | Converter IDs Steam em UIDs Palworld |
| **Restaurar mapa** | Aplique o progresso do mapa totalmente desbloqueado a todos os mundos/servidores |
| **Injetor de slot** | Aumentar slots de palbox por jogador |
| **Modificar Salvar** | Abra e modifique dados brutos salvos |
| **Transferência de personagem** | Transferir personagens entre mundos/servidores diferentes (salvamento cruzado) |
| **Corrigir o salvamento do host** | Troca de UIDs entre dois jogadores (troca de host, migração de plataforma) |

### Limpeza e funções utilitárias

Acessíveis via **Menu → Funções**, essas operações de nível de servidor incluem:

- **Exclusão** — Exclui guildas vazias, bases/jogadores inativos, jogadores duplicados, dados não referenciados.
- **Limpeza** — Remova itens inválidos/modificados, pals e passives inválidos, estruturas inválidas; corrigir pals ilegal (limite ao máximo legal); redefinir torres antiaéreas; desbloquear private chests; reparar todas as estruturas.
- **Redefinições** — Redefina missões, masmorras, plataforma de petróleo, invasor, entrega de suprimentos.
- **Timestamps** — Corrige timestamps negativos; redefinir os tempos dos jogadores.
- **PalDefender** — Gera comandos `killnearestbase`.





---




<div align="center">

## Instalação

<img src="https://readme-typing-svg.demolab.com?lines=Fa%C3%A7a+funcionar+em+minutos;Baixe+e+v%C3%A1;Nenhuma+configura%C3%A7%C3%A3o+necess%C3%A1ria&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Construções independentes (recomendado)

Binários pré-construídos estão disponíveis para todas as três plataformas principais de [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest):

| Plataforma | Baixar | Requisitos |
|----------|----------|-------------|
| **Janelas** | `PalworldSaveTools-*.exe` | Janelas 10/11, [VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022) |
| **Linux** | `PalworldSaveTools-*-linux` | Qualquer distribuição moderna |
| **macOS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+ (Monterey ou posterior) |

Também disponível em [Nexus Mods](https://www.nexusmods.com/palworld/mods/3190).

1. Baixe a versão apropriada para sua plataforma.
2. Extraia (se arquivado) e execute o executável.
3. É isso aí - não é necessário Python ou dependências.

> **Windows:** Se você vir "VCRUNTIME140.dll não encontrado", instale o [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170).

> **Linux:** Talvez seja necessário marcar o arquivo como executável: `chmod +x PalworldSaveTools-*-linux`

> **macOS:** Se o Gatekeeper bloquear o aplicativo, clique com o botão direito → **Abrir** na primeira vez ou execute `xattr -d com.apple.quarantine /path/to/app`.

### Da fonte (todas as plataformas)

PST usa [`uv`](https://docs.astral.sh/uv/) para gerenciamento de dependências. O script inicial cria automaticamente um ambiente virtual e instala tudo.

**Pré-requisitos:** [Python 3.11+](https://www.python.org/) e [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows** (clique duas vezes no iniciador):
```
start.cmd
```

O inicializador cria um `.venv`, instala dependências via `uv sync` e inicializa o aplicativo. Ele limpa o arquivo de bloqueio ao sair para que cada execução seja reproduzível.





---




<div align="center">

## Início rápido

<img src="https://readme-typing-svg.demolab.com?lines=Carregar.+Editar.+Salvar.+T%C3%A3o+simples.;Tr%C3%AAs+passos+para+a+gl%C3%B3ria;%C3%89+t%C3%A3o+f%C3%A1cil&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **Carregue seu arquivo salvo**
   - Clique em **Menu → Carregar Salvar** ou arraste e solte um arquivo `.sav` na janela.
   - Navegue até a pasta salva do Palworld e selecione `Level.sav`.

2. **Explore seus dados**
   - Use as abas — **Mapa**, **Ferramentas**, **Jogadores**, **Guildas**, **Bases**, **Inventário de Jogadores**, **Inventário Base**, **Pal Editor**, **Exclusões** — para explorar seu salvamento.
   - A barra de estatísticas mostra contagens ao vivo; ícones de navegação rápida saltam para cada seção.

3. **Faça alterações**
   - Clique com o botão esquerdo para selecionar; clique com o botão direito em quase tudo para ações contextuais.
   - Clique duas vezes para editar ou excluir rapidamente (consulte os guias do aplicativo para obter detalhes).

4. **Salve suas alterações**
   - Clique em **Menu → Salvar alterações**. Os backups são criados automaticamente.

> **Dica:** Cada guia possui um guia integrado. Clique no ícone de ajuda em qualquer guia para ver exatamente o que ela pode fazer. Para um conhecimento mais profundo, **passe o mouse sobre qualquer botão, campo ou controle** para revelar dicas de ferramentas detalhadas no cabeçalho. O sistema de ajuda com dicas de ferramentas no aplicativo é sua melhor referência para entender exatamente o que cada recurso faz e como usá-lo.





---




<div align="center">

## Guias

<img src="https://readme-typing-svg.demolab.com?lines=Passo+a+passo;Siga+o+guia;Mostraremos+como&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Salvar locais de arquivos

**Host/Cooperativo (Windows):**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Servidor Dedicado:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Desbloqueio de mapa

O PST pode desbloquear o mapa completo (todos os pontos de viagem rápida) para você salvar:

1. Carregue seu arquivo salvo em PST.
2. Abra a aba **Inventário do Jogador** e clique em **Desbloquear todos os mapas + Viagem rápida** para um único jogador, **ou**
3. Use a ferramenta **Restaurar Mapa** na guia Ferramentas para aplicar o progresso do mapa desbloqueado em **todos** os seus mundos/servidores de uma só vez.
4. Salve as alterações. Backups automáticos são criados.

### Cooperativo → Servidor Dedicado

<details>
<summary>Clique para expandir</summary>

Mova seu mundo cooperativo (onde você hospeda seu PC) para um servidor dedicado para que outras pessoas possam jogar mesmo quando você estiver offline.

**Como funciona:** Os salvamentos cooperativos usam `0001.sav` para o jogador anfitrião. Servidores dedicados não — cada jogador tem um UID regular. Fix Host Save **troca** arquivos de dois jogadores (como assentos de negociação), não uma cópia. Seu personagem cooperativo em `0001.sav` é trocado no slot do servidor.

1. **Copie seu salvamento cooperativo para o servidor.**
   - Local de salvamento cooperativo: `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`
   - Copie `Level.sav` e a pasta `Players` de lá.
   - Cole na pasta server save: `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`

2. **Entre no servidor e crie um personagem temporário.**
   - Inicie o servidor, entre nele e crie um novo personagem (qualquer nome/aparência — isso é apenas um espaço reservado).
   - Aguarde o salvamento automático e desligue o servidor.

3. **Troque seu personagem cooperativo no slot do servidor.**
   - Abra PST → **Ferramentas** → **Corrigir Host Save**.
   - Navegue até o `Level.sav` do servidor.
   - **Jogador Fonte**: Selecione seu personagem cooperativo (aquele em `0001.sav` – listado como o anfitrião).
   - **Jogador alvo**: Selecione o personagem temporário que você acabou de criar.
- Clique no botão para executar a troca.

4. **Inicie o servidor.**
   - Seu personagem cooperativo original (com todo o progresso, Pals, bases) agora está vinculado ao servidor. O espaço reservado temporário desapareceu.

</details>

### Servidor Dedicado → Cooperativo

<details>
<summary>Clique para expandir</summary>

Leve seu personagem de servidor dedicado de volta para um salvamento cooperativo local – útil se você parar de alugar um servidor ou quiser jogar offline.

**Como funciona:** A mesma troca de GUID ao contrário — Fix Host Save **troca** dois arquivos, não uma cópia. O personagem do seu servidor (UID normal) é trocado para `0001.sav` (o slot do host) para que você possa hospedar o modo cooperativo com o progresso do seu servidor.

1. **Copie o arquivo salvo do servidor para o seu PC local.**
   - Local de salvamento do servidor: `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`
   - Copie `Level.sav` e a pasta `Players` de lá.
   - Cole na pasta cooperativa local: `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`

2. **Organize um jogo cooperativo e crie um personagem temporário.**
   - Inicie o Palworld, organize uma sessão cooperativa e crie um novo personagem.
   - Deixe salvar automaticamente e feche o Palworld.

3. **Troque seu personagem do servidor no slot de host.**
   - Abra PST → **Ferramentas** → **Corrigir Host Save**.
   - Navegue até a cooperativa local `Level.sav`.
   - **Jogador Fonte**: Selecione seu personagem de servidor dedicado (listado por seu UID).
   - **Jogador alvo**: Selecione o personagem cooperativo temporário (aquele em `0001.sav` — listado como o anfitrião).
   - Clique no botão para executar a troca.

4. **Hospede o modo cooperativo normalmente.**
   - Seu personagem do servidor agora é o host (`0001.sav`). Todo o progresso, Pals, e bases intactas.

</details>

### Mudança de host (troca cooperativa)

<details>
<summary>Clique para expandir</summary>

Dois jogadores querem trocar o anfitrião. O jogador A está hospedando – seu personagem mora em `0001.sav`. O Jogador B entra como cliente – seu personagem mora em `1234.sav`. Agora eles querem que o Jogador B se torne o anfitrião, mas o slot do anfitrião é sempre `0001.sav`.

**Conceito principal - Fix Host Save sempre TROCA dois jogadores.** Ele troca seus arquivos salvos, como duas pessoas trocando de lugar. NÃO copia um para o outro. Após qualquer troca, ambos os players ainda existem — eles estão apenas em arquivos diferentes.

Como uma troca move o Jogador B para o slot de host, mas deixa os dados do Jogador A no arquivo antigo de B, uma segunda troca é necessária para colocar o personagem original do Jogador A de volta. Veja como:

---

**Estado inicial:**
```
0001.sav  = Player A (current host)
1234.sav  = Player B (current client)
```

---

**Etapa 1 – Trocar A e B.**
- Abra PST → **Ferramentas** → **Corrigir Host Save**.
- Navegue até sua cooperativa `Level.sav`.
- **Fonte**: Jogador A (`0001.sav`). **Alvo**: Jogador B (`1234.sav`).
- Clique no botão. Fix Host Save troca os dois arquivos.

**Após a etapa 1:**
```
0001.sav  = Player B  ← now the host with B's character
1234.sav  = Player A  ← A's data is here, but this UID no longer exists in the game
```

---

**Etapa 2 — O Jogador B hospeda, o Jogador A entra.**
- O jogador B hospeda o mundo. O jogador A entra.
- Como A não é mais o host, Palworld atribui um UID totalmente novo para o personagem temporário de A (por exemplo, `9999.sav`).
- O jogador A atinge o **Nível 2** com o personagem temporário e então todos saem do jogo.

**Após a etapa 2:**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's original data (not linked to any active UID)
9999.sav  = Player A's temporary character (fresh, Level 2+)
```

---

**Etapa 3 — Troque os dados originais de A pelo novo UID de A.**
- Abra **Fix Host Save** novamente com o mesmo `Level.sav`.
- **Fonte**: `1234.sav` (dados originais do jogador A). **Alvo**: `9999.sav` (personagem temporário do Jogador A).
- Clique no botão. Eles trocam novamente.

**Após a etapa 3:**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's temp character (unused, can delete)
9999.sav  = Player A's original character  ← restored!
```

---

**Concluído.** O Jogador B hospeda o personagem original do Jogador B. O Jogador A junta-se ao personagem original do Jogador A. O `1234.sav` restante pode ser ignorado ou excluído.

> **Por que duas trocas?** Fix Host Save **troca** dois arquivos — não é uma cópia. A primeira troca coloca B no slot de host, mas os dados de A acabam no UID antigo de B (que não existe mais no jogo). A segunda troca move os dados de A para o novo UID do cliente de A. Duas trocas, todo o progresso preservado.

</details>

### Transferência de personagem (salvamento cruzado)

<details>
<summary>Clique para expandir</summary>

Copie um jogador (com todos os Pals, inventário, tecnologia e progresso) de um mundo para outro — útil para mover seu personagem entre um mundo cooperativo e um servidor dedicado ou entre dois servidores.

**Como funciona:** Ao contrário do Fix Host Save (que **troca** dois arquivos), o Character Transfer **copia** um jogador de um `Level.sav` para outro. O salvamento da fonte permanece intacto.

1. Abra PST → **Ferramentas** → **Transferência de personagem**.
2. **Carregue o arquivo fonte** — clique no botão Fonte e selecione o `Level.sav` que contém o caractere que você deseja copiar (por exemplo, seu servidor antigo).
3. **Carregue o destino salvo** — clique no botão Destino e selecione o `Level.sav` para o qual deseja copiar (por exemplo, seu novo servidor).
4. **Selecione o jogador** para transferir na lista de jogadores de origem à esquerda.
5. **Escolha onde colocá-los** na lista de jogadores alvo à direita — você pode substituir um jogador existente ou deixá-lo vazio para um novo slot.
6. Clique em **Transferir**. O personagem, Pals, inventário e associação à guilda são copiados para o salvamento de destino.
7. Salve as alterações. Backups automáticos são criados.

Você também pode transferir **todos os jogadores** de uma só vez usando o botão "Transferir todos".

</details>

### Exportação/Importação/Clonagem Base

<details>
<summary>Clique para expandir</summary>

**Exportando uma Base:**
1. Vá para a aba **Bases** (ou use o Map Viewer).
2. Clique com o botão direito em uma base → **Exportar Base**.
3. Salve como um arquivo de blueprint `.json`.

**Importando uma Base:**
1. Clique com o botão direito na guilda alvo (na aba Bases, Map Viewer ou na aba Guildas).
2. Selecione **Importar Base** (arquivo único) ou **Importar Bases (Vários Arquivos)**.
3. Selecione o(s) arquivo(s) `.json` exportado(s).

**Clonando uma Base:**
1. Clique com o botão direito em uma base → **Clone Base**.
2. Selecione a guilda alvo.
3. A base é clonada com posicionamento deslocado.

**Ajustando o raio base:**
1. Clique com o botão direito em uma base → **Ajustar raio**.
2. Insira um novo raio (50%–1000%).
3. Salve e recarregue o arquivo salvo no jogo para que as estruturas sejam reatribuídas.

</details>





---




<div align="center">

## Solução de problemas

<img src="https://readme-typing-svg.demolab.com?lines=Quando+as+coisas+v%C3%A3o+para+o+lado;N%C3%A3o+entre+em+p%C3%A2nico;N%C3%B3s+vimos+tudo&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### "VCRUNTIME140.dll não foi encontrado" (Windows)

Instale o [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022).

### `struct.error` ao analisar um salvamento

O formato do arquivo salvo está desatualizado. Carregue o jogo salvo (Solo, Co-op ou Servidor Dedicado) uma vez para acionar uma atualização automática da estrutura e tente novamente. Certifique-se de que o salvamento foi atualizado no ou após o patch mais recente do jogo.

### GamePass conversor não funciona

1. Feche totalmente a versão GamePass do Palworld.
2. Aguarde alguns minutos para que os identificadores de arquivo sejam liberados.
3. Execute o conversor GamePass → Steam.
4. Inicie o Palworld em GamePass para verificar.

### O binário Linux/macOS não inicia

- **Linux:** `chmod +x PalworldSaveTools-*-linux` para marcá-lo como executável.
- **macOS:** Se bloqueado pelo Gatekeeper, clique com o botão direito → **Abrir** ou execute `xattr -d com.apple.quarantine /path/to/app`.





---




<div align="center">

## Construindo a partir da fonte

<img src="https://readme-typing-svg.demolab.com?lines=Compile+voc%C3%AA+mesmo;Construa+o+seu+pr%C3%B3prio;Da+fonte+ao+bin%C3%A1rio&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST oferece suporte a dois caminhos de construção. O pipeline de CI/CD usa Nuitka para binários de lançamento multiplataforma; cx_Freeze é usado para o instalador local do Windows.

### Nuitka (plataforma cruzada — usado por CI/lançamentos)

Requer Python 3.11+ e `uv`. Nuitka é instalado automaticamente.

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

As saídas vão para `dist/`:
- Janelas → `dist/PalworldSaveTools-*.exe`
-Linux → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → empacotado como `.dmg`

### cx_Freeze (Instalador do Windows)

Para um pacote local do Windows `.7z`:

```
scripts\build_cx.cmd
```

Isso cria `PST_standalone_v{version}.zip` na raiz do projeto.

### Construtor interativo

Um menu interativo para escolher um modo de construção:

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## Contribuindo

<img src="https://readme-typing-svg.demolab.com?lines=Quer+ajudar%3F+Veja+como;Junte-se+%C3%A0+equipe;Cada+contribui%C3%A7%C3%A3o+conta&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Contribuições são bem-vindas! Sinta-se à vontade para enviar uma solicitação pull.

1. Bifurque o repositório.
2. Crie sua ramificação de recursos (`git checkout -b feature/AmazingFeature`).
3. Confirme suas alterações (`git commit -m 'Add some AmazingFeature'`).
4. Empurre para a ramificação (`git push origin feature/AmazingFeature`).
5. Abra uma solicitação pull.





---




<div align="center">

## Isenção de responsabilidade

<img src="https://readme-typing-svg.demolab.com?lines=Leia+isto+antes+de+quebrar+algo;Voc%C3%AA+foi+avisado;Fa%C3%A7a+backup+primeiro%21;Com+grande+poder...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

**Use esta ferramenta por sua conta e risco. Sempre faça backup dos seus arquivos salvos antes de fazer qualquer modificação.**

Os desenvolvedores não são responsáveis por qualquer perda de dados salvos ou problemas que possam surgir com o uso desta ferramenta.





---




<div align="center">

## Suporte

<img src="https://readme-typing-svg.demolab.com?lines=N%C3%B3s+protegemos+voc%C3%AA;Precisa+de+ajuda%3F;Estamos+aqui+para+voc%C3%AA&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- Problemas **GitHub:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Modificações Nexus:** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## Licença

<img src="https://readme-typing-svg.demolab.com?lines=MIT+%E2%80%93+fa%C3%A7a+o+que+quiser;Gr%C3%A1tis+como+na+cerveja;C%C3%B3digo+aberto%2C+mente+aberta&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Este projeto está licenciado sob a licença MIT — consulte o arquivo [license](license) para obter detalhes.





---




<div align="center">

## A Equipe Palworld

<img src="https://readme-typing-svg.demolab.com?lines=As+pessoas+por+tr%C3%A1s+da+magia;Conhe%C3%A7a+a+equipe;Constru%C3%ADdo+com+paix%C3%A3o&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Este projeto não existiria sem as pessoas por trás dele.

### Mantenedores Ativos

**[Pylar](https://github.com/deafdudecomputers)** — O homem que começou tudo. Cada linha desta ferramenta remonta à sua visão e trabalho incansável no mecanismo de salvamento, na GUI e nos recursos que você usa todos os dias.

**[cyrix](https://github.com/CyrixJD115)** — Refatorador e submantenedor. Focado na qualidade do código, simplificação e melhorias estruturais — mantendo a base de código limpa, menor e mais fácil de manter à medida que o projeto cresce.

### Colaboradores

**[dkoz](https://github.com/dkoz)** — O homem por trás das identidades. Fornece IDs de dados de jogos, visão estrutural sobre os códigos de ID e conhecimento profundo de como os dados do Palworld são conectados, o que mantém a ferramenta precisa a cada atualização do jogo.

**[oMaN-Rod](https://github.com/oMaN-Rod)** — Fornecido o analisador de salvamento original do qual este projeto se bifurcou. Sem seu trabalho fundamental para quebrar o formato de salvamento do Palworld, nada disso existiria. O fork simplificou e simplificou seu analisador no que o PST é hoje.
**[Okaetsu](https://github.com/Okaetsu)** — Modificação de insights que tornaram possível a importação/exportação básica. Sua compreensão de como o Palworld estrutura os dados básicos do lado do modding preencheu a lacuna entre o modding e a edição salva, tornando esse recurso uma realidade.





---




<div align="center">

## Agradecimentos

<img src="https://readme-typing-svg.demolab.com?lines=Onde+o+cr%C3%A9dito+%C3%A9+devido;Obrigado+a+todos;Estamos+nos+ombros&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Um enorme obrigado a:

- **Palworld** desenvolvido pela Pocketpair, Inc. — para o jogo que nos uniu.
- **Os repórteres de bugs** — cada problema registrado, cada caso extremo encontrado, cada log colado em Discord. Você torna essa ferramenta mais robusta a cada relatório.
- **A comunidade de modding Palworld** — colegas modders, desenvolvedores de ferramentas e criadores que compartilham conhecimento, fazem engenharia reversa de formatos e impulsionam o ecossistema. Este projeto está apoiado nesse esforço coletivo.
- **Todos os colaboradores e membros da comunidade** — quer você tenha enviado um PR, respondido uma pergunta em Discord ou simplesmente contado a um amigo sobre o PST — obrigado.

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**Feito com ❤️ para a comunidade Palworld**

[⬆ Back to Top](#palworld-save-tools)

</div>