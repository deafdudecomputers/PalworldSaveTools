<div align="center">

![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Une boîte à outils complète pour l'édition de fichiers de sauvegarde Palworld**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md) | [Português (Brasil)](README.pt_BR.md) | [Português (Portugal)](README.pt_PT.md)

---

### **Téléchargez la version autonome depuis [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** 

---

</div>
<div align="center">

## Aperçu

<img src="https://readme-typing-svg.demolab.com?lines=C%27est+quoi+exactement+cette+chose+%3F;Votre+sauvegarde%2C+%C3%A0+votre+fa%C3%A7on;Un+outil+pour+les+gouverner+tous&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) est une application de bureau rapide et tout-en-un permettant d'inspecter et de modifier les fichiers de sauvegarde Palworld. Construit avec Python et PySide6, il lit et écrit directement le format de sauvegarde compressé du jeu – aucun module de jeu n'est requis.

Que vous ayez besoin de gérer un serveur dédié, de migrer entre des serveurs coopératifs et dédiés, de nettoyer des données abandonnées ou d'affiner un Pals individuel, PST fournit une interface unifiée unique pour tout cela.

### Faits saillants

- **Multiplateforme** : binaires prédéfinis pour **Windows**, **Linux** et **macOS**.
- **Analyse native rapide** — L'un des lecteurs de fichiers de sauvegarde les plus rapides disponibles, alimenté par le moteur [`palsav`](src/palsav).
- **Carte visuelle** — Carte du monde interactive avec marqueurs de base/joueur, zones d'exclusion et étalonnage des coordonnées.
- **Édition approfondie de Pal** — Contrôle total sur les statistiques, IVs, les âmes, les compétences, passives, les aptitudes au travail, le rang et les drapeaux d'apparence.
- **Outils de qualité serveur** — Suppression, nettoyage, conversion et transfert de caractères en masse conçus pour les administrateurs.
- **Sauvegardes automatiques** — Chaque opération de sauvegarde crée une sauvegarde avant l'écriture.
- **9 langues** — Interface utilisateur localisée, guides intégrés à l'application et documentation.





---





## Table des matières

- [Aperçu](#aperçu)
- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Démarrage rapide](#démarrage-rapide)
- [Guides](#guides)
- [Dépannage](#dépannage)
- [Construire à partir de la source](#construire-à-partir-de-la-source)
- [Contribuer](#contribuer)
- [Licence](#licence)
- [L'équipe Palworld](#léquipe-palworld)





---




<div align="center">

## Fonctionnalités

<img src="https://readme-typing-svg.demolab.com?lines=Les+bonnes+choses;V%C3%A9rifiez-le;Plein+d%27outils&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

| Catégorie | Ce que vous pouvez faire |
|---|---|
| **Gestion des joueurs** | Modifiez les noms, les niveaux, les statistiques et les points techniques. Gérez en masse les éléments, pals, la technologie entre les joueurs. Nettoyez les joueurs inactifs ou en double. |
| **Pal Editor** | Changez les statistiques, IVs, les âmes, le rang, les compétences, passives, l'aptitude au travail, le patron/les drapeaux porte-bonheur. Exporter/importer pals. Détectez et corrigez les pals illégaux. Mode de triche pour une édition non plafonnée. |
| **Gestion de guilde** | Renommez les guildes, changez de chef, définissez les niveaux. Débloquez la recherche en laboratoire. Déplacez les joueurs entre les guildes. Supprimez les guildes vides ou inactives. |
| **Outils du camp de base** | Afficher toutes les bases avec des informations sur la guilde. Exporter/importer des plans. Clonez des bases vers d'autres guildes. Repositionnez les bases sur la carte. Ajustez le rayon. Supprimez les bases inactives. |
| **Visionneuse de carte** | Carte du monde interactive avec marqueurs de base et de joueur. Dessinez des zones d’exclusion. Mode calibrage. Vues de la carte du monde et de la carte des arbres. Zoomez, faites un panoramique, survolez. |
| **Gestion des stocks** | Modifiez les éléments du joueur, les éléments clés et les emplacements d'équipement. Débloquez tous les points de voyage rapide. Parcourez et modifiez les inventaires de base et les conteneurs dans toutes les guildes. Gérer le travailleur de base pals. |
| **Exclusions** | Protégez les joueurs, les guildes et les bases du nettoyage grâce à des listes d'exclusion persistantes. Ajoutez des entrées à partir des menus contextuels. |
| **Enregistrer les outils** | Convertissez les sauvegardes entre SAV et JSON. Convertissez GamePass en Steam. Transférez des personnages entre les mondes. Correction des sauvegardes de l'hôte. Restaurez la progression de la carte. Développez les emplacements Palbox. |
| **Nettoyage et utilitaires** | Supprimez les guildes vides, les bases/joueurs inactifs, les données non référencées. Supprimez les éléments/pals/structures non valides. Réinitialisez les donjons, la plate-forme pétrolière, les baisses de ravitaillement. Corrigez les horodatages. |

### Gestion des joueurs

- Affichez et recherchez tous les joueurs par nom, niveau, nombre pal, UID, guilde et heure de dernière visite.
- Modifiez les noms des joueurs, les niveaux, les statistiques et les points technologiques.
- **Onglet Statistiques** — Statistiques des héros (Santé, Endurance, Attaque, Défense, Vitesse de travail, Poids) avec les valeurs calculées correctes dans le jeu ; Capacités reliques avec bascules et spinners.
- **Max All Stats** — Limitez instantanément toutes les statistiques au maximum (50 points).
- **Opérations groupées** sur plusieurs joueurs : gestion des objets, gestion pal et déverrouillages technologiques.
- Supprimer les joueurs inactifs par seuil de temps ; supprimer les doublons.

### Pal Editor

Une interface d'édition approfondie pour n'importe quel Pal appartenant à n'importe quel joueur. Pals sont organisés par **Party** (équipe active) et **Palbox** (stockage).

- **Statistiques et IVs** — HP, attaque, défense (IV 0-100), niveau (1-80), rang de confiance (0-10).
- **Âmes** — HP, Attaque, Défense, Vitesse d'artisanat (0–20).
- **Compétences** — Sélecteur de compétences actif ; apprendre tous les mouvements ; compétences de synchronisation en masse sur Pals.
- **Traits passifs** — Sélecteur passif avec données de jeu complètes.
- **Aptitude au travail** — Définissez les niveaux individuels d'aptitude au travail (0 à 10).
- **Drapeaux d'apparence** — Basculez entre Boss/Alpha, Chanceux/Brillant, Prédateur, Éveillé et Importé/ADN.
- **Rank & Lock** — Définissez le classement et le niveau de verrouillage des favoris (0 à 3).
- **Cheat Mode** — Basculez pour étendre toutes les majuscules : niveau, IVs, âmes, rang du condenseur à 255 ; débloquez des compétences actives/passives illimitées avec des doublons autorisés.
- **Exporter/Importer** — Cliquez avec le bouton droit sur n'importe quel pal pour l'exporter au format `.pstpal` (compressé) ou `.json`. Importez dans des emplacements vides parmi les travailleurs du groupe, de la palbox, du DPS ou de la base. Fonctionne sur les sauvegardes et les joueurs.
- **Max All Pals** — Maximisez toutes les statistiques (IVs, âmes, rang, niveau) pour tous les pals du groupe, toutes les pages palbox ou tous les travailleurs de la base — respecte les limites du mode de triche.
- **Correction du Pals** illégal — Détectez et limitez le pals avec des statistiques, des compétences ou des traits illégaux par joueur.
- **Bulk Clone/Delete** — Boîte de dialogue de sélection d'espèces avec contrôles de quantité et basculement de source (Party/Palbox/DPS) pour les opérations par lots.
- Ajoutez un nouveau Pals ou supprimez-le rapidement avec un double-clic.

### Gestion de guilde

Vue à deux panneaux : liste des guildes en haut, liste des membres en bas.

- Renommer les guildes, changer de chef, définir le niveau de guilde, le niveau de guilde maximum.
- Débloquez toutes les recherches en laboratoire ; reconstruisez toutes les guildes.
- Déplacez les joueurs entre les guildes ; supprimer les guildes vides ou inactives.

### Outils du camp de base

- Voir tous les camps de base avec association de guilde.
- **Exporter** les plans de base vers `.json` ; **importer** (un ou plusieurs fichiers) dans n'importe quelle guilde.
- **Cloner** des bases vers d'autres guildes avec un positionnement décalé.
- **Modifier les coordonnées** — Faites un clic droit sur un marqueur de base sur la carte, choisissez « Modifier les coordonnées », puis cliquez sur n'importe quel endroit pour téléporter la base.
- **Base Nudge** — Déplacez une base par des décalages X/Y/Z exacts pour corriger l'écrêtage ou le flottement du sol.
- **Ajuster le rayon de base** (50 % à 1 000 %).
- Supprimer les bases inactives et les objets cartographiques non-base.

### Visionneuse de cartes

Visualisation interactive de votre monde entier.

- Marqueurs de base (icône de maison) et marqueurs de joueur (icône de personne) avec panneaux de détails.
- Basculer les superpositions : bases, joueurs, anneaux de rayon, zones d'exclusion.
- **Dessin de zone** — Dessinez des zones d'exclusion rectangulaires ou polygonales directement sur la carte.
- **Mode de calibrage** — Alignez avec précision la carte avec les coordonnées du jeu.
- Vues de la carte du monde et de la carte des arbres ; filtrer par guilde ou nom de joueur.
- Zoom (1,0x – 30,0x), panoramique, double-clic pour voler vers un marqueur.
- Cliquez avec le bouton droit sur les marqueurs et l'espace vide pour les actions de gestion.

### Gestion des stocks

**Inventaire des joueurs** — Trois sous-onglets :
- *Inventaire* — Tous les articles et équipements contenus dans le sac principal ; modifier la quantité, ajouter, supprimer.
- *Objets clés* — Objets de quête, effigies et technologie ; ajoutez en masse toutes les effigies/éléments clés.
- *Statistiques* — Niveau, HP, Endurance, Attaque, Défense, Vitesse de travail, Poids.
- Panneau d'équipement pour les emplacements d'armes, d'accessoires, de nourriture, d'armure, de bouclier, de planeur et de module.
- Débloquez toutes les cartes + points de déplacement rapide en un clic.

**Inventaire de base** – Parcourez et gérez les articles et travaillez Pals dans toutes les bases :
- Afficher/modifier les éléments dans les conteneurs ; conteneurs transparents; modifier les emplacements des conteneurs.
- Opérations d'objets entre guildes (trouver/supprimer des objets dans toutes les guildes).
- Suppression de la structure inter-guilde.
- Sous-onglet **Base Pals** — Gérez les Pals de travail attribués à chaque base avec les menus contextuels complets de l'éditeur pal.

### Exclusions

Listes de protection qui protègent les joueurs, les guildes et les bases des opérations de nettoyage.

- Trois panneaux côte à côte : exclus les UID des joueurs, les ID de guilde et les ID de base.
- Ajoutez des entrées via les menus contextuels du clic droit dans les onglets Joueurs, Guildes ou Bases.
- Enregistrez et chargez les listes d'exclusion de manière persistante.
- Construisez votre liste **avant** d'exécuter un nettoyage en masse.

### Enregistrer les outils

Accessible depuis l'onglet **Outils** sous forme de cartes cliquables :

| Outil | Descriptif |
|------|-------------|
| **Convertir les sauvegardes** | Convertir entre les formats SAV et JSON |
| **Convertir GamePass → Steam** | Convertir les sauvegardes Xbox/GamePass au format Steam |
| **Convertir SteamID** | Convertir les identifiants Steam en UID Palworld |
| **Restaurer la carte** | Appliquer la progression de la carte entièrement déverrouillée à tous les mondes/serveurs |
| **Injecteur à fente** | Augmenter les emplacements palbox par joueur |
| **Modifier Enregistrer** | Ouvrir et modifier les données de sauvegarde brutes |
| **Transfert de personnage** | Transférer des personnages entre différents mondes/serveurs (sauvegarde croisée) |
| **Correction de la sauvegarde de l'hôte** | Échanger les UID entre deux joueurs (échange d'hôte, migration de plateforme) |

### Fonctions de nettoyage et utilitaires

Accessibles via **Menu → Fonctions**, ces opérations de niveau serveur incluent :

- **Suppression** — Supprimez les guildes vides, les bases/joueurs inactifs, les joueurs en double, les données non référencées.
- **Nettoyage** — Supprimez les éléments invalides/modifiés, les pals et passives invalides, les structures invalides ; correction du pals illégal (plafond au maximum légal) ; réinitialiser les tourelles anti-aériennes ; débloquer private chests ; réparer toutes les structures.
- **Réinitialisations** — Réinitialisez les missions, les donjons, la plate-forme pétrolière, l'envahisseur, les baisses de ravitaillement.
- **Horodatage** — Correction des horodatages négatifs ; réinitialiser les temps des joueurs.
- **PalDefender** — Génère des commandes `killnearestbase`.





---




<div align="center">

## Installation

<img src="https://readme-typing-svg.demolab.com?lines=Faites-le+fonctionner+en+quelques+minutes;T%C3%A9l%C3%A9chargez+et+partez;Aucune+configuration+requise&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Builds autonomes (recommandées)

Des binaires prédéfinis sont disponibles pour les trois principales plates-formes à partir de [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) :

| Plateforme | Télécharger | Exigences |
|--------------|----------|--------------|
| **Windows** | `PalworldSaveTools-*.exe` | Windows 10/11, [VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015-2022) |
| **Linux** | `PalworldSaveTools-*-linux.AppImage` | Toute distribution moderne |
| **macOS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+ (Monterey ou version ultérieure) |

Également disponible sur [Nexus Mods](https://www.nexusmods.com/palworld/mods/3190).

1. Téléchargez la version appropriée pour votre plateforme.
2. Extrayez (si archivé) et exécutez l'exécutable.
3. C'est tout – aucun Python ni dépendance n'est nécessaire.

> **Windows :** Si vous voyez « VCRUNTIME140.dll n'a pas été trouvé », installez le [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170).

> **Linux :** Vous devrez peut-être marquer le fichier comme exécutable : `chmod +x PalworldSaveTools-*-linux.AppImage`

> **macOS :** Si Gatekeeper bloque l'application, cliquez avec le bouton droit → **Ouvrir** pour la première fois ou exécutez `xattr -d com.apple.quarantine /path/to/app`.

### Depuis la source (toutes les plateformes)

PST utilise [`uv`](https://docs.astral.sh/uv/) pour la gestion des dépendances. Le script de démarrage crée automatiquement un environnement virtuel et installe tout.

**Prérequis :** [Python 3.11+](https://www.python.org/) et [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows** (lanceur double-clic) :
```
start.cmd
```

Le lanceur crée un `.venv`, installe les dépendances via `uv sync` et démarre l'application. Il nettoie le fichier de verrouillage à la sortie afin que chaque exécution soit reproductible.





---




<div align="center">

## Démarrage rapide

<img src="https://readme-typing-svg.demolab.com?lines=Charger.+Modifier.+Sauvegarder.+C%27est+aussi+simple+que+cela.;Trois+%C3%A9tapes+vers+la+gloire;C%27est+aussi+simple+que+%C3%A7a&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **Chargez votre sauvegarde**
   - Cliquez sur **Menu → Load Save** ou faites glisser et déposez un fichier `.sav` sur la fenêtre.
   - Accédez à votre dossier de sauvegarde Palworld et sélectionnez `Level.sav`.

2. **Explorez vos données**
   - Utilisez les onglets — **Carte**, **Outils**, **Joueurs**, **Guildes**, **Bases**, **Inventaire des joueurs**, **Inventaire de base**, **Pal Editor**, **Exclusions** — pour explorer votre sauvegarde.
   - La barre de statistiques affiche les décomptes en direct ; les icônes de navigation rapide passent à chaque section.

3. **Apporter des modifications**
   - Faites un clic gauche pour sélectionner ; faites un clic droit sur presque n'importe quoi pour des actions contextuelles.
   - Double-cliquez pour effectuer une modification ou une suppression rapide (voir les guides intégrés à l'application pour plus de détails).

4. **Enregistrez vos modifications**
   - Cliquez sur **Menu → Enregistrer les modifications**. Les sauvegardes sont créées automatiquement.

> **Conseil :** Chaque onglet dispose d'un guide intégré : cliquez sur l'icône d'aide dans n'importe quel onglet pour voir exactement ce qu'il peut faire. Pour en savoir plus, **passez la souris sur n'importe quel bouton, champ ou contrôle** pour afficher des info-bulles détaillées dans l'en-tête. Le système d'aide par info-bulles intégré à l'application est votre meilleure référence pour comprendre exactement ce que fait chaque fonctionnalité et comment l'utiliser.





---




<div align="center">

## Guides

<img src="https://readme-typing-svg.demolab.com?lines=Proc%C3%A9dures+pas+%C3%A0+pas;Suivez+le+guide;Nous+allons+vous+montrer+comment&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Enregistrer les emplacements des fichiers

**Hôte/Coop (Windows) :**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Serveur dédié :**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Déverrouillage de la carte

PST peut déverrouiller la carte complète (tous les points de déplacement rapide) pour votre sauvegarde :

1. Chargez votre sauvegarde dans PST.
2. Ouvrez l'onglet **Inventaire du joueur** et cliquez sur **Déverrouiller toutes les cartes + Voyage rapide** pour un seul joueur, **ou**
3. Utilisez l'outil **Restaurer la carte** dans l'onglet Outils pour appliquer la progression de la carte déverrouillée sur **tous** vos mondes/serveurs à la fois.
4. Enregistrez les modifications. Des sauvegardes automatiques sont créées.

### Coopération → Serveur dédié

<details>
<summary>Cliquez pour agrandir</summary>

Déplacez votre monde coopératif (que vous hébergez depuis votre PC) vers un serveur dédié afin que d'autres puissent jouer même lorsque vous êtes hors ligne.

**Comment ça marche :** Les sauvegardes coopératives utilisent `0001.sav` pour le joueur hôte. Ce n'est pas le cas des serveurs dédiés : chaque joueur a un UID standard. Fix Host Save **échange** deux fichiers de joueur (comme les sièges d'échange), pas une copie. Votre personnage coopératif dans `0001.sav` est échangé dans l'emplacement du serveur.

1. **Copiez votre sauvegarde coopérative sur le serveur.**
   - Emplacement de sauvegarde en coopération : `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`
   - Copiez `Level.sav` et le dossier `Players` à partir de là.
   - Collez dans le dossier de sauvegarde du serveur : `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`

2. **Rejoignez le serveur et créez un personnage temporaire.**
   - Démarrez le serveur, rejoignez-le et créez un nouveau personnage (n'importe quel nom/apparence — ce n'est qu'un espace réservé).
   - Attendez une sauvegarde automatique, puis arrêtez le serveur.

3. **Échangez votre personnage coopératif dans l'emplacement du serveur.**
   - Ouvrez PST → **Outils** → **Fix Host Save**.
   - Accédez au `Level.sav` du serveur.
   - **Source Player** : sélectionnez votre personnage coopératif (celui de `0001.sav` — répertorié comme hôte).
   - **Joueur cible** : Sélectionnez le personnage temporaire que vous venez de créer.
- Cliquez sur le bouton pour exécuter le swap.

4. **Démarrez le serveur.**
   - Votre personnage coopératif d'origine (avec toute la progression, Pals, bases) est désormais lié au serveur. L'espace réservé temporaire a disparu.

</details>

### Serveur dédié → Coopération

<details>
<summary>Cliquez pour agrandir</summary>

Ramenez votre personnage de serveur dédié dans une sauvegarde coopérative locale – utile si vous arrêtez de louer un serveur ou si vous souhaitez jouer hors ligne.

**Comment ça marche :** Même échange de GUID à l'envers — Correction de l'enregistrement de l'hôte **échange** deux fichiers, pas une copie. Votre personnage de serveur (UID normal) est remplacé par `0001.sav` (l'emplacement hôte) afin que vous puissiez héberger une coopération avec la progression de votre serveur.

1. **Copiez la sauvegarde de votre serveur sur votre PC local.**
   - Emplacement de sauvegarde du serveur : `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`
   - Copiez `Level.sav` et le dossier `Players` à partir de là.
   - Collez dans votre dossier coopératif local : `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`

2. **Hébergez une partie coopérative et créez un personnage temporaire.**
   - Démarrez Palworld, organisez une session coopérative et créez un nouveau personnage.
   - Laissez-le s'enregistrer automatiquement, puis fermez Palworld.

3. **Échangez votre personnage de serveur dans l'emplacement hôte.**
   - Ouvrez PST → **Outils** → **Fix Host Save**.
   - Accédez à la coopérative locale `Level.sav`.
   - **Source Player** : Sélectionnez votre personnage de serveur dédié (répertorié par son UID).
   - **Joueur cible** : sélectionnez le personnage coopératif temporaire (celui de `0001.sav` — répertorié comme hôte).
   - Cliquez sur le bouton pour exécuter le swap.

4. **Hébergez normalement une coopérative.**
   - Votre personnage serveur est désormais l'hôte (`0001.sav`). Tous les progrès, Pals, et les bases intactes.

</details>

### Changement d'hôte (échange coopératif)

<details>
<summary>Cliquez pour agrandir</summary>

Deux joueurs veulent changer qui héberge. Le joueur A a hébergé – son personnage vit dans `0001.sav`. Le joueur B rejoint en tant que client – ​​son personnage vit à `1234.sav`. Maintenant, ils veulent que le joueur B devienne l'hôte, mais l'emplacement d'hôte est toujours `0001.sav`.

**Concept clé — Fix Host Save échange toujours deux joueurs.** Il échange leurs fichiers de sauvegarde, comme deux personnes échangeant des sièges. Il ne copie PAS l'un sur l'autre. Après tout échange, les deux lecteurs existent toujours – ils se trouvent simplement dans des fichiers différents.

Puisqu'un échange déplace le joueur B dans l'emplacement hôte mais laisse les données du joueur A dans l'ancien fichier de B, un deuxième échange est nécessaire pour remettre le personnage d'origine du joueur A. Voici comment procéder :

---

**État de départ :**
```
0001.sav  = Player A (current host)
1234.sav  = Player B (current client)
```

---

**Étape 1 — Échangez A et B.**
- Ouvrez PST → **Outils** → **Fix Host Save**.
- Accédez à votre coopérative `Level.sav`.
- **Source** : Joueur A (`0001.sav`). **Cible** : Joueur B (`1234.sav`).
- Cliquez sur le bouton. Fix Host Save échange les deux fichiers.

**Après l'étape 1 :**
```
0001.sav  = Player B  ← now the host with B's character
1234.sav  = Player A  ← A's data is here, but this UID no longer exists in the game
```

---

**Étape 2 — Le joueur B héberge, le joueur A rejoint.**
- Le joueur B héberge le monde. Le joueur A rejoint.
- Puisque A n'est plus l'hôte, Palworld attribue un tout nouvel UID au personnage temporaire de A (par exemple, `9999.sav`).
- Le joueur A atteint le **Niveau 2** avec le personnage temporaire, puis tout le monde quitte la partie.

**Après l'étape 2 :**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's original data (not linked to any active UID)
9999.sav  = Player A's temporary character (fresh, Level 2+)
```

---

**Étape 3 — Échangez les données originales de A dans le nouvel UID de A.**
- Ouvrez à nouveau **Fix Host Save** avec le même `Level.sav`.
- **Source** : `1234.sav` (données originales du joueur A). **Cible** : `9999.sav` (personnage temporaire du joueur A).
- Cliquez sur le bouton. Ils échangent à nouveau.

**Après l'étape 3 :**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's temp character (unused, can delete)
9999.sav  = Player A's original character  ← restored!
```

---

**Terminé.** Le joueur B héberge le personnage original du joueur B. Le joueur A rejoint le personnage original du joueur A. Le `1234.sav` restant peut être ignoré ou supprimé.

> **Pourquoi deux échanges ?** Fix Host Save **échange** deux fichiers — ce n'est pas une copie. Le premier échange place B dans l'emplacement hôte, mais les données de A se retrouvent dans l'ancien UID de B (qui n'existe plus dans le jeu). Le deuxième échange déplace les données de A vers le nouvel UID client de A. Deux échanges, tous les progrès préservés.

</details>

### Transfert de personnage (sauvegarde croisée)

<details>
<summary>Cliquez pour agrandir</summary>

Copiez un joueur (avec tous les Pals, l'inventaire, la technologie et la progression) d'un monde à un autre – utile pour déplacer votre personnage entre un monde coopératif et un serveur dédié, ou entre deux serveurs.

**Comment ça marche :** Contrairement à Fix Host Save (qui **échange** deux fichiers), Character Transfer **copie** un joueur d'un `Level.sav` vers un autre. La sauvegarde source est intacte.

1. Ouvrez PST → **Outils** → **Transfert de caractères**.
2. **Chargez la sauvegarde source** — cliquez sur le bouton Source et sélectionnez le `Level.sav` qui contient le caractère que vous souhaitez copier (par exemple, votre ancien serveur).
3. **Chargez la sauvegarde cible** — cliquez sur le bouton Cible et sélectionnez le `Level.sav` dans lequel vous souhaitez copier (par exemple, votre nouveau serveur).
4. **Sélectionnez le joueur** à transférer dans la liste des lecteurs sources sur la gauche.
5. **Choisissez où les placer** dans la liste Joueur cible à droite : vous pouvez écraser un joueur existant ou le laisser vide pour un nouvel emplacement.
6. Cliquez sur **Transférer**. Le personnage, Pals, l'inventaire et l'appartenance à la guilde sont copiés dans la sauvegarde cible.
7. Enregistrez les modifications. Des sauvegardes automatiques sont créées.

Vous pouvez également transférer **tous les joueurs** en même temps en utilisant le bouton « Transférer tout ».

</details>

### Base Export / Import / Clone

<details>
<summary>Cliquez pour agrandir</summary>

**Exportation d'une base :**
1. Accédez à l'onglet **Bases** (ou utilisez la visionneuse de carte).
2. Cliquez avec le bouton droit sur une base → **Exporter la base**.
3. Enregistrez en tant que fichier de plan `.json`.

**Importation d'une base :**
1. Faites un clic droit sur la guilde cible (dans l'onglet Bases, Visionneuse de carte ou Guildes).
2. Sélectionnez **Importer une base** (fichier unique) ou **Importer des bases (multi-fichiers)**.
3. Sélectionnez vos fichiers `.json` exportés.

**Clonage d'une base :**
1. Cliquez avec le bouton droit sur une base → **Cloner la base**.
2. Sélectionnez la guilde cible.
3. La base est clonée avec un positionnement décalé.

**Ajustement du rayon de base :**
1. Cliquez avec le bouton droit sur une base → **Ajuster le rayon**.
2. Entrez un nouveau rayon (50 % à 1 000 %).
3. Enregistrez et rechargez la sauvegarde dans le jeu pour les structures à réaffecter.

</details>





---




<div align="center">

## Dépannage

<img src="https://readme-typing-svg.demolab.com?lines=Quand+les+choses+tournent+mal;Ne+paniquez+pas;Nous+avons+tout+vu&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### "VCRUNTIME140.dll est introuvable" (Windows)

Installez le [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015-2022).

### `struct.error` lors de l'analyse d'une sauvegarde

Le format du fichier de sauvegarde est obsolète. Chargez la sauvegarde dans le jeu (Solo, Co-op ou Serveur dédié) une fois pour déclencher une mise à jour automatique de la structure, puis réessayez. Assurez-vous que la sauvegarde a été mise à jour avec ou après le dernier patch du jeu.

### Le convertisseur GamePass ne fonctionne pas

1. Fermez complètement la version GamePass de Palworld.
2. Attendez quelques minutes que les descripteurs de fichiers soient libérés.
3. Exécutez le convertisseur GamePass → Steam.
4. Lancez Palworld sur GamePass pour vérifier.

### Le binaire Linux / macOS ne se lance pas

- **Linux :** `chmod +x PalworldSaveTools-*-linux.AppImage` pour le marquer comme exécutable.
- **macOS :** Si bloqué par Gatekeeper, cliquez avec le bouton droit → **Ouvrir** ou exécutez `xattr -d com.apple.quarantine /path/to/app`.





---




<div align="center">

## Construire à partir de la source

<img src="https://readme-typing-svg.demolab.com?lines=Compilez-le+vous-m%C3%AAme;Construisez+le+v%C3%B4tre;De+la+source+au+binaire&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST prend en charge deux chemins de construction. Le pipeline CI/CD utilise Nuitka pour les versions binaires multiplateformes ; cx_Freeze est utilisé pour le programme d'installation Windows local.

### Nuitka (Multiplateforme — Utilisé par CI/Releases)

Nécessite Python 3.11+ et `uv`. Nuitka est installé automatiquement.

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

Les sorties vont à `dist/` :
-Windows → `dist/PalworldSaveTools-*.exe`
-Linux → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → conditionné sous la forme `.dmg`

### cx_Freeze (Windows Installer)

Pour un package Windows `.zip` local :

```
scripts\build_cx.cmd
```

Cela crée `PST_standalone_v{version}.zip` à la racine du projet.

### Constructeur interactif

Un menu interactif pour choisir un mode de construction :

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## Contribuer

<img src="https://readme-typing-svg.demolab.com?lines=Vous+voulez+aider+%3F+Voici+comment;Rejoignez+l%27%C3%A9quipe;Chaque+contribution+compte&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Les contributions sont les bienvenues ! N'hésitez pas à soumettre une Pull Request.

1. Forkez le référentiel.
2. Créez votre branche de fonctionnalités (`git checkout -b feature/AmazingFeature`).
3. Validez vos modifications (`git commit -m 'Add some AmazingFeature'`).
4. Poussez vers la branche (`git push origin feature/AmazingFeature`).
5. Ouvrez une demande de tirage.





---




<div align="center">

## Avertissement

<img src="https://readme-typing-svg.demolab.com?lines=Lisez+ceci+avant+de+casser+quelque+chose;Vous+avez+%C3%A9t%C3%A9+pr%C3%A9venu;Sauvegardez+d%27abord%C2%A0%21;Avec+une+grande+puissance...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

**Utilisez cet outil à vos propres risques. Sauvegardez toujours vos fichiers de sauvegarde avant d'apporter des modifications.**

Les développeurs ne sont pas responsables de toute perte de données de sauvegarde ou des problèmes pouvant résulter de l'utilisation de cet outil.





---




<div align="center">

## Assistance

<img src="https://readme-typing-svg.demolab.com?lines=Nous+avons+votre+dos;Besoin+d%27aide+%3F;Nous+sommes+l%C3%A0+pour+vous&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

-**Discord :** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub Problèmes :** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Mods Nexus :** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## Licence

<img src="https://readme-typing-svg.demolab.com?lines=MIT+-+faites+ce+que+vous+voulez;Gratuit+comme+dans+la+bi%C3%A8re;Open+source%2C+esprit+ouvert&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Ce projet est sous licence MIT – voir le fichier [license](license) pour plus de détails.





---




<div align="center">

## L'équipe Palworld

<img src="https://readme-typing-svg.demolab.com?lines=Les+gens+derri%C3%A8re+la+magie;Rencontrez+l%27%C3%A9quipe;Construit+avec+passion&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Ce projet n'existerait pas sans les personnes qui le soutiennent.

### Mainteneurs actifs

**[Pylar](https://github.com/deafdudecomputers)** — L'homme qui a tout déclenché. Chaque ligne de cet outil remonte à sa vision et à son travail acharné sur le moteur de sauvegarde, l'interface graphique et les fonctionnalités que vous utilisez quotidiennement.

**[cyrix](https://github.com/CyrixJD115)** — Refactoriste et sous-responsable. Axé sur la qualité du code, la simplification et les améliorations structurelles, en gardant la base de code propre, plus petite et plus facile à maintenir à mesure que le projet se développe.

### Contributeurs

**[dkoz](https://github.com/dkoz)** — L'homme derrière les pièces d'identité. Fournit des identifiants de données de jeu, un aperçu structurel des codes d'identification et une connaissance approfondie de la manière dont les données de Palworld sont reliées entre elles, ce qui garantit la précision de l'outil à chaque mise à jour du jeu.

**[oMaN-Rod](https://github.com/oMaN-Rod)** — Fourni l'analyseur de sauvegarde d'origine à partir duquel ce projet est dérivé. Sans son travail fondamental sur le piratage du format de sauvegarde Palworld, rien de tout cela n’existerait. Le fork a rationalisé et simplifié son analyseur pour en faire ce qu'est PST aujourd'hui.
**[Okaetsu](https://github.com/Okaetsu)** — Informations sur le modding qui ont rendu possible l'importation/exportation de base. Sa compréhension de la façon dont Palworld structure les données de base du côté du modding a comblé le fossé entre le modding et l'édition de sauvegarde, faisant de cette fonctionnalité une réalité.





---




<div align="center">

## Remerciements

<img src="https://readme-typing-svg.demolab.com?lines=O%C3%B9+le+cr%C3%A9dit+est+d%C3%BB;Merci+%C3%A0+tous;Nous+nous+tenons+sur+les+%C3%A9paules&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Un immense merci à :

- **Palworld** développé par Pocketpair, Inc. — pour le jeu qui nous a tous réunis.
- **Les rapporteurs de bogues** — chaque problème déposé, chaque cas limite trouvé, chaque journal collé dans Discord. Vous rendez cet outil plus robuste à chaque rapport.
- **La communauté de modding Palworld** : d'autres moddeurs, développeurs d'outils et bricoleurs qui partagent leurs connaissances, effectuent de l'ingénierie inverse des formats et font avancer l'écosystème. Ce projet repose sur cet effort collectif.
- **Tous les contributeurs et membres de la communauté** — que vous ayez soumis un PR, répondu à une question dans Discord ou simplement parlé de PST à un ami — merci.

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**Réalisé avec ❤️ pour la communauté Palworld**

[⬆ Back to Top](#palworld-save-tools)

</div>