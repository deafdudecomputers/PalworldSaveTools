# 《幻兽帕鲁》简体中文中英对照词汇表

> 适用范围：PalworldSaveTools 2.4.0 与《幻兽帕鲁》1.0 数据。
> 生成日期：2026-08-31。界面显示名采用游戏 `zh-Hans` 简体中文文本；内部 `asset` / 存档 ID 始终保持原样。

## 资料来源与使用原则

- [Palworld Save Pal 游戏数据镜像](https://github.com/oMaN-Rod/palworld-save-pal/tree/63fb57b4619605f80f17abc4fb6fc62e80ed7142/data/json/l10n)（固定提交 `63fb57b46196`）：游戏资源导出的英文与 `zh-Hans` 本地化表。
- [Palworld.gg 简体中文数据库](https://palworld.gg/zh-Hans/)：用于交叉核验帕鲁、主动技能和被动技能的公开显示名称。
- [PalDB 伙伴技能数据库](https://paldb.cc/cn/Partner_Skill)：用于按帕鲁内部 ID 对齐中英文伙伴技能名与效果说明。
- [PalMods 被动技能 ID 参考](https://www.palmods.gg/docs/authors/game-ids/passive-skills)：用于核对存档内部被动技能 ID 与显示词条的边界。
- 本文档只翻译玩家可见文本。`asset`、`EPalWazaID::...`、`BOSS_...` 等标识是存档协议的一部分，不得翻译或写回中文。
- 同一帕鲁的头目、暴走、强袭等特殊个体沿用本体中文名，并追加“头目 / 暴走 / 强袭”等形态标签。

## 核心术语

| English | 简体中文 | 说明 |
|---|---|---|
| Pal | 帕鲁 | 游戏生物的统一称呼；不要译作“好友”或“伙伴”。 |
| Palbox | 帕鲁终端 | 基地核心建筑及帕鲁管理界面。 |
| Palpedia | 帕鲁图鉴 | 帕鲁登记、捕获次数与图鉴浏览。 |
| Party | 队伍 | 玩家当前携带的帕鲁队伍。 |
| Base Pal | 据点帕鲁 | 分配到据点工作的帕鲁。 |
| Global Pal Storage | 全局帕鲁仓库 | 跨世界使用的全局帕鲁存储。 |
| Active Skill | 主动技能 | 帕鲁在战斗中主动施放的招式。 |
| Passive Skill / Trait | 被动技能 / 词条 | 帕鲁固有的增益或减益特性。 |
| Partner Skill | 伙伴技能 | 特定帕鲁独有、由玩家触发或常驻的能力。 |
| Work Suitability | 工作适应性 | 生火、浇水、采矿等据点工作能力。 |
| Alpha / Boss | 头目 | 大型头目帕鲁；内部 ID 通常带 BOSS_ 前缀。 |
| Predator Pal | 暴走帕鲁 | 特殊暴走个体；内部 ID 通常带 PREDATOR_ 前缀。 |
| Raid Boss | 强袭头目 | 通过祭坛等方式挑战的强袭头目。 |
| Lucky Pal | 幸运帕鲁 | 带有幸运特征的稀有大型个体。 |
| Awakened | 觉醒 | 帕鲁的觉醒状态标记。 |
| Rank | 星级 | 帕鲁浓缩后的星级，不译作“排名”。 |
| Soul Enhancement | 帕鲁之魂强化 | 使用帕鲁之魂提升个体属性。 |
| IV / Talent | 个体值（IV） | 生命、攻击、防御的先天数值。 |
| SAN | SAN 值 | 帕鲁的精神状态数值。 |
| Satiety | 饱腹度 | 角色或帕鲁的饥饿状态数值。 |
| Guild | 公会 | 玩家与据点所属的组织。 |
| Base | 据点 | 由帕鲁终端建立的玩家据点。 |
| Inventory | 物品栏 | 玩家或容器持有的物品集合。 |
| Slot | 栏位 | 物品栏、队伍或帕鲁终端中的位置。 |
| Save | 存档 | Level.sav、玩家 .sav 等游戏存档；不要译作“保存文件”。 |

## 属性

| Internal ID | English | 简体中文 |
|---|---|---|
| `Dark` | Dark | 暗属性 |
| `Dragon` | Dragon | 龙属性 |
| `Earth` | Ground | 地属性 |
| `Electricity` | Electric | 雷属性 |
| `Fire` | Fire | 火属性 |
| `Ice` | Ice | 冰属性 |
| `Leaf` | Grass | 草属性 |
| `Normal` | Neutral | 无属性 |
| `Water` | Water | 水属性 |

## 工作适应性

| Internal ID | English | 简体中文 |
|---|---|---|
| `Collection` | Gathering | 采集 |
| `Cool` | Cooling | 冷却 |
| `Deforest` | Lumbering | 伐木 |
| `EmitFlame` | Kindling | 生火 |
| `GenerateElectricity` | Generating Electricity | 发电 |
| `Handcraft` | Handiwork | 手工作业 |
| `Mining` | Mining | 采矿 |
| `MonsterFarm` | Farming | 牧场 |
| `OilExtraction` | Crude Oil Extraction | 原油提取 |
| `ProductMedicine` | Medicine Production | 制药 |
| `Seeding` | Planting | 播种 |
| `Transport` | Transporting | 搬运 |
| `Watering` | Watering | 浇水 |

## 帕鲁名称

| 图鉴编号 | English | 简体中文 | Asset ID |
|---:|---|---|---|
| 001 | Lamball | 棉悠悠 | `SheepBall` |
| 002 | Cattiva | 捣蛋猫 | `PinkCat` |
| 003 | Chikipi | 皮皮鸡 | `ChickenPal` |
| 004 | Lifmunk | 翠叶鼠 | `Carbunclo` |
| 005 | Fuack | 冲浪鸭 | `Blueplatypus` |
| 005b | Fuack Ignis | 热浪鸭 | `BluePlatypus_Fire` |
| 006 | Vixy | 玉藻狐 | `CuteFox` |
| 007 | Celaray | 鲁米儿 | `FlyingManta` |
| 007b | Celaray Lux | 雷米儿 | `FlyingManta_Thunder` |
| 008 | Cremis | 米露菲 | `WoolFox` |
| 009 | Croajiro | 武道蛙 | `KendoFrog` |
| 009b | Croajiro Noct | 极道蛙 | `KendoFrog_Dark` |
| 010 | Herbil | 达鼠泥 | `LeafMomonga` |
| 011 | Teafant | 壶小象 | `Ganesha` |
| 012 | Gumoss | 叶泥泥 | `PlantSlime` |
| 013 | Pupperai | 宗铭丸 | `SamuraiDog` |
| 014 | Clovee | 幸叶茸 | `CloverFairy` |
| 015 | Jolthog | 电棘鼠 | `Hedgehog` |
| 015b | Jolthog Cryst | 冰刺鼠 | `Hedgehog_Ice` |
| 016 | Depresso | 瞅什魔 | `NegativeKoala` |
| 017 | Pengullet | 企丸丸 | `Penguin` |
| 017b | Pengullet Lux | 闪丸丸 | `Penguin_Electric` |
| 018 | Penking | 企丸王 | `CaptainPenguin` |
| 018b | Penking Lux | 闪丸王 | `CaptainPenguin_Black` |
| 019 | Hoocrates | 啼卡尔 | `WizardOwl` |
| 020 | Melpaca | 美露帕 | `Alpaca` |
| 021 | Kingpaca | 君王美露帕 | `KingAlpaca` |
| 021b | Kingpaca Cryst | 冰帝美露帕 | `KingAlpaca_ice` |
| 022 | Daedream | 寐魔 | `DreamDemon` |
| 023 | Tanzee | 新叶猿 | `Monkey` |
| 023b | Tanzee Ignis | 秋叶猿 | `Monkey_Fire` |
| 024 | Nox | 露娜蒂 | `NightFox` |
| 025 | Flambelle | 融焰娘 | `LavaGirl` |
| 026 | Rooby | 燎火鹿 | `FlameBambi` |
| 027 | Mau | 喵丝特 | `Bastet` |
| 027b | Mau Cryst | 冰丝特 | `Bastet_Ice` |
| 028 | Rushoar | 草莽猪 | `Boar` |
| 029 | Foxparks | 火绒狐 | `Kitsunebi` |
| 029b | Foxparks Cryst | 雪绒狐 | `Kitsunebi_Ice` |
| 030 | Killamari | 勾魂鱿 | `NegativeOctopus` |
| 030b | Killamari Primo | 蚀魂鱿 | `NegativeOctopus_Neutral` |
| 031 | Fuddler | 遁地鼠 | `CuteMole` |
| 032 | Eikthyrdeer | 紫霞鹿 | `Deer` |
| 032b | Eikthyrdeer Terra | 祇岳鹿 | `Deer_Ground` |
| 033 | Direhowl | 猎狼 | `Garm` |
| 034 | Caprity | 灌木羊 | `BerryGoat` |
| 034b | Caprity Noct | 郁木羊 | `BerryGoat_Dark` |
| 035 | Swee | 毛掸儿 | `MopBaby` |
| 036 | Sweepa | 毛老爹 | `MopKing` |
| 037 | Turtacle | 盔盔仔 | `TentacleTurtle` |
| 037b | Turtacle Terra | 金盔仔 | `TentacleTurtle_Ground` |
| 038 | Hangyu | 吊缚灵 | `WindChimes` |
| 038b | Hangyu Cryst | 冰缚灵 | `WindChimes_Ice` |
| 039 | Woolipop | 棉花糖 | `SweetsSheep` |
| 039b | Woolipop Terra | 可可棉花糖 | `SweetsSheep_Ground` |
| 040 | Mozzarina | 波霸牛 | `Cowpal` |
| 041 | Azurobe | 碧海龙 | `BlueDragon` |
| 041b | Azurobe Cryst | 碧月龙 | `BlueDragon_Ice` |
| 042 | Sparkit | 伏特喵 | `ElecCat` |
| 043 | Kelpsea | 水灵儿 | `Kelpie` |
| 043b | Kelpsea Ignis | 火灵儿 | `Kelpie_Fire` |
| 044 | Ribbuny | 姬小兔 | `PinkRabbit` |
| 044b | Ribbuny Botan | 艾小兔 | `PinkRabbit_Grass` |
| 045 | Jelliette | 海月仙 | `JellyfishFairy` |
| 046 | Jellroy | 海月灵 | `JellyfishGhost` |
| 047 | Amione | 莉欧·莉涅 | `ClioneTwins` |
| 048 | Gloopie | 墨沫姬 | `OctopusGIrl` |
| 048b | Gloopie Primo | 梦沫姬 | `OctopusGirl_Neutral` |
| 049 | Galeclaw | 天擒鸟 | `Eagle` |
| 050 | Wispaw | 念影喵 | `GhostBlackCat` |
| 051 | Nitewing | 疾风隼 | `HawkBird` |
| 052 | Tombat | 猫蝠怪 | `CatBat` |
| 053 | Tocotoco | 炸蛋鸟 | `ColorfulBird` |
| 054 | Univolt | 雷角马 | `Kirin` |
| 054b | Univolt Cryst | 凌角马 | `Kirin_ice` |
| 055 | Gobfin | 鲨小子 | `SharkKid` |
| 055b | Gobfin Ignis | 红小鲨 | `SharkKid_Fire` |
| 056 | Loupmoon | 月镰魔 | `Werewolf` |
| 056b | Loupmoon Cryst | 霜镰魔 | `Werewolf_Ice` |
| 057 | Cawgnito | 黑鸦隐士 | `DarkCrow` |
| 058 | Arsox | 炽焰牛 | `FlameBuffalo` |
| 059 | Muffly | 雪绵啾 | `FluffyBird` |
| 060 | Bristla | 荊棘魔仙 | `LittleBriarRose` |
| 061 | Cinnamoth | 幻悦蝶 | `CuteButterfly` |
| 062 | Puffolt | 电汪汪 | `ElecPomeranian` |
| 063 | Elphidran | 精灵龙 | `FairyDragon` |
| 063b | Elphidran Aqua | 水灵龙 | `FairyDragon_Water` |
| 064 | Vanwyrm | 烽歌龙 | `BirdDragon` |
| 064b | Vanwyrm Cryst | 霜歌龙 | `BirdDragon_Ice` |
| 065 | Felbat | 夜幕魔蝠 | `CatVampire` |
| 066 | Vaelet | 薇莉塔 | `VioletFairy` |
| 067 | Beegarde | 骑士蜂 | `SoldierBee` |
| 068 | Elizabee | 女皇蜂 | `QueenBee` |
| 069 | Lovander | 博爱蜥 | `PinkLizard` |
| 070 | Grintale | 笑魇猫 | `NaughtyCat` |
| 071 | Tarantriss | 桃蛛娘 | `PurpleSpider` |
| 072 | Polapup | 香草豹冰 | `IceSeal` |
| 072b | Polapup Terra | 巧克力豹冰 | `IceSeal_Ground` |
| 073 | Leezpunk | 朋克蜥 | `LizardMan` |
| 073b | Leezpunk Ignis | 热血蜥 | `LizardMan_Fire` |
| 074 | Gorirat | 铁拳猿 | `Gorilla` |
| 074b | Gorirat Terra | 石掌猿 | `Gorilla_Ground` |
| 075 | Surfent | 滑水蛇 | `Serpent` |
| 075b | Surfent Terra | 流沙蛇 | `Serpent_Ground` |
| 076 | Robinquill | 羽箭射手 | `RobinHood` |
| 076b | Robinquill Terra | 山岳射手 | `RobinHood_Ground` |
| 077 | Flopie | 波娜兔 | `FlowerRabbit` |
| 078 | Wixen | 焰巫狐 | `FoxMage` |
| 078b | Wixen Noct | 幽巫狐 | `FoxMage_Dark` |
| 079 | Katress | 暗巫猫 | `CatMage` |
| 079b | Katress Ignis | 炽巫猫 | `CatMage_Fire` |
| 080 | Helzephyr | 雷冥鸟 | `HadesBird` |
| 080b | Helzephyr Lux | 雷鸣鸟 | `HadesBird_Electric` |
| 081 | Elgrove | 密林陶洛斯 | `GrassMinotaur` |
| 081b | Elgrove Cryst | 冰峰陶洛斯 | `GrassMinotaur_Ice` |
| 082 | Lunaris | 秘斯媞雅 | `Mutant` |
| 083 | Fenglope | 云海鹿 | `FengyunDeeper` |
| 083b | Fenglope Lux | 雷隐鹿 | `FengyunDeeper_Electric` |
| 084 | Dinossom | 花冠龙 | `FlowerDinosaur` |
| 084b | Dinossom Lux | 雷冠龙 | `FlowerDinosaur_Electric` |
| 085 | Bushi | 浪刃武士 | `Ronin` |
| 085b | Bushi Noct | 鬼刃武士 | `Ronin_Dark` |
| 086 | Munchill | 肚肚鳄 | `IceCrocodile` |
| 087 | Mammorest | 森猛犸 | `GrassMammoth` |
| 087b | Mammorest Cryst | 雪猛犸 | `GrassMammoth_Ice` |
| 088 | Finsider | 布偶鲨 | `StuffedShark` |
| 088b | Finsider Ignis | 粉粉布偶鲨 | `StuffedShark_Fire` |
| 089 | Petallia | 花丽娜 | `FlowerDoll` |
| 089b | Petallia Ignis | 樱丽娜 | `FlowerDoll_Fire` |
| 090 | Leafan | 莉芳 | `PandaGirl` |
| 091 | Incineram | 炎魔羊 | `Baphomet` |
| 091b | Incineram Noct | 暗魔羊 | `Baphomet_Dark` |
| 092 | Dazzi | 雷鸣童子 | `RaijinDaughter` |
| 092b | Dazzi Noct | 天阴童子 | `RaijinDaughter_Water` |
| 093 | Pyrin | 火麒麟 | `FireKirin` |
| 093b | Pyrin Noct | 邪麒麟 | `FireKirin_Dark` |
| 094 | Relaxaurus | 佩克龙 | `LazyDragon` |
| 094b | Relaxaurus Lux | 派克龙 | `LazyDragon_Electric` |
| 095 | Foxcicle | 吹雪狐 | `IceFox` |
| 096 | Beakon | 迅雷鸟 | `ThunderBird` |
| 096b | Beakon Cryst | 疾霜鸟 | `ThunderBird_Ice` |
| 097 | Ghangler | 冥灯鱼 | `GhostAnglerfish` |
| 097b | Ghangler Ignis | 炙灯鱼 | `GhostAnglerfish_Fire` |
| 098 | Rayhound | 霹雳犬 | `ThunderDog` |
| 098b | Rayhound Cryst | 凛光犬 | `ThunderDog_Ice` |
| 099 | Menasting | 冥铠蝎 | `DarkScorpion` |
| 099b | Menasting Terra | 金铠蝎 | `DarkScorpion_Ground` |
| 100 | Needoll | 球抱苞 | `CactusDoll` |
| 100b | Needoll Noct | 妖抱苞 | `CactusDoll_Dark` |
| 101 | Reindrix | 严冬鹿 | `IceDeer` |
| 102 | Mossanda | 叶胖达 | `GrassPanda` |
| 102b | Mossanda Lux | 雷胖达 | `GrassPanda_Electric` |
| 103 | Chillet | 疾旋鼬 | `WeaselDragon` |
| 103b | Chillet Ignis | 桃旋鼬 | `WeaselDragon_Fire` |
| 104 | Ragnahawk | 燧火鸟 | `RedArmorBird` |
| 105 | Moldron | 流焰龙 | `VolcanoDragon` |
| 105b | Moldron Cryst | 川霜龙 | `VolcanoDragon_Ice` |
| 106 | Palumba | 咕咕桑葩 | `TropicalOstrich` |
| 107 | Digtoise | 碎岩龟 | `DrillGame` |
| 108 | Broncherry | 连理龙 | `SakuraSaurus` |
| 108b | Broncherry Aqua | 海誓龙 | `SakuraSaurus_Water` |
| 109 | Dumud | 趴趴鲶 | `LazyCatfish` |
| 109b | Dumud Gild | 梆梆鲶 | `LazyCatfish_Gold` |
| 110 | Braloha | 梁叶龙 | `Plesiosaur` |
| 111 | Kitsun | 苍焰狼 | `AmaterasuWolf` |
| 111b | Kitsun Noct | 幽焰狼 | `AmaterasuWolf_Dark` |
| 112 | Blazehowl | 狱焰王 | `Manticore` |
| 112b | Blazehowl Noct | 狱阎王 | `Manticore_Dark` |
| 113 | Warsect | 铠格力斯 | `HerculesBeetle` |
| 113b | Warsect Terra | 格鲁力斯 | `HerculesBeetle_Ground` |
| 114 | Frostplume | 白真雪雀 | `SnowPeafowl` |
| 115 | Majex | 紫狐娇 | `DarkFlameFox` |
| 116 | Sibelyx | 绸笠蛾 | `WhiteMoth` |
| 116b | Sibelyx Primo | 绢笠蛾 | `WhiteMoth_Neutral` |
| 117 | Maraith | 噬魂兽 | `GhostBeast` |
| 118 | Shroomer | 菇咚 | `MushroomDragon` |
| 118b | Shroomer Noct | 菇波 | `MushroomDragon_Dark` |
| 119 | Icelyn | 冰姬灵 | `IceWitch` |
| 120 | Gildra | 缚乃伊 | `MummyPal` |
| 121 | Jormuntide | 覆海龙 | `Umihebi` |
| 121b | Jormuntide Ignis | 腾炎龙 | `Umihebi_Fire` |
| 122 | Suzaku | 朱雀 | `Suzaku` |
| 122b | Suzaku Aqua | 清雀 | `Suzaku_Water` |
| 123 | Dazemu | 战冠雀 | `FeatherOstrich` |
| 124 | Quivern | 天羽龙 | `SkyDragon` |
| 124b | Quivern Botan | 翠羽龙 | `SkyDragon_Grass` |
| 125 | Lullu | 春彩娘 | `LeafPrincess` |
| 126 | Kikit | 球犰 | `SmallArmadillo` |
| 127 | Yakumo | 八云犬 | `GuardianDog` |
| 128 | Skutlass | 鞘刀鱼 | `SwordCutlassFish` |
| 128b | Skutlass Ignis | 炼刃鱼 | `SwordCutlassFish_Fire` |
| 129 | Reptyro | 熔岩兽 | `Volcanicmonster` |
| 129b | Reptyro Cryst | 寒霜兽 | `VolcanicMonster_Ice` |
| 130 | Starryon | 夜冥驹 | `NightBlueHorse` |
| 130b | Starryon Primo | 日耀驹 | `NightBlueHorse_Neutral` |
| 131 | Pierdon | 磐峰兽 | `RockBeast` |
| 131b | Pierdon Cryst | 寒峰兽 | `RockBeast_Ice` |
| 132 | Cryolinx | 冰棘兽 | `WhiteTiger` |
| 132b | Cryolinx Terra | 金棘兽 | `WhiteTiger_Ground` |
| 133 | Snugloo | 雪墩墩 | `SmallYeti` |
| 134 | Wumpo | 白绒雪怪 | `Yeti` |
| 134b | Wumpo Botan | 绿苔绒怪 | `Yeti_Grass` |
| 135 | Sootseer | 恐炬灵 | `CandleGhost` |
| 136 | Carnibora | 颚莉丝 | `VenusFlytrap` |
| 137 | Blazamut | 焰煌 | `KingBahamut` |
| 137b | Blazamut Ryu | 殁殃 | `KingBahamut_Dragon` |
| 138 | Dualith | 双心岩傀 | `GrassGolem` |
| 138b | Dualith Noct | 咒心岩傀 | `GrassGolem_Dark` |
| 139 | Anubis | 阿努比斯 | `Anubis` |
| 140 | Sekhmet | 塞赫麦特 | `Sekhmet` |
| 141 | Prixter | 蛊刺妖 | `ScorpionMan` |
| 141b | Prixter Lux | 电针妖 | `ScorpionMan_Electric` |
| 142 | Tetroise | 重岩龟 | `CubeTurtle` |
| 142b | Tetroise Primo | 净岩龟 | `CubeTurtle_Neutral` |
| 143 | Nyafia | 妮瞅莎 | `BadCatGirl` |
| 144 | Mimog | 旺财 | `MimicDog` |
| 145 | Xenovader | 杰诺贝达 | `DarkAlien` |
| 146 | Xenogard | 杰诺路达 | `WhiteAlienDragon` |
| 147 | Prunelia | 梅莉姆 | `BlueberryFairy` |
| 148 | Nitemary | 魅爱莉 | `GhostRabbit` |
| 148b | Nitemary Botan | 碧艾莉 | `GhostRabbit_Grass` |
| 149 | Smokie | 墨丸 | `BlackPuppy` |
| 149b | Smokie Cryst | 冬丸 | `BlackPuppy_Ice` |
| 150 | Omascul | 面惧 | `MysteryMask` |
| 151 | Whalaska | 凉晶鲸 | `IceNarwhal` |
| 151b | Whalaska Ignis | 桃晶鲸 | `IceNarwhal_Fire` |
| 152 | Verdash | 踏春兔 | `GrassRabbitMan` |
| 153 | Splatterina | 幽恋娜 | `GrimGirl` |
| 154 | Gildane | 金驰兽 | `GoldenHorse` |
| 155 | Dogen | 汪宗师 | `SifuDog` |
| 156 | Bulldosu | 力士獒 | `SumoDog` |
| 157 | Celesdir | 净世鹿 | `WhiteDeer` |
| 157b | Celesdir Noct | 织夜鹿 | `WhiteDeer_Dark` |
| 158 | Astegon | 魔渊龙 | `BlackMetalDragon` |
| 159 | Knocklem | 泰锋 | `WingGolem` |
| 159b | Knocklem Ignis | 丹烽 | `WingGolem_Fire` |
| 160 | Silvegis | 艾基鲁迦 | `WhiteShieldDragon` |
| 161 | Azurmane | 驭雷马 | `BlueThunderHorse` |
| 162 | Valentail | 喵璐璐 | `LongCat` |
| 163 | Snock | 电涡蜗 | `ElecSnail` |
| 163b | Snock Terra | 金涡蜗 | `ElecSnail_Ground` |
| 164 | Souffline | 蒲蒲飞芽 | `DandelionGirl` |
| 165 | Lapiron | 詹兔曼 | `BrownRabbit` |
| 166 | Hoodle | 兜兜灵 | `HoodGhost` |
| 167 | Slowatt | 电懒懒 | `ElecLizard` |
| 168 | Bakemi | 吓丝妮 | `OniGhostGirl` |
| 169 | Solmora | 曼波王 | `KingSunfish` |
| 169b | Solmora Lux | 曼波皇 | `KingSunfish_Thunder` |
| 170 | Lapure | 兔绣袖 | `SleeveRabbit` |
| 171 | Eidrolon | 灵曦龙 | `GhostDragon` |
| 171b | Eidrolon Ignis | 狱熙龙 | `GhostDragon_Fire` |
| 172 | Dynamoff | 雷云鹫 | `ThunderFluffyBird` |
| 173 | Tropicaw | 大红呱 | `RedFlowerBird` |
| 174 | Flaracle | 昭炎狐 | `FoxExorcist` |
| 175 | Ophydia | 沁莲龙 | `LotusDragon` |
| 176 | Dupin | 拉比耶尔 | `ClownRabbit` |
| 177 | Roujay | 盗影鸦 | `ThiefBird` |
| 178 | Venusa | 梅杜娜 | `SnakeGirl` |
| 179 | Mycora | 红菇娘 | `MushroomLady` |
| 180 | Loomen | 妖焰灯 | `LanternButler` |
| 181 | Wistella | 缀夜星 | `MoonChild` |
| 182 | Solenne | 墨罗娜 | `MonochromeQueen` |
| 183 | Renjishi | 燎火舞伶 | `KabukiMan` |
| 184 | Aegidron | 磐甲龙 | `DomeArmorDragon` |
| 185 | Grizzbolt | 暴电熊 | `ElecPanda` |
| 186 | Lyleen | 百合女王 | `LilyQueen` |
| 186b | Lyleen Noct | 黑月女王 | `LilyQueen_Dark` |
| 187 | Orserk | 波鲁杰克斯 | `ThunderDragonMan` |
| 188 | Faleris | 荷鲁斯 | `Horus` |
| 188b | Faleris Aqua | 伊西斯 | `Horus_Water` |
| 189 | Shadowbeak | 异构格里芬 | `BlackGriffon` |
| 190 | Selyne | 辉月伊 | `MoonQueen` |
| 191 | Bastigor | 霜牙王 | `SnowTigerBeastMan` |
| 192 | Shaolong | 霄龙 | `BlueSkyDragon` |
| 193 | Silvance | 暮尘蛾 | `Mothman` |
| 194 | Dandilord | 夜蔓爵 | `FlowerPrince` |
| 195 | Bellanoir | 贝菈诺娃 | `NightLady` |
| 195b | Bellanoir Libero | 贝菈露洁 | `NightLady_Dark` |
| 196 | Xenolord | 杰诺多兰 | `DarkMechaDragon` |
| 197 | Hartalis | 默世鹿 | `LegendDeer` |
| 198 | Paladius | 圣光骑士 | `SaintCentaur` |
| 199 | Necromus | 混沌骑士 | `BlackCentaur` |
| 200 | Frostallion | 唤冬兽 | `IceHorse` |
| 200b | Frostallion Noct | 唤夜兽 | `IceHorse_Dark` |
| 201 | Neptilius | 海皇鲸 | `PoseidonOrca` |
| 202 | Jetragon | 空涡龙 | `JetDragon` |
| 203 | Panthalus | 奥沧鲸 | `KingWhale` |
| 204 | Astralym | 枯星龙 | `WorldTreeDragon` |

## 伙伴技能

| 帕鲁 | Partner Skill | 伙伴技能 | 中文效果 | Asset ID |
|---|---|---|---|---|
| 棉悠悠 | Fluffy Shield | 茸茸盾牌 | 发动后，它会化身为装备在玩家身上的盾牌。 将它分派到家畜牧场，它就有机会掉落羊毛。 | `SheepBall` |
| 捣蛋猫 | Cat Helper | 跟猫借手手 | 若它在队伍中，捣蛋猫就会帮忙载运行李，玩家的负重上限将提高(100~200)。（不可叠加） | `PinkCat` |
| 皮皮鸡 | Egg Layer | 产蛋 | 将它分派到家畜牧场，它就有机会产下蛋。 | `ChickenPal` |
| 翠叶鼠 | Lifmunk Recoil | 翠叶鼠出击 | 发动后它会坐在玩家的头上，配合玩家的攻击用冲锋枪进行追击。 科技11 | `Carbunclo` |
| 热浪鸭 | Fire Tackle | 热浪滚滚 | 发动后，热浪鸭会乘着焰浪冲向敌人。 | `BluePlatypus_Fire` |
| 玉藻狐 | Dig Here! | 挖掘指导 | 将它分派到家畜牧场，它就有机会从地里挖出道具。 | `CuteFox` |
| 鲁米儿 | Zephyr Glider | 微风滑翔 | 若它在队伍中，会改变滑翔伞的性能，并使玩家免受坠落伤害。 滑翔期间能够长时间快速移动。 | `FlyingManta` |
| 雷米儿 | Jolt Glider | 电风滑翔 | 若它在队伍中，会改变滑翔伞的性能，并使玩家免受坠落伤害。 滑翔期间能够长时间快速移动。 | `FlyingManta_Thunder` |
| 米露菲 | Fluffy Wool | 蓬松毛毛 | 若它在队伍中，无属性帕鲁的攻击力会提升(15~30)%。（不可叠加） 将它分派到家畜牧场，它就有机会掉落羊毛。 | `WoolFox` |
| 武道蛙 | Leap Stance | 蓄势跳跃 | 发动后，武道蛙会靠忠诚心和膨胀的腹部积蓄力量。玩家在踩上去后能高高跳起。 在落地前，玩家的攻击力提升(50~86)%。 | `KendoFrog` |
| 极道蛙 | Shadow Stance | 蓄势暗跃 | 发动后，极道蛙会靠忠诚心和膨胀的腹部积蓄力量。 玩家在踩上去后能高高跳起。 若它在队伍中，玩家和帕鲁以暗属性攻击克制的属性时伤害提升(25~40)%。（不可叠加） | `KendoFrog_Dark` |
| 达鼠泥 | Herbil Pulse | 起搏鼠鼠 | 若它在队伍中，达鼠泥会在玩家陷入濒死状态时，通过疗愈能力让玩家以最大HP(30~60)%的状态复活。 | `LeafMomonga` |
| 壶小象 | Soothing Shower | 疗伤之浴 | 若它在队伍中，若玩家的生命值低于30%，恢复(20~40)%的生命值。（不可叠加） ※发动后需120秒冷却方可再次触发 | `Ganesha` |
| 叶泥泥 | Logging Assistance | 樵夫啦啦队 | 若它在队伍中，玩家伐木时造成的伤害将提升(30~50)%，所有木材种类的重量都将减轻(40~60)%。（不可叠加） | `PlantSlime` |
| 宗铭丸 | Best Boy | 干劲支援 | 若它在队伍中，玩家使用近战武器时的伤害提升(10~35)%。（不可叠加） | `SamuraiDog` |
| 幸叶茸 | Happy Clover | 幸运三叶草 | 若它在据点里，其他据点帕鲁的采集工作适应性等级+1。（不可叠加） | `CloverFairy` |
| 电棘鼠 | Jolt Bomb | 电击炸弹 | 发动后就能将电棘鼠装备在手上，若将它投向敌人且命中目标，便会引发雷属性爆炸。 | `Hedgehog` |
| 冰刺鼠 | Cold Bomb | 冻结炸弹 | 发动后就能将冰刺鼠装备在手上，若将它投向敌人且命中目标，便会引发冰属性爆炸。 | `Hedgehog_Ice` |
| 瞅什魔 | Caffeine Inoculation | 摄取咖啡因 | 发动后，瞅什魔会大量饮用能量饮料，瞅什魔的移动速度和工作速度会因此提升(100~900)%。 将它分派到家畜牧场，它就有机会掉落毒腺。 | `NegativeKoala` |
| 企丸丸 | Pengullet Launcher | 企丸丸发射 | 发动后玩家将装备火箭发射器，并可将企丸丸当作炮弹射出。 命中目标后企丸丸会爆炸，并陷入濒死状态。 科技17 | `Penguin` |
| 闪丸丸 | Pengullet Lux Launcher | 闪丸丸发射 | 发动后玩家将装备火箭发射器，并可将闪丸丸当作炮弹射出。 命中目标后闪丸丸会爆炸，并陷入濒死状态。 科技18 | `Penguin_Electric` |
| 企丸王 | Brave Sailor | 勇敢的海之战士 | 若它在队伍中，击倒火属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） | `CaptainPenguin` |
| 闪丸王 | Unyielding Storm Commander | 不屈的雷击船长 | 若它在队伍中，玩家和帕鲁以水属性攻击克制的属性时伤害提升(25~40)%。（不可叠加） | `CaptainPenguin_Black` |
| 啼卡尔 | Dark Knowledge | 暗影睿智 | 若它在队伍中，暗属性帕鲁的攻击力会提升(15~30)%。（不可叠加） | `WizardOwl` |
| 美露帕 | Pacapaca Wool | 蓬蓬羊毛 | 可骑在它的背上移动。 若它在队伍中，君王美露帕的防御力和移动速度将会提升。 将它分派到家畜牧场，它就有机会掉落羊毛。 科技7 | `Alpaca` |
| 君王美露帕 | King of Muscles | 大力国王 | 可骑在它的背上移动。 此帕鲁的防御力和移动速度会按照队伍中美露帕的数量提升，每只增加(5~14)%。 科技23 | `KingAlpaca` |
| 寐魔 | Dream Chaser | 逐梦者 | 若它在队伍中，就会出现于玩家身边。 它会用暗属性的魔弹追击敌对个体。 且该追击不会使猎物毙命。 | `DreamDemon` |
| 新叶猿 | Cheery Rifle | 猴急步枪 | 发动后，新叶猿会在一定时间内用突击步枪猛烈扫射附近的敌人。 科技12 | `Monkey` |
| 秋叶猿 | Chipper Chimp Gunfire | 枪火奇猿 | 发动后，秋叶猿会在一定时间内以火属性突击步枪猛烈扫射附近的敌人。 科技13 | `Monkey_Fire` |
| 露娜蒂 | Kuudere | 冷娇 | 发动后，它会探测附近的帕鲁雕像。 | `NightFox` |
| 融焰娘 | Magma Tears | 熔岩之泪 | 若它在队伍中，非战斗时每秒令玩家与队伍帕鲁的生命值恢复(0.1~0.5)%。（不可叠加） 将它分派到家畜牧场，它就有机会掉落喷火器官。 | `LavaGirl` |
| 燎火鹿 | Tiny Spark | 微小火种 | 若它在队伍中，火属性帕鲁的防御力会提升(15~30)%。（不可叠加） 将它分派到家畜牧场，它就有机会掉落喷火器官。 | `FlameBambi` |
| 喵丝特 | Gold Digger | 招财猫 | 将它分派到家畜牧场，它就有机会从地里挖出金币。 | `Bastet` |
| 冰丝特 | Icy Whispers | 晴天冰雳 | 将它分派到家畜牧场，它就有机会掉落结冰器官。 | `Bastet_Ice` |
| 草莽猪 | Hard Head | 坚硬头壳 | 可骑在它的背上移动。 骑乘期间破坏岩石的效率将提升(500~2000)%。 科技6 | `Boar` |
| 火绒狐 | Huggy Fire | 抱抱火焰 | 发动后，它会化身为装备在玩家身上的火焰喷射器。 科技6 | `Kitsunebi` |
| 雪绒狐 | Huggy Frost | 抱抱寒冰 | 发动后，它会化身为装备在玩家身上的冷冻喷射器。 科技24 | `Kitsunebi_Ice` |
| 勾魂鱿 | Fried Squid | 炸鱿鱼 | 若它在队伍中，会改变滑翔伞的性能。 滑翔期间能够长时间漂浮在空中。 | `NegativeOctopus` |
| 蚀魂鱿 | Fried Killamari | 炸鱿鱼 | 若它在队伍中，会改变滑翔伞的性能。 滑翔期间能够长时间漂浮在空中。 | `NegativeOctopus_Neutral` |
| 遁地鼠 | Mining Assistance | 矿工啦啦队 | 若它在队伍中，玩家采矿时造成的伤害将提升(30~60)%，石头的重量将减轻(80~100)%。（不可叠加） | `CuteMole` |
| 紫霞鹿 | Guardian of the Forest | 森林守护者 | 可骑在它的背上移动。 骑乘期间可以进行2段跳跃，破坏树木的效率也会提升(220~500)%。 科技12 | `Deer` |
| 祇岳鹿 | Guardian of the Golden Forest | 金之森守护者 | 可骑在它的背上移动。骑乘期间可以进行2段跳跃。 若它在据点里，其他据点帕鲁的伐木工作适应性等级+1。（不可叠加） 科技21 | `Deer_Ground` |
| 猎狼 | Direhowl Rider | 猎狼骑手 | 可骑在它的背上移动。 骑乘期间的移动速度会稍微变快一点。 科技9 | `Garm` |
| 灌木羊 | Berry Picker | 采摘野莓 | 将它分派到家畜牧场，就有机会从背上掉落红色野莓。 若它在队伍中，每5分钟会让当前饱腹度最低的帕鲁恢复(100~200)点饱腹度。（不可叠加） | `BerryGoat` |
| 郁木羊 | Venom Picker | 采摘毒腺 | 将它分派到家畜牧场，有机会从背上掉落毒腺。 若它在队伍中，每5分钟会让当前饱腹度最低的帕鲁恢复(100~200)点饱腹度。（不可叠加） | `BerryGoat_Dark` |
| 毛掸儿 | Fluffy | 毛茸茸茸茸 | 若它在队伍中，毛老爹的防御力和攻击力会有所提升。 | `MopBaby` |
| 毛老爹 | King of Fluff | 毛茸茸之王 | 可骑在它的背上移动。 此帕鲁的防御力和攻击力会按照队伍中毛掸儿的数量提升，每只增加(12~24)%。 科技20 | `MopKing` |
| 盔盔仔 | Spikey Carrier | 尖刺刺运输 | 若它在队伍中，金属矿石的重量会减轻(80~100)%。（不可叠加） | `TentacleTurtle` |
| 金盔仔 | Shiny Hauler | 亮闪闪运输 | 若它在队伍中，硫磺和石炭的重量将减轻(80~100)%，且玩家和帕鲁以地属性攻击克制的属性时伤害提升(25~40)%。（不可叠加） | `TentacleTurtle_Ground` |
| 吊缚灵 | Flying Trapeze | 空中秋千 | 若它在队伍中，会改变滑翔伞的性能。 滑翔期间能够缓缓上升。 | `WindChimes` |
| 冰缚灵 | Winter Trapeze | 寒空秋千 | 若它在队伍中，会改变滑翔伞的性能。 滑翔期间能够缓缓上升。 | `WindChimes_Ice` |
| 棉花糖 | Candy Pop | 糖果甜心 | 将它分派到家畜牧场，它就有机会掉落棉花糖。 若它在据点里，据点帕鲁的饱腹度的减少幅度将会(-10~-20)%。（不可叠加） | `SweetsSheep` |
| 可可棉花糖 | Bitter Pop | 苦涩甜心 | 将它分派到家畜牧场，它就有机会掉落焦糖棉花糖。 若它在据点里，据点帕鲁的饱腹度的减少幅度将会(-15~-25)%。（不可叠加） | `SweetsSheep_Ground` |
| 碧海龙 | Waterwing Dance | 水翔之舞 | 可骑在它的背上在水上移动。 骑乘期间玩家的攻击会转变为水属性，且攻击力提升(5~20)%。 科技24 | `BlueDragon` |
| 碧月龙 | Icewing Dance | 冰翔之舞 | 可骑在它的背上在水上移动。 骑乘期间玩家的攻击会转变为冰属性，且攻击力提升(5~20)%。 科技27 | `BlueDragon_Ice` |
| 伏特喵 | Static Electricity | 静电 | 若它在队伍中，雷属性帕鲁的攻击力会提升(15~30)%。（不可叠加） 将它分派到家畜牧场，它就有机会掉落发电器官。 | `ElecCat` |
| 水灵儿 | Aqua Spout | 洒水 | 若它在队伍中，水属性帕鲁的攻击力会提升(15~30)%。（不可叠加） 将它分派到家畜牧场，它就有机会掉落水栖帕鲁的黏液。 | `Kelpie` |
| 火灵儿 | Lava Spout | 熔岩泼洒 | 若它在队伍中，火属性帕鲁的攻击力会提升(15~30)%。（不可叠加） 将它分派到家畜牧场，它就有机会掉落喷火器官。 | `Kelpie_Fire` |
| 姬小兔 | Happy-Go-Lucky Bunny | 微笑公主兔 | 若它在队伍中，无属性帕鲁的攻击力会提升(15~30)%。（不可叠加） 若它在据点里，其他据点帕鲁的手工作业工作适应性等级+1。（不可叠加） | `PinkRabbit` |
| 艾小兔 | Ground 'n' Pound | 暴力青草兔 | 若它在队伍中，玩家和帕鲁以草属性攻击克制的属性时伤害提升(25~40)%。（不可叠加） 艾小兔在武器制作台或武器工厂等处工作时，工作效率将会提升(200~400)%。 | `PinkRabbit_Grass` |
| 海月仙 | Jelliette Drop | 海月仙祝福 | 若它在队伍中，垂钓时获得的道具增加(55~95)%。（不可叠加） 此外，当海月仙和海月灵同时在据点里时，海月仙浇水的工作速度提升(50~120)%。（不可叠加） | `JellyfishFairy` |
| 海月灵 | Jellroy Drop | 海月灵祝福 | 若它在队伍中，打捞时获得的道具增加(55~95)%。（不可叠加） 此外，当海月仙和海月灵同时在据点里时，海月灵浇水的工作速度提升(50~120)%。（不可叠加） | `JellyfishGhost` |
| 莉欧·莉涅 | Magical Twin Powers | 魔力双子 | 若它在据点里，其他据点帕鲁的浇水工作适应性等级+1。（不可叠加） | `ClioneTwins` |
| 梦沫姬 | Cephalo-Princess | 咬咬姬 | 若它在队伍中，水属性帕鲁的防御力提升(15~30)%。（不可叠加） | `OctopusGirl_Neutral` |
| 天擒鸟 | Galeclaw Glider | 天擒鸟滑翔 | 若它在队伍中，会改变滑翔伞的性能。 能够高速滑翔，且右手能在滑翔期间使用枪械射击。 | `Eagle` |
| 念影喵 | Death-Cheating Feline | 附体灵猫 | 若它在队伍中，触发背面奖励时的捕获概率增加。（不可叠加） | `GhostBlackCat` |
| 疾风隼 | Travel Companion | 旅伴 | 可骑在它的背上在空中飞行。 科技15 | `HawkBird` |
| 猫蝠怪 | Ultrasonic Sensor | 猫妖感应 | 发动后能够发出超声波，来探测附近地下城、宝箱以及废品的位置。 | `CatBat` |
| 炸蛋鸟 | Eggbomb Launcher | 炸蛋发射器 | 发动后会化身为装备在玩家身上的发射器，并制造出会爆炸的蛋。 科技18 | `ColorfulBird` |
| 雷角马 | Swift Deity | 疾风迅雷 | 可骑在它的背上移动。 若它在队伍中，玩家和帕鲁以雷属性攻击克制的属性时伤害提升(25~40)%。（不可叠加） 科技14 | `Kirin` |
| 鲨小子 | Angry Shark | 易怒鲨鲨 | 发动后会以水枪攻击锁定的目标敌人。 此帕鲁使用的水枪的威力将提升至(1.1~2.5)倍。 若它在队伍中，玩家的攻击力提升(10~20)%。 | `SharkKid` |
| 红小鲨 | Angry Shark | 易怒鲨鲨 | 发动后会以烈焰溅射攻击锁定的目标敌人。 此帕鲁使用的烈焰溅射的威力将提升至(1.1~2.5)倍。 若它在队伍中，玩家的攻击力提升(10~20)%。 | `SharkKid_Fire` |
| 月镰魔 | Dark Gleam Strike | 黑暗中的闪亮利爪 | 发动后会以飞跃爪击攻击锁定的目标敌人。 此帕鲁使用的飞跃爪击的威力将提升至(1.1~2.5)倍。 若它在队伍中，玩家的近战武器攻击速度提升(15~30)%。（不可叠加） | `Werewolf` |
| 霜镰魔 | Frozen Gleam Strike | 冰结利爪 | 发动后会以吹雪爪击攻击锁定的目标敌人。 此帕鲁使用的吹雪爪击的威力将提升至(1.1~2.5)倍。 若它在队伍中，玩家的近战武器攻击速度提升(15~30)%。（不可叠加） | `Werewolf_Ice` |
| 黑鸦隐士 | Eerie Nightstreaker | 夜袭怪鸟 | 发动后可以使用夜视，即使在黑暗中也能看得一清二楚。 再次发动即可解除该效果。 将它分派到家畜牧场，它就有机会从地里挖出骨头。 | `DarkCrow` |
| 炽焰牛 | Warm Body | 温暖之躯 | 可骑在它的背上移动。 若它在队伍中，玩家的耐寒能力+2。（不可叠加） 科技15 | `FlameBuffalo` |
| 雪绵啾 | Fluffy Flutterer | 软萌圆圆鸟 | 若它在队伍中，提升对陷入冻结状态帕鲁的捕获概率。（不可叠加） | `FluffyBird` |
| 荊棘魔仙 | Princess Gaze | 公主的视线 | 若它在队伍中，草属性帕鲁的攻击力会提升(15~30)%。（不可叠加） | `LittleBriarRose` |
| 幻悦蝶 | Mysterious Scales | 神秘鳞粉 | 发动后会以毒雾攻击锁定的目标敌人。 若它在据点里，其他据点帕鲁的牧场的工作适应性等级+1。（不可叠加） | `CuteButterfly` |
| 电汪汪 | Crackle Booster | 电光强化 | 若它在据点里，其他据点帕鲁的发电工作适应性等级+1。（不可叠加） | `ElecPomeranian` |
| 精灵龙 | Amicable Holy Dragon | 善良的圣洁之龙 | 可骑在它的背上在空中飞行。 飞行时移动速度会提升。 若它在队伍中，击倒暗属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） 科技20 | `FairyDragon` |
| 水灵龙 | Amicable Water Dragon | 善良的流水之龙 | 可骑在它的背上在空中飞行。 飞行时移动速度会提升。 若它在队伍中，玩家和帕鲁受到的火属性伤害减轻(15~30)%，并且不会陷入点燃状态。（不可叠加） 科技32 | `FairyDragon_Water` |
| 烽歌龙 | Aerial Marauder | 大空袭击者 | 可骑在它的背上在空中飞行。 若它在队伍中，玩家攻击敌方弱点部位造成的伤害将提升(20~40)%。（不可叠加） 科技21 | `BirdDragon` |
| 霜歌龙 | Aerial Marauder | 大空袭击者 | 可骑在它的背上在空中飞行。 若它在队伍中，玩家攻击敌方弱点部位造成的伤害将提升(30~50)%。（不可叠加） 科技22 | `BirdDragon_Ice` |
| 夜幕魔蝠 | Life Steal | 窃取生命 | 与它并肩作战时，会为玩家和夜幕魔蝠赋予生命窃取效果，攻击造成伤害时将恢复等同于伤害量(5~9)%的HP。 | `CatVampire` |
| 薇莉塔 | Purification of Gaia | 大地净化 | 若它在队伍中，击倒地属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） 将它分派到家畜牧场，它就有机会掉落各种各样的种子。 | `VioletFairy` |
| 骑士蜂 | Worker Bee | 工蜂 | 将它分派到家畜牧场，它就有机会掉落蜂蜜。 若它在队伍中，女皇蜂的攻击力会有所提升。 | `SoldierBee` |
| 女皇蜂 | Queen Bee Command | 女王蜂的统率 | 此帕鲁的攻击力会按照队伍中骑士蜂的数量提升，每只增加(12~24)%。 | `QueenBee` |
| 博爱蜥 | Heart Drain | 爱心吸取 | 与它并肩作战时，会为玩家和博爱蜥赋予生命窃取效果，攻击造成伤害时将恢复等同于伤害量(5~9)%的HP。 | `PinkLizard` |
| 笑魇猫 | Glaring Cat's Eye | 猫眼逼人 | 可骑在它的背上移动。 若它在队伍中，捡到帕鲁蛋时将有(50~75)%的概率再捡到1颗。（不可叠加） 科技19 | `NaughtyCat` |
| 桃蛛娘 | Tarantriss’ Web | 桃色之网 | 可骑在它的背上移动。 骑乘期间可以进行2段跳跃， 并向射击地点发射蜘蛛丝，牵引身体快速移动。 科技20 | `PurpleSpider` |
| 香草豹冰 | Rider of the Snowy Mountain | 滑雪行家 | 可骑在它的背上移动。 在雪地上时，移动速度提升(80~160)%。 并且可以在斜坡处快速向下滑行。 科技26 | `IceSeal` |
| 巧克力豹冰 | Snowy Mountain Slider | 雪山速滑 | 可骑在它的背上移动。 在雪地上时，移动速度提升(80~160)%。 并且可以在斜坡处快速向下滑行。 滑行时初始速度较慢，但最高速度更快。 科技55 | `IceSeal_Ground` |
| 朋克蜥 | Too Cool to be Seen | 透明化 | 发动后(10~20)秒内，朋克蜥与玩家将变得透明，在敌方视野中隐去身形。 | `LizardMan` |
| 热血蜥 | Too Cool to be Seen | 透明化 | 发动后(10~20)秒内，热血蜥与玩家将变得透明，在敌方视野中隐去身形。 | `LizardMan_Fire` |
| 铁拳猿 | Full-Power Gorilla Mode | 火力全开大猩猩模式 | 发动后会解放野性之力，并在一定时间内铁拳猿的攻击力将提升(75~300)%。 | `Gorilla` |
| 石掌猿 | Full-Power Gorilla Pound | 火力全开铁臂大猩猩 | 若它在队伍中，玩家的攀爬速度提升(50~100)%。（不可叠加） | `Gorilla_Ground` |
| 滑水蛇 | Swift Swimmer | 滑滑水蛇 | 可骑在它的背上在水上移动。 将它分派到家畜牧场，它就有机会掉落皮革。 科技16 | `Serpent` |
| 流沙蛇 | Sand Swimmer | 滑滑沙蛇 | 可骑在它的背上移动。 若它在队伍中，会为玩家的攻击附加(2~6)点泥泞异常状态值。（不可叠加） 科技25 | `Serpent_Ground` |
| 羽箭射手 | Grounded Archer | 射箭达人 | 若它在队伍中，玩家使用弓箭时的伤害提升(10~35)%。（不可叠加） | `RobinHood` |
| 山岳射手 | Master Archer | 挽弓达人 | 若它在队伍中，玩家使用弓箭时的蓄力速度提升(15~30)%。（不可叠加） | `RobinHood_Ground` |
| 波娜兔 | Helper Bunny | 兔兔助手 | 若它在队伍中，就会出现在玩家身边。 它会自动前去拾取附近的道具。 | `FlowerRabbit` |
| 焰巫狐 | Lord Fox | 狐神大人 | 发动后，焰巫狐会将力量分给玩家，让玩家的攻击转变为火属性，且攻击力提升(30~50)%。 | `FoxMage` |
| 幽巫狐 | Black Fox Lord | 巫神大人 | 发动后，幽巫狐会将力量分给玩家，让玩家的攻击转变为暗属性，且攻击力提升(30~50)%。 | `FoxMage_Dark` |
| 暗巫猫 | Mystical Black Magic | 怪奇黑魔法 | 若它在队伍中，击倒无属性帕鲁时获得的掉落道具增加(40~80)%。 此外，玩家投掷帕鲁球时，有(10~50)%的概率不会消耗帕鲁球。（不可叠加） | `CatMage` |
| 炽巫猫 | Blazing Black Magic | 热情黑魔法 | 若它在据点里，其他据点帕鲁的生火工作适应性等级+1。（不可叠加） | `CatMage_Fire` |
| 雷冥鸟 | Wings of Death | 冥府之翼 | 可骑在它的背上在空中飞行。 骑乘期间玩家的攻击会转变为暗属性，且攻击力提升(5~20)%。 科技25 | `HadesBird` |
| 雷鸣鸟 | Wings of Thunder | 雷鸣之翼 | 可骑在它的背上在空中飞行。 骑乘期间玩家的攻击会转变为雷属性，且攻击力提升(5~20)%。 科技47 | `HadesBird_Electric` |
| 密林陶洛斯 | Mother Nature's Menace | 大自然之威 | 发动后，密林陶洛斯会将力量分给玩家，让玩家的攻击转变为草属性，且攻击力提升(30~50)%。 | `GrassMinotaur` |
| 冰峰陶洛斯 | Father Winter's Threat | 永冻土之威 | 若它在队伍中，玩家攻击浸湿状态的敌人时，一击就会让敌人陷入冻结状态。 | `GrassMinotaur_Ice` |
| 秘斯媞雅 | Antigravity | 反重力 | 若它在队伍中，投掷出去的帕鲁球将会自动追踪帕鲁，且玩家的负重上限提高(300~600)。 （不可叠加） | `Mutant` |
| 云海鹿 | Wind and Clouds | 风云 | 可骑在它的背上移动。 骑乘期间可以进行2段跳跃。 科技26 | `FengyunDeeper` |
| 雷隐鹿 | Stormcloud | 雷云 | 可骑在它的背上移动。 骑乘期间可以进行2段跳跃。 若它在队伍中，击倒水属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） 科技57 | `FengyunDeeper_Electric` |
| 花冠龙 | Fragrant Dragon | 馥郁花香之龙 | 可骑在它的背上移动。 若它在队伍中，龙属性帕鲁的防御力会提升(15~30)%。（不可叠加） 科技24 | `FlowerDinosaur` |
| 雷冠龙 | Thunder Dragon | 落雷绽放之龙 | 可骑在它的背上移动。 若它在队伍中，雷属性帕鲁的防御力会提升(15~30)%。（不可叠加） 科技34 | `FlowerDinosaur_Electric` |
| 浪刃武士 | Brandish Blade | 紫电一闪 | 发动后会以居合斩攻击锁定的目标敌人。 此帕鲁使用的居合斩的威力将提升至(1.1~2.5)倍。 | `Ronin` |
| 鬼刃武士 | Void Blade | 秘技·紫电一闪 | 发动后会以居合斩攻击锁定的目标敌人。 此帕鲁使用的居合斩的威力将提升至(1.1~2.5)倍。 若它在队伍中，玩家的近战武器攻击伤害在非战斗时提升(30~65)%。（不可叠加） | `Ronin_Dark` |
| 肚肚鳄 | Icy Maw | 雪盆大口 | 若它在队伍中，食材和料理的重量会减轻(30~60)%。并在冰属性帕鲁原有的防腐效果基础上，让腐败速度进一步(-30~-80)%。（不可叠加） | `IceCrocodile` |
| 森猛犸 | Gaia Crusher | 盖亚粉碎者 | 可骑在它的背上移动。 骑乘期间破坏树木的效率会提高(220~500)%，破坏矿石的效率会提高(500~2000)%。 科技28 | `GrassMammoth` |
| 雪猛犸 | Ice Crusher | 冰霜粉碎者 | 可骑在它的背上移动。 骑乘期间破坏树木的效率会提高(220~500)%，破坏矿石的效率会提高(500~2000)%。 科技41 | `GrassMammoth_Ice` |
| 布偶鲨 | Water Gun | 水流扳机 | 发动后，布偶鲨会将力量分给玩家，让玩家的攻击转变为水属性，且攻击力提升(30~50)%。 | `StuffedShark` |
| 粉粉布偶鲨 | Ember Chamber | 炎炎收纳间 | 若它在队伍中，粉粉布偶鲨会帮忙分担负重，背包内武器的重量减轻(60~100)%，且玩家和帕鲁以火属性攻击克制的属性时伤害提升(25~40)%。（不可叠加） | `StuffedShark_Fire` |
| 花丽娜 | Blessing of the Flower Spirit | 花精灵的祝福 | 发动后可通过花朵的治愈能力，来恢复玩家(75~85)%的生命值。 若它在据点里，其他据点帕鲁的播种工作适应性等级+1。（不可叠加） | `FlowerDoll` |
| 樱丽娜 | Passion of the Flower Spirit | 花精灵的热情 | 发动后，它会用花朵的治愈之力让玩家的生命值恢复(80~90)%。 若它在队伍中，玩家和帕鲁受到的草属性伤害减轻(15~30)%，并且不会陷入缠绕状态。（不可叠加） | `FlowerDoll_Fire` |
| 莉芳 | Selfless Discipline | 克己复礼 | 莉芳的攻击力和防御力，会随着队伍中其他草属性帕鲁的数量提升，每只增加(2~6)%。 | `PandaGirl` |
| 炎魔羊 | Flameclaw Hunter | 焰爪猎人 | 发动后会以狱火爪攻击锁定的目标敌人。 此帕鲁使用的狱火爪的威力将提升至(1.1~2.5)倍。 | `Baphomet` |
| 暗魔羊 | Darkclaw Hunter | 黑爪猎人 | 发动后会以恶梦爪攻击锁定的目标敌人。 此帕鲁使用的恶梦爪的威力将提升至(1.1~2.5)倍。 | `Baphomet_Dark` |
| 雷鸣童子 | Lady of Lightning | 雷电姑娘 | 若它在队伍中，就会出现于玩家身边。 它会用雷属性的落雷追击敌对个体。 且该追击不会使猎物毙命。 | `RaijinDaughter` |
| 天阴童子 | Lady of Dark Lightning | 乌云姑娘 | 若它在队伍中，就会出现于玩家身边。 它会用暗属性的落雷追击敌对个体。 且该追击不会使猎物毙命。 | `RaijinDaughter_Water` |
| 火麒麟 | Red Hare | 赤兔马 | 可骑在它的背上移动。 骑乘期间玩家的攻击会转变为火属性，且攻击力提升(5~20)%。 科技29 | `FireKirin` |
| 邪麒麟 | Black Hare | 黑兔马 | 可骑在它的背上移动。 骑乘期间玩家的攻击会转变为暗属性，且攻击力提升(5~20)%。 科技34 | `FireKirin_Dark` |
| 佩克龙 | Hungry Missile | 饿饿飞弹 | 可骑在它的背上移动。 骑乘期间它还能用导弹发射器连续攻击。 科技45 | `LazyDragon` |
| 派克龙 | Missile Party | 飞弹盛宴 | 可骑在它的背上移动。 骑乘期间它还能用导弹发射器连续攻击。 科技48 | `LazyDragon_Electric` |
| 吹雪狐 | Aurora Guide | 极光的指引 | 若它在队伍中，冰属性帕鲁的攻击力会提升(15~30)%。（不可叠加） 将它分派到家畜牧场，它就有机会掉落结冰器官。 | `IceFox` |
| 迅雷鸟 | Thunderous | 天雷 | 可骑在它的背上在空中飞行。 骑乘期间玩家的攻击会转变为雷属性，且攻击力提升(5~20)%。 迅雷鸟的移动速度，会随着队伍中其他雷属性帕鲁的数量提升，每只增加(5~25)%。 科技29 | `ThunderBird` |
| 疾霜鸟 | Coldsnap | 天霰 | 可骑在它的背上在空中飞行。 骑乘期间玩家的攻击会转变为冰属性，且攻击力提升(5~20)%。 疾霜鸟的移动速度，会随着队伍中其他冰属性帕鲁的数量提升，每只增加(5~25)%。 科技71 | `ThunderBird_Ice` |
| 冥灯鱼 | Master of Darkness | 暗夜引路人 | 可骑在它的背上在水上移动。 冥灯鱼的移动速度，会随着队伍中其他暗属性或水属性帕鲁的数量提升，每只增加(5~25)%。 科技31 | `GhostAnglerfish` |
| 炙灯鱼 | Abyssal Celebrity Chef | 深海名厨 | 可骑在它的背上在水上移动。 炙灯鱼的移动速度，会随着队伍中其他火属性或水属性帕鲁的数量提升，每只增加(5~25)%。 科技42 | `GhostAnglerfish_Fire` |
| 霹雳犬 | Lightning Shepherd | 雷雳跃行 | 可骑在它的背上移动。 骑乘期间可以进行2段跳跃。 霹雳犬的移动速度，会随着队伍中其他雷属性帕鲁的数量提升，每只增加(5~25)%。 科技30 | `ThunderDog` |
| 凛光犬 | Snow Shepherd | 霜跃疾行 | 可骑在它的背上移动。 骑乘期间可以进行2段跳跃。 若它在队伍中，冰属性帕鲁的防御力会提升(15~30)%。（不可叠加） 科技32 | `ThunderDog_Ice` |
| 冥铠蝎 | Steel Scorpion | 钢铁之蝎 | 若它在队伍中，玩家的防御力将提升(5~10)%，且击倒雷属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） | `DarkScorpion` |
| 金铠蝎 | Golden Scorpion | 黄金之蝎 | 若它在队伍中，玩家的防御力将提升(5~10)%，且击倒雷属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） | `DarkScorpion_Ground` |
| 球抱苞 | Hug Me Please | 请你抱抱我 | 若它在队伍中，玩家和帕鲁对缠绕状态的敌人造成的伤害将提升(50~65)%。（不可叠加） | `CactusDoll` |
| 妖抱苞 | Hug You So Much | 紧紧抱住你 | 若它在队伍中，会为玩家的攻击附加(2~6)点缠绕异常状态值。（不可叠加） | `CactusDoll_Dark` |
| 严冬鹿 | Cool Body | 冰凉之躯 | 可骑在它的背上移动。 若它在队伍中，玩家的耐暑能力+2。（不可叠加） 科技31 | `IceDeer` |
| 叶胖达 | Grenadier Panda | 不良熊猫 | 可骑在它的背上移动。 骑乘期间它还能用榴弹发射器连续攻击。 科技32 | `GrassPanda` |
| 雷胖达 | Grenadier Panda | 不良熊猫 | 可骑在它的背上移动。 骑乘期间它还能用榴弹发射器连续攻击。 科技34 | `GrassPanda_Electric` |
| 疾旋鼬 | Wriggling Weasel | 扭扭鼬鼬 | 可骑在它的背上移动。 骑乘期间玩家的攻击会转变为龙属性，且攻击力提升(5~20)%。 科技11 | `WeaselDragon` |
| 桃旋鼬 | Sparkling Weasel | 烧鼬鼬 | 可骑在它的背上移动。 骑乘期间玩家的攻击会转变为火属性，且攻击力提升(5~20)%。 科技40 | `WeaselDragon_Fire` |
| 燧火鸟 | Flame Wing | 烈焰之翼 | 可骑在它的背上在空中飞行。 骑乘期间玩家的攻击会转变为火属性，且攻击力提升(5~20)%。 科技33 | `RedArmorBird` |
| 流焰龙 | Magma Overload | 熔岩霸主 | 可骑在它的背上移动。 流焰龙的攻击力，会随着队伍中其他火属性或地属性帕鲁的数量提升，每只增加(4~8)%。 科技36 | `VolcanoDragon` |
| 川霜龙 | Ice Overload | 寒冰霸主 | 可骑在它的背上移动。 若它在队伍中，玩家和帕鲁以冰属性攻击克制的属性时伤害提升(25~40)%。（不可叠加） 科技70 | `VolcanoDragon_Ice` |
| 咕咕桑葩 | Samba Step | 桑巴舞步 | 可骑在它的背上移动。 在草地上时，移动速度提高(155~240)%。 科技35 | `TropicalOstrich` |
| 碎岩龟 | Drill Crusher | 钻头粉碎者 | 发动后会进入甲壳回旋状态。 它会一边旋转一边跟随玩家，且破坏矿石的效率将提升(800~2000)%。 | `DrillGame` |
| 连理龙 | Love's First Blossom | 恋香初绽 | 可骑在它的背上移动。 若它在队伍中，捡到的帕鲁蛋将有(35~45)%的概率变为头目帕鲁蛋。（不可叠加） 科技33 | `SakuraSaurus` |
| 海誓龙 | Purity's Full Bloom | 纯心盛绽 | 可骑在它的背上移动。 若它在队伍中，捡到的帕鲁蛋将有(45~55)%的概率变为头目帕鲁蛋。（不可叠加） 科技44 | `SakuraSaurus_Water` |
| 趴趴鲶 | Soil Improver | 改善土质 | 若它在队伍中，地属性帕鲁的攻击力会提升(15~30)%。（不可叠加） 将它分派到家畜牧场，它就有机会掉落优质帕鲁油。 | `LazyCatfish` |
| 梆梆鲶 | Golden Harvest | 黄金丰收 | 若它在队伍中，打倒的敌人掉落的金币提升(100~200)%。（不可叠加） 将它分派到家畜牧场，它就会掉落优质帕鲁油或者小概率掉落金币。 | `LazyCatfish_Gold` |
| 梁叶龙 | Balmy Weather | 暖洋洋晴日 | 可骑在它的背上移动。 若它在据点里，分派到配种牧场的帕鲁产蛋速度加快(20~50)%。（不可叠加） 科技36 | `Plesiosaur` |
| 苍焰狼 | Wolf of the Sun | 日轮之狼 | 可骑在它的背上移动。 若它在队伍中，玩家和帕鲁受到的冰属性伤害减轻(15~30)%，并且不会陷入冻结状态。（不可叠加） 科技57 | `AmaterasuWolf` |
| 幽焰狼 | Gloomhowl | 昙天之狼 | 可骑在它的背上移动。 若它在队伍中，玩家和帕鲁受到的暗属性伤害减轻(15~30)%，并且不会陷入黑暗状态。（不可叠加） 科技59 | `AmaterasuWolf_Dark` |
| 狱焰王 | Hellflame Lion | 狱炎狮子 | 可骑在它的背上移动。 若它在队伍中，击倒草属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） 科技33 | `Manticore` |
| 狱阎王 | Darkflame Lion | 黑炎狮子 | 可骑在它的背上移动。 若它在队伍中，击倒无属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） 科技35 | `Manticore_Dark` |
| 铠格力斯 | Cast-Iron Shell | 攻守一体的黑甲 | 若它在队伍中，当玩家的近战攻击在(5~9)秒内命中5次时，它会在玩家周边生成护盾。（不可叠加） | `HerculesBeetle` |
| 格鲁力斯 | Fullmetal Shell | 攻守一体的金甲 | 若它在队伍中，当玩家的近战攻击在(5~9)秒内命中5次时，它会在玩家周边生成护盾。（不可叠加） | `HerculesBeetle_Ground` |
| 白真雪雀 | Peacock Pounce | 孔雀迅捷 | 若它在队伍中，受到白真雪雀释放的冷气影响，玩家会更专注，武器重新装弹的速度提升(20~50)%。（不可叠加） | `SnowPeafowl` |
| 紫狐娇 | Phantasmal Arcana | 暗狐秘咒 | 若它在队伍中，玩家的攻击击中点燃状态的敌人时，会使敌人周边燃烧，对碰到火焰的敌人持续造成相当于玩家攻击力(15~30)%的伤害。（不可叠加） | `DarkFlameFox` |
| 绸笠蛾 | Silk Shroud | 神秘缠丝者 | 发动后会以钻石星辰攻击锁定的目标敌人。 此帕鲁使用的钻石星辰的威力将提升至(1.1~2.5)倍。 将它分派到家畜牧场，它就有机会制造出优质的布。 | `WhiteMoth` |
| 绢笠蛾 | Gilded Shroud | 神秘缠金丝者 | 若它在队伍中，无属性帕鲁的防御力会提升(15~30)%。（不可叠加） 将它分派到家畜牧场，它就有机会制作优质的布。 | `WhiteMoth_Neutral` |
| 噬魂兽 | Messenger of Death | 冥界使者 | 可骑在它的背上移动。 若它在队伍中，每次打倒敌人时，全体队伍帕鲁的主动技能冷却时间缩短(30~60)%。（不可叠加） 科技37 | `GhostBeast` |
| 菇咚 | Rampant Spores | 飘飘然孢子 | 可骑在它的背上移动。 将它分派到家畜牧场，它就有机会掉落蘑菇或者洞穴蘑菇。 科技39 | `MushroomDragon` |
| 菇波 | Roiling Spores | 幽幽然孢子 | 可骑在它的背上移动。 若它在据点里，菇波的神奇孢子将会使据点内帕鲁的SAN值下降速度减缓(10~15)%。 科技39 | `MushroomDragon_Dark` |
| 冰姬灵 | Witch's Icy Veil | 魔女的冷气 | 发动后，冰姬灵会将力量分给玩家，让玩家的攻击转变为冰属性，且攻击力提升(30~50)%。 | `IceWitch` |
| 缚乃伊 | Resurrection | 黄泉归来 | 与玩家并肩作战时，若缚乃伊陷入濒死状态，缚乃伊会消耗全部的饱腹度并复活。 | `MummyPal` |
| 覆海龙 | Stormbringer Sea Dragon | 呼唤风暴的深海龙 | 可骑在它的背上在水上移动。 若它在队伍中，玩家和帕鲁对浸湿状态的敌人造成的伤害将提升(50~65)%。（不可叠加） 科技40 | `Umihebi` |
| 腾炎龙 | Stormbringer Lava Dragon | 呼唤风暴的熔岩龙 | 可骑在它的背上移动。 若它在队伍中，能让熔岩伤害无效化，且玩家和帕鲁对点燃状态的敌人造成的伤害将提升(50~65)%。（不可叠加） 科技59 | `Umihebi_Fire` |
| 朱雀 | Wings of Flame | 炎之翼 | 可骑在它的背上在空中飞行。 朱雀的移动速度，会随着队伍中其他火属性帕鲁的数量提升，每只增加(5~25)%。 科技43 | `Suzaku` |
| 清雀 | Wings of Water | 水之翼 | 可骑在它的背上在空中飞行。 清雀的移动速度，会随着队伍中其他水属性帕鲁的数量提升，每只增加(5~25)%。 科技44 | `Suzaku_Water` |
| 战冠雀 | Sand Sprint | 飞砂腿 | 可骑在它的背上移动。 在砂地上时，移动速度提高(50~100)%。 科技28 | `FeatherOstrich` |
| 天羽龙 | Sky Dragon Affection | 天空龙的慈爱 | 可骑在它的背上在空中飞行。 若它在队伍中，龙属性帕鲁的攻击力会提升(15~30)%。（不可叠加） 科技38 | `SkyDragon` |
| 翠羽龙 | Grass Dragon Affection | 翠龙的慈爱 | 可骑在它的背上在空中飞行。 骑乘期间玩家的攻击会转变为草属性，且攻击力提升(5~20)%。 科技45 | `SkyDragon_Grass` |
| 春彩娘 | Floral Boost | 繁花告春 | 若它在据点里，春彩娘会为农园注入元气，使作物的生长加速(50~70)%。 | `LeafPrincess` |
| 球犰 | Sandball Soccer | 滚滚沙滩球 | 若它在队伍中，地属性帕鲁的防御力提升(15~30)%。（不可叠加） | `SmallArmadillo` |
| 八云犬 | Birds of a Feather | 物以类聚 | 可骑在它的背上移动。 与它并肩作战时，遇到和它有着相同被动技能的帕鲁的概率将提升(15~30)%。 ※部分被动技能除外 科技41 | `GuardianDog` |
| 寒霜兽 | Ice-Loving Beast | 贪食冰霜之兽 | 可骑在它的背上移动。 若它在队伍中，所有矿石种类的重量会减轻(35~65)%。（不可叠加） 科技43 | `VolcanicMonster_Ice` |
| 夜冥驹 | Night Dancer | 夜舞者 | 可骑在它的背上移动。骑乘期间跳跃能力提升。 夜晚期间，此帕鲁的移动速度提升(50~100)%。（不可叠加） 科技57 | `NightBlueHorse` |
| 日耀驹 | Light Dancer | 光舞者 | 可骑在它的背上移动，骑乘期间跳跃能力提升。 日耀驹的移动速度，会随着队伍中其他无属性帕鲁的数量提升，每只增加(5~25)%。 科技77 | `NightBlueHorse_Neutral` |
| 磐峰兽 | Power Stone | 能量石 | 若它在队伍中，玩家和帕鲁对泥泞状态的敌人造成的伤害将提升(50~65)%。（不可叠加） | `RockBeast` |
| 寒峰兽 | Power Crystal | 能量水晶 | 若它在队伍中，玩家和帕鲁受到的龙属性伤害减轻(15~30)%。（不可叠加） | `RockBeast_Ice` |
| 冰棘兽 | Dragon Hunter | 猎龙者 | 若它在队伍中，击倒龙属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） | `WhiteTiger` |
| 金棘兽 | Explosive Strength | 爆碎铁腕 | 若它在队伍中，攻击击中弱点部位时，下次击中弱点部位的攻击威力提升(30~60)%。（不可叠加） | `WhiteTiger_Ground` |
| 雪墩墩 | Invisible Eye | 不见之眼 | 若它在队伍中，会使玩家不容易被敌人发现。（不可叠加） | `SmallYeti` |
| 白绒雪怪 | Guardian of the Snowy Mountain | 雪山巨人 | 可骑在它的背上移动。 若它在据点里，其他据点帕鲁的搬运工作适应性等级+1。（不可叠加） 科技45 | `Yeti` |
| 绿苔绒怪 | Guardian of the South | 南方巨人 | 可骑在它的背上移动。 若它在队伍中，玩家和帕鲁受到的地属性伤害减轻(15~30)%，并且不会陷入泥泞状态。（不可叠加） 科技51 | `Yeti_Grass` |
| 恐炬灵 | Grave Robber | 古墓烛影 | 若它在队伍中，玩家和帕鲁受到的无属性伤害减轻(15~30)%。（不可叠加） 将它分派到家畜牧场，它就有机会从地里挖出骨头。 | `CandleGhost` |
| 颚莉丝 | Entangling Tongue | 巨舌缠绕 | 若它在队伍中，玩家进行翻滚或滑步动作时，颚莉丝会卷起旋风攻击接触到的敌人（草属性 / 威力: (40~80)）。（不可叠加） | `VenusFlytrap` |
| 焰煌 | Magma Kaiser | 熔岩凯撒 | 可骑在它的背上移动。 若它在队伍中，打倒敌人时，一同并肩作战的帕鲁的攻击力与防御力会提升(5~10)%。 该效果最多可累积5层，持续20秒。（不可叠加） 科技46 | `KingBahamut` |
| 殁殃 | Dragon Kaiser | 巨龙凯撒 | 可骑在它的背上移动。 若它在队伍中，玩家和帕鲁以龙属性攻击克制的属性时伤害提升(25~40)%。（不可叠加） 科技55 | `KingBahamut_Dragon` |
| 双心岩傀 | Forest Laser | 自然光炮 | 可骑在它的背上移动。 骑乘期间，可以从双心岩傀的右手发射草属性的强力激光。 科技48 | `GrassGolem` |
| 咒心岩傀 | Corruption Laser | 枯萎光炮 | 可骑在它的背上移动。 骑乘期间，可以从咒心岩傀的右手发射暗属性的强力激光。 科技69 | `GrassGolem_Dark` |
| 阿努比斯 | Guardian of the Desert | 沙漠守护神 | 发动后，阿努比斯会将力量分给玩家，让玩家的攻击转变为地属性，且攻击力提升(30~50)%。 战斗时偶尔会以高速移步回避攻击。 | `Anubis` |
| 塞赫麦特 | Desert Empress | 沙漠女帝 | 若它在据点里，据点中的阿努比斯的工作速度提升(20~40)%。（不可叠加） 塞赫麦特在工作台或作业工厂等处工作时，工作效率将会提升(30~60)%。 | `Sekhmet` |
| 蛊刺妖 | Phantom Venom | 无毒毒蝎 | 若它在队伍中，玩家和帕鲁对中毒状态的敌人造成的伤害将提升(50~65)%。（不可叠加） | `ScorpionMan` |
| 电针妖 | Scorpion Longwave | 低频脉冲蝎 | 发动后，电针妖会将力量分给玩家，让玩家的攻击转变为雷属性，且攻击力提升(30~50)%。 | `ScorpionMan_Electric` |
| 重岩龟 | Masonry Archelon | 负石古代龟 | 可骑在它的背上移动。 若它在据点里，其他据点帕鲁的采矿工作适应性等级+1。（不可叠加） 科技48 | `CubeTurtle` |
| 净岩龟 | Stone-Chaser Archelon | 逐石古代龟 | 可骑在它的背上移动。 若它在队伍中，武器和防具的耐久度损耗减缓(80~100)%。（不可叠加） 科技75 | `CubeTurtle_Neutral` |
| 旺财 | Master of Unlocking | 撬锁 | 与它并肩作战时，能借助旺财的力量，在不使用钥匙的情况下打开各种等级的宝箱。 但无法打开需要特定工作适应性的宝箱。 | `MimicDog` |
| 杰诺贝达 | Unknown Invader | 未知侵略者 | 若它在队伍中，全自动武器的弹匣中最后一发子弹的伤害提升(100~160)%。（不可叠加） | `DarkAlien` |
| 杰诺路达 | Unknown Intruder | 未知入侵者 | 可骑在它的背上移动。 若它在队伍中，玩家使用能量武器时的伤害提升(10~35)%。（不可叠加） 科技41 | `WhiteAlienDragon` |
| 梅莉姆 | Prayer for Abundant Harvest | 丰收祈愿 | 若它在据点里，梅莉姆会进行祈祷， 让作物的收获量提升(18~35)%。 | `BlueberryFairy` |
| 魅爱莉 | Soul Collector | 夺魂幽灵兔 | 若它在队伍中，击倒帕鲁时帕鲁之魂的获得量提升+(100~200)%。（不可叠加） | `GhostRabbit` |
| 碧艾莉 | Soul Binder | 缚魂幽灵兔 | 若它在队伍中，草属性帕鲁的防御力提升(15~30)%。（不可叠加） | `GhostRabbit_Grass` |
| 墨丸 | Dig, Smokie! Dig! | 忠犬墨丸 | 发动后能够以敏锐的嗅觉，来探测附近铬铁矿的位置。 与它并肩作战时，铬铁矿的掉落量也会提升(100~200)%。 科技58 | `BlackPuppy` |
| 冬丸 | Cryo Instincts | 忠犬冬丸 | 若它在据点里，其他据点帕鲁的冷却工作适应性等级+1。（不可叠加） | `BlackPuppy_Ice` |
| 面惧 | Masquerade Dance | 假面舞会 | 若它在队伍中，队伍帕鲁获得的经验值会提升(40~80)%。（不可叠加） | `MysteryMask` |
| 凉晶鲸 | Chilled Whale Cruiser | 凉冰冰鲸鱼号 | 可骑在它的背上在水上移动。 若它在队伍中，垂钓的捕获计量槽在小游戏开始时的初始位置升高(5~14)%，并且在判定条与鱼的图标重合期间，捕获计量槽的上升量增加(5~14)%。（不可叠加） 科技42 | `IceNarwhal` |
| 桃晶鲸 | Cozy Whale Cruiser | 暖烘烘鲸鱼号 | 可骑在它的背上在水上移动。 若它在队伍中，垂钓的捕获计量槽在小游戏开始时的初始位置升高(7~17)%，并且在判定条与鱼的图标重合期间，捕获计量槽的上升量增加(7~17)%。（不可叠加） 科技71 | `IceNarwhal_Fire` |
| 踏春兔 | Grassland Gymnast | 草原特技之星 | 若它在队伍中，可以额外进行+1次跳跃和+1次空中冲刺。（不可叠加） | `GrassRabbitMan` |
| 幽恋娜 | Blade of Uncontrolled Passion | 狂爱之刃 | 若它在队伍中， 使用切肉刀进行解体时，获得的掉落道具增加(100~200)%。（不可叠加） | `GrimGirl` |
| 金驰兽 | Sandstorm's Blessing | 沙尘加护 | 可骑在它的背上移动。 骑乘期间玩家的攻击会转变为地属性，且攻击力提升(5~20)%。 科技54 | `GoldenHorse` |
| 汪宗师 | Homeward Prayer | 归去来兮 | 发动后可以移动至最近的据点。 无法在地下城里使用。 | `SifuDog` |
| 力士獒 | Yokozuna's Presence | 横纲风范 | 可骑在它的背上移动。 若它在队伍中，玩家和帕鲁受到的雷属性伤害减轻(15~30)%，并且不会陷入感电状态。（不可叠加） 科技53 | `SumoDog` |
| 净世鹿 | Blessing of Purification | 净化的祝福 | 可骑在它的背上移动。 净世鹿的攻击力和移动速度，会随着队伍中其他无属性帕鲁的数量提升，每只增加(2~6)%。 若它在队伍中，非战斗时每秒令玩家与队伍帕鲁的生命值恢复(0.15~0.75)%。（不可叠加） 科技54 | `WhiteDeer` |
| 织夜鹿 | Blessing of Chaos | 混沌的祝福 | 可骑在它的背上移动。 若它在队伍中，一同并肩作战的帕鲁的生命值会逐渐减少，但攻击力将提升(40~80)%。（不可叠加） 科技78 | `WhiteDeer_Dark` |
| 魔渊龙 | Black Ankylosaur | 黑铠之龙 | 可骑在它的背上在空中飞行。 骑乘期间对矿石造成的伤害将提升(1100~3300)%，且金属矿石的掉落量提升(150~300)%。 科技39 | `BlackMetalDragon` |
| 泰锋 | Steel Guardian Mode | 钢铁卫士模式 | 发动后会以钢铁般的意志，在一定时间内提高泰锋的攻击力(50~200)%，防御力(50~200)%。 | `WingGolem` |
| 丹烽 | Iron Guardian Mode | 铁血卫士模式 | 发动后会以钢铁般的意志，在一定时间内提高丹烽的攻击力(60~210)%，防御力(60~210)%。 | `WingGolem_Fire` |
| 艾基鲁迦 | Aegis Shield | 埃癸斯之盾 | 可骑在它的背上移动。 若它在队伍中，玩家的护盾开始修复的等候时间缩短(30~60)%，且护盾受到的伤害减少(65~80)%。（不可叠加） 科技60 | `WhiteShieldDragon` |
| 驭雷马 | Plasma Dash | 电离冲刺 | 可骑在它的背上移动。 此外，可在空中进行冲刺以高速移动。 科技58 | `BlueThunderHorse` |
| 喵璐璐 | Big Stretch | 伸展喵咪 | 若它在队伍中，玩家承受的重力减弱，跳跃或坠落时会漂浮落地。（不可叠加） | `LongCat` |
| 电涡蜗 | Charging Shell | 电电电池 | 若它在队伍中，会为玩家的攻击附加(2~6)点感电异常状态值。（不可叠加） | `ElecSnail` |
| 金涡蜗 | Grounding Shell | 咚咚甲壳 | 若它在队伍中，玩家和帕鲁受到的水属性伤害减轻(15~30)%，并且不会陷入浸湿状态。（不可叠加） | `ElecSnail_Ground` |
| 蒲蒲飞芽 | Fuzzy Fairy | 绒毛妖精 | 若它在队伍中，提升对陷入缠绕状态帕鲁的捕获概率。（不可叠加） | `DandelionGirl` |
| 詹兔曼 | Friend of Earth | 大地是好朋友 | 若它在队伍中，玩家在冲刺期间的防御力提升(50~65)%。（不可叠加） | `BrownRabbit` |
| 兜兜灵 | Void-Dweller | 潜于虚无之物 | 若它在队伍中，玩家对非战斗状态的敌人造成的伤害提升(50~100)%。（不可叠加） | `HoodGhost` |
| 电懒懒 | Chillswitch | 懒懒电键 | 若它在队伍中，玩家的攻击击中感电状态的敌人时，会令敌人放电，对周围的敌人造成相当于玩家攻击力(40~60)%的伤害。（不可叠加） | `ElecLizard` |
| 吓丝妮 | Grinning Death | 播撒欢笑的亡者 | 若它在队伍中，攻击陷入中毒状态的敌人时，会使该敌人的攻击力降低(40~80)%。（不可叠加） | `OniGhostGirl` |
| 曼波王 | Charming Fish | 领袖翻车鱼 | 可骑在它的背上在水上移动。 若它在队伍中，会更容易钓上高潜力帕鲁。（不可叠加） 科技65 | `KingSunfish` |
| 曼波皇 | Shocking Fish | 电光翻车鱼 | 可骑在它的背上在水上移动。 骑乘期间玩家的攻击会转变为雷属性，且攻击力提升(5~20)%。 此外，若它在队伍中，会更容易钓上高潜力帕鲁。（不可叠加） 科技66 | `KingSunfish_Thunder` |
| 兔绣袖 | Long-Sleeved Hurray | 长袖啦啦队员 | 若它在队伍中，其他队伍帕鲁的伙伴技能冷却时间缩短(10~50)%。（不可叠加） | `SleeveRabbit` |
| 灵曦龙 | Liberated Pterosaur | 自由翼龙 | 可骑在它的背上在空中飞行。 灵曦龙的攻击力和移动速度，会随着队伍中其他龙属性或暗属性帕鲁的数量提升，每只增加(2~6)%。 科技68 | `GhostDragon` |
| 狱熙龙 | Resentful Pterosaur | 愤怒翼龙 | 可骑在它的背上在空中飞行。 狱熙龙的攻击力和移动速度，会随着队伍中其他龙属性或火属性帕鲁的数量提升，每只增加(2~6)%。 科技76 | `GhostDragon_Fire` |
| 雷云鹫 | Electro-Massage Incubation | 电动按摩式抱窝 | 可骑在它的背上在空中飞行。 若它在据点里，帕鲁蛋的孵化速度加快(20~40)%。（不可叠加） 科技66 | `ThunderFluffyBird` |
| 大红呱 | Flower Dance | 花之舞 | 若它在队伍中，玩家进行翻滚或滑步动作时，无敌时间延长(15~30)%。（不可叠加） | `RedFlowerBird` |
| 昭炎狐 | Burning Future | 未来之炎 | 若它在队伍中，玩家的攻击击中点燃状态的敌人时，会使敌人爆炸，额外造成相当于玩家攻击力(40~60)%的伤害。（不可叠加） | `FoxExorcist` |
| 沁莲龙 | Glorious Mist | 清灿迷雾 | 可骑在它的背上移动。 若它在队伍中，会为玩家的攻击附加(2~6)点浸湿异常状态值。（不可叠加） 科技72 | `LotusDragon` |
| 拉比耶尔 | Trick-Loving Fluffle | 拉比拉比魔术秀 | 若它在队伍中，当玩家的生命值低于50%时，拉比耶尔会在玩家周边掀起爆炸冲击波（火属性 / 威力: (100~200) / 点燃积蓄值: 777）。）。 此外，玩家的生命值低于50%期间，玩家的攻击力提升(30~50)%。（不可叠加） | `ClownRabbit` |
| 盗影鸦 | Dark-Nester | 潜影怪鸟 | 可骑在它的背上在空中飞行。 若它在队伍中，玩家和帕鲁对黑暗状态的敌人造成的伤害将提升(50~65)%。（不可叠加） 科技72 | `ThiefBird` |
| 梅杜娜 | Snake's Sagacity | 灵蛇之智 | 若它在队伍中，会为玩家的攻击附加(2~6)点黑暗异常状态值。（不可叠加） | `SnakeGirl` |
| 红菇娘 | Charming Spore | 魅惑孢子 | 若它在据点里，其他据点帕鲁的制药工作适应性等级+1。（不可叠加） | `MushroomLady` |
| 妖焰灯 | Lantern Enchantment | 提灯附魔 | 若它在队伍中，玩家射箭命中目标时会爆炸，额外造成相当于玩家攻击力(15~30)%的伤害。（不可叠加） | `LanternButler` |
| 缀夜星 | Hidden Dark Energy | 隐藏的暗能量 | 若它在队伍中，暗属性帕鲁的防御力提升(15~30)%。（不可叠加） | `MoonChild` |
| 墨罗娜 | Untainted Maiden | 孤染公主 | 若它在队伍中，并且所有队伍帕鲁的种类都不同时，玩家的攻击力会提升(30~80)%。（不可叠加） | `MonochromeQueen` |
| 燎火舞伶 | Stage Combat | 大显身手 | 若它在队伍中，会为玩家的攻击附加(2~6)点点燃异常状态值。（不可叠加） | `KabukiMan` |
| 磐甲龙 | Indestructible Fortress | 不破要塞龙 | 可骑在它的背上移动。 若它在队伍中，玩家和帕鲁受到的爆炸攻击伤害减轻(60~80)%，并且不会陷入眩晕状态。（不可叠加） 科技79 | `DomeArmorDragon` |
| 暴电熊 | Yellow Tank | 黄色重型战车 | 可骑在它的背上移动。 骑乘期间它还能用机关枪连续攻击。 科技40 | `ElecPanda` |
| 百合女王 | Harvest Goddess | 丰饶女神 | 发动后便能通过女王的疗愈能力，为玩家和队伍内的帕鲁恢复(80~90)%的生命值。 | `LilyQueen` |
| 黑月女王 | Goddess of the Tranquil Light | 幽光女神 | 发动后便能通过女王的疗愈能力，为玩家和队伍内的帕鲁恢复(85~95)%的生命值。 | `LilyQueen_Dark` |
| 波鲁杰克斯 | Ferocious Thunder Dragon | 凶猛的迅雷龙 | 若它在队伍中，子弹击中敌人时，一同并肩作战的帕鲁的攻击力与防御力会提升(1~5)%。 该效果最多可累积30层，持续5秒。（不可叠加） | `ThunderDragonMan` |
| 荷鲁斯 | Scorching Predator | 灼热捕食者 | 可骑在它的背上在空中飞行。 若它在队伍中，击倒冰属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） 科技60 | `Horus` |
| 伊西斯 | Tidal Predator | 潮汐捕食者 | 可骑在它的背上在空中飞行。 若它在队伍中，击倒火属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） 科技60 | `Horus_Water` |
| 异构格里芬 | Modified DNA | 基因改造 | 可骑在它的背上在空中飞行。 骑乘期间的暗属性攻击将提升(15~30)%。 且飞行时移动速度会提升。 科技47 | `BlackGriffon` |
| 辉月伊 | Celestial Darkness | 晦暗辉光 | 可坐在它背后的月亮在空中飞行。 骑乘期间的无属性和暗属性攻击将强化(15~30)%。 科技53 | `MoonQueen` |
| 霄龙 | Azure Sovereign | 苍天统治者 | 可骑在它的背上在空中飞行。 霄龙的攻击力，会随着队伍中其他龙属性帕鲁的数量提升，每只增加(4~8)%。 科技77 | `BlueSkyDragon` |
| 暮尘蛾 | Spore Stalwart | 孢子守卫 | 若它在队伍中，玩家的攻击击中缠绕状态的敌人时，会使敌人爆炸，额外造成相当于玩家攻击力(40~60)%的伤害。（不可叠加） 另外，能让玩家与帕鲁不受世界树的爆炸孢子影响。 | `Mothman` |
| 夜蔓爵 | Mist Stalwart | 迷雾守卫 | 发动后，为玩家的攻击附加(2~6)点中毒异常状态值。（不可叠加） 若它在队伍中，玩家和帕鲁不会陷入中毒状态，并且不受世界树区域的毒气影响。 | `FlowerPrince` |
| 贝菈诺娃 | Nightmare Iris | 梦魇之瞳 | 发动后会以噩梦射线攻击锁定的目标敌人。 此帕鲁使用的噩梦射线的威力将提升至(1.1~2.5)倍。 | `NightLady` |
| 贝菈露洁 | Nightmare Stare | 噩梦凝视 | 发动后会以噩梦绽放攻击锁定的目标敌人。 此帕鲁使用的噩梦绽放的威力将提升至(1.1~2.5)倍。 | `NightLady_Dark` |
| 杰诺多兰 | Meteor Wings | 陨星之翼 | 可骑在它的背上在空中飞行。 若它在队伍中，持有武器的帕鲁的伙伴技能伤害将提升(20~50)%。（不可叠加） 科技66 | `DarkMechaDragon` |
| 默世鹿 | Sacred Barrier | 庇佑圣盾 | 可骑在它的背上移动。 骑乘期间可生成护盾，抵御一切攻击。 此外，骑乘期间可进行3段跳跃。 科技70 | `LegendDeer` |
| 圣光骑士 | Holy Knight of the Firmament | 天翔圣骑士 | 可骑在它的背上移动。 骑乘期间可以进行3段跳跃，发动闪枪冲锋后，会召唤出1只队伍中的混沌骑士，一起进行攻击。 科技61 | `SaintCentaur` |
| 混沌骑士 | Dark Knight of the Abyss | 深渊黑骑士 | 可骑在它的背上移动。 骑乘期间可以进行2段跳跃，发动双枪一闪后，会召唤出1只队伍中的圣光骑士，一起进行攻击。 科技61 | `BlackCentaur` |
| 唤冬兽 | Icy Steed | 冰天马 | 可骑在它的背上在空中飞行。 骑乘期间玩家的攻击会转变为冰属性，攻击力提升(10~40)%，且攻击会附加(2~6)点冻结异常状态值。 科技62 | `IceHorse` |
| 唤夜兽 | Black Steed | 黑天马 | 可骑在它的背上在空中飞行。 骑乘期间玩家的攻击会转变为暗属性，攻击力提升(10~40)%，且攻击会附加(2~6)点黑暗异常状态值。 科技62 | `IceHorse_Dark` |
| 海皇鲸 | Sentinel of the Great Sea | 大海的霸主 | 与玩家并肩作战时，它会配合玩家的攻击用水属性的长枪进行追击。 可骑在它的背上在水上移动。 骑乘期间可在水面高高跃起。 科技64 | `PoseidonOrca` |
| 空涡龙 | Aerial Missile | 地毯式轰炸 | 可骑在它的背上在空中飞行。 骑乘期间它还能用导弹发射器连续攻击。 科技70 | `JetDragon` |
| 奥沧鲸 | Resonant Guardian | 残响守护者 | 可骑在它的背上在空中飞行。 在据点最多只能召唤1只。 若它在据点里，会在据点上空持续盘旋，远程炮轰入侵据点的敌人。 | `KingWhale` |
| 枯星龙 | - | - | 这个帕鲁擅长的事情仍在调查中。 | `WorldTreeDragon` |
| 绿史莱姆 | Slime Body | 史莱姆之躯 | 可骑在它的背上移动。 骑乘期间可高高跃起。 | `YakushimaMonster001` |
| 蓝史莱姆 | Slime Body | 史莱姆之躯 | 可骑在它的背上移动。 骑乘期间可高高跃起。 | `YakushimaMonster001_Blue` |
| 红史莱姆 | Slime Body | 史莱姆之躯 | 可骑在它的背上移动。 骑乘期间可高高跃起。 | `YakushimaMonster001_Red` |
| 紫史莱姆 | Slime Body | 史莱姆之躯 | 可骑在它的背上移动。 骑乘期间可高高跃起。 | `YakushimaMonster001_Purple` |
| 夜明史莱姆 | Slime Body | 史莱姆之躯 | 可骑在它的背上移动。 骑乘期间可高高跃起。 | `YakushimaMonster001_Pink` |
| 彩虹史莱姆 | Slime Body | 史莱姆之躯 | 可骑在它的背上移动。 骑乘期间可高高跃起。 | `YakushimaMonster001_Rainbow` |
| 附魔剑 | Enchant | 附魔 | 若它在队伍中，击倒暗属性帕鲁时获得的掉落道具增加(40~80)%。（不可叠加） | `YakushimaMonster002` |
| 洞穴蝙蝠 | Bat Backup | 支援蝙蝠 | 若它在队伍中，就会出现在玩家身边。 它会自动前去拾取附近的道具。 | `YakushimaMonster003` |
| 夜明蝙蝠 | Bat Backup | 支援蝙蝠 | 若它在队伍中，就会出现在玩家身边。 它会自动前去拾取附近的道具。 | `YakushimaMonster003_Purple` |
| 克苏鲁之眼 | Mad Eye Lunge | 进击的克苏鲁之眼 | 发动后，克苏鲁之眼会向前方突进并攻击锁定的敌人。 | `YakushimaBoss001` |
| 恶魔眼 | Demonic Sight | 恶魔的视野 | 若它在队伍中，暗属性帕鲁的攻击力会提升(15~30)%。（不可叠加） | `YakushimaBoss001_Small` |

## 可选被动词条

> 仅列出游戏标记为 `SortDisplayable`、会出现在普通被动选择器中的词条。伙伴技能、装备效果和测试项仍可在存档中存在，但不应混入普通词条列表。

| Rank | English | 简体中文 | 中文效果 | Asset ID |
|---:|---|---|---|---|
| 5 | Demon’s Hand | 恶魔之手 | 工作速度<NumBlue_13>+</>90.0<NumBlue_13>%</> SAN值下降速度加快<NumRed_13>+15.0%</> 世界树区域的树木/矿石不会因接近而消失 | `WorldTree_CraftSpeed` |
| 5 | Dimensional Leap | 次元跳跃 | 移动速度提升<NumBlue_13>+</>50.0<NumBlue_13>%</> 饱腹度下降速度加快<NumRed_13>+15.0%</> 世界树区域的树木/矿石不会因接近而消失 | `WorldTree_MoveSpeed` |
| 5 | God of Destruction | 破坏神 | 攻击<NumBlue_13>+</>40.0% 防御<NumBlue_13>+</>20.0% 最大HP-50.0% 世界树区域的树木/矿石不会因接近而消失 | `WorldTree_ATK_DEF` |
| 5 | Hermit Sage | 仙人 | 减少SAN值下降速度<NumBlue_13>+50.0%</> 工作速度-20.0<NumRed_13>%</> 世界树区域的树木/矿石不会因接近而消失 | `WorldTree_Sanity` |
| 5 | Sanctified Meat Shield | 守护圣盾 | 防御<NumBlue_13>+</>50.0% 攻击-30.0% 世界树区域的树木/矿石不会因接近而消失 | `WorldTree_DEF` |
| 5 | Twin-Edged Holy Blade | 双刃圣剑 | 攻击<NumBlue_13>+</>50.0% 防御-30.0% 世界树区域的树木/矿石不会因接近而消失 | `WorldTree_ATK` |
| 5 | World Tree's Bounty | 神树苗床 | 减少饱腹度下降速度<NumBlue_13>+50.0%</> 生命值-20.0<NumRed_13>%</> 世界树区域的树木/矿石不会因接近而消失 | `WorldTree_FullStomach` |
| 4 | Babysitter | 育婴师 | 在据点内时，分派到配种牧场的帕鲁的 产蛋速度+30.0%，孵化速度+30.0% | `MutationPal_Babysitter` |
| 4 | Demon God | 鬼神 | 攻击 +30.0% 防御 +5.0% | `PAL_ALLAttack_up3` |
| 4 | Diamond Body | 金刚之躯 | 防御力+30.0% 免疫硬直 免疫击退 | `Deffence_up3` |
| 4 | Eternal Engine | 永动机 | 最大耐力+75.0% ※此效果仅对可骑乘的帕鲁有效。 | `Stamina_Up_3` |
| 4 | Eternal Flame | 永炎 | 火属性攻击伤害增加30.0% 雷属性攻击伤害增加30.0% | `EternalFlame` |
| 4 | Heart of the Immovable King | 明镜止水 | 减少SAN值下降速度<NumBlue_13>+20.0%</> | `PAL_Sanity_Down_3` |
| 4 | Heavily Armored | 重装甲 | <Status_Up>免疫</>爆破伤害 | `MutationPal_ExplosionResist` |
| 4 | Idiosyncratic | 特殊体质 | 帕鲁和玩家的生命值自然恢复量+50.0% 防御力+25.0% <Status_Up>免疫</>中毒伤害 <Status_Up>免疫</>灼烧伤害 | `MutationPal_Mutant` |
| 4 | Immortality | 不死之身 | 窃取生命+5.0% 帕鲁生命值自然恢复量+100.0% 攻击力+15.0% | `MutationPal_Immortal` |
| 4 | Invader | 侵略者 | 暗属性攻击伤害增加30.0% 龙属性攻击伤害增加30.0% | `Invader` |
| 4 | King of the Waves | 破浪王者 | 水上移动速度提升50.0% | `SwimSpeed_up_3` |
| 4 | Lavish Hospitality | 慷慨就义 | 自身道具掉落量+100.0% | `SelfDeathAddItemDrop_up_3` |
| 4 | Legend | 传说 | 攻击+20.0% 防御+20.0% 移动速度提升20.0% | `Legend` |
| 4 | Lightfooted | 身轻如燕 | 骑乘期间连续跳跃次数+1 | `RideJumpCount_Increase1` |
| 4 | Lucky | 稀有 | 攻击 +15.0% 防御 +15.0% 工作速度 +20.0% | `Rare` |
| 4 | Lunker | 湖之主 | 水属性攻击伤害增加20.0% 冰属性攻击伤害增加20.0% 防御+20.0% | `Nushi` |
| 4 | Mastery of Fasting | 极限绝食 | 减少饱腹度下降速度<NumBlue_13>+20.0%</> | `PAL_FullStomach_Down_3` |
| 4 | Ranch Master | 牧场之主 | 牧场的工作适应性+2 | `WorkSuitabilityAddRank_MonsterFarm_2` |
| 4 | Remarkable Craftsmanship | 卓绝技艺 | 工作速度 +75.0% | `CraftSpeed_up3` |
| 4 | Savior | 救世主 | 无属性攻击伤害增加30.0% 草属性攻击伤害增加30.0% | `Salvation` |
| 4 | Siren of the Void | 魔女 | 暗属性攻击伤害增加30.0% 冰属性攻击伤害增加30.0% | `Witch` |
| 4 | Sky Strider | 凌空微步 | 骑乘期间连续跳跃次数+2 | `RideJumpCount_Increase2` |
| 4 | Swift | 神速 | 移动速度提升30.0% | `MoveSpeed_up_3` |
| 4 | Vampiric | 吸血鬼 | 会吸收造成伤害的一部分恢复自身的HP。 即使到夜晚也不会睡觉，可以一直工作。 | `Vampire` |
| 3 | Ace Swimmer | 游泳健将 | 水上移动速度提升40.0% | `SwimSpeed_up_2` |
| 3 | Artisan | 工匠精神 | 工作速度 +50.0% | `CraftSpeed_up2` |
| 3 | Burly Body | 顽强肉体 | 防御力+20.0% 免疫硬直 | `Deffence_up2` |
| 3 | Celestial Emperor | 圣天 | 无属性攻击伤害增加30.0% | `ElementBoost_Normal_2_PAL` |
| 3 | Diet Lover | 节食大师 | 减少饱腹度下降速度<NumBlue_13>+15.0%</> | `PAL_FullStomach_Down_2` |
| 3 | Divine Dragon | 神龙 | 龙属性攻击伤害增加30.0% | `ElementBoost_Dragon_2_PAL` |
| 3 | Earth Emperor | 岩帝 | 地属性攻击伤害增加30.0% | `ElementBoost_Earth_2_PAL` |
| 3 | Farmhand | 牧场之子 | 牧场的工作适应性+1 | `WorkSuitabilityAddRank_MonsterFarm_1` |
| 3 | Ferocious | 凶猛 | 攻击 +20.0% | `PAL_ALLAttack_up2` |
| 3 | Flame Emperor | 炎帝 | 火属性攻击伤害增加30.0% | `ElementBoost_Fire_2_PAL` |
| 3 | Healing Coach | 疗愈教练 | 玩家的生命值自然恢复量+5.0% | `AutoHPRegeneRate_Passive` |
| 3 | Ice Emperor | 冰帝 | 冰属性攻击伤害增加30.0% | `ElementBoost_Ice_2_PAL` |
| 3 | Infinite Stamina | 无限精力 | 最大耐力+50.0% ※此效果仅对可骑乘的帕鲁有效。 | `Stamina_Up_1` |
| 3 | Logging Foreman | 采伐领袖 | 玩家的采伐速度提升25.0% | `TrainerLogging_up1` |
| 3 | Lord of Lightning | 雷帝 | 雷属性攻击伤害增加30.0% | `ElementBoost_Thunder_2_PAL` |
| 3 | Lord of the Sea | 海皇 | 水属性攻击伤害增加30.0% | `ElementBoost_Aqua_2_PAL` |
| 3 | Lord of the Underworld | 冥王 | 暗属性攻击伤害增加30.0% | `ElementBoost_Dark_2_PAL` |
| 3 | Mine Foreman | 矿山首领 | 玩家的挖掘速度提升25.0% | `TrainerMining_up1` |
| 3 | Motivational Leader | 啦啦队 | 玩家的工作速度提升25.0% | `TrainerWorkSpeed_UP_1` |
| 3 | Noble | 高贵 | 改善交易价格+5.0% | `SalePrice_Up_1` |
| 3 | Philanthropist | 博爱主义者 | 当分配到配种牧场时，产出蛋的速度将加快100.0%。 | `Test_PalEgg_HatchingSpeed_Up` |
| 3 | Reload Master | 装填大师 | 玩家的装填速度提升+4.0% | `ReloadSpeedUp_Passive` |
| 3 | Runner | 运动健将 | 移动速度提升20.0% | `MoveSpeed_up_2` |
| 3 | Serenity | 沉着冷静 | 主动技能的冷却时间缩短30.0% 攻击+10.0% | `CoolTimeReduction_Up_1` |
| 3 | Service-Minded | 奉献精神 | 自身道具掉落量+50.0% | `SelfDeathAddItemDrop_up_2` |
| 3 | Spirit Emperor | 精灵王 | 草属性攻击伤害增加30.0% | `ElementBoost_Leaf_2_PAL` |
| 3 | Stronghold Strategist | 铁壁军师 | 玩家的防御提升10.0% | `TrainerDEF_UP_1` |
| 3 | Vanguard | 突袭指挥官 | 玩家的攻击提升10.0% | `TrainerATK_UP_1` |
| 3 | Wellness Watcher | 防过劳帮手 | 玩家的耐力消耗量减缓+<NumBlue_13>5.0</>% | `PlayerSP_DecreaseRate_Passive` |
| 3 | Whopper | 大猎物 | 水属性攻击伤害增加5.0% 冰属性攻击伤害增加5.0% 防御+5.0% | `MiniNushi` |
| 3 | Workaholic | 工作狂 | 减少SAN值下降速度<NumBlue_13>+15.0%</> | `PAL_Sanity_Down_2` |
| 2 | Heavyweight | 重量级 | 防御力+20.0% 免疫击退 | `Deffence_up2_2` |
| 2 | Musclehead | 脑筋 | 攻击 +30.0% 工作速度 -50.0% | `Noukin` |
| 1 | Abnormal | 一反常态 | 无属性伤害减少10.0% | `ElementResist_Normal_1_PAL` |
| 1 | Aggressive | 强势 | 攻击 +10.0% 防御 -10.0% | `PAL_oraora` |
| 1 | Blood of the Dragon | 龙之血脉 | 龙属性攻击伤害增加10.0% | `ElementBoost_Dragon_1_PAL` |
| 1 | Botanical Barrier | 除草效果 | 草属性伤害减少10.0% | `ElementResist_Leaf_1_PAL` |
| 1 | Brave | 勇敢 | 攻击 +10.0% | `PAL_ALLAttack_up1` |
| 1 | Capacitor | 电容 | 雷属性攻击伤害增加10.0% | `ElementBoost_Thunder_1_PAL` |
| 1 | Cheery | 阳光开朗 | 暗属性伤害减少10.0% | `ElementResist_Dark_1_PAL` |
| 1 | Coldblooded | 冷血 | 冰属性攻击伤害增加10.0% | `ElementBoost_Ice_1_PAL` |
| 1 | Conceited | 自恋狂 | 工作速度 +10.0% 防御 -10.0% | `PAL_conceited` |
| 1 | Dainty Eater | 小胃 | 减少饱腹度下降速度<NumBlue_13>+10.0%</> | `PAL_FullStomach_Down_1` |
| 1 | Dragonkiller | 屠龙者 | 龙属性伤害减少10.0% | `ElementResist_Dragon_1_PAL` |
| 1 | Earthquake Resistant | 抗震结构 | 地属性伤害减少10.0% | `ElementResist_Earth_1_PAL` |
| 1 | Fine Furs | 贵族 | 改善交易价格+3.0% | `SalePrice_Up_2` |
| 1 | Fit as a Fiddle | 健康宝宝 | 最大耐力+25.0% ※此效果仅对可骑乘的帕鲁有效。 | `Stamina_Up_2` |
| 1 | Fragrant Foliage | 草木馨香 | 草属性攻击伤害增加10.0% | `ElementBoost_Leaf_1_PAL` |
| 1 | Hard Skin | 坚硬皮肤 | 防御 +10.0% | `Deffence_up1` |
| 1 | Heated Body | 高温体质 | 冰属性伤害减少10.0% | `ElementResist_Ice_1_PAL` |
| 1 | Hooligan | 粗暴 | 攻击 +15.0% 工作速度 -10.0% | `PAL_rude` |
| 1 | Hydromaniac | 喜欢戏水 | 水属性攻击伤害增加10.0% | `ElementBoost_Aqua_1_PAL` |
| 1 | Impatient | 急性子 | 主动技能的冷却时间缩短15.0% | `CoolTimeReduction_Up_2` |
| 1 | Insomnia | 不眠 | 即使到夜晚也不会睡觉，会一直工作。 | `Nocturnal` |
| 1 | Insulated Body | 绝缘体 | 雷属性伤害减少10.0% | `ElementResist_Thunder_1_PAL` |
| 1 | Masochist | 受虐狂 | 防御 +15.0% 攻击 -15.0% | `PAL_masochist` |
| 1 | Nimble | 灵活 | 移动速度提升10.0% | `MoveSpeed_up_1` |
| 1 | Otherworldly Cells | 未知生物细胞 | 攻击力+10.0% 火属性伤害减免15.0% 雷属性伤害减免15.0% | `Alien` |
| 1 | Positive Thinker | 积极思维 | 减少SAN值下降速度<NumBlue_13>+10.0%</> | `PAL_Sanity_Down_1` |
| 1 | Power of Gaia | 大地之力 | 地属性攻击伤害增加10.0% | `ElementBoost_Earth_1_PAL` |
| 1 | Pyromaniac | 喜欢玩火 | 火属性攻击伤害增加10.0% | `ElementBoost_Fire_1_PAL` |
| 1 | Sadist | 虐待狂 | 攻击 +15.0% 防御 -15.0% | `PAL_sadist` |
| 1 | Serious | 认真 | 工作速度 +20.0% | `CraftSpeed_up1` |
| 1 | Sleek Stroke | 悠然泳姿 | 水上移动速度提升30.0% | `SwimSpeed_up_1` |
| 1 | Spirit of Zen | 禅境 | 无属性攻击伤害增加10.0% | `ElementBoost_Normal_1_PAL` |
| 1 | Suntan Lover | 拥抱烈日 | 火属性伤害减少10.0% | `ElementResist_Fire_1_PAL` |
| 1 | Veil of Darkness | 夜幕 | 暗属性攻击伤害增加10.0% | `ElementBoost_Dark_1_PAL` |
| 1 | Waterproof | 防水性能 | 水属性伤害减少10.0% | `ElementResist_Aqua_1_PAL` |
| 1 | Work Slave | 社畜 | 工作速度 +30.0% 攻击 -30.0% | `PAL_CorporateSlave` |
| -1 | Clumsy | 笨手笨脚 | 工作速度 -10.0% | `CraftSpeed_down1` |
| -1 | Coward | 胆小 | 攻击 -10.0% | `PAL_ALLAttack_down1` |
| -1 | Downtrodden | 弱不禁风 | 防御 -10.0% | `Deffence_down1` |
| -1 | Easygoing | 慢性子 | 主动技能的冷却时间延长-15.0% | `CoolTimeReduction_Down_1` |
| -1 | Glutton | 贪吃 | 增加饱腹度下降速度<NumRed_13>+10.0%</> | `PAL_FullStomach_Up_1` |
| -1 | Mercy Hit | 手下留情 | 和平主义者。 使攻击目标的生命值不会小于1。 | `NonKilling` |
| -1 | Night Owl | 夜猫子 | 因为总是熬夜，白天常常睡午觉。 | `NightOwl` |
| -1 | Shabby | 寒酸 | 交易价格恶化-10.0% | `SalePrice_Down_1` |
| -1 | Sickly | 家里蹲 | 最大耐力-25.0% ※此效果仅对可骑乘的帕鲁有效。 | `Stamina_Down_1` |
| -1 | Unstable | 情绪不稳 | 增加SAN值下降速度<NumRed_13>+10.0%</> | `PAL_Sanity_Up_1` |
| -2 | Bottomless Stomach | 无底之胃 | 增加饱腹度下降速度<NumRed_13>+15.0%</> | `PAL_FullStomach_Up_2` |
| -2 | Destructive | 毁灭欲望 | 增加SAN值下降速度<NumRed_13>+15.0%</> | `PAL_Sanity_Up_2` |
| -3 | Brittle | 骨质疏松 | 防御 -20.0% | `Deffence_down2` |
| -3 | Pacifist | 消极主义者 | 攻击 -20.0% | `PAL_ALLAttack_down2` |
| -3 | Slacker | 偷懒成瘾 | 工作速度 -30.0% | `CraftSpeed_down2` |

## 主动技能

| English | 简体中文 | Asset ID |
|---|---|---|
| Absolute Frost | 冰极冻域 | `IceAge` |
| Acid Rain | 酸雨 | `AcidRain` |
| Aegis Charge | 圣盾冲锋 | `Unique_WhiteShieldDragon_ShieldTackle` |
| Air Blade | 真空刃 | `AirBlade` |
| Air Cannon | 空气弹 | `AirCanon` |
| All Range Thunder | 雷动八方 | `RangeThunder` |
| Antler Uppercut | 尖角顶击 | `Unique_Deer_PushupHorn` |
| Apocalypse | 启示录 | `Apocalypse` |
| Aqua Blade | 波涛万仞 | `Unique_KingWhale_AquaBlade` |
| Aqua Burst | 爆裂水球 | `WaterBall` |
| Aqua Gun | 水枪 | `WaterGun` |
| Aqua Surge | 漩涡新星 | `RipTide` |
| Aqua Tornado | 风暴召唤 | `Unique_KingWhale_AquaTornado` |
| Astral Ray | 星幽炮 | `Unique_DarkMechaDragon_ConvergentBeam` |
| Azure Dracoflare | 苍龙炎 | `Unique_BlueSkyDragon_SweepBreath` |
| Beam Comet | 光束彗星 | `Unique_JetDragon_JumpBeam` |
| Beam Slash | 光连斩 | `Unique_DarkMechaDragon_BeamSlash` |
| Beam Slicer | 切割龙息 | `BeamSlicer` |
| Beckon Lightning | 召雷 | `Unique_ThunderDog_InazumaShorai` |
| Bee Quiet | 蜂！蜂！蜂！ | `SelfDestruct_Bee` |
| Black Quilled Ballet | 黑天鹅之舞 | `Unique_MonochromeQueen_BalletJump` |
| Blast Cannon | 绽裂龙息 | `BlastCanon` |
| Blast Punch | 爆裂拳击 | `Unique_GrassPanda_Electric_ElectricPunch` |
| Blazing Beam | 火花射线 | `Unique_GhostDragon_PhosphorousBeam` |
| Blazing Horn | 炽热角击 | `Unique_FlameBuffalo_FlameHorn` |
| Blizzard Claw | 暴雪爪 | `Unique_WhiteTiger_IceScratch` |
| Blizzard Spike | 钻石星辰 | `IcicleThrow` |
| Bog Blast | 泥浆投掷 | `MudShot` |
| Bolt Blink | 风驰电掣 | `Unique_BlueThunderHorse_FlashDash` |
| Botanical Smash | 花龙摆尾 | `Unique_FlowerDinosaur_Whip` |
| Bountiful Protection | 丰饶加护 | `Unique_LilyQueen_LilyHealing` |
| Brawn Impact | 焚天爆炎 | `Unique_KingBahamut_ArmSmash` |
| Bubble Blast | 泡泡射击 | `BubbleShot` |
| Bubble Rain | 泡沫之雨 | `Unique_KingWhale_HomingBubble` |
| Bull Rush | 蛮牛奔袭 | `Unique_GrassMinotaur_BullRush_Lower` |
| Cat Press | 喵咪扑击 | `Unique_NaughtyCat_CatPress` |
| Celestial Vortex | 天变之涡 | `Unique_BlueSkyDragon_DrainStorm` |
| Chaotic Spray | 妙玉连珠 | `Unique_IceCrocodile_SpitAttack` |
| Charge Cannon | 龙息炮 | `ChargeCanon` |
| Chicken Rush | 皮皮冲鸡 | `Unique_ChickenPal_ChickenPeck` |
| Circle Vine | 缠根牢狱 | `RootLance` |
| Cloud Tempest | 阴云之岚 | `Unique_FengyunDeeper_CloudTempest` |
| Comet Barrage | 三重陨星 | `ThreeCommet` |
| Comet Strike | 陨星 | `Commet` |
| Cosmic Meteor | 苍穹落星 | `Unique_DarkMechaDragon_WarpComet` |
| Crash Dash | 碎岩冲锋 | `Unique_GoldenHorse_StoneDash` |
| Creeping Bubbles | 泡沫聚涌 | `CreepingBubble` |
| Crosswind | 十字风切 | `CrossWind` |
| Crushing Punch | 筋肉重拳 | `Unique_GrassPanda_MusclePunch` |
| Crystal Breath | 凛冬之息 | `FrostBreath` |
| Crystal Wing | 冰晶之翼 | `Unique_IceHorse_IceBladeAttack` |
| Cube Press | 巨石压顶 | `Unique_CubeTurtle_CubePress` |
| Curtain Splash | 间隙潮 | `WallSplash` |
| Daring Flames | 风林火山 | `Unique_AmaterasuWolf_FireCharge` |
| Daring Shadowstorm | 火阴山雷 | `Unique_AmaterasuWolf_Dark_DarkCharge` |
| Dark Arrow | 黑暗箭 | `DarkArrow` |
| Dark Ball | 暗黑球 | `DarkBall` |
| Dark Cannon | 黑暗弹 | `DarkCanon` |
| Dark Charge | 暗焰冲撞 | `Unique_FireKirin_Dark_DarkTossin` |
| Dark Laser | 暗黑雷射 | `DarkLaser` |
| Dark Nova | 混沌新星 | `Unique_WhiteDeer_Dark_DarkPillar` |
| Dark Root | 枯须大炮 | `Unique_GrassGolem_Dark_DarkArmCannon` |
| Dark Shot | 暗能弹 | `GravityShot` |
| Dark Whisp | 黑暗之拥 | `DarkLegion` |
| Dark Wing | 幽夜之翼 | `Unique_IceHorse_Dark_DarkBladeAttack` |
| Dash Kick | 冲锋踢 | `Unique_TropicalOstrich_DashKick` |
| Deep Breath | 花粉吐息 | `Unique_Plesiosaur_LongBreath` |
| Diamond Rain | 晶钻之雨 | `DiamondFall` |
| Divine Disaster | 神圣灾祸 | `Unique_BlackGriffon_TackleLaser` |
| Divine Disaster II | 神圣灾祸Ⅱ | `Unique_BlackGriffon_TackleLaser2` |
| Divine Wing | 流光翼彩 | `Unique_LegendDeer_RadiantWingRush` |
| Double Blizzard Spike | 极寒双星 | `DoubleIcicleThrow` |
| Double Fang | 狂野双牙 | `Unique_Garm_BiteV2` |
| Double Fang | 狂野双牙 | `Unique_GuardianDog_BiteV2` |
| Double Fang (Dark) | 暗影双牙 | `Unique_AmaterasuWolf_Dark_BiteV2` |
| Double Fang (Dark) | 暗影双牙 | `Unique_BlackPuppy_BiteV2` |
| Double Fang (Electric) | 狂雷双牙 | `Unique_ElecPomeranian_BiteV2` |
| Double Fang (Electric) | 狂雷双牙 | `Unique_ThunderDog_BiteV2` |
| Double Fang (Fire) | 狂炎双牙 | `Unique_AmaterasuWolf_BiteV2` |
| Double Fang (Ground) | 碎岩双牙 | `Unique_GoldenHorse_BiteV2` |
| Double Fang (Ground) | 碎岩双牙 | `Unique_SamuraiDog_BiteV2` |
| Double Fang (Ice) | 寒冰双牙 | `Unique_ThunderDog_Ice_BiteV2` |
| Dragon Breath | 龙息 | `DragonBreath` |
| Dragon Burst | 龙之波动 | `DragonWave` |
| Dragon Cannon | 龙息弹 | `DragonCanon` |
| Dragon Meteor | 龙彗星 | `DragonMeteor` |
| Earth Dash | 地之冲锋 | `Unique_FeatherOstrich_Tossin` |
| Earth Impact | 地震 | `Unique_Grassmammoth_Earthquake` |
| Electric Ball | 闪电球 | `ThunderBall` |
| Emperor Slide | 王者滑击 | `Unique_CaptainPenguin_BodySlide` |
| Evil Slash | 恶之爪 | `Unique_DarkAlien_JumpScractch` |
| Fierce Fang | 狂野獠牙 | `Unique_Garm_Bite` |
| Fierce Fang | 狂野之牙 | `Unique_GuardianDog_Bite` |
| Fierce Fang (Dark) | 暗影之牙 | `Unique_AmaterasuWolf_Dark_Bite` |
| Fierce Fang (Dark) | 暗影之牙 | `Unique_BlackPuppy_Bite` |
| Fierce Fang (Electric) | 狂雷之牙 | `Unique_ElecPomeranian_Bite` |
| Fierce Fang (Electric) | 狂雷之牙 | `Unique_ThunderDog_Bite` |
| Fierce Fang (Fire) | 狂炎之牙 | `Unique_AmaterasuWolf_Bite` |
| Fierce Fang (Ground) | 碎岩之牙 | `Unique_GoldenHorse_Bite` |
| Fierce Fang (Ground) | 碎岩之牙 | `Unique_SamuraiDog_Bite` |
| Fierce Fang (Ice) | 寒冰之牙 | `Unique_ThunderDog_Ice_Bite` |
| Fire Ball | 烈焰球 | `FireBall` |
| Fire Tackle | 热浪滚滚 | `Unique_BluePlatypus_Toboggan_Fire` |
| Firefist Breathstorm | 魔龙焚炎 | `Unique_BlackMetalDragon_FirePunch` |
| Flame Breath | 炽焰掠空 | `Unique_BirdDragon_FireBreath` |
| Flame Cutter | 回旋炎锯 | `Unique_WingGolem_Fire_FlameCutter` |
| Flame Funnel | 流火 | `FlameFunnel` |
| Flame Wall | 爆烈火墙 | `FlameWall` |
| Flame Waltz | 烈焰华尔兹 | `Unique_NightLady_FlameNightmare` |
| Flare Arrow | 烈焰箭 | `FlareArrow` |
| Flare Storm | 烈焰风暴 | `FlareTornado` |
| Flash Charge | 闪雷冲锋 | `Unique_BlueThunderHorse_Tossin` |
| Flower Stomp | 落花踏 | `Unique_RedFlowerBird_JumpKick` |
| Fluffy Tackle | 绒毛冲撞 | `Unique_Alpaca_Tackle` |
| Focus Shot | 精准狙击 | `Unique_RobinHood_BowSnipe` |
| Forceful Charge | 巨力冲锋 | `Unique_Anubis_Tackle` |
| Freeze Wall | 寒冰之壁 | `IceWall` |
| Freezing Charge | 霜角猛攻 | `Unique_IceDeer_IceHorn` |
| Frenzied Charge | 高速突击 | `Unique_Yakushima_MouthTossin` |
| Frost Burst | 霜冻爆裂 | `Unique_VolcanicMonster_Ice_IceAttack` |
| Frost Talon | 烈冻爪 | `Unique_SnowTigerBeastman_TrampleSlash` |
| Frostcall | 召雪 | `Unique_ThunderDog_Ice_KoriShorai` |
| Frozen Press | 冰山压顶 | `Unique_KingAlpaca_Ice_IcePress` |
| Fuddler Tunneler | 掘地潜行 | `Unique_CuteMole_DiggingAttack` |
| Gale Claw | 滑空爪 | `Unique_Eagle_GlidingNail` |
| Geyser Gush | 潮涌迸发 | `SeaGush` |
| Giant Spore | 巨大孢子 | `Unique_Mothman_GiantSpore` |
| Giga Horn | 终极角击 | `Unique_HerculesBeetle_BeetleTackle` |
| Glacial Impact | 冰川碎击 | `Unique_SnowTigerBeastman_SnowImpact` |
| Glacial Plunge | 冰锥俯冲 | `Unique_ThunderBird_Ice_SnowStrom` |
| Grand Breach | 巨鲸跃 | `Unique_KingWhale_Breaching` |
| Grass Tornado | 绿野飓风 | `GrassTornado` |
| Ground Cutter | 回旋岩锯 | `Unique_WingGolem_RoundCutter` |
| Ground Pound | 猩猩连打 | `Unique_Gorilla_GroundPunch` |
| Ground Smash | 粉碎大地 | `Unique_Anubis_GroundPunch` |
| Grudge Barrage | 怨念连击 | `Unique_GrimGirl_BrutalMachete` |
| Heavy Thunder Tank | 雷击的重型战车 | `Unique_ElecPanda_GatlingAttack` |
| Hellfire Claw | 狱火爪 | `Unique_Baphomet_SwallowKite` |
| High Breach | 冰鲸跃 | `Unique_IceNarwhal_JumpingHorn` |
| Holy Burst | 光击阵 | `HolyBlast` |
| Holy Nova | 神圣新星 | `Unique_WhiteDeer_HolyPillar` |
| Holy Press | 圣石压顶 | `Unique_CubeTurtle_Neutral_HolyPress` |
| Horn Burst | 岩角爆 | `Unique_RockBeast_RockHorn` |
| Hydra Charge | 水龙突进 | `Unique_BlueSkyDragon_Tossin` |
| Hydro Jet | 水流射击 | `AquaJet` |
| Hydro Laser | 高压水炮 | `HydroPump` |
| Hydro Slicer | 水刀切割 | `HydroSlicer` |
| Hydro Spin | 漩涡回旋 | `Unique_TentacleTurtle_HydroSpin` |
| Iaigiri | 居合斩 | `Unique_Ronin_Iai` |
| Iaigiri | 居合斩 | `Unique_Ronin_Iai_PartnerSkill` |
| Ice Burst | 冰角爆 | `Unique_RockBeast_Ice_IceHorn` |
| Ice Gale Strike | 疾风冰击 | `Unique_Kirin_Ice_IceTackle` |
| Ice Laser | 急冻吐息 | `Unique_VolcanoDragon_Ice_IceLaser` |
| Ice Missile | 冰雪飞弹 | `IceMissile` |
| Ice Spit | 寒冰喷溅 | `Unique_VolcanoDragon_Ice_IcicleSpit` |
| Iceberg | 冰刺 | `BlizzardLance` |
| Icicle Bullet | 冰霜连弹 | `IciclePierce` |
| Icicle Cutter | 冰刃 | `IceBlade` |
| Icicle Line | 冰锋之路 | `IcicleLine` |
| Ignis Blast | 烈焰射击 | `FireBlast` |
| Ignis Breath | 烈焰放射 | `Flamethrower` |
| Ignis Charge | 烈焰冲撞 | `Unique_FireKirin_Tackle` |
| Ignis Rage | 地狱火 | `Inferno` |
| Implode | 自爆 | `SelfDestruct` |
| Jumping Claw | 飞跃爪击 | `Unique_Werewolf_Scratch` |
| Jumping Stinger | 跳跃重刺 | `Unique_DarkScorpion_Pierce` |
| Kerauno | 雷神之枪 | `Unique_ThunderDragonMan_ThunderSwordAttack` |
| Kingly Slam | 泰山压顶 | `Unique_KingAlpaca_BodyPress` |
| Konoha Flip | 叶返 | `Unique_LeafMomonga_SomerSault` |
| Lantern Flame | 提灯妖火 | `Unique_LanternButler_LanternFlame` |
| Lantern Sweep | 提灯横扫 | `Unique_GhostAnglerfish_SweepBait` |
| Lawn Bowling | 滚草球 | `Unique_Yeti_Grass_GrassBall` |
| Leaping Roundhouse | 回旋猛踢 | `Unique_GrassRabbitMan_GrassRoundKick` |
| Lethal Laser | 处刑雷射 | `ShokeiLaser` |
| Lethal Step | 致命舞步 | `Unique_NightBlueHorse_DeathStep` |
| Lightning Bolt | 闪电伏特 | `Thunderbolt` |
| Lightning Claw | 霹雳连爪 | `Unique_ElecPanda_ElecScratch` |
| Lightning Dive | 闪电俯冲 | `Unique_ThunderBird_ThunderStorm` |
| Lightning Gale | 疾风雷击 | `Unique_Kirin_LightningTackle` |
| Lightning Smash | 雷龙摆尾 | `Unique_FlowerDinosaur_Electric_ThunderWhip` |
| Lightning Streak | 雷击 | `LineThunder` |
| Lightning Strike | 闪电冲击 | `LightningStrike` |
| Lock-On Lunge | 凝视突击 | `Unique_Yakushima_EyeTossin` |
| Lock-on Laser | 锁定雷射 | `LockonLaser` |
| Lotus Bloom | 怒放莲华 | `Unique_LotusDragon_LotusBloom` |
| Maelstrom | 漩涡风暴 | `Unique_KingWhale_Maelstrom` |
| Magma Laser | 岩浆吐息 | `Unique_VolcanoDragon_VolcanicLaser` |
| Magma Serpent | 腾龙奔炎 | `Unique_Umihebi_Fire_FireWindingTackle` |
| Magma Spit | 熔岩喷溅 | `Unique_VolcanoDragon_MagmaSpit` |
| Magna Crush | 龙陨震击 | `Unique_KingBahamut_AirCrash` |
| Megaton Implode | 超自爆 | `SelfExplosion` |
| Meteorain | 陨星雨 | `CommetRain` |
| Missile Burst | 轰天之翼 | `Unique_DomeArmorDragon_ExplosiveMissile` |
| Moonlight Beam | 皎月射线 | `Unique_MoonQueen_MoonBeam` |
| Mud Horn | 泥角顶击 | `Unique_Deer_Ground_DirtyHorn` |
| Multicutter | 三重风刃 | `SpecialCutter` |
| Mummy Rush | 突袭木乃伊 | `Unique_MummyPal_MummyAttack` |
| Muscle Slam | 铁山靠 | `Unique_SakuraSaurus_SideTackle` |
| Mystic Whirlwind | 神秘旋风 | `Unique_FairyDragon_FairyTornado` |
| Needle Spear | 针刺长矛 | `Unique_SoldierBee_NeedleLance` |
| Nightmare Ball | 恶梦球 | `ShadowBall` |
| Nightmare Bloom | 噩梦绽放 | `Unique_NightLady_WarpBeam` |
| Nightmare Claw | 恶梦爪 | `Unique_Baphomet_Dark_DarkKite` |
| Nightmare Ray | 噩梦射线 | `Unique_NightLady_WarpBeam_Straight` |
| Ocular Rush | 眼球突击 | `Unique_YakushimaBoss001_Small_DemonEyeCharge` |
| Omega Laser | 欧米伽雷射 | `Unique_DarkMechaDragon_FunnelLaser` |
| Pal Blast | 帕鲁光束 | `HyperBeam` |
| Persistent Slash | 汪汪连斩 | `Unique_SamuraiDog_DashSlash` |
| Phantom Peck | 幻影突袭 | `Unique_DarkCrow_TelePoke` |
| Phoenix Flare | 凤凰翔波 | `Unique_Horus_FlareBird` |
| Phoenix Tide | 凤凰浪涛 | `Unique_Horus_Water_AquaStorm` |
| Plasma Funnel | 等离子浮游砲 | `ThunderFunnel` |
| Poison Blast | 剧毒射击 | `PoisonShot` |
| Poison Fog | 毒雾 | `PoisonFog` |
| Poison Promenade | 毒雾花滑 | `Unique_FlowerPrince_PoisonGasTackle` |
| Poison Scatter | 毒液漫射 | `Unique_SnakeGirl_SnakeShot` |
| Poison Shower | 毒雨 | `BubbleShower` |
| Polykeraunos | 雷神之怒 | `Unique_ThunderDragonMan_NumerousSwordAttack` |
| Power Bomb | 元气弹 | `PowerBall` |
| Power Shot | 能量射击 | `PowerShot` |
| Predator Blast | 捕食者光束 | `PredatorBeam` |
| Predator Mark | 捕食者锁定雷射 | `PredatorLockon` |
| Predator Surge | 捕食者激波 | `PredatorWave` |
| Psycho Gravity | 念动引力 | `Psychokinesis` |
| Punch | 击打 | `Human_Punch` |
| Punch Flurry | 喵喵拳 | `Unique_PinkCat_CatPunch` |
| Purifying Light | 神光尽灭 | `Unique_LegendDeer_RadiantPurge_Otomo` |
| Radiant Barrage | 辉耀弹 | `RadiantBarrage` |
| Raging Bull Rush | 狂牛奔袭 | `Unique_GrassMinotaur_BullRush` |
| Raging Flame Wave | 炎凰烈波 | `Unique_Horus_PerfectStorm` |
| Raging Snow Rush | 狂牛冰袭 | `Unique_GrassMinotaur_Ice_BullRush` |
| Raid Cutter | 连环风刃 | `RaidCutter` |
| Rapid Kick | 连续回旋踢 | `Unique_PandaGirl_RapidKick` |
| Reckless Charge | 猪突猛进 | `Unique_Boar_Tackle` |
| Reflect Leaf | 连锁叶刃 | `ReflectiveShuriken` |
| Rock Lance | 岩石锐矛 | `RockLance` |
| Rockburst | 岩爆 | `Tremor` |
| Rocket Arm | 火箭飞拳 | `Unique_GrassGolem_RocketPunch` |
| Rocket Slam | 火箭冲撞 | `Unique_WeaselDragon_FlyingTackle` |
| Rocky Impact | 震岩 | `RockBeat` |
| Rolling Scratch | 空翻爪袭 | `Unique_Sekhmet_RollingScratch` |
| Roly Poly | 滚滚毛球 | `Unique_SheepBall_Roll` |
| Root Cannon | 根须大炮 | `Unique_GrassGolem_ArmCannon` |
| Royal Step | 皇家舞步 | `Unique_NightBlueHorse_Neutral_AirStep` |
| Rumble Combo | 猩猩撼地击 | `Unique_Gorilla_Ground_EarthPunch` |
| Rush Beak | 燧火连击 | `Unique_RedArmorBird_TriplePeck` |
| Sacred Rain | 光之雨 | `Unique_LegendDeer_WarpPillarBurst` |
| Sand Tornado | 沙尘旋风 | `SandTornado` |
| Sand Twister | 沙尘暴 | `SandTwister` |
| Satellite Bit | 唤星 | `Unique_DarkMechaDragon_SetFunnel` |
| Scorching Lantern Sweep | 炽灯横扫 | `Unique_GhostAnglerfish_Fire_SweepBait_Fire` |
| Seed Machine Gun | 种子机关枪 | `SeedMachinegun` |
| Seed Mine | 种子地雷 | `SeedMine` |
| Seigetsu Blade | 青月刃 | `Unique_MoonQueen_MoonBlade` |
| Seigetsu Flash | 青月闪 | `Unique_MoonQueen_IceMoonBlade` |
| Servant Call | 召唤仆从 | `Unique_Yakushima_SummonServant` |
| Shadow Burst | 暗影波动 | `DarkWave` |
| Shell Charge | 涡壳充电 | `Unique_ElecSnail_ShellCharge` |
| Shell Spin | 甲壳回旋 | `Unique_DrillGame_ShellAttack` |
| Shockwave | 冲击波 | `ElecWave` |
| Silver Steed | 银影疾驰 | `Unique_NightBlueHorse_Neutral_Tossin` |
| Slime Press (Dark) | 史莱姆重压（暗） | `Unique_YakushimaMonster001_SlimePress_Dark` |
| Slime Press (Fire) | 史莱姆重压（火） | `Unique_YakushimaMonster001_SlimePress_Fire` |
| Slime Press (Grass) | 史莱姆重压（草） | `Unique_YakushimaMonster001_SlimePress_Leaf` |
| Slime Press (Neutral) | 史莱姆重压（无） | `Unique_YakushimaMonster001_SlimePress_Normal` |
| Slime Press (Rainbow) | 史莱姆重压（彩虹） | `Unique_YakushimaMonster001_SlimePress_Rainbow` |
| Slime Press (Water) | 史莱姆重压（水） | `Unique_YakushimaMonster001_SlimePress_Water` |
| Slither Slam | 断海覆潮 | `Unique_Umihebi_WindingTackle` |
| Smoke Jet | 墨沫头槌 | `Unique_OctopursGirl_InkJet` |
| Snow Bowling | 滚雪球 | `Unique_Yeti_SnowBall` |
| Snow Claw | 吹雪爪击 | `Unique_Werewolf_Ice_SnowScratch` |
| Snow Rush | 蛮牛冰袭 | `Unique_GrassMinotaur_Ice_BullRush_Lower` |
| Solar Blast | 太阳光束 | `SolarBeam` |
| Somersault Scratch | 空爪返 | `Unique_Sekhmet_SomersaultScratch` |
| Soul Drain | 窃魂 | `Unique_MysteryMask_LifeSteal` |
| Spark Blast | 电火花 | `SpreadPulse` |
| Spear Thrust | 闪枪冲锋 | `Unique_SaintCentaur_OneSpearRushes` |
| Spectral Steed | 幽影疾驰 | `Unique_NightBlueHorse_Tossin` |
| Spine Vine | 缠绕地刺 | `RootAttack` |
| Spinning Roundhouse | 回旋踢 | `Unique_Anubis_LowRoundKick` |
| Spinning Staff | 回旋杖击 | `Unique_QueenBee_SpinLance` |
| Spirit Dash | 心灵冲刺 | `Unique_GhostBeast_Tossin` |
| Spirit Fire | 烈焰溅射 | `FireSeed` |
| Spirit Flame | 鬼火 | `GhostFlame` |
| Splash | 瀑流击 | `LineGeyser` |
| Splash Tackle | 凌波铁山靠 | `Unique_SakuraSaurus_Water_SplashTackle` |
| Spore Burst | 孢子爆发 | `Unique_Mothman_SporeScatter` |
| Star Mine | 诡雷繁星 | `StarMine` |
| Stone Blast | 碎石霰弹 | `StoneShotgun` |
| Stone Cannon | 投石 | `ThrowRock` |
| Stone Claw | 碎岩爪 | `Unique_WhiteTiger_Ground_IronScratch` |
| Sumo Stomp | 四股踏 | `Unique_SumoDog_SumoStomp` |
| Surfing Slam | 乘风破浪 | `Unique_BluePlatypus_Toboggan` |
| Sword Charge | 剑舞冲锋 | `Unique_YakushimaMonster002_SwordCharge` |
| Tail Slash | 曳尾斩 | `Unique_GhostDragon_TailSlash` |
| Tempest Blizzard | 寒霜掠空 | `Unique_BirdDragon_Ice_IceBreath` |
| Thalassonic Laser | 风暴潮 | `Unique_PoseidonOrca_TorrentLaser` |
| Thunder Rail | 并联雷光 | `Railbolt` |
| Thunder Rain | 广域雷击 | `ThunderRain` |
| Thunder Spear | 雷矛 | `ThunderSpear` |
| Thunder Tempest | 雷云之岚 | `Unique_FengyunDeeper_Electric_ThunderTempest` |
| Thunder Uppercut | 升雷拳 | `Unique_ScorpionMan_Erectric_UpperThunder` |
| Thunderslide | 王者闪击 | `Unique_CaptainPenguin_Black_BodySlide_Electric` |
| Thunderstorm | 雷霆飓风 | `ThunderStorm` |
| Tidal Charge | 潮涌袭浪 | `Unique_KingWhale_WaveTackle` |
| Tornado Attack | 龙卷风 | `Unique_HawkBird_Storm` |
| Torrential Blast | 分流水炮 | `DiversionLaser` |
| Toxic Dance | 毒雾之舞 | `Unique_FlowerPrince_PoisonGasDance` |
| Tri-Lightning | 三重雷击 | `ThreeThunder` |
| TriSpark | 三相火花 | `TriSpark` |
| Trickster Show | 好戏上演 | `Unique_ClownRabbit_TrickShow` |
| Trigger Happy | 午时已到 | `Unique_StuffedShark_HiddenWeapon` |
| Twin Spears | 双枪一闪 | `Unique_BlackCentaur_TwoSpearRushes` |
| Umbral Surge | 黑暗霰射 | `DarkPulse` |
| Upper Smash | 升虫拳 | `Unique_ScorpionMan_Uppercut` |
| Use Weapon | 使用武器 | `Weapon_Use` |
| Volcanic Burst | 火山爆发 | `Unique_VolcanicMonster_MagmaAttack` |
| Volcanic Fang | 火山獠牙 | `Unique_Manticore_InfernoStrike` |
| Volcanic Rain | 熔岩爆发 | `Eruption` |
| Webstrike Impact | 蜘蛛猛袭 | `Unique_PurpleSpider_SpiderRaid` |
| Wholehearted Stance | 气合返 | `Unique_SifuDog_Counter` |
| Wind Barrier | 风之结界 | `Unique_LilyQueen_WindBarrier` |
| Wind Burst | 翠耀罡风 | `WindBurst` |
| Wind Cutter | 风刃 | `WindCutter` |
| Wind Edge | 烈风切 | `WindEdge` |
| Winged Assault | 蝙蝠袭击 | `Unique_YakushimaMonster003_BatCharge` |

## 维护说明

1. 游戏更新后先更新英文 `resources/game_data/*.json`，再审阅并更新本脚本中的 `SOURCE_COMMIT`。
2. 运行 `python scripts/scrs/update_game_localization.py` 重新生成简中覆盖表与本文档。
3. 检查生成报告中的缺失项；未在游戏 `zh-Hans` 表中出现的测试/占位内容保留英文，不猜译。
4. 运行 `pytest tests/unit/core_logic/test_game_localization.py tests/unit/core_logic/test_i18n.py` 验证键、占位符和核心译名。
