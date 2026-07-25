<div align="center">

![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Palworld를 위한 포괄적인 저장 파일 편집 툴킷**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md) | [Português (Brasil)](README.pt_BR.md) | [Português (Portugal)](README.pt_PT.md)

---

### ** [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** 에서 독립형 버전을 다운로드하세요

---

</div>
<div align="center">

## 개요

<img src="https://readme-typing-svg.demolab.com?lines=%EC%9D%B4%EA%B2%8C+%EC%A0%95%ED%99%95%ED%9E%88+%EB%AD%90%EC%A3%A0%3F;%EB%8B%B9%EC%8B%A0%EC%9D%98+%EC%A0%80%EC%9E%A5%2C+%EB%8B%B9%EC%8B%A0%EC%9D%98+%EB%B0%A9%EC%8B%9D;%EB%AA%A8%EB%93%A0+%EA%B2%83%EC%9D%84+%EC%A7%80%EB%B0%B0%ED%95%98%EB%8A%94+%ED%95%98%EB%82%98%EC%9D%98+%EB%8F%84%EA%B5%AC&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools(PST)는 Palworld 저장 파일을 검사하고 편집하기 위한 빠른 올인원 데스크탑 애플리케이션입니다. Python 및 PySide6으로 구축되어 게임의 압축된 저장 형식을 직접 읽고 씁니다. 게임 모드가 필요하지 않습니다.

전용 서버 관리, 협동 서버와 전용 서버 간 마이그레이션, 버려진 데이터 정리 또는 개별 Pals 미세 조정이 필요한 경우 PST는 모든 작업에 대해 단일 통합 인터페이스를 제공합니다.

### 하이라이트

- **교차 플랫폼** — **Windows**, **Linux** 및 **macOS**용으로 사전 구축된 바이너리입니다.
- **빠른 기본 구문 분석** — [`palsav`](src/palsav) 엔진으로 구동되는 사용 가능한 가장 빠른 저장 파일 리더 중 하나입니다.
- **시각적 지도** — 기지/플레이어 마커, 제외 구역 및 좌표 보정이 포함된 대화형 세계 지도입니다.
- **심층적인 Pal 편집** — 통계, IVs, 영혼, 스킬, passives, 작업 적합성, 순위 및 외모 플래그를 완벽하게 제어할 수 있습니다.
- **서버급 도구** — 관리자를 위해 구축된 대량 삭제, 정리, 변환 및 문자 전송.
- **자동 백업** — 모든 저장 작업은 쓰기 전에 백업을 생성합니다.
- **9개 언어** — 현지화된 UI, 인앱 가이드 및 문서.





---





## 목차

- [개요](#개요)
- [기능](#기능)
- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [가이드](#가이드)
- [문제 해결](#문제-해결)
- [소스에서 빌드](#소스에서-빌드)
- [기여](#기여)
- [라이센스](#라이센스)
- [팔월드 팀](#팔월드-팀)





---




<div align="center">

## 기능

<img src="https://readme-typing-svg.demolab.com?lines=%EC%A2%8B%EC%9D%80+%EA%B2%83%EB%93%A4;%ED%99%95%EC%9D%B8%ED%95%B4+%EB%B3%B4%EC%84%B8%EC%9A%94;%EB%8F%84%EA%B5%AC%EA%B0%80+%EA%B0%80%EB%93%9D&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

| 카테고리 | 당신이 할 수 있는 일 |
|---|---|
| **플레이어 관리** | 이름, 레벨, 통계, 기술 포인트를 편집합니다. 플레이어 전반에 걸쳐 항목, pals, 기술을 대량 관리합니다. 비활성 또는 중복 플레이어를 정리합니다. |
| **Pal Editor** | 변경 통계, IVs, 영혼, 순위, 기술, passives, 작업 적합성, 보스/행운 플래그. 내보내기/가져오기 pals. 불법적인 pals을 감지하고 수정합니다. 무제한 편집을 위한 치트 모드. |
| **길드 관리** | 길드 이름을 바꾸고, 리더를 바꾸고, 레벨을 설정하세요. 실험실 연구를 잠금 해제하세요. 길드 간에 플레이어를 이동합니다. 비어 있거나 활동하지 않는 길드를 삭제하세요. |
| **베이스캠프 도구** | 길드 정보가 포함된 모든 기지를 확인하세요. 청사진 내보내기/가져오기. 기지를 다른 길드에 복제하세요. 지도에서 기지 위치를 변경하세요. 반경을 조정합니다. 비활성 기지를 삭제합니다. |
| **맵 뷰어** | 기지 및 플레이어 마커가 포함된 대화형 세계 지도입니다. 제외 구역을 그립니다. 교정 모드. 월드맵과 트리맵 보기. 확대/축소, 이동, 이동. |
| **재고관리** | 플레이어 아이템, 키 아이템, 장비 슬롯을 편집합니다. 모든 빠른 이동 지점을 잠금 해제하세요. 모든 길드의 기본 인벤토리와 컨테이너를 탐색하고 편집하세요. 기본 작업자 pals을 관리합니다. |
| **제외** | 지속적인 제외 목록을 사용하여 플레이어, 길드 및 기지를 정리로부터 보호하세요. 상황에 맞는 메뉴에서 항목을 추가합니다. |
| **도구 저장** | SAV와 JSON 간에 저장을 변환합니다. GamePass을 Steam로 변환합니다. 세계 간 캐릭터 전송. 호스트 저장을 수정합니다. 지도 진행 상황을 복원합니다. 팔박스 슬롯을 확장하세요. |
| **청소 및 유틸리티** | 빈 길드, 비활성 기지/플레이어, 참조되지 않은 데이터를 삭제하세요. 잘못된 항목/pals/구조를 제거하세요. 던전, 석유 굴착 장치, 보급품 투하를 재설정하세요. 타임스탬프를 수정하세요. |

### 플레이어 관리

- 이름, 레벨, pal 수, UID, 길드, 마지막 접속 시간을 기준으로 모든 플레이어를 보고 검색할 수 있습니다.
- 플레이어 이름, 레벨, 통계, 기술 포인트를 편집합니다.
- **통계 탭** — 게임 내에서 계산된 값이 포함된 영웅 통계(건강, 체력, 공격, 방어, 작업 속도, 체중) 토글과 스피너가 있는 유물 능력.
- **모든 통계 최대치** — 모든 통계를 즉시 최대(50포인트)로 제한합니다.
- 여러 플레이어에 걸친 **대량 작업**: 아이템 관리, pal 관리 및 기술 잠금 해제.
- 시간 기준에 따라 비활성 플레이어를 삭제합니다. 중복을 제거하십시오.

### Pal Editor

모든 플레이어가 소유한 Pal에 대한 심층 편집 인터페이스입니다. Pals은 **파티**(활성 분대)와 **Palbox**(저장소)로 구성됩니다.

- **통계 및 IVs** — HP, 공격, 방어(IV 0–100), 레벨(1–80), 신뢰 순위(0–10).
- **소울** — HP, 공격, 방어, 제작 속도(0–20).
- **스킬** — 활성 스킬 선택기; 모든 동작을 배우십시오. Pals 전반에 걸친 대량 동기화 기술.
- **패시브 특성** — 전체 게임 데이터를 포함하는 패시브 선택기입니다.
- **작업 적합성** — 개별 작업 적합성 수준(0~10)을 설정합니다.
- **외모 플래그** — 보스/알파, 럭키/샤이니, 프레데터, 각성 및 수입/DNA를 전환합니다.
- **순위 및 잠금** — 순위 및 즐겨찾기 잠금 수준(0~3)을 설정합니다.
- **치트 모드** — 레벨, IVs, 영혼, 응축기 등급을 255로 확장하려면 토글하세요. 중복이 허용되는 무제한 액티브/패시브 스킬을 잠금 해제하세요.
- **내보내기/가져오기** — pal을 마우스 오른쪽 버튼으로 클릭하여 `.pstpal`(압축) 또는 `.json`로 내보냅니다. 파티, 팔박스, DPS 또는 기본 작업자의 빈 슬롯으로 가져옵니다. 저장 및 플레이어 전반에 걸쳐 작동합니다.
- **최대 전체 Pals** — 파티의 모든 pals, 모든 팔박스 페이지 또는 모든 기본 작업자에 대한 모든 통계(IVs, 영혼, 순위, 레벨)를 최대화합니다. — 치트 모드 한도를 준수합니다.
- **불법 Pals 수정** — 불법적인 통계, 기술 또는 플레이어별 특성이 있는 pals을 감지하고 제한합니다.
- **대량 복제/삭제** — 일괄 작업을 위한 수량 제어 및 소스 토글(파티/팔박스/DPS)이 있는 종 선택 대화 상자입니다.
- 새로운 Pals을 추가하거나 두 번 클릭하여 빠르게 삭제하세요.

### 길드 관리

2패널 보기: 상단에는 길드 목록, 하단에는 회원 명단이 표시됩니다.

- 길드 이름 바꾸기, 리더 변경, 길드 레벨 설정, 최대 길드 레벨 설정.
- 모든 연구실 연구를 잠금 해제하세요. 모든 길드를 재건하세요.
- 길드 간에 플레이어를 이동합니다. 비어 있거나 활동하지 않는 길드를 삭제하세요.

### 베이스캠프 도구

- 길드 연합이 있는 모든 베이스캠프를 볼 수 있습니다.
- 기본 청사진을 `.json`로 **내보내기**; **가져오기**(단일 또는 다중 파일)를 모든 길드로 가져옵니다.
- 오프셋 위치 지정을 통해 다른 길드에 기지를 **복제**합니다.
- **좌표 변경** — ​​지도에서 기지 마커를 마우스 오른쪽 버튼으로 클릭하고 "좌표 변경"을 선택한 다음 기지를 순간 이동할 지점을 클릭합니다.
- **베이스 너지** — 정확한 X/Y/Z 오프셋으로 베이스를 조금씩 움직여 지면이 잘리거나 떠 있는 문제를 해결합니다.
- **기본 반경을 조정합니다**(50%~1000%).
- 비활성 기지와 기지가 아닌 지도 개체를 삭제합니다.

### 맵 뷰어

전체 세계를 대화형으로 시각화합니다.

- 세부 패널이 포함된 기본 마커(집 아이콘) 및 플레이어 마커(사람 아이콘).
- 오버레이 전환: 기지, 플레이어, 반경 링, 제외 구역.
- **구역 그리기** — 지도에 직접 직사각형 또는 다각형 제외 구역을 그립니다.
- **보정 모드** — 지도를 게임 좌표에 정확하게 맞춥니다.
- 세계 지도 및 트리 지도 보기 길드나 플레이어 이름으로 필터링하세요.
- 확대/축소(1.0x~30.0x), 이동, 두 번 클릭하여 마커로 이동합니다.
- 관리 작업을 위한 마커 및 빈 공간을 마우스 오른쪽 버튼으로 클릭합니다.

### 재고 관리

**플레이어 인벤토리** — 세 개의 하위 탭:
- *인벤토리* — 메인 가방에 있는 모든 아이템과 장비; 수량 편집, 추가, 제거.
- *주요 아이템* — 퀘스트 아이템, 조각상, 기술 모든 조각상/핵심 항목을 대량 추가합니다.
- *통계* — 레벨, HP, 체력, 공격, 방어, 작업 속도, 무게.
- 무기, 액세서리, 음식, 방어구, 방패, 글라이더, 모듈 슬롯을 위한 장비 패널입니다.
- 한 번의 클릭으로 모든 지도와 빠른 이동 지점을 잠금 해제할 수 있습니다.

**기본 인벤토리** — 항목을 찾아보고 관리하며 모든 기지에서 Pals 작업을 수행합니다.
- 컨테이너의 항목 보기/편집 투명한 용기; 컨테이너 슬롯을 수정합니다.
- 길드 간 아이템 작업(모든 길드에서 아이템 찾기/제거)
- 길드 간 구조 삭제.
- **베이스 Pals** 하위 탭 — 전체 pal 편집기 상황에 맞는 메뉴를 사용하여 각 베이스에 할당된 작업 Pals을 관리합니다.

### 제외

플레이어, 길드, 기지를 청소 작업으로부터 보호하는 보호 목록입니다.

- 3개의 나란히 있는 패널: 제외된 플레이어 UID, 길드 ID 및 기본 ID.
- 플레이어, 길드 또는 기지 탭에서 마우스 오른쪽 버튼 클릭 상황에 맞는 메뉴를 통해 항목을 추가합니다.
- 제외 목록을 지속적으로 저장하고 로드합니다.
- 대량 정리를 실행하기 **전에** 목록을 작성하세요.

### 저장 도구

**도구** 탭에서 클릭 가능한 카드로 액세스 가능:

| 도구 | 설명 |
|------|-------------|
| **저장 내용 변환** | SAV와 JSON 형식 간 변환 |
| **GamePass → Steam** 변환 | Xbox/GamePass 변환을 Steam 형식으로 저장 |
| **SteamID 변환** | Steam ID를 Palworld UID로 변환 |
| **지도 복원** | 모든 월드/서버에 완전히 잠금 해제된 지도 진행 상황 적용 |
| **슬롯 인젝터** | 플레이어당 팔박스 슬롯 늘리기 |
| **수정 저장** | 원시 저장 데이터 열기 및 수정 |
| **캐릭터 이전** | 다른 월드/서버 간 캐릭터 전송(교차 저장) |
| **호스트 저장 수정** | 두 플레이어 간 UID 교환(호스트 교환, 플랫폼 마이그레이션) |

### 정리 및 유틸리티 기능

**메뉴 → 기능**을 통해 액세스할 수 있는 이러한 서버급 작업에는 다음이 포함됩니다.

- **삭제** — 빈 길드, 비활성 기지/플레이어, 중복 플레이어, 참조되지 않은 데이터를 삭제합니다.
- **정리** — 유효하지 않은/수정된 항목, 유효하지 않은 pals 및 passives, 유효하지 않은 구조를 제거합니다. 불법적인 pals을 수정합니다(적법한 최대값으로 제한). 대공 포탑을 재설정합니다. private chests 잠금 해제; 모든 구조물을 수리하십시오.
- **재설정** — 미션, 던전, 석유 굴착 장치, 침입자, 보급품 투하를 재설정합니다.
- **타임스탬프** — 부정적인 타임스탬프를 수정합니다. 플레이어 시간을 재설정합니다.
- **PalDefender** — `killnearestbase` 명령을 생성합니다.





---




<div align="center">

## 설치

<img src="https://readme-typing-svg.demolab.com?lines=%EB%AA%87+%EB%B6%84+%EB%A7%8C%EC%97%90+%EC%8B%A4%ED%96%89%ED%95%B4+%EB%B3%B4%EC%84%B8%EC%9A%94;%EB%8B%A4%EC%9A%B4%EB%A1%9C%EB%93%9C%ED%95%98%EA%B3%A0+%EC%9D%B4%EB%8F%99;%EC%84%A4%EC%A0%95%EC%9D%B4+%ED%95%84%EC%9A%94%ED%95%98%EC%A7%80+%EC%95%8A%EC%8A%B5%EB%8B%88%EB%8B%A4&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 독립형 빌드(권장)

사전 빌드된 바이너리는 [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)의 세 가지 주요 플랫폼 모두에서 사용할 수 있습니다.

| 플랫폼 | 다운로드 | 요구사항 |
|------------|------------|-------------|
| **창** | `PalworldSaveTools-*.exe` | 윈도우 10/11, [VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)(2015~2022) |
| **리눅스** | `PalworldSaveTools-*-linux` | 모든 최신 배포판 |
| **맥OS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+(몬트레이 이상) |

[Nexus Mods](https://www.nexusmods.com/palworld/mods/3190)에서도 사용 가능합니다.

1. 귀하의 플랫폼에 적합한 빌드를 다운로드하십시오.
2. 실행 파일을 추출하고(보관된 경우) 실행합니다.
3. 그게 다입니다. Python이나 종속성이 필요하지 않습니다.

> **Windows:** "VCRUNTIME140.dll을 찾을 수 없습니다."라는 메시지가 표시되면 [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)을 설치하세요.

> **Linux:** 파일을 실행 가능으로 표시해야 할 수도 있습니다: `chmod +x PalworldSaveTools-*-linux`

> **macOS:** Gatekeeper가 앱을 차단하는 경우 마우스 오른쪽 버튼을 클릭하고 → **처음 열기**를 클릭하거나 `xattr -d com.apple.quarantine /path/to/app`을 실행하세요.

### 소스에서(모든 플랫폼)

PST는 종속성 관리를 위해 [`uv`](https://docs.astral.sh/uv/)을 사용합니다. 시작 스크립트는 자동으로 가상 환경을 생성하고 모든 것을 설치합니다.

**전제 조건:** [Python 3.11+](https://www.python.org/) 및 [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows**(더블클릭 실행 프로그램):
```
start.cmd
```

런처는 `.venv`을 생성하고, `uv sync`을 통해 종속성을 설치하고, 앱을 부팅합니다. 각 실행을 재현할 수 있도록 종료 시 잠금 파일을 정리합니다.





---




<div align="center">

## 빠른 시작

<img src="https://readme-typing-svg.demolab.com?lines=%EB%A1%9C%EB%93%9C.+%ED%8E%B8%EC%A7%91%ED%95%98%EB%8B%A4.+%EA%B5%AC%ED%95%98%EB%8B%A4.+%EA%B0%84%EB%8B%A8%ED%95%B4%EC%9A%94.;%EC%98%81%EA%B4%91%EC%9D%84+%ED%96%A5%ED%95%9C+%EC%84%B8+%EB%8B%A8%EA%B3%84;%EA%B7%B8%EB%A7%8C%ED%81%BC+%EC%89%BD%EC%A3%A0&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **저장 파일 로드**
   - **메뉴 → 저장 로드**를 클릭하거나 `.sav` 파일을 창에 끌어다 놓습니다.
   - Palworld 저장 폴더로 이동하여 `Level.sav`을 선택하세요.

2. **데이터 탐색**
   - **지도**, **도구**, **플레이어**, **길드**, **기지**, **플레이어 인벤토리**, **베이스 인벤토리**, **Pal Editor**, **제외** 탭을 사용하여 저장 내용을 살펴보세요.
   - 통계 표시줄에는 실시간 카운트가 표시됩니다. 빠른 탐색 아이콘은 각 섹션으로 이동합니다.

3. **변경**
   - 선택하려면 마우스 왼쪽 버튼을 클릭하세요. 상황에 맞는 작업을 수행하려면 거의 모든 것을 마우스 오른쪽 버튼으로 클릭하세요.
   - 더블클릭하면 빠른 편집, 빠른 삭제가 가능합니다. (자세한 내용은 앱 내 가이드를 참고하세요.)

4. **변경 사항 저장**
   - **메뉴 → 변경사항 저장**을 클릭합니다. 백업은 자동으로 생성됩니다.

> **팁:** 각 탭에는 기본 제공 가이드가 있습니다. 탭에서 수행할 수 있는 작업을 정확히 보려면 ​​탭에서 도움말 아이콘을 클릭하세요. 더 자세한 내용을 보려면 **버튼, 필드 또는 컨트롤 위로 마우스를 가져가면** 헤더에 자세한 툴팁이 표시됩니다. 앱 내 도구 설명 도움말 시스템은 모든 기능의 기능과 사용 방법을 정확히 이해하기 위한 최고의 참고 자료입니다.





---




<div align="center">

## 가이드

<img src="https://readme-typing-svg.demolab.com?lines=%EB%8B%A8%EA%B3%84%EB%B3%84+%EC%97%B0%EC%8A%B5;%EA%B0%80%EC%9D%B4%EB%93%9C%EB%A5%BC+%EB%94%B0%EB%A5%B4%EC%84%B8%EC%9A%94;%EB%B0%A9%EB%B2%95%EC%9D%84+%EC%95%8C%EB%A0%A4%EB%93%9C%EB%A6%AC%EA%B2%A0%EC%8A%B5%EB%8B%88%EB%8B%A4.&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### 저장 파일 위치

**호스트/협동조합(Windows):**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**전용 서버:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### 지도 잠금 해제

PST는 저장을 위해 전체 지도(모든 빠른 이동 지점)를 잠금 해제할 수 있습니다.

1. PST로 저장 내용을 로드합니다.
2. **플레이어 인벤토리** 탭을 열고 단일 플레이어의 경우 **모든 지도 잠금 해제 + 빠른 이동**을 클릭합니다. **또는**
3. 도구 탭의 **지도 복원** 도구를 사용하여 **모든** 월드/서버에 잠금 해제된 지도 진행 상황을 한 번에 적용합니다.
4. 변경 사항을 저장합니다. 자동 백업이 생성됩니다.

### 협동 → 전용 서버

<details>
<summary>확대하려면 클릭하세요</summary>

PC에서 호스팅하는 협동 세계를 전용 서버로 이동하면 오프라인에서도 다른 사람들이 플레이할 수 있습니다.

**작동 방식:** 협동 저장은 호스트 플레이어에 `0001.sav`을 사용합니다. 전용 서버는 그렇지 않습니다. 모든 플레이어는 일반 UID를 가지고 있습니다. 호스트 수정 복사본이 아닌 **교환** 두 개의 플레이어 파일(예: 거래 좌석)을 저장합니다. `0001.sav`의 협동 캐릭터가 서버 슬롯으로 교체됩니다.

1. **협동 저장을 서버에 복사하세요.**
   - 협동전 저장 위치: `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`
   - 거기에서 `Level.sav` 및 `Players` 폴더를 복사합니다.
   - 서버 저장 폴더에 붙여넣기: `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`

2. **서버에 접속하여 임시 캐릭터를 생성합니다.**
   - 서버를 시작하고, 가입하고, 새 캐릭터를 생성하세요(이름/외모는 상관없습니다. 이는 단지 자리 표시자일 뿐입니다).
   - 자동 저장을 기다린 후 서버를 종료하세요.

3. **협동 캐릭터를 서버 슬롯으로 교체하세요.**
   - PST → **도구** → **호스트 저장 수정**을 엽니다.
   - 서버의 `Level.sav`을 탐색합니다.
   - **소스 플레이어**: 협동 캐릭터(`0001.sav`에 있는 캐릭터 - 호스트로 나열됨)를 선택합니다.
   - **대상 플레이어**: 방금 생성한 임시 캐릭터를 선택합니다.
- 버튼을 클릭하면 스왑이 실행됩니다.

4. **서버를 시작합니다.**
   - 귀하의 원래 협동 캐릭터(모든 진행 상황, Pals, 베이스 포함)가 이제 서버에 연결되었습니다. 임시 자리 표시자가 사라졌습니다.

</details>

### 전용서버 → 협동

<details>
<summary>확대하려면 클릭하세요</summary>

전용 서버 캐릭터를 로컬 협동 저장으로 되돌리세요. 서버 임대를 중단하거나 오프라인으로 플레이하고 싶을 때 유용합니다.

**작동 방식:** 동일한 GUID 역방향 교체 — 호스트 수정 복사본이 아닌 두 개의 파일을 **교환** 저장합니다. 귀하의 서버 캐릭터(일반 UID)는 `0001.sav`(호스트 슬롯)로 교체되므로 서버 진행 상황에 맞춰 협동 플레이를 호스트할 수 있습니다.

1. **서버 저장을 로컬 PC에 복사하세요.**
   - 서버 저장 위치 : `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`
   - 거기에서 `Level.sav` 및 `Players` 폴더를 복사합니다.
   - 로컬 협동 폴더에 붙여넣습니다: `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`

2. **협동 게임을 호스팅하고 임시 캐릭터를 생성하세요.**
   - Palworld를 시작하고, 협동 세션을 주최하고, 새로운 캐릭터를 생성하세요.
   - 자동 저장 후 Palworld를 닫으세요.

3. **서버 캐릭터를 호스트 슬롯으로 교체하세요.**
   - PST → **도구** → **호스트 저장 수정**을 엽니다.
   - 지역 협동조합 `Level.sav`을 찾아보세요.
   - **소스 플레이어**: 전용 서버 캐릭터를 선택합니다(UID별로 나열).
   - **대상 플레이어**: 임시 협동 캐릭터(`0001.sav`에 있는 캐릭터 - 호스트로 나열됨)를 선택합니다.
   - 버튼을 클릭하면 스왑이 실행됩니다.

4. **일반적으로 호스트 협동조합이 가능합니다.**
   - 귀하의 서버 캐릭터가 이제 호스트입니다(`0001.sav`). 모든 진행 상황, Pals 및 기지는 그대로 유지됩니다.

</details>

### 호스트 변경(협동 교환)

<details>
<summary>확대하려면 클릭하세요</summary>

두 명의 플레이어가 호스트를 바꾸고 싶어합니다. 플레이어 A가 호스팅 중입니다. 해당 캐릭터는 `0001.sav`에 살고 있습니다. 플레이어 B는 클라이언트로 참여합니다. 그들의 캐릭터는 `1234.sav`에 살고 있습니다. 이제 그들은 플레이어 B가 호스트가 되기를 원하지만 호스트 슬롯은 항상 `0001.sav`입니다.

**핵심 개념 — 호스트 저장 수정은 항상 두 명의 플레이어를 교환합니다.** 두 사람이 자리를 교환하는 것처럼 저장 파일을 교환합니다. 하나를 다른 것으로 복사하지 않습니다. 교체 후에도 두 플레이어는 여전히 존재합니다. 단지 서로 다른 파일에 있을 뿐입니다.

한 번의 스왑은 플레이어 B를 호스트 슬롯으로 이동하지만 플레이어 A의 데이터는 B의 이전 파일에 남겨두기 때문에 플레이어 A의 원래 캐릭터를 다시 되돌리려면 두 번째 스왑이 필요합니다. 방법은 다음과 같습니다.

---

**시작 상태:**
```
0001.sav  = Player A (current host)
1234.sav  = Player B (current client)
```

---

**1단계 - A와 B를 교환합니다.**
- PST → **도구** → **호스트 저장 수정**을 엽니다.
- 협동조합 `Level.sav`을(를) 찾아보세요.
- **출처**: 플레이어 A(`0001.sav`). **대상**: 플레이어 B(`1234.sav`).
- 버튼을 클릭하세요. Fix Host Save는 두 파일을 교환합니다.

**1단계 이후:**
```
0001.sav  = Player B  ← now the host with B's character
1234.sav  = Player A  ← A's data is here, but this UID no longer exists in the game
```

---

**2단계 — 플레이어 B 호스트, 플레이어 A가 합류합니다.**
- 플레이어 B가 세계를 호스팅합니다. 플레이어 A가 합류합니다.
- A는 더 이상 호스트가 아니므로 Palworld는 A의 임시 캐릭터(예: `9999.sav`)에 대해 새로운 UID를 할당합니다.
- 플레이어 A가 임시 캐릭터로 **레벨 2**에 도달한 후 모두가 게임을 종료합니다.

**2단계 이후:**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's original data (not linked to any active UID)
9999.sav  = Player A's temporary character (fresh, Level 2+)
```

---

**3단계 - A의 원본 데이터를 A의 새 UID로 바꿉니다.**
- 동일한 `Level.sav`로 **Fix Host Save**를 다시 엽니다.
- **출처**: `1234.sav` (플레이어 A의 원본 데이터). **대상**: `9999.sav`(플레이어 A의 임시 캐릭터).
- 버튼을 클릭하세요. 그들은 다시 교환합니다.

**3단계 이후:**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's temp character (unused, can delete)
9999.sav  = Player A's original character  ← restored!
```

---

**완료.** 플레이어 B는 플레이어 B의 오리지널 캐릭터로 호스트합니다. 플레이어 A가 플레이어 A의 원래 캐릭터와 합류합니다. 남은 `1234.sav`은 무시하거나 삭제할 수 있습니다.

> **두 개의 스왑이 필요한 이유는 무엇입니까?** 호스트 수정 두 개의 파일을 **교환** 저장합니다. 이는 복사본이 아닙니다. 첫 번째 교체에서는 B를 호스트 슬롯에 넣지만 A의 데이터는 B의 이전 UID(더 이상 게임에 존재하지 않음)로 끝납니다. 두 번째 스왑은 A의 데이터를 A의 새 클라이언트 UID로 이동합니다. 두 번의 교체, 모든 진행 상황이 유지됩니다.

</details>

### 캐릭터 이전(교차저장)

<details>
<summary>확대하려면 클릭하세요</summary>

플레이어(모든 Pals, 인벤토리, 기술 및 진행 상황 포함)를 한 세계에서 다른 세계로 복사합니다. 협동 세계와 전용 서버 간 또는 두 서버 간에 캐릭터를 이동하는 데 유용합니다.

**작동 방식:** 두 개의 파일을 **교환**하는 Fix Host Save와 달리 캐릭터 전송은 한 `Level.sav`에서 다른 `Level.sav`로 플레이어를 **복사**합니다. 소스 저장은 그대로 유지됩니다.

1. PST → **도구** → **문자 전송**을 엽니다.
2. **소스 저장 로드** — 소스 버튼을 클릭하고 복사하려는 캐릭터가 있는 `Level.sav`을 선택합니다(예: 이전 서버).
3. **저장된 대상 로드** — 대상 버튼을 클릭하고 복사하려는 `Level.sav`(예: 새 서버)을 선택합니다.
4. 왼쪽 소스 플레이어 목록에서 전송할 플레이어를 선택하세요**.
5. 오른쪽의 대상 플레이어 목록에서 **배치할 위치를 선택**하세요. 기존 플레이어를 덮어쓰거나 새 슬롯을 위해 비워 둘 수 있습니다.
6. **전송**을 클릭합니다. 캐릭터, Pals, 인벤토리, 길드원 정보가 대상 저장에 복사됩니다.
7. 변경 사항을 저장합니다. 자동 백업이 생성됩니다.

"모두 전송" 버튼을 사용하여 **모든 플레이어**를 한 번에 전송할 수도 있습니다.

</details>

### 기본 내보내기/가져오기/복제

<details>
<summary>확대하려면 클릭하세요</summary>

**베이스 내보내기:**
1. **기지** 탭으로 이동합니다(또는 Map Viewer를 사용합니다).
2. 베이스를 마우스 오른쪽 버튼으로 클릭 → **베이스 내보내기**.
3. `.json` 청사진 파일로 저장합니다.

**베이스 가져오기:**
1. 대상 길드(거점 탭, 맵 뷰어, 길드 탭)를 마우스 오른쪽 버튼으로 클릭하세요.
2. **베이스 가져오기**(단일 파일) 또는 **베이스 가져오기(다중 파일)**를 선택합니다.
3. 내보낸 `.json` 파일을 선택합니다.

**베이스 복제:**
1. 베이스를 마우스 오른쪽 버튼으로 클릭 → **베이스 복제**.
2. 대상 길드를 선택하세요.
3. 오프셋 위치 지정을 통해 베이스가 복제됩니다.

**베이스 반경 조정:**
1. 베이스를 마우스 오른쪽 버튼으로 클릭 → **반경 조정**.
2. 새 반경(50%~1000%)을 입력합니다.
3. 구조를 재할당하려면 게임 내 저장 내용을 저장하고 다시 로드하세요.

</details>





---




<div align="center">

## 문제 해결

<img src="https://readme-typing-svg.demolab.com?lines=%EC%9D%BC%EC%9D%B4+%EC%98%86%EC%9C%BC%EB%A1%9C+%ED%9D%98%EB%9F%AC%EA%B0%88+%EB%95%8C;%EB%8B%B9%ED%99%A9%ED%95%98%EC%A7%80+%EB%A7%88%EC%84%B8%EC%9A%94;%EC%9A%B0%EB%A6%AC%EB%8A%94+%EA%B7%B8%EA%B2%83%EC%9D%84+%EB%AA%A8%EB%91%90+%EB%B3%B4%EC%95%98%EB%8B%A4&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### "VCRUNTIME140.dll을 찾을 수 없습니다."(Windows)

[Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)(2015~2022)을 설치합니다.

### `struct.error` 저장 파일을 분석할 때

저장 파일 형식이 오래되었습니다. 자동 구조 업데이트를 실행하려면 게임 내 저장 파일(솔로, 협동 또는 전용 서버)을 한 번 로드한 후 다시 시도하세요. 최신 게임 패치나 그 이후에 저장 내용이 업데이트되었는지 확인하세요.

### GamePass 변환기가 작동하지 않습니다

1. Palworld의 GamePass 버전을 완전히 닫습니다.
2. 파일 핸들이 해제될 때까지 몇 분 정도 기다립니다.
3. GamePass → Steam 변환기를 실행합니다.
4. GamePass에서 Palworld를 실행하여 확인하세요.

### Linux/macOS 바이너리가 실행되지 않습니다.

- **Linux:** `chmod +x PalworldSaveTools-*-linux` 실행 가능으로 표시합니다.
- **macOS:** Gatekeeper에 의해 차단된 경우 마우스 오른쪽 버튼을 클릭하고 → **열기**를 클릭하거나 `xattr -d com.apple.quarantine /path/to/app`을 실행하세요.





---




<div align="center">

## 소스에서 빌드

<img src="https://readme-typing-svg.demolab.com?lines=%EC%A7%81%EC%A0%91+%EC%BB%B4%ED%8C%8C%EC%9D%BC%ED%95%B4%EB%B3%B4%EC%84%B8%EC%9A%94;%EB%82%98%EB%A7%8C%EC%9D%98+%EA%B2%83%EC%9D%84+%EB%A7%8C%EB%93%A4%EC%96%B4%EB%B3%B4%EC%84%B8%EC%9A%94;%EC%86%8C%EC%8A%A4%EC%97%90%EC%84%9C+%EB%B0%94%EC%9D%B4%EB%84%88%EB%A6%AC%EB%A1%9C&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST는 두 가지 빌드 경로를 지원합니다. CI/CD 파이프라인은 크로스 플랫폼 릴리스 바이너리에 Nuitka를 사용합니다. cx_Freeze는 로컬 Windows 설치 프로그램에 사용됩니다.

### Nuitka(교차 플랫폼 — CI/릴리스에서 사용)

Python 3.11+ 및 `uv`이 필요합니다. Nuitka는 자동으로 설치됩니다.

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

출력은 `dist/`로 이동합니다.
- 윈도우 → `dist/PalworldSaveTools-*.exe`
- 리눅스 → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → `.dmg`으로 패키징됨

### cx_Freeze(Windows 설치 프로그램)

로컬 Windows `.7z` 패키지의 경우:

```
scripts\build_cx.cmd
```

그러면 프로젝트 루트에 `PST_standalone_v{version}.zip`이 생성됩니다.

### 인터랙티브 빌더

빌드 모드를 선택하는 대화형 메뉴:

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## 기여

<img src="https://readme-typing-svg.demolab.com?lines=%EB%8F%84%EC%9B%80%EC%9D%84+%EC%A3%BC%EA%B3%A0+%EC%8B%B6%EC%9C%BC%EC%8B%A0%EA%B0%80%EC%9A%94%3F+%EB%B0%A9%EB%B2%95%EC%9D%80+%EB%8B%A4%EC%9D%8C%EA%B3%BC+%EA%B0%99%EC%8A%B5%EB%8B%88%EB%8B%A4;%ED%8C%80%EC%97%90+%ED%95%A9%EB%A5%98%ED%95%98%EC%84%B8%EC%9A%94;%EB%AA%A8%EB%93%A0+%EA%B8%B0%EC%97%AC%EA%B0%80+%EC%A4%91%EC%9A%94%ED%95%A9%EB%8B%88%EB%8B%A4&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

기여를 환영합니다! 언제든지 Pull Request를 제출해 주세요.

1. 저장소를 포크하십시오.
2. 기능 분기(`git checkout -b feature/AmazingFeature`)를 만듭니다.
3. 변경 사항을 커밋합니다(`git commit -m 'Add some AmazingFeature'`).
4. 분기(`git push origin feature/AmazingFeature`)로 푸시합니다.
5. 끌어오기 요청을 엽니다.





---




<div align="center">

## 면책조항

<img src="https://readme-typing-svg.demolab.com?lines=%EB%AC%B4%EC%96%B8%EA%B0%80%EB%A5%BC+%EA%B9%A8%EA%B8%B0+%EC%A0%84%EC%97%90+%EC%9D%B4%EA%B2%83%EC%9D%84+%EC%9D%BD%EC%9C%BC%EC%8B%AD%EC%8B%9C%EC%98%A4;%EB%8B%B9%EC%8B%A0%EC%9D%80+%EA%B2%BD%EA%B3%A0%EB%A5%BC+%EB%B0%9B%EC%95%98%EC%8A%B5%EB%8B%88%EB%8B%A4;%EB%A8%BC%EC%A0%80+%EB%B0%B1%EC%97%85%ED%95%98%EC%84%B8%EC%9A%94%21;%EC%97%84%EC%B2%AD%EB%82%9C+%ED%9E%98%EC%9C%BC%EB%A1%9C...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

**이 도구를 사용할 때 발생하는 위험은 사용자 본인의 책임입니다. 수정하기 전에 항상 저장 파일을 백업하십시오.**

이 도구를 사용함으로써 발생할 수 있는 저장 데이터의 손실이나 문제에 대해 개발자는 책임을 지지 않습니다.





---




<div align="center">

## 지원

<img src="https://readme-typing-svg.demolab.com?lines=%EC%9A%B0%EB%A6%AC%EB%8A%94+%EB%8B%B9%EC%8B%A0%EC%9D%98+%EB%92%A4%EB%A5%BC+%EC%A7%80%EC%9B%90%ED%95%A9%EB%8B%88%EB%8B%A4;%EB%8F%84%EC%9B%80%EC%9D%B4+%ED%95%84%EC%9A%94%ED%95%98%EC%8B%A0%EA%B0%80%EC%9A%94%3F;%EC%9A%B0%EB%A6%AC%EB%8A%94+%EB%8B%B9%EC%8B%A0%EC%9D%84+%EC%9C%84%ED%95%B4+%EC%97%AC%EA%B8%B0+%EC%9E%88%EC%8A%B5%EB%8B%88%EB%8B%A4&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub 문제:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Nexus 모드:** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## 라이센스

<img src="https://readme-typing-svg.demolab.com?lines=MIT+-+%EC%9B%90%ED%95%98%EB%8A%94+%EB%8C%80%EB%A1%9C+%ED%95%98%EC%84%B8%EC%9A%94;%EB%A7%A5%EC%A3%BC%EC%B2%98%EB%9F%BC+%EB%AC%B4%EB%A3%8C;%EC%98%A4%ED%94%88+%EC%86%8C%EC%8A%A4%2C+%EC%97%B4%EB%A6%B0+%EB%A7%88%EC%9D%8C&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다. 자세한 내용은 [license](license) 파일을 참조하세요.





---




<div align="center">

## 팔월드 팀

<img src="https://readme-typing-svg.demolab.com?lines=%EB%A7%88%EB%B2%95+%EB%92%A4%EC%97%90+%EC%88%A8%EC%9D%80+%EC%82%AC%EB%9E%8C%EB%93%A4;%ED%8C%80%EC%9D%84+%EB%A7%8C%EB%82%98%EB%B3%B4%EC%84%B8%EC%9A%94;%EC%97%B4%EC%A0%95%EC%9C%BC%EB%A1%9C+%EB%A7%8C%EB%93%A4%EC%96%B4%EC%A1%8C%EC%8A%B5%EB%8B%88%EB%8B%A4.&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

이 프로젝트는 뒤에 있는 사람들이 없었다면 존재하지 않았을 것입니다.

### 활동적인 유지관리자

**[Pylar](https://github.com/deafdudecomputers)** — 모든 것을 시작한 사람. 이 도구의 모든 라인은 저장 엔진, GUI 및 매일 사용하는 기능에 대한 그의 비전과 끊임없는 작업으로 거슬러 올라갑니다.

**[cyrix](https://github.com/CyrixJD115)** — 리팩터러 및 하위 유지관리자. 코드 품질, 단순화 및 구조적 개선에 중점을 두고 프로젝트가 성장함에 따라 코드베이스를 깔끔하고 작게 유지하고 유지 관리하기 쉽게 만듭니다.

### 기여자

**[dkoz](https://github.com/dkoz)** — ID 뒤에 있는 남자. 게임 데이터 ID, ID 코드에 대한 구조적 통찰력, 모든 게임 업데이트에서 도구의 정확성을 유지하는 Palworld의 데이터 연결 방식에 대한 깊은 지식을 제공합니다.

**[oMaN-Rod](https://github.com/oMaN-Rod)** — 이 프로젝트가 분기된 원본 저장 파서를 제공했습니다. Palworld 저장 형식을 해독하는 그의 기초적인 작업이 없었다면 이 중 어떤 것도 존재하지 않았을 것입니다. 포크는 파서를 오늘날의 PST로 간소화하고 단순화했습니다.
**[Okaetsu](https://github.com/Okaetsu)** — 기본 가져오기/내보내기를 가능하게 하는 모딩 통찰력. Palworld가 모딩 측면에서 기본 데이터를 구성하는 방법에 대한 그의 이해는 모딩과 저장 편집 사이의 격차를 해소하여 이 기능을 현실화했습니다.





---




<div align="center">

## 감사의 말씀

<img src="https://readme-typing-svg.demolab.com?lines=%EC%8B%A0%EC%9A%A9%EC%9D%B4+%ED%95%84%EC%9A%94%ED%95%9C+%EA%B3%B3;%EB%AA%A8%EB%91%90+%EA%B0%90%EC%82%AC%ED%95%A9%EB%8B%88%EB%8B%A4;%EC%9A%B0%EB%A6%AC%EB%8A%94+%EC%96%B4%EA%B9%A8+%EC%9C%84%EC%97%90+%EC%84%9C+%EC%9E%88%EB%8B%A4&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

다음 분들께 큰 감사를 드립니다:

- **Palworld**는 Pocketpair, Inc.에서 개발했습니다. — 우리 모두를 하나로 모으는 게임을 위해.
- **버그 보고자** — 제출된 모든 문제, 발견된 모든 극단적인 사례, Discord에 붙여넣은 모든 로그. 각 보고서를 통해 이 도구를 더욱 강력하게 만들 수 있습니다.
- **Palworld 모딩 커뮤니티** — 지식, 리버스 엔지니어링 형식을 공유하고 생태계를 발전시키는 동료 모더, 도구 개발자 및 땜장이입니다. 이 프로젝트는 그러한 공동 노력의 어깨 위에 서 있습니다.
- **모든 기여자와 커뮤니티 구성원** — PR을 제출했든, Discord의 질문에 답변했든, 아니면 단순히 친구에게 PST에 대해 이야기했든 — 감사합니다.

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**Palworld 커뮤니티를 위해 ❤️으로 제작**

[⬆ Back to Top](#palworld-save-tools)

</div>