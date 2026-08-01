<div align="center">

![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Palworld 的综合保存文件编辑工具包**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md) | [Português (Brasil)](README.pt_BR.md) | [Português (Portugal)](README.pt_PT.md)

---

### **从 [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** 下载独立版本

---

</div>
<div align="center">

## 概述

<img src="https://readme-typing-svg.demolab.com?lines=%E8%BF%99%E4%B8%9C%E8%A5%BF%E5%88%B0%E5%BA%95%E6%98%AF%E4%BB%80%E4%B9%88%EF%BC%9F;%E4%BD%A0%E7%9A%84%E6%8B%AF%E6%95%91%EF%BC%8C%E4%BD%A0%E7%9A%84%E6%96%B9%E5%BC%8F;%E4%B8%80%E7%A7%8D%E5%B7%A5%E5%85%B7%E5%8D%B3%E5%8F%AF%E7%BB%9F%E6%B2%BB%E4%B8%80%E5%88%87&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) 是一款快速、一体化的桌面应用程序，用于检查和编辑 Palworld 保存文件。它使用 Python 和 PySide6 构建，可以直接读取和写入游戏的压缩保存格式 - 无需游戏模组。

无论您需要管理专用服务器、在合作服务器和专用服务器之间迁移、清理废弃的数据还是微调单个 Pals，PST 都为所有这些提供了一个统一的界面。

### 亮点

- **跨平台** — 适用于 **Windows**、**Linux** 和 **macOS** 的预构建二进制文件。
- **快速本机解析** — 最快的保存文件读取器之一，由 [`palsav`](src/palsav) 引擎提供支持。
- **视觉地图** — 带有基地/玩家标记、禁区和坐标校准的交互式世界地图。
- **深度 Pal 编辑** — 完全控制统计数据、IVs、灵魂、技能、passives、工作适宜性、等级和外观标志。
- **服务器级工具** — 为管理员构建的批量删除、清理、转换和字符传输。
- **自动备份** — 每个保存操作都会在写入之前创建备份。
- **9 种语言** — 本地化 UI、应用内指南和文档。





---





## 目录

- [概述](#概述)
- [特点](#特点)
- [安装](#安装)
- [快速入门](#快速入门)
- [指南](#指南)
- [故障排除](#故障排除)
- [从源代码构建](#从源代码构建)
- [贡献](#贡献)
- [许可证](#许可证)
- [Palworld 团队](#palworld-团队)





---




<div align="center">

## 特点

<img src="https://readme-typing-svg.demolab.com?lines=%E5%A5%BD%E4%B8%9C%E8%A5%BF;%E6%A3%80%E6%9F%A5%E4%B8%80%E4%B8%8B;%E8%A3%85%E6%BB%A1%E4%BA%86%E5%B7%A5%E5%85%B7&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

|类别 |你能做什么|
|---|---|
| **玩家管理** |编辑名称、等级、统计数据、技术点。批量管理物品、pals、跨玩家的技术。清理不活跃或重复的玩家。 |
| **Pal Editor** |改变统计数据，IVs，灵魂，等级，技能，passives，工作适合性，老板/幸运标志。导出/导入pals。检测并修复非法pals。无上限编辑的作弊模式。 |
| **公会管理** |重命名公会、更换领导者、设定等级。解锁实验室研究。在公会之间移动玩家。删除空的或不活跃的公会。 |
| **大本营工具** |查看所有基地的公会信息。导出/导入蓝图。将基地克隆到其他公会。在地图上重新定位基地。调整半径。删除不活跃的碱基。 |
| **地图查看器** |带有基地和玩家标记的交互式世界地图。绘制禁区。校准模式。世界地图和树状地图视图。缩放、平移、飞至。 |
| **库存管理** |编辑玩家物品、关键物品、装备槽位。解锁所有快速旅行点。浏览和编辑所有公会的基础库存和容器。管理基础工人pals。 |
| **排除** |通过持久的排除列表保护玩家、公会和基地免遭清理。从上下文菜单添加条目。 |
| **保存工具** |在 SAV 和 JSON 之间转换保存。将 GamePass 转换为 Steam。在世界之间转移角色。修复主机保存。恢复地图进度。扩展 palbox 插槽。 |
| **清洁和公用事业** |删除空公会、不活跃的基地/玩家、未引用的数据。删除无效项目/pals/结构。重置地下城、石油钻井平台、补给品。修复时间戳。 |

### 玩家管理

- 按姓名、等级、pal 计数、UID、公会和最后上线时间查看和搜索所有玩家。
- 编辑玩家姓名、等级、统计数据和技术点。
- **统计选项卡** — 英雄统计数据（生命值、耐力、攻击、防御、工作速度、体重）以及正确的游戏内计算值；具有切换器和旋转器的遗物能力。
- **最大所有统计数据** — 立即将所有统计数据限制为最大（50 点）。
- **跨多个玩家的批量操作**：物品管理、pal 管理和技术解锁。
- 按时间阈值删除不活跃玩家；删除重复项。

### Pal Editor

适用于任何玩家拥有的任何 Pal 的深度编辑界面。 Pals 由 **Party**（现役小队）和 **Palbox**（存储）组织。

- **统计数据和 IVs** — 生命值、攻击力、防御力 (IV 0–100)、等级 (1–80)、信任等级 (0–10)。
- **灵魂** — 生命值、攻击力、防御力、工艺速度 (0–20)。
- **技能** — 主动技能选择器；学习所有动作；跨 Pals 的批量同步技能。
- **被动特征** - 具有完整游戏数据的被动选择器。
- **工作适宜性** — 设置个人工作适宜性级别 (0–10)。
- **外观标志** — 切换 Boss/Alpha、Lucky/Shiny、Predator、Awakened 和 Imported/DNA。
- **排名和锁定** — 设置排名和最喜欢的锁定级别 (0–3)。
- **作弊模式** — 切换以展开所有大写：等级、IVs、灵魂、冷凝等级至 255；解锁无限的主动/被动技能，并允许重复。
- **导出/导入** — 右键单击​​任何 pal 以导出为 `.pstpal`（压缩）或 `.json`。导入到队伍、palbox、DPS 或基础工人的空槽中。适用于保存和玩家。
- **最大化所有 Pals** — 最大化队伍中所有 pals、所有 palbox 页面或所有基地工人的所有统计数据（IVs、灵魂、等级、等级）— 尊重作弊模式上限。
- **修复非法 Pals** — 检测并限制 pals 的每个玩家的非法统计数据、技能或特征。
- **批量克隆/删除** — 物种选择器对话框，带有用于批量操作的数量控制和源切换（Party/Palbox/DPS）。
- 添加新的 Pals 或双击快速删除。

### 公会管理

两面板视图：顶部是公会列表，下面是成员名册。

- 重命名公会，更换领导者，设置公会等级，最高公会等级。
- 解锁所有实验室研究；重建所有公会。
- 在公会之间移动玩家；删除空的或不活跃的公会。

### 大本营工具

- 查看所有有公会协会的大本营。
- **导出**基础蓝图到 `.json`； **导入**（单个或多个文件）到任何公会。
- **克隆**基地到其他具有偏移定位的公会。
- **更改坐标** — 右键单击​​地图上的基地标记，选择“更改坐标”，然后单击任意点以传送基地。
- **底座微移** — 按精确的 X/Y/Z 偏移微移底座以修复地面剪切或浮动。
- **调整基础半径** (50%–1000%)。
- 删除不活动的基地和非基地地图对象。

### 地图查看器

整个世界的交互式可视化。

- 带有详细面板的基地标记（房屋图标）和玩家标记（人物图标）。
- 切换覆盖：基地、球员、半径环、禁区。
- **区域绘制** — 直接在地图上绘制矩形或多边形禁区。
- **校准模式** — 将地图与游戏坐标精确对齐。
- 世界地图和树状地图视图；按公会或玩家名称过滤。
- 缩放 (1.0x–30.0x)、平移、双击以飞至标记。
- 右键单击​​标记和空白区域以进行管理操作。

### 库存管理

**玩家清单** — 三个子选项卡：
- *库存* — 主包中的所有物品和设备；编辑数量、添加、删除。
- *关键物品* — 任务物品、雕像和技术；批量添加所有肖像/关键物品。
- *统计数据* — 等级、生命值、耐力、攻击力、防御力、工作速度、重量。
- 武器、配件、食物、盔甲、盾牌、滑翔机和模块插槽的设备面板。
- 一键解锁所有地图+快速旅行点。

**基地库存** — 浏览和管理所有基地的物品和工作 Pals：
- 查看/编辑容器中的项目；透明容器；修改容器槽位。
- 跨公会物品操作（查找/删除所有公会的物品）。
- 跨行会结构删除。
- **Base Pals** 子选项卡 — 使用完整的 pal 编辑器上下文菜单管理分配给每个底座的工作 Pals。

### 排除情况

保护名单，保护玩家、公会和基地免受清理行动的影响。

- 三个并排面板：排除的玩家 UID、公会 ID 和基本 ID。
- 通过右键单击“玩家”、“公会”或“基地”选项卡中的上下文菜单添加条目。
- 持久保存和加载排除列表。
- **在**运行批量清理之前**构建您的列表。

### 保存工具

可从 **工具** 选项卡作为可点击的卡片进行访问：

|工具|描述 |
|------|-------------|
| **转换保存** | SAV 和 JSON 格式之间的转换 |
| **转换 GamePass → Steam** |将 Xbox/GamePass 保存转换为 Steam 格式 |
| **转换 SteamID** |将 Steam ID 转换为 Palworld UID |
| **恢复地图** |将完全解锁的地图进度应用于所有世界/服务器 |
| **槽式注入器** |增加每位玩家的 palbox 槽位 |
| **修改保存** |打开并修改原始保存数据 |
| **角色转移** |在不同世界/服务器之间转移角色（交叉保存）|
| **修复主机保存** |在两个玩家之间交换 UID（主机交换、平台迁移）|

### 清理和实用函数

这些服务器级操作可通过**菜单 → 功能**进行访问，包括：

- **删除** — 删除空公会、不活跃的基地/玩家、重复的玩家、未引用的数据。
- **清理** — 删除无效/修改的项目、无效的 pals 和 passives、无效的结构；修复非法 pals （上限为合法最大值）；重置防空炮塔；解锁private chests；修复所有结构。
- **重置** — 重置任务、地下城、石油钻井平台、入侵者、空投补给。
- **时间戳** — 修复负时间戳；重置玩家时间。
- **PalDefender** — 生成 `killnearestbase` 命令。





---




<div align="center">

## 安装

<img src="https://readme-typing-svg.demolab.com?lines=%E5%87%A0%E5%88%86%E9%92%9F%E5%86%85%E5%8D%B3%E5%8F%AF%E8%BF%90%E8%A1%8C;%E4%B8%8B%E8%BD%BD%E5%B9%B6%E5%BC%80%E5%A7%8B;%E6%97%A0%E9%9C%80%E8%AE%BE%E7%BD%AE&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 独立构建（推荐）

预构建的二进制文件适用于 [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) 的所有三个主要平台：

|平台|下载 |要求|
|----------|----------|--------------|
| **Windows** | `PalworldSaveTools-*.exe` | Windows 10/11，[VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)（2015–2022）|
| **Linux** | `PalworldSaveTools-*-linux.AppImage` |任何现代发行版 |
| **macOS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+（蒙特利或更高版本）|

也可在 [Nexus Mods](https://www.nexusmods.com/palworld/mods/3190) 上找到。

1. 下载适合您平台的版本。
2. 解压（如果已存档）并运行可执行文件。
3. 就是这样——不需要 Python 或依赖项。

> **Windows：** 如果您看到“未找到 VCRUNTIME140.dll”，请安装 [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)。

> **Linux:** 您可能需要将文件标记为可执行文件：`chmod +x PalworldSaveTools-*-linux.AppImage`

> **macOS：** 如果 Gatekeeper 阻止该应用程序，请首次右键单击 → **打开**，或运行 `xattr -d com.apple.quarantine /path/to/app`。

### 来自源头（所有平台）

PST 使用 [`uv`](https://docs.astral.sh/uv/) 进行依赖性管理。启动脚本会自动创建虚拟环境并安装所有内容。

**先决条件：** [Python 3.11+](https://www.python.org/) 和 [uv](https://docs.astral.sh/uv/getting-started/installation/)。

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows**（双击启动器）：
```
start.cmd
```

启动器创建 `.venv`，通过 `uv sync` 安装依赖项，然后启动应用程序。它会在退出时清除锁定文件，因此每次运行都是可重现的。





---




<div align="center">

## 快速入门

<img src="https://readme-typing-svg.demolab.com?lines=%E8%B4%9F%E8%BD%BD%E3%80%82%E7%BC%96%E8%BE%91%E3%80%82%E8%8A%82%E7%9C%81%E3%80%82%E5%B0%B1%E8%BF%99%E4%B9%88%E7%AE%80%E5%8D%95%E3%80%82;%E8%BF%88%E5%90%91%E8%8D%A3%E8%80%80%E7%9A%84%E4%B8%89%E6%AD%A5;%E5%B0%B1%E6%98%AF%E8%BF%99%E4%B9%88%E7%AE%80%E5%8D%95&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **加载您的保存**
   - 单击 **菜单 → 加载保存**，或将 `.sav` 文件拖放到窗口上。
   - 导航到您的 Palworld 保存文件夹并选择 `Level.sav`。

2. **探索您的数据**
   - 使用选项卡 - **地图**、**工具**、**玩家**、**公会**、**基地**、**玩家库存**、**基地库存**、**Pal Editor**、**排除** - 探索您的保存。
   - 统计栏显示实时计数；快速导航图标跳转到每个部分。

3. **做出改变**
   - 左键单击选择；右键单击几乎任何内容即可执行上下文操作。
   - 双击可快速编辑或快速删除（详情请参阅应用内指南）。

4. **保存您的更改**
   - 单击**菜单 → 保存更改**。备份是自动创建的。

> **提示：** 每个选项卡都有一个内置指南 - 单击任何选项卡中的帮助图标即可准确查看其功能。如需更深入的了解，**将鼠标悬停在任何按钮、字段或控件上**即可在标题处显示详细的工具提示。应用程序内工具提示帮助系统是您准确了解每个功能的用途以及如何使用它的最佳参考。





---




<div align="center">

## 指南

<img src="https://readme-typing-svg.demolab.com?lines=%E5%88%86%E6%AD%A5%E6%BC%94%E7%BB%83;%E8%B7%9F%E9%9A%8F%E6%8C%87%E5%8D%97;%E6%88%91%E4%BB%AC%E5%B0%86%E5%90%91%E6%82%A8%E5%B1%95%E7%A4%BA%E5%A6%82%E4%BD%95&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 保存文件位置

**主机/合作社 (Windows)：**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**专用服务器：**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### 地图解锁

PST 可以解锁完整地图（所有快速旅行点）以供您保存：

1. 将您的保存加载到 PST 中。
2. 打开**玩家清单**选项卡，然后单击单个玩家的**解锁全地图+快速旅行**，**或**
3. 使用“工具”选项卡中的“恢复地图”工具一次性将解锁的地图进度应用到“所有”世界/服务器。
4. 保存更改。创建自动备份。

### 合作 → 专用服务器

<details>
<summary>点击展开</summary>

将您的合作世界（您在 PC 上托管的地方）移至专用服务器，以便其他人即使在您离线时也可以玩游戏。

**工作原理：** 合作模式存档使用 `0001.sav` 作为主机玩家。专用服务器则不然——每个玩家都有一个常规的 UID。修复主机保存**交换**两个玩家文件（如交易席位），而不是副本。您在 `0001.sav` 中的合作角色会被交换到服务器的插槽中。

1. **将你的合作存档复制到服务器。**
   - 合作保存位置：`%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`
   - 从那里复制 `Level.sav` 和 `Players` 文件夹。
   - 粘贴到服务器保存文件夹：`steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`

2. **加入服务器并创建临时角色。**
   - 启动服务器，加入它，然后创建一个新角色（任何名称/外观 - 这只是一个占位符）。
   - 等待自动保存，然后关闭服务器。

3. **将您的合作角色交换到服务器插槽中。**
   - 打开 PST → **工具** → **修复主机保存**。
   - 浏览到服务器的 `Level.sav`。
   - **源玩家**：选择您的合作角色（`0001.sav` 中的角色 — 列为主机）。
   - **目标玩家**：选择您刚刚创建的临时角色。
- 单击按钮运行交换。

4. **启动服务器。**
   - 你原来的合作角色（所有进度，Pals，基础）现在已链接到服务器。临时占位符消失了。

</details>

### 专用服务器 → 合作

<details>
<summary>点击展开</summary>

将您的专用服务器角色带回本地合作保存 - 如果您停止租用服务器或想要离线玩，这很有用。

**工作原理：** 相同的 GUID 反向交换 — 修复主机保存 **交换**两个文件，而不是副本。你的服务器角色（常规 UID）会被交换到 `0001.sav` （主机槽），这样你就可以在服务器进程中主持合作游戏。

1. **将服务器保存的内容复制到本地PC。**
   - 服务器保存位置：`steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`
   - 从那里复制 `Level.sav` 和 `Players` 文件夹。
   - 粘贴到您的本地合作文件夹：`%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`

2. **举办合作游戏并创建一个临时角色。**
   - 启动 Palworld，主持合作会话并创建新角色。
   - 让它自动保存，然后关闭 Palworld。

3. **将您的服务器角色交换到主机插槽中。**
   - 打开 PST → **工具** → **修复主机保存**。
   - 浏览本地合作社`Level.sav`。
   - **源玩家**：选择您的专用服务器角色（按其 UID 列出）。
   - **目标玩家**：选择临时合作角色（`0001.sav` 中的角色 — 列为主机）。
   - 单击按钮运行交换。

4. **正常主持合作社。**
   - 您的服务器角色现在是主机（`0001.sav`）。所有进展，Pals，并且基础完好无损。

</details>

### 更换主机（合作社交换）

<details>
<summary>点击展开</summary>

两名玩家想要交换主办方。玩家 A 一直在主持——他们的角色住在 `0001.sav`。玩家 B 作为客户加入 - 他们的角色住在 `1234.sav`。现在他们希望玩家 B 成为主机，但主机槽始终是 `0001.sav`。

**关键概念 - 修复主机保存总是交换两个玩家的问题。** 它交换他们的保存文件，就像两个人交换座位一样。它不会将一个复制到另一个上。在任何交换之后，两个玩家仍然存在——他们只是在不同的文件中。

由于一次交换将玩家 B 移动到主机槽中，但将玩家 A 的数据保留在 B 的旧文件中，因此需要第二次交换才能将玩家 A 的原始角色放回原处。方法如下：

---

**起始状态：**
```
0001.sav  = Player A (current host)
1234.sav  = Player B (current client)
```

---

**步骤 1 — 交换 A 和 B。**
- 打开 PST → **工具** → **修复主机保存**。
- 浏览到您的合作社`Level.sav`。
- **来源**：玩家 A (`0001.sav`)。 **目标**：玩家 B (`1234.sav`)。
- 单击按钮。修复主机保存交换两个文件的问题。

**第 1 步之后：**
```
0001.sav  = Player B  ← now the host with B's character
1234.sav  = Player A  ← A's data is here, but this UID no longer exists in the game
```

---

**第 2 步 — 玩家 B 主持，玩家 A 加入。**
- 玩家 B 主持世界。玩家A加入。
- 由于A不再是宿主，Palworld为A的临时角色分配了一个全新的UID（例如`9999.sav`）。
- 玩家 A 的临时角色达到 **2 级**，然后所有人退出游戏。

**第 2 步之后：**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's original data (not linked to any active UID)
9999.sav  = Player A's temporary character (fresh, Level 2+)
```

---

**步骤 3 — 将 A 的原始数据交换为 A 的新 UID。**
- 使用相同的 `Level.sav` 再次打开 **修复主机保存**。
- **来源**：`1234.sav`（玩家 A 的原始数据）。 **目标**：`9999.sav`（玩家A的临时角色）。
- 单击按钮。他们再次交换。

**第 3 步之后：**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's temp character (unused, can delete)
9999.sav  = Player A's original character  ← restored!
```

---

**完成。** 玩家 B 以玩家 B 的原始角色主持。玩家 A 加入玩家 A 的原始角色。剩余的 `1234.sav` 可以忽略或删除。

> **为什么要进行两次交换？** 修复主机保存 **交换**两个文件 - 它不是副本。第一次交换将 B 放入主机插槽中，但 A 的数据最终出现在 B 的旧 UID 中（游戏中不再存在）。第二次交换将 A 的数据移至 A 的新客户端 UID 中。两次交换，所有进度均保留。

</details>

### 角色传输（交叉保存）

<details>
<summary>点击展开</summary>

将一名玩家（包含所有 Pals、库存、技术和进度）从一个世界复制到另一个世界 - 对于在合作世界和专用服务器或两个服务器之间移动角色非常有用。

**工作原理：**与“修复主机保存”（**交换**两个文件）不同，角色传输**将**玩家从一个 `Level.sav` 复制到另一个 `Level.sav` 中。源保存未受影响。

1. 打开 PST → **工具** → **字符传输**。
2. **加载源保存** — 单击“源”按钮并选择具有您要复制的角色的 `Level.sav`（例如，您的旧服务器）。
3. **加载目标保存** — 单击“目标”按钮并选择要复制到的 `Level.sav`（例如，您的新服务器）。
4. **从左侧的源播放器列表中选择要传输的播放器**。
5. **在右侧的目标玩家列表中选择放置它们的位置** - 您可以覆盖现有玩家或将其留空以添加新位置。
6. 单击**传输**。角色、Pals、库存和公会成员资格将复制到目标保存。
7. 保存更改。创建自动备份。

您还可以使用“全部转移”按钮一次性转移**所有玩家**。

</details>

### 基础导出/导入/克隆

<details>
<summary>点击展开</summary>

**导出基地：**
1. 转到 **Bases** 选项卡（或使用地图查看器）。
2. 右键单击​​基地 → **导出基地**。
3. 另存为 `.json` 蓝图文件。

**导入基础：**
1. 右键单击目标公会（在“基地”选项卡、地图查看器或“公会”选项卡中）。
2. 选择**导入库**（单个文件）或**导入库（多文件）**。
3. 选择导出的 `.json` 文件。

**克隆基地：**
1. 右键单击一个碱基 → **克隆碱基**。
2. 选择目标公会。
3. 底座采用偏移定位克隆。

**调整基础半径：**
1. 右键单击底座 → **调整半径**。
2. 输入新的半径 (50%–1000%)。
3. 保存并重新加载游戏中的保存内容以重新分配结构。

</details>





---




<div align="center">

## 故障排除

<img src="https://readme-typing-svg.demolab.com?lines=%E5%BD%93%E4%BA%8B%E6%83%85%E5%87%BA%E7%8E%B0%E5%B2%94%E5%AD%90%E6%97%B6;%E4%B8%8D%E8%A6%81%E6%83%8A%E6%85%8C;%E6%88%91%E4%BB%AC%E5%B7%B2%E7%BB%8F%E7%9C%8B%E5%88%B0%E4%BA%86%E8%BF%99%E4%B8%80%E5%88%87&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### “未找到 VCRUNTIME140.dll”(Windows)

安装 [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022)。

### 解析保存时的 `struct.error`

保存文件格式已过时。在游戏中加载保存（单人、合作或专用服务器）一次以触发自动结构更新，然后重试。确保在最新游戏补丁时或之后更新了保存。

### GamePass 转换器不工作

1.完全关闭GamePass版本的Palworld。
2. 等待几分钟，让文件句柄释放。
3. 运行GamePass → Steam 转换器。
4. 在GamePass上启动Palworld进行验证。

### Linux / macOS 二进制文件无法启动

- **Linux:** `chmod +x PalworldSaveTools-*-linux.AppImage` 将其标记为可执行。
- **macOS：** 如果被 Gatekeeper 阻止，请右键单击 → **打开**，或运行 `xattr -d com.apple.quarantine /path/to/app`。





---




<div align="center">

## 从源代码构建

<img src="https://readme-typing-svg.demolab.com?lines=%E8%87%AA%E5%B7%B1%E7%BC%96%E8%AF%91%E4%B8%80%E4%B8%8B;%E5%BB%BA%E7%AB%8B%E4%BD%A0%E8%87%AA%E5%B7%B1%E7%9A%84;%E4%BB%8E%E6%BA%90%E4%BB%A3%E7%A0%81%E5%88%B0%E4%BA%8C%E8%BF%9B%E5%88%B6%E6%96%87%E4%BB%B6&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST 支持两种构建路径。 CI/CD 管道使用 Nuitka 来跨平台发布二进制文件； cx_Freeze 用于本地 Windows 安装程序。

### Nuitka（跨平台 — 由 CI/版本使用）

需要 Python 3.11+ 和 `uv`。 Nuitka 会自动安装。

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

输出转到 `dist/`：
- Windows → `dist/PalworldSaveTools-*.exe`
- Linux → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → 打包为 `.dmg`

### cx_Freeze（Windows 安装程序）

对于本地 Windows `.zip` 包：

```
scripts\build_cx.cmd
```

这将在项目根目录中创建 `PST_standalone_v{version}.zip` 。

### 交互式生成器

用于选择构建模式的交互式菜单：

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## 贡献

<img src="https://readme-typing-svg.demolab.com?lines=%E6%83%B3%E5%B8%AE%E5%BF%99%E5%90%97%EF%BC%9F%E6%96%B9%E6%B3%95%E5%A6%82%E4%B8%8B;%E5%8A%A0%E5%85%A5%E5%9B%A2%E9%98%9F;%E6%AF%8F%E4%B8%80%E6%AC%A1%E8%B4%A1%E7%8C%AE%E9%83%BD%E5%BE%88%E9%87%8D%E8%A6%81&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

欢迎贡献！请随时提交 Pull 请求。

1. 分叉存储库。
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)。
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4. 推送到分支 (`git push origin feature/AmazingFeature`)。
5. 打开拉取请求。





---




<div align="center">

## 免责声明

<img src="https://readme-typing-svg.demolab.com?lines=%E5%9C%A8%E7%A0%B4%E5%9D%8F%E6%9F%90%E4%BA%9B%E4%B8%9C%E8%A5%BF%E4%B9%8B%E5%89%8D%E8%AF%B7%E9%98%85%E8%AF%BB%E6%9C%AC%E6%96%87;%E4%BD%A0%E5%B7%B2%E8%A2%AB%E8%AD%A6%E5%91%8A%E8%BF%87;%E5%85%88%E5%A4%87%E4%BB%BD%EF%BC%81;%E5%87%AD%E5%80%9F%E7%9D%80%E5%BC%BA%E5%A4%A7%E7%9A%84%E5%8A%9B%E9%87%8F...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

**使用此工具的风险由您自行承担。在进行任何修改之前，请务必备份您的保存文件。**

开发人员对任何保存数据丢失或使用此工具可能出现的问题不承担任何责任。





---




<div align="center">

## 支持

<img src="https://readme-typing-svg.demolab.com?lines=%E6%88%91%E4%BB%AC%E4%B8%BA%E6%82%A8%E6%8F%90%E4%BE%9B%E6%94%AF%E6%8C%81;%E9%9C%80%E8%A6%81%E5%B8%AE%E5%8A%A9%E5%90%97%EF%BC%9F;%E6%88%91%E4%BB%AC%E9%9A%8F%E6%97%B6%E4%B8%BA%E6%82%A8%E6%9C%8D%E5%8A%A1&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

- **Discord：** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub 问题：** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Nexus 模组：** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## 许可证

<img src="https://readme-typing-svg.demolab.com?lines=%E9%BA%BB%E7%9C%81%E7%90%86%E5%B7%A5%E5%AD%A6%E9%99%A2%E2%80%94%E2%80%94%E5%81%9A%E4%BD%A0%E6%83%B3%E5%81%9A%E7%9A%84%E4%BA%8B;%E5%83%8F%E5%95%A4%E9%85%92%E4%B8%80%E6%A0%B7%E5%85%8D%E8%B4%B9;%E5%BC%80%E6%BA%90%EF%BC%8C%E5%BC%80%E6%94%BE%E7%9A%84%E5%BF%83%E6%80%81&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

该项目根据 MIT 许可证获得许可 - 有关详细信息，请参阅 [license](license) 文件。





---




<div align="center">

## Palworld 团队

<img src="https://readme-typing-svg.demolab.com?lines=%E9%AD%94%E6%B3%95%E8%83%8C%E5%90%8E%E7%9A%84%E4%BA%BA%E4%BB%AC;%E8%AE%A4%E8%AF%86%E5%9B%A2%E9%98%9F;%E5%85%85%E6%BB%A1%E6%BF%80%E6%83%85%E5%9C%B0%E5%BB%BA%E9%80%A0&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

如果没有背后的人，这个项目就不会存在。

### 活跃维护者

**[Pylar](https://github.com/deafdudecomputers)** — 这一切的始作俑者。这个工具的每一行都可以追溯到他对保存引擎、GUI 和您每天使用的功能的愿景和不懈的工作。

**[cyrix](https://github.com/CyrixJD115)** — 重构者和子维护者。专注于代码质量、简化和结构改进——随着项目的发展，保持代码库干净、更小、更易于维护。

### 贡献者

**[dkoz](https://github.com/dkoz)** — ID 背后的人。提供游戏数据 ID、对 ID 代码的结构洞察，以及对 Palworld 数据如何连接在一起的深入了解，从而使工具在每次游戏更新时保持准确。

**[oMaN-Rod](https://github.com/oMaN-Rod)** — 提供了该项目派生的原始保存解析器。如果没有他在破解 Palworld 保存格式方面的基础工作，这一切都不会存在。该分支简化了他的解析器，成为今天的 PST。
**[Okaetsu](https://github.com/Okaetsu)** — 修改见解，使基本导入/导出成为可能。他对 Palworld 如何从模组方面构建基础数据的理解弥合了模组和保存编辑之间的差距，使这一功能成为现实。





---




<div align="center">

## 致谢

<img src="https://readme-typing-svg.demolab.com?lines=%E4%BF%A1%E7%94%A8%E5%88%B0%E6%9C%9F%E7%9A%84%E5%9C%B0%E6%96%B9;%E8%B0%A2%E8%B0%A2%E5%A4%A7%E5%AE%B6;%E6%88%91%E4%BB%AC%E7%AB%99%E5%9C%A8%E8%82%A9%E8%86%80%E4%B8%8A&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

非常感谢：

- **Palworld** 由 Pocketpair, Inc. 开发 - 这款游戏将我们所有人聚集在一起。
- **错误报告者** - 提交的每个问题、发现的每个边缘案例、粘贴在 Discord 中的每条日志。您可以通过每个报告使该工具更加强大。
- **Palworld 模组社区** — 模组制作者、工具开发者和修补者，他们分享知识、逆向工程格式并推动生态系统向前发展。这个项目是建立在集体努力的基础上的。
- **所有贡献者和社区成员** - 无论您是提交了 PR、在 Discord 中回答了问题，还是只是向朋友介绍了 PST - 谢谢。

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**用 ❤️ 为 Palworld 社区制作**

[⬆ Back to Top](#palworld-save-tools)

</div>