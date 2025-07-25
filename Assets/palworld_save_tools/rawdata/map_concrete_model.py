from typing import Any, Optional, Sequence

from loguru import logger
from palworld_save_tools.archive import (
    FArchiveReader,
    FArchiveWriter,
    uuid_reader,
    uuid_writer,
)
from palworld_save_tools.rawdata.common import (
    pal_item_and_num_read,
    pal_item_and_slot_writer,
    pal_item_booth_trade_info_read,
    pal_item_booth_trade_info_writer,
)


def pal_instance_id_reader(reader: FArchiveReader) -> dict[str, Any]:
    return {
        "player_uid": reader.guid(),
        "instance_id": reader.guid(),
    }


def pal_instance_id_writer(writer: FArchiveWriter, p: dict[str, Any]) -> None:
    writer.guid(p["player_uid"])
    writer.guid(p["instance_id"])


# Generate using extract_map_object_concrete_classes.py
MAP_OBJECT_NAME_TO_CONCRETE_MODEL_CLASS: dict[str, str] = {
    "droppedcharacter": "PalMapObjectDeathDroppedCharacterModel",
    "blastfurnace": "PalMapObjectConvertItemModel",
    "blastfurnace2": "PalMapObjectConvertItemModel",
    "blastfurnace3": "PalMapObjectConvertItemModel",
    "blastfurnace4": "PalMapObjectConvertItemModel",
    "blastfurnace5": "PalMapObjectConvertItemModel",
    "campfire": "PalMapObjectConvertItemModel",
    "characterrankup": "PalMapObjectRankUpCharacterModel",
    "commondropitem3d": "PalMapObjectDropItemModel",
    "commondropitem3d_sk": "PalMapObjectDropItemModel",
    "cookingstove": "PalMapObjectConvertItemModel",
    "damagablerock_pv": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0001": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0002": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0003": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0004": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0005": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0017": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0006": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0007": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0008": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0009": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0010": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0011": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0012": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0013": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0014": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0015": "PalMapObjectItemDropOnDamagModel",
    "damagablerock0016": "PalMapObjectItemDropOnDamagModel",
    "deathpenaltychest": "PalMapObjectDeathPenaltyStorageModel",
    "defensegatlinggun": "PalMapObjectDefenseBulletLauncherModel",
    "defensemachinegun": "PalMapObjectDefenseBulletLauncherModel",
    "defenseminigun": "DEFAULT_UNKNOWN_PalMapObjectConcreteModelBase",
    "defensebowgun": "PalMapObjectDefenseBulletLauncherModel",
    "defensemissile": "PalMapObjectDefenseBulletLauncherModel",
    "defensewait": "PalMapObjectDefenseWaitModel",
    "electricgenerator": "PalMapObjectGenerateEnergyModel",
    "electricgenerator_slave": "PalMapObjectGenerateEnergyModel",
    "electricgenerator2": "PalMapObjectGenerateEnergyModel",
    "electricgenerator3": "PalMapObjectGenerateEnergyModel",
    "electrickitchen": "PalMapObjectConvertItemModel",
    "hugekitchen": "PalMapObjectConvertItemModel",
    "factory_comfortable_01": "PalMapObjectConvertItemModel",
    "factory_comfortable_02": "PalMapObjectConvertItemModel",
    "factory_hard_01": "PalMapObjectConvertItemModel",
    "factory_hard_02": "PalMapObjectConvertItemModel",
    "factory_hard_03": "PalMapObjectConvertItemModel",
    "factory_hard_04": "PalMapObjectConvertItemModel",
    "farmblockv2_grade01": "PalMapObjectFarmBlockV2Model",
    "farmblockv2_grade02": "PalMapObjectFarmBlockV2Model",
    "farmblockv2_grade03": "PalMapObjectFarmBlockV2Model",
    "farmblockv2_wheet": "PalMapObjectFarmBlockV2Model",
    "farmblockv2_tomato": "PalMapObjectFarmBlockV2Model",
    "farmblockv2_lettuce": "PalMapObjectFarmBlockV2Model",
    "farmblockv2_berries": "PalMapObjectFarmBlockV2Model",
    "fasttravelpoint": "PalMapObjectFastTravelPointModel",
    "hightechkitchen": "PalMapObjectConvertItemModel",
    "itemchest": "PalMapObjectItemChestModel",
    "itemchest_02": "PalMapObjectItemChestModel",
    "itemchest_03": "PalMapObjectItemChestModel",
    "dev_itemchest": "PalMapObjectItemChestModel",
    "medicalpalbed": "PalMapObjectMedicalPalBedModel",
    "medicalpalbed_02": "PalMapObjectMedicalPalBedModel",
    "medicalpalbed_03": "PalMapObjectMedicalPalBedModel",
    "medicalpalbed_04": "PalMapObjectMedicalPalBedModel",
    "medicinefacility_01": "PalMapObjectConvertItemModel",
    "medicinefacility_02": "PalMapObjectConvertItemModel",
    "medicinefacility_03": "PalMapObjectConvertItemModel",
    "palfoodbox": "PalMapObjectPalFoodBoxModel",
    "palboxv2": "PalMapObjectBaseCampPoint",
    "displaycharacter": "PalMapObjectDisplayCharacterModel",
    "pickupitem_flint": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_log": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_redberry": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_stone": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_potato": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_poppy": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_nightstone": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_yakushimamushroom_01": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_yakushimamushroom_02": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_yakushimamushroom_03": "PalMapObjectPickupItemOnLevelModel",
    "playerbed": "PalMapObjectPlayerBedModel",
    "playerbed_02": "PalMapObjectPlayerBedModel",
    "playerbed_03": "PalMapObjectPlayerBedModel",
    "shippingitembox": "PalMapObjectShippingItemModel",
    "spherefactory_black_01": "PalMapObjectConvertItemModel",
    "spherefactory_black_02": "PalMapObjectConvertItemModel",
    "spherefactory_black_03": "PalMapObjectConvertItemModel",
    "spherefactory_black_04": "PalMapObjectConvertItemModel",
    "spherefactory_white_01": "PalMapObjectConvertItemModel",
    "spherefactory_white_02": "PalMapObjectConvertItemModel",
    "spherefactory_white_03": "PalMapObjectConvertItemModel",
    "stonehouse1": "PalBuildObject",
    "stonepit": "PalMapObjectProductItemModel",
    "strawhouse1": "PalBuildObject",
    "weaponfactory_clean_01": "PalMapObjectConvertItemModel",
    "weaponfactory_clean_02": "PalMapObjectConvertItemModel",
    "weaponfactory_clean_03": "PalMapObjectConvertItemModel",
    "weaponfactory_dirty_01": "PalMapObjectConvertItemModel",
    "weaponfactory_dirty_02": "PalMapObjectConvertItemModel",
    "weaponfactory_dirty_03": "PalMapObjectConvertItemModel",
    "weaponfactory_dirty_04": "PalMapObjectConvertItemModel",
    "well": "PalMapObjectProductItemModel",
    "woodhouse1": "PalBuildObject",
    "workbench": "PalMapObjectConvertItemModel",
    "recoverotomo": "PalMapObjectRecoverOtomoModel",
    "palegg": "PalMapObjectPalEggModel",
    "palegg_fire": "PalMapObjectPalEggModel",
    "palegg_water": "PalMapObjectPalEggModel",
    "palegg_leaf": "PalMapObjectPalEggModel",
    "palegg_electricity": "PalMapObjectPalEggModel",
    "palegg_ice": "PalMapObjectPalEggModel",
    "palegg_earth": "PalMapObjectPalEggModel",
    "palegg_dark": "PalMapObjectPalEggModel",
    "palegg_dragon": "PalMapObjectPalEggModel",
    "hatchingpalegg": "PalMapObjectHatchingEggModel",
    "treasurebox": "PalMapObjectTreasureBoxModel",
    "treasurebox_visiblecontent": "PalMapObjectPickupItemOnLevelModel",
    "treasurebox_visiblecontent_skillfruits": "PalMapObjectPickupItemOnLevelModel",
    "stationdeforest2": "PalMapObjectProductItemModel",
    "workbench_skillunlock": "PalMapObjectConvertItemModel",
    "workbench_skillcard": "PalMapObjectConvertItemModel",
    "wooden_foundation": "PalBuildObject",
    "wooden_wall": "PalBuildObject",
    "wooden_roof": "PalBuildObject",
    "wooden_stair": "PalBuildObject",
    "wooden_doorwall": "PalMapObjectDoorModel",
    "stone_foundation": "PalBuildObject",
    "stone_wall": "PalBuildObject",
    "stone_roof": "PalBuildObject",
    "stone_stair": "PalBuildObject",
    "stone_doorwall": "PalMapObjectDoorModel",
    "metal_foundation": "PalBuildObject",
    "metal_wall": "PalBuildObject",
    "metal_roof": "PalBuildObject",
    "metal_stair": "PalBuildObject",
    "metal_doorwall": "PalMapObjectDoorModel",
    "buildablegoddessstatue": "PalMapObjectCharacterStatusOperatorModel",
    "spa": "PalMapObjectAmusementModel",
    "spa2": "PalMapObjectAmusementModel",
    "pickupitem_mushroom": "PalMapObjectPickupItemOnLevelModel",
    "defensewall_wood": "PalBuildObject",
    "defensewall": "PalBuildObject",
    "defensewall_metal": "PalBuildObject",
    "heater": "PalMapObjectHeatSourceModel",
    "electricheater": "PalMapObjectHeatSourceModel",
    "cooler": "PalMapObjectHeatSourceModel",
    "electriccooler": "PalMapObjectHeatSourceModel",
    "torch": "PalMapObjectTorchModel",
    "walltorch": "PalMapObjectTorchModel",
    "lamp": "PalMapObjectLampModel",
    "ceilinglamp": "PalMapObjectLampModel",
    "largelamp": "PalMapObjectLampModel",
    "largeceilinglamp": "PalMapObjectLampModel",
    "crusher": "PalMapObjectConvertItemModel",
    "woodcrusher": "PalMapObjectConvertItemModel",
    "flourmill": "PalMapObjectConvertItemModel",
    "trap_leghold": "DEFAULT_UNKNOWN_PalMapObjectConcreteModelBase",
    "trap_leghold_big": "DEFAULT_UNKNOWN_PalMapObjectConcreteModelBase",
    "trap_noose": "DEFAULT_UNKNOWN_PalMapObjectConcreteModelBase",
    "trap_movingpanel": "DEFAULT_UNKNOWN_PalMapObjectConcreteModelBase",
    "trap_mineelecshock": "DEFAULT_UNKNOWN_PalMapObjectConcreteModelBase",
    "trap_minefreeze": "DEFAULT_UNKNOWN_PalMapObjectConcreteModelBase",
    "trap_mineattack": "DEFAULT_UNKNOWN_PalMapObjectConcreteModelBase",
    "breedfarm": "PalMapObjectBreedFarmModel",
    "wood_gate": "PalMapObjectDoorModel",
    "stone_gate": "PalMapObjectDoorModel",
    "metal_gate": "PalMapObjectDoorModel",
    "repairbench": "PalMapObjectRepairItemModel",
    "skillfruit_test": "PalMapObjectPickupItemOnLevelModel",
    "toolboxv1": "PalMapObjectBaseCampPassiveEffectModel",
    "toolboxv2": "PalMapObjectBaseCampPassiveEffectModel",
    "fountain": "PalMapObjectBaseCampPassiveEffectModel",
    "silo": "PalMapObjectBaseCampPassiveEffectModel",
    "transmissiontower": "PalMapObjectBaseCampPassiveEffectModel",
    "flowerbed": "PalMapObjectBaseCampPassiveEffectModel",
    "stump": "PalMapObjectBaseCampPassiveEffectModel",
    "miningtool": "PalMapObjectBaseCampPassiveEffectModel",
    "cauldron": "PalMapObjectBaseCampPassiveEffectModel",
    "snowman": "PalMapObjectBaseCampPassiveEffectModel",
    "olympiccauldron": "PalMapObjectBaseCampPassiveEffectModel",
    "basecampworkhard": "PalMapObjectBaseCampPassiveWorkHardModel",
    "coolerbox": "PalMapObjectItemChest_AffectCorruption",
    "refrigerator": "PalMapObjectItemChest_AffectCorruption",
    "damagedscarecrow": "PalMapObjectDamagedScarecrowModel",
    "signboard": "PalMapObjectSignboardModel",
    "basecampbattledirector": "PalMapObjectBaseCampWorkerDirectorModel",
    "monsterfarm": "PalMapObjectMonsterFarmModel",
    "wood_windowwall": "PalBuildObject",
    "stone_windowwall": "PalBuildObject",
    "metal_windowwall": "PalBuildObject",
    "wood_trianglewall": "PalBuildObject",
    "stone_trianglewall": "PalBuildObject",
    "metal_trianglewall": "PalBuildObject",
    "wood_slantedroof": "PalBuildObject",
    "stone_slantedroof": "PalBuildObject",
    "metal_slantedroof": "PalBuildObject",
    "table1": "PalBuildObject",
    "barrel_wood": "PalMapObjectItemChestModel",
    "box_wood": "PalMapObjectItemChestModel",
    "box01_iron": "PalMapObjectItemChestModel",
    "box02_iron": "PalMapObjectItemChestModel",
    "shelf_wood": "PalMapObjectItemChestModel",
    "shelf_cask_wood": "PalMapObjectItemChestModel",
    "shelf_hang01_wood": "PalMapObjectItemChestModel",
    "shelf01_iron": "PalMapObjectItemChestModel",
    "shelf02_iron": "PalMapObjectItemChestModel",
    "shelf03_iron": "PalMapObjectItemChestModel",
    "shelf04_iron": "PalMapObjectItemChestModel",
    "shelf05_stone": "PalMapObjectItemChestModel",
    "shelf06_stone": "PalMapObjectItemChestModel",
    "shelf07_stone": "PalMapObjectItemChestModel",
    "shelf01_wall_stone": "PalMapObjectItemChestModel",
    "shelf01_wall_iron": "PalMapObjectItemChestModel",
    "shelf01_stone": "PalMapObjectItemChestModel",
    "shelf02_stone": "PalMapObjectItemChestModel",
    "shelf03_stone": "PalMapObjectItemChestModel",
    "shelf04_stone": "PalMapObjectItemChestModel",
    "container01_iron": "PalMapObjectItemChestModel",
    "tablesquare_wood": "PalBuildObject",
    "tablecircular_wood": "PalBuildObject",
    "bench_wood": "PalMapObjectPlayerSitModel",
    "stool_wood": "PalMapObjectPlayerSitModel",
    "decal_palsticker_pinkcat": "PalBuildObject",
    "stool_high_wood": "PalMapObjectPlayerSitModel",
    "counter_wood": "PalBuildObject",
    "rug_wood": "PalBuildObject",
    "shelf_hang02_wood": "PalBuildObject",
    "ivy01": "PalBuildObject",
    "ivy02": "PalBuildObject",
    "ivy03": "PalBuildObject",
    "chair01_wood": "PalMapObjectPlayerSitModel",
    "box01_stone": "PalBuildObject",
    "barrel01_iron": "PalBuildObject",
    "barrel02_iron": "PalBuildObject",
    "barrel03_iron": "PalBuildObject",
    "cablecoil01_iron": "PalBuildObject",
    "chair01_iron": "PalMapObjectPlayerSitModel",
    "chair02_iron": "PalMapObjectPlayerSitModel",
    "clock01_wall_iron": "PalBuildObject",
    "garbagebag_iron": "PalBuildObject",
    "goalsoccer_iron": "PalBuildObject",
    "machinegame01_iron": "PalBuildObject",
    "machinevending01_iron": "PalBuildObject",
    "pipeclay01_iron": "PalBuildObject",
    "signexit_ceiling_iron": "PalBuildObject",
    "signexit_wall_iron": "PalBuildObject",
    "sofa01_iron": "PalMapObjectPlayerSitModel",
    "sofa02_iron": "PalMapObjectPlayerSitModel",
    "stool01_iron": "PalMapObjectPlayerSitModel",
    "tablecircular01_iron": "PalBuildObject",
    "tableside01_iron": "PalBuildObject",
    "tablesquare01_iron": "PalBuildObject",
    "tablesquare02_iron": "PalBuildObject",
    "tire01_iron": "PalBuildObject",
    "trafficbarricade01_iron": "PalBuildObject",
    "trafficbarricade02_iron": "PalBuildObject",
    "trafficbarricade03_iron": "PalBuildObject",
    "trafficbarricade04_iron": "PalBuildObject",
    "trafficbarricade05_iron": "PalBuildObject",
    "trafficcone01_iron": "PalBuildObject",
    "trafficcone02_iron": "PalBuildObject",
    "trafficcone03_iron": "PalBuildObject",
    "trafficlight01_iron": "PalBuildObject",
    "bathtub_stone": "PalBuildObject",
    "chair01_stone": "PalMapObjectPlayerSitModel",
    "chair02_stone": "PalMapObjectPlayerSitModel",
    "clock01_stone": "PalBuildObject",
    "curtain01_wall_stone": "PalBuildObject",
    "desk01_stone": "PalBuildObject",
    "globe01_stone": "PalBuildObject",
    "mirror01_stone": "PalBuildObject",
    "mirror02_stone": "PalBuildObject",
    "mirror01_wall_stone": "PalBuildObject",
    "partition_stone": "PalBuildObject",
    "piano01_stone": "PalBuildObject",
    "piano02_stone": "PalBuildObject",
    "rug01_stone": "PalBuildObject",
    "rug02_stone": "PalBuildObject",
    "rug03_stone": "PalBuildObject",
    "rug04_stone": "PalBuildObject",
    "sofa01_stone": "PalMapObjectPlayerSitModel",
    "sofa02_stone": "PalMapObjectPlayerSitModel",
    "sofa03_stone": "PalBuildObject",
    "stool01_stone": "PalMapObjectPlayerSitModel",
    "stove01_stone": "PalBuildObject",
    "tablecircular01_stone": "PalBuildObject",
    "tabledresser01_stone": "PalMapObjectCharacterMakeModel",
    "tablesink01_stone": "PalBuildObject",
    "toilet01_stone": "PalMapObjectPlayerSitModel",
    "toiletholder01_stone": "PalBuildObject",
    "towlrack01_stone": "PalBuildObject",
    "plant01_plant": "PalBuildObject",
    "plant02_plant": "PalBuildObject",
    "plant03_plant": "PalBuildObject",
    "plant04_plant": "PalBuildObject",
    "light_floorlamp01": "PalMapObjectLampModel",
    "light_floorlamp02": "PalMapObjectLampModel",
    "light_lightpole01": "PalMapObjectLampModel",
    "light_lightpole02": "PalMapObjectLampModel",
    "light_lightpole03": "PalMapObjectLampModel",
    "light_lightpole04": "PalMapObjectLampModel",
    "light_fireplace01": "PalMapObjectTorchModel",
    "light_fireplace02": "PalMapObjectTorchModel",
    "light_candlesticks_top": "PalMapObjectLampModel",
    "light_candlesticks_wall": "PalMapObjectLampModel",
    "television01_iron": "PalBuildObject",
    "desk01_iron": "PalBuildObject",
    "trafficsign01_iron": "PalBuildObject",
    "trafficsign02_iron": "PalBuildObject",
    "trafficsign03_iron": "PalBuildObject",
    "trafficsign04_iron": "PalBuildObject",
    "chair01_pal": "PalMapObjectPlayerSitModel",
    "altar": "PalBuildObjectRaidBossSummon",
    "copperpit": "PalMapObjectProductItemModel",
    "copperpit_2": "PalMapObjectProductItemModel",
    "electrichatchingpalegg": "PalMapObjectHatchingEggModel",
    "pickupitem_cavemushroom": "PalMapObjectPickupItemOnLevelModel",
    "coolerpalfoodbox": "PalMapObjectPalFoodBoxModel",
    "treasurebox_oilrig": "PalMapObjectTreasureBoxModel",
    "sulfurpit": "PalMapObjectProductItemModel",
    "coalpit": "PalMapObjectProductItemModel",
    "icecrusher": "PalMapObjectConvertItemModel",
    "dismantlingconveyor": "PalBuildObjectConvertCharacterToItem",
    "wallsignboard": "PalMapObjectSignboardModel",
    "treasurebox_electric": "PalMapObjectTreasureBoxModel",
    "treasurebox_fire": "PalMapObjectTreasureBoxModel",
    "treasurebox_water": "PalMapObjectTreasureBoxModel",
    "glass_foundation": "PalBuildObject",
    "glass_wall": "PalBuildObject",
    "glass_roof": "PalBuildObject",
    "glass_stair": "PalBuildObject",
    "glass_doorwall": "PalMapObjectDoorModel",
    "glass_trianglewall": "PalBuildObject",
    "glass_slantedroof": "PalBuildObject",
    "glass_windowwall": "PalBuildObject",
    "wooden_pillar": "PalBuildObject",
    "stone_pillar": "PalBuildObject",
    "metal_pillars": "PalBuildObject",
    "glass_pillars": "PalBuildObject",
    "meteordrop_pickup": "PalMapObjectPickupItemOnLevelModel",
    "supplydrop": "PalMapObjectSupplyStorageModel",
    "meteordrop_damagable": "PalMapObjectItemDropOnDamagModel",
    "electricgenerator_large": "PalMapObjectGenerateEnergyModel",
    "treasurebox_requiredlonghold": "PalMapObjectTreasureBoxModel",
    "oilpump": "PalMapObjectProductItemModel",
    "pickupitem_lotus_attack_01": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_lotus_attack_02": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_lotus_hp_01": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_lotus_hp_02": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_lotus_stamina_01": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_lotus_stamina_02": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_lotus_workspeed_01": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_lotus_workspeed_02": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_lotus_weight_01": "PalMapObjectPickupItemOnLevelModel",
    "pickupitem_lotus_weight_02": "PalMapObjectPickupItemOnLevelModel",
    "skinchange": "PalMapObjectSkinChangeModel",
    "pickupitem_dogcoin": "PalMapObjectPickupItemOnLevelModel",
    "japanesestyle_wall_01": "PalBuildObject",
    "japanesestyle_doorwall_01": "PalMapObjectDoorModel",
    "japanesestyle_doorwall_02": "PalMapObjectDoorModel",
    "japanesestyle_roof_01": "PalBuildObject",
    "japanesestyle_roof_02": "PalBuildObject",
    "japanesestyle_slantedroof": "PalBuildObject",
    "japanesestyle_trianglewall": "PalBuildObject",
    "japanesestyle_windowwall": "PalBuildObject",
    "japanesestyle_foundation": "PalBuildObject",
    "japanesestyle_stair": "PalBuildObject",
    "japanesestyle_pillar": "PalBuildObject",
    "sanitydecrease1": "PalMapObjectBaseCampPassiveEffectModel",
    "workspeedincrease1": "PalMapObjectBaseCampPassiveEffectModel",
    "quartzpit": "PalMapObjectProductItemModel",
    "factory_money": "PalMapObjectConvertItemModel",
    "itemchest_04": "PalMapObjectItemChestModel",
    "medicalpalbed_05": "PalMapObjectMedicalPalBedModel",
    "farmblockv2_carrot": "PalMapObjectFarmBlockV2Model",
    "farmblockv2_onion": "PalMapObjectFarmBlockV2Model",
    "farmblockv2_potato": "PalMapObjectFarmBlockV2Model",
    "basecampitemdispenser": "PalMapObjectBaseCampItemDispenserModel",
    "guildchest": "PalMapObjectGuildChestModel",
    "woodcreator": "PalMapObjectProductItemModel",
    "expedition": "PalMapObjectCharacterTeamMissionModel",
    "itembooth": "PalMapObjectItemBoothModel",
    "lab": "PalMapObjectLabModel",
    "palbooth": "PalMapObjectPalBoothModel",
    "multielectrichatchingpalegg": "PalMapObjectMultiHatchingEggModel",
    "operatingtable": "PalMapObjectOperatingTableModel",
    "manualelectricgenerator": "PalMapObjectGenerateEnergyModel",
    "farm_skillfruits": "PalMapObjectFarmSkillFruitsModel",
    "wooden_ladder": "PalBuildObject",
    "palmedicinebox": "PalMapObjectPalMedicineBoxModel",
    "energystorage_electric": "PalMapObjectEnergyStorageModel",
    "damagablerock0018": "PalMapObjectItemDropOnDamagModel",
    "headstone": "PalMapObjectSignboardModel",
    "japanesestyle_doorwall_03": "PalMapObjectDoorModel",
    "damagablerock0019": "PalMapObjectItemDropOnDamagModel",
    "byobu": "PalBuildObject",
    "kakejiku": "PalBuildObject",
    "zaisu": "PalMapObjectPlayerSitModel",
    "zabuton": "PalMapObjectPlayerSitModel",
    "irori": "PalBuildObject",
    "toro": "PalBuildObject",
    "andon": "PalBuildObject",
    "shishiodoshi": "PalBuildObject",
    "bonsai": "PalBuildObject",
    "koro": "PalBuildObject",
    "seika": "PalBuildObject",
    "tansu": "PalMapObjectItemChestModel",
    "fudukue": "PalBuildObject",
    "compositedesk": "PalMapObjectConvertItemModel",
    "globalpalstorage": "PalMapObjectGlobalPalStorageModel",
    "dimensionpalstorage": "PalMapObjectDimensionPalStorageModel",
    "wire_fence": "PalBuildObject",
    "sf_foundation": "PalBuildObject",
    "sf_wall": "PalBuildObject",
    "sf_roof": "PalBuildObject",
    "sf_stair": "PalBuildObject",
    "sf_doorwall": "PalMapObjectDoorModel",
    "sf_trianglewall": "PalBuildObject",
    "sf_slantedroof": "PalBuildObject",
    "sf_windowwall": "PalBuildObject",
    "sf_pillars": "PalBuildObject",
    "lilyqueenstatue": "PalBuildObject",
    "conservationgroupbannera": "PalBuildObject",
    "conservationgroupbannerb": "PalBuildObject",
    "banyan_big": "PalBuildObject",
    "hunter_gangflag": "PalBuildObject",
    "palcage": "PalBuildObject",
    "treasurebox_enemycampgoal": "PalMapObjectTreasureBoxModel",
    "treasurebox_enemycamp": "PalMapObjectTreasureBoxModel",
    "woodenbarricade": "PalBuildObject",
    "walltorch02": "PalMapObjectTorchModel",
    "candlestand": "PalMapObjectTorchModel",
    "firestand": "PalMapObjectTorchModel",
    "wood_fence": "PalBuildObject",
    "stone_fence": "PalBuildObject",
    "iron_fence": "PalBuildObject",
    "glass_fence": "PalBuildObject",
    "japanesestyle_fence": "PalBuildObject",
    "sf_fence": "PalBuildObject",
    "destroyablewall_rock01": "PalMapObjectItemDropOnDamagModel",
    "destroyablewall_rock02": "PalMapObjectItemDropOnDamagModel",
    "pickupitem_affectionfruit": "PalMapObjectPickupItemOnLevelModel",
    "crystalpit": "PalMapObjectProductItemModel",
    "spa3": "PalMapObjectAmusementModel",
    "multihatchingpalegg": "PalMapObjectMultiHatchingEggModel",
    "treasurebox_fishingjunk_requiredlonghold": "PalMapObjectTreasureBoxModel",
    "treasurebox_fishingjunk_requiredlonghold2": "PalMapObjectTreasureBoxModel",
    "fishingpond1": "PalMapObjectFishPondModel",
    "fishingpond2": "PalMapObjectFishPondModel",
    "basecampworkerextrastation": "PalMapObjectBaseCampWorkerExtraStationModel",
    "sf_desk": "PalBuildObject",
    "sf_chair": "PalMapObjectPlayerSitModel",
    "damagabletree_yakushima001": "PalMapObjectItemDropOnDamagModel",
    "damagabletree_yakushima002": "PalMapObjectItemDropOnDamagModel",
    "damagabletree_yakushima003": "PalMapObjectItemDropOnDamagModel",
    "lanterntop": "PalMapObjectLampModel",
    "shrine_lantern": "PalMapObjectLampModel",
    "guardiandogstatue": "PalBuildObject",
    "yakushima_crystal": "PalMapObjectItemDropOnDamagModel",
    "yakushima_pot": "PalMapObjectItemDropOnDamagModel",
    "hunter_flag": "PalBuildObject",
    "hunter_banner": "PalBuildObject",
    "believer_flag": "PalBuildObject",
    "believer_banner": "PalBuildObject",
    "firecult_flag": "PalBuildObject",
    "firecult_banner": "PalBuildObject",
    "police_flag": "PalBuildObject",
    "police_banner": "PalBuildObject",
    "scientist_flag": "PalBuildObject",
    "scientist_banner": "PalBuildObject",
    "ninja_flag": "PalBuildObject",
    "ninja_banner": "PalBuildObject",
    "treasurebox_yakushima": "PalMapObjectTreasureBoxModel",
    "yakushima_healheart": "PalMapObjectInstantEffectModel",
    "enemycamp_wooden_foundation": "PalBuildObject",
    "enemycamp_wooden_wall": "PalBuildObject",
    "enemycamp_wood_windowwall": "PalBuildObject",
    "enemycamp_wood_trianglewall": "PalBuildObject",
    "enemycamp_wooden_roof": "PalBuildObject",
    "enemycamp_wood_slantedroof": "PalBuildObject",
    "enemycamp_wooden_stair": "PalBuildObject",
    "enemycamp_wooden_doorwall": "PalMapObjectDoorModel",
    "enemycamp_wooden_pillar": "PalBuildObject",
    "enemycamp_defensewall_wood": "PalBuildObject",
    "enemycamp_wood_gate": "PalMapObjectDoorModel",
    "enemycamp_wooden_ladder": "PalBuildObject",
    "enemycamp_stone_foundation": "PalBuildObject",
    "enemycamp_stone_wall": "PalBuildObject",
    "enemycamp_stone_windowwall": "PalBuildObject",
    "enemycamp_stone_trianglewall": "PalBuildObject",
    "enemycamp_stone_roof": "PalBuildObject",
    "enemycamp_stone_slantedroof": "PalBuildObject",
    "enemycamp_stone_stair": "PalBuildObject",
    "enemycamp_stone_doorwall": "PalMapObjectDoorModel",
    "enemycamp_stone_pillar": "PalBuildObject",
    "enemycamp_defensewall": "PalBuildObject",
    "enemycamp_stone_gate": "PalMapObjectDoorModel",
    "enemycamp_metal_foundation": "PalBuildObject",
    "enemycamp_metal_wall": "PalBuildObject",
    "enemycamp_metal_windowwall": "PalBuildObject",
    "enemycamp_metal_trianglewall": "PalBuildObject",
    "enemycamp_metal_roof": "PalBuildObject",
    "enemycamp_metal_slantedroof": "PalBuildObject",
    "enemycamp_metal_stair": "PalBuildObject",
    "enemycamp_metal_doorwall": "PalMapObjectDoorModel",
    "enemycamp_metal_pillars": "PalBuildObject",
    "enemycamp_defensewall_metal": "PalBuildObject",
    "enemycamp_metal_gate": "PalMapObjectDoorModel",
    "enemycamp_glass_foundation": "PalBuildObject",
    "enemycamp_glass_wall": "PalBuildObject",
    "enemycamp_glass_windowwall": "PalBuildObject",
    "enemycamp_glass_trianglewall": "PalBuildObject",
    "enemycamp_glass_roof": "PalBuildObject",
    "enemycamp_glass_slantedroof": "PalBuildObject",
    "enemycamp_glass_stair": "PalBuildObject",
    "enemycamp_glass_doorwall": "PalMapObjectDoorModel",
    "enemycamp_glass_pillars": "PalBuildObject",
    "enemycamp_japanesestyle_foundation": "PalBuildObject",
    "enemycamp_japanesestyle_wall_01": "PalBuildObject",
    "enemycamp_japanesestyle_windowwall": "PalBuildObject",
    "enemycamp_japanesestyle_trianglewall": "PalBuildObject",
    "enemycamp_japanesestyle_roof_01": "PalBuildObject",
    "enemycamp_japanesestyle_roof_02": "PalBuildObject",
    "enemycamp_japanesestyle_slantedroof": "PalBuildObject",
    "enemycamp_japanesestyle_stair": "PalBuildObject",
    "enemycamp_japanesestyle_doorwall_01": "PalMapObjectDoorModel",
    "enemycamp_japanesestyle_doorwall_02": "PalMapObjectDoorModel",
    "enemycamp_japanesestyle_doorwall_03": "PalMapObjectDoorModel",
    "enemycamp_japanesestyle_pillar": "PalBuildObject",
    "enemycamp_wooden_wall_destructable": "PalBuildObject",
    "enemycamp_stone_wall_destructable": "PalBuildObject",
    "enemycamp_metal_wall_destructable": "PalBuildObject",
    "enemycamp_glass_wall_destructable": "PalBuildObject",
    "enemycamp_japanesestyle_wall_01_destructable": "PalBuildObject",
    "enemycamp_sf_wall_destructable": "PalBuildObject",
    "enemycamp_workbench": "PalBuildObject",
    "enemycamp_repairbench": "PalBuildObject",
    "enemycamp_workbench_skillunlock": "PalBuildObject",
    "enemycamp_blastfurnace": "PalBuildObject",
    "enemycamp_factory_hard_01": "PalBuildObject",
    "enemycamp_medicinefacility_01": "PalBuildObject",
    "enemycamp_weaponfactory_dirty_01": "PalBuildObject",
    "enemycamp_weaponfactory_dirty_02": "PalBuildObject",
    "enemycamp_blastfurnace2": "PalBuildObject",
    "enemycamp_medicinefacility_02": "PalBuildObject",
    "enemycamp_blastfurnace3": "PalBuildObject",
    "enemycamp_oilpump": "PalBuildObject",
    "enemycamp_blastfurnace4": "PalBuildObject",
    "enemycamp_medicinefacility_03": "PalBuildObject",
    "enemycamp_buildablegoddessstatue": "PalBuildObject",
    "enemycamp_spherefactory_black_01": "PalBuildObject",
    "enemycamp_characterrankup": "PalBuildObject",
    "enemycamp_lab": "PalBuildObject",
    "enemycamp_hatchingpalegg": "PalBuildObject",
    "enemycamp_electrichatchingpalegg": "PalBuildObject",
    "enemycamp_dismantlingconveyor": "PalBuildObject",
    "enemycamp_multielectrichatchingpalegg": "PalBuildObject",
    "enemycamp_spherefactory_black_04": "PalBuildObject",
    "enemycamp_itemchest": "PalBuildObject",
    "enemycamp_coolerbox": "PalBuildObject",
    "enemycamp_itemchest_02": "PalBuildObject",
    "enemycamp_refrigerator": "PalBuildObject",
    "enemycamp_itemchest_03": "PalBuildObject",
    "enemycamp_barrel_wood": "PalBuildObject",
    "enemycamp_box_wood": "PalBuildObject",
    "enemycamp_shelf_wood": "PalBuildObject",
    "enemycamp_shelf_cask_wood": "PalBuildObject",
    "enemycamp_shelf_hang01_wood": "PalBuildObject",
    "enemycamp_shelf01_stone": "PalBuildObject",
    "enemycamp_shelf02_stone": "PalBuildObject",
    "enemycamp_shelf03_stone": "PalBuildObject",
    "enemycamp_shelf04_stone": "PalBuildObject",
    "enemycamp_shelf01_wall_iron": "PalBuildObject",
    "enemycamp_shelf05_stone": "PalBuildObject",
    "enemycamp_shelf06_stone": "PalBuildObject",
    "enemycamp_shelf07_stone": "PalBuildObject",
    "enemycamp_shelf01_wall_stone": "PalBuildObject",
    "enemycamp_shelf01_iron": "PalBuildObject",
    "enemycamp_shelf02_iron": "PalBuildObject",
    "enemycamp_shelf03_iron": "PalBuildObject",
    "enemycamp_shelf04_iron": "PalBuildObject",
    "enemycamp_container01_iron": "PalBuildObject",
    "enemycamp_box01_iron": "PalBuildObject",
    "enemycamp_box02_iron": "PalBuildObject",
    "enemycamp_basecampitemdispenser": "PalBuildObject",
    "enemycamp_itemchest_04": "PalBuildObject",
    "enemycamp_tansu": "PalBuildObject",
    "enemycamp_campfire": "PalBuildObject",
    "enemycamp_palfoodbox": "PalBuildObject",
    "enemycamp_cookingstove": "PalBuildObject",
    "enemycamp_electrickitchen": "PalBuildObject",
    "enemycamp_farmblockv2_wheet": "PalBuildObject",
    "enemycamp_hugekitchen": "PalBuildObject",
    "enemycamp_playerbed_02": "PalBuildObject",
    "enemycamp_medicalpalbed_02": "PalBuildObject",
    "enemycamp_spa": "PalBuildObject",
    "enemycamp_manualelectricgenerator": "PalBuildObject",
    "enemycamp_heater": "PalBuildObject",
    "enemycamp_cooler": "PalBuildObject",
    "enemycamp_palmedicinebox": "PalBuildObject",
    "enemycamp_medicalpalbed_03": "PalBuildObject",
    "enemycamp_electricgenerator": "PalBuildObject",
    "enemycamp_playerbed_03": "PalBuildObject",
    "enemycamp_energystorage_electric": "PalBuildObject",
    "enemycamp_sanitydecrease1": "PalBuildObject",
    "enemycamp_electricheater": "PalBuildObject",
    "enemycamp_electriccooler": "PalBuildObject",
    "enemycamp_workspeedincrease1": "PalBuildObject",
    "enemycamp_electricgenerator_large": "PalBuildObject",
    "enemycamp_medicalpalbed_05": "PalBuildObject",
    "enemycamp_torch": "PalBuildObject",
    "enemycamp_walltorch": "PalBuildObject",
    "enemycamp_lamp": "PalBuildObject",
    "enemycamp_ceilinglamp": "PalBuildObject",
    "enemycamp_largelamp": "PalBuildObject",
    "enemycamp_largeceilinglamp": "PalBuildObject",
    "enemycamp_light_fireplace01": "PalBuildObject",
    "enemycamp_light_fireplace02": "PalBuildObject",
    "enemycamp_light_lightpole01": "PalBuildObject",
    "enemycamp_light_lightpole02": "PalBuildObject",
    "enemycamp_light_lightpole03": "PalBuildObject",
    "enemycamp_light_lightpole04": "PalBuildObject",
    "enemycamp_light_floorlamp01": "PalBuildObject",
    "enemycamp_light_floorlamp02": "PalBuildObject",
    "enemycamp_light_candlesticks_top": "PalBuildObject",
    "enemycamp_light_candlesticks_wall": "PalBuildObject",
    "enemycamp_basecampbattledirector": "PalMapObjectBaseCampWorkerDirectorModel",
    "enemycamp_trap_noose": "PalBuildObject",
    "enemycamp_defensewait": "PalBuildObject",
    "enemycamp_defensebowgun": "PalBuildObject",
    "enemycamp_defensemachinegun": "PalBuildObject",
    "enemycamp_defensemissile": "PalBuildObject",
    "enemycamp_damagedscarecrow": "PalBuildObject",
    "enemycamp_headstone": "PalBuildObject",
    "enemycamp_fountain": "PalBuildObject",
    "enemycamp_flowerbed": "PalBuildObject",
    "enemycamp_silo": "PalBuildObject",
    "enemycamp_stump": "PalBuildObject",
    "enemycamp_cauldron": "PalBuildObject",
    "enemycamp_tablesquare_wood": "PalBuildObject",
    "enemycamp_tablecircular_wood": "PalBuildObject",
    "enemycamp_bench_wood": "PalBuildObject",
    "enemycamp_stool_wood": "PalBuildObject",
    "enemycamp_stool_high_wood": "PalBuildObject",
    "enemycamp_chair01_wood": "PalBuildObject",
    "enemycamp_shelf_hang02_wood": "PalBuildObject",
    "enemycamp_counter_wood": "PalBuildObject",
    "enemycamp_plant01_plant": "PalBuildObject",
    "enemycamp_plant02_plant": "PalBuildObject",
    "enemycamp_plant03_plant": "PalBuildObject",
    "enemycamp_plant04_plant": "PalBuildObject",
    "enemycamp_ivy01": "PalBuildObject",
    "enemycamp_ivy02": "PalBuildObject",
    "enemycamp_ivy03": "PalBuildObject",
    "enemycamp_rug01_stone": "PalBuildObject",
    "enemycamp_rug02_stone": "PalBuildObject",
    "enemycamp_rug03_stone": "PalBuildObject",
    "enemycamp_rug04_stone": "PalBuildObject",
    "enemycamp_chair01_stone": "PalBuildObject",
    "enemycamp_chair02_stone": "PalBuildObject",
    "enemycamp_stool01_stone": "PalBuildObject",
    "enemycamp_desk01_stone": "PalBuildObject",
    "enemycamp_tablecircular01_stone": "PalBuildObject",
    "enemycamp_tabledresser01_stone": "PalBuildObject",
    "enemycamp_sofa01_stone": "PalBuildObject",
    "enemycamp_sofa02_stone": "PalBuildObject",
    "enemycamp_sofa03_stone": "PalBuildObject",
    "enemycamp_bathtub_stone": "PalBuildObject",
    "enemycamp_box01_stone": "PalBuildObject",
    "enemycamp_partition_stone": "PalBuildObject",
    "enemycamp_towlrack01_stone": "PalBuildObject",
    "enemycamp_mirror01_stone": "PalBuildObject",
    "enemycamp_mirror02_stone": "PalBuildObject",
    "enemycamp_mirror01_wall_stone": "PalBuildObject",
    "enemycamp_piano01_stone": "PalBuildObject",
    "enemycamp_piano02_stone": "PalBuildObject",
    "enemycamp_tablesink01_stone": "PalBuildObject",
    "enemycamp_toilet01_stone": "PalBuildObject",
    "enemycamp_toiletholder01_stone": "PalBuildObject",
    "enemycamp_curtain01_wall_stone": "PalBuildObject",
    "enemycamp_globe01_stone": "PalBuildObject",
    "enemycamp_stove01_stone": "PalBuildObject",
    "enemycamp_clock01_wall_iron": "PalBuildObject",
    "enemycamp_clock01_stone": "PalBuildObject",
    "enemycamp_chair02_iron": "PalBuildObject",
    "enemycamp_stool01_iron": "PalBuildObject",
    "enemycamp_tablecircular01_iron": "PalBuildObject",
    "enemycamp_desk01_iron": "PalBuildObject",
    "enemycamp_tableside01_iron": "PalBuildObject",
    "enemycamp_tablesquare01_iron": "PalBuildObject",
    "enemycamp_tablesquare02_iron": "PalBuildObject",
    "enemycamp_cablecoil01_iron": "PalBuildObject",
    "enemycamp_garbagebag_iron": "PalBuildObject",
    "enemycamp_pipeclay01_iron": "PalBuildObject",
    "enemycamp_tire01_iron": "PalBuildObject",
    "enemycamp_barrel01_iron": "PalBuildObject",
    "enemycamp_barrel02_iron": "PalBuildObject",
    "enemycamp_barrel03_iron": "PalBuildObject",
    "enemycamp_chair01_iron": "PalBuildObject",
    "enemycamp_sofa01_iron": "PalBuildObject",
    "enemycamp_sofa02_iron": "PalBuildObject",
    "enemycamp_chair01_pal": "PalBuildObject",
    "enemycamp_machinegame01_iron": "PalBuildObject",
    "enemycamp_machinevending01_iron": "PalBuildObject",
    "enemycamp_television01_iron": "PalBuildObject",
    "enemycamp_signexit_ceiling_iron": "PalBuildObject",
    "enemycamp_signexit_wall_iron": "PalBuildObject",
    "enemycamp_trafficcone01_iron": "PalBuildObject",
    "enemycamp_trafficcone02_iron": "PalBuildObject",
    "enemycamp_trafficcone03_iron": "PalBuildObject",
    "enemycamp_trafficsign01_iron": "PalBuildObject",
    "enemycamp_trafficsign02_iron": "PalBuildObject",
    "enemycamp_trafficbarricade01_iron": "PalBuildObject",
    "enemycamp_trafficbarricade02_iron": "PalBuildObject",
    "enemycamp_trafficbarricade03_iron": "PalBuildObject",
    "enemycamp_trafficbarricade04_iron": "PalBuildObject",
    "enemycamp_trafficbarricade05_iron": "PalBuildObject",
    "enemycamp_byobu": "PalBuildObject",
    "enemycamp_kakejiku": "PalBuildObject",
    "enemycamp_zaisu": "PalBuildObject",
    "enemycamp_zabuton": "PalBuildObject",
    "enemycamp_irori": "PalBuildObject",
    "enemycamp_toro": "PalBuildObject",
    "enemycamp_andon": "PalBuildObject",
    "enemycamp_shishiodoshi": "PalBuildObject",
    "enemycamp_bonsai": "PalBuildObject",
    "enemycamp_koro": "PalBuildObject",
    "enemycamp_seika": "PalBuildObject",
    "enemycamp_fudukue": "PalBuildObject",
    "enemycamp_wire_fence": "PalBuildObject",
    "enemycamp_sf_foundation": "PalBuildObject",
    "enemycamp_sf_wall": "PalBuildObject",
    "enemycamp_sf_roof": "PalBuildObject",
    "enemycamp_sf_stair": "PalBuildObject",
    "enemycamp_sf_doorwall": "PalMapObjectDoorModel",
    "enemycamp_sf_trianglewall": "PalBuildObject",
    "enemycamp_sf_slantedroof": "PalBuildObject",
    "enemycamp_sf_windowwall": "PalBuildObject",
    "enemycamp_sf_pillars": "PalBuildObject",
    "enemycamp_lilyqueenstatue": "PalBuildObject",
    "enemycamp_conservationgroupbannera": "PalBuildObject",
    "enemycamp_conservationgroupbannerb": "PalBuildObject",
    "enemycamp_banyan_big": "PalBuildObject",
    "enemycamp_hunter_gangflag": "PalBuildObject",
    "enemycamp_palcage": "PalBuildObject",
    "enemycamp_woodenbarricade": "PalBuildObject",
    "enemycamp_olympiccauldron": "PalBuildObject",
    "enemycamp_crusher": "PalBuildObject",
    "enemycamp_flourmill": "PalBuildObject",
    "enemycamp_compositedesk": "PalBuildObject",
    "enemycamp_factory_money": "PalBuildObject",
    "enemycamp_icecrusher": "PalBuildObject",
    "enemycamp_basecampworkhard": "PalBuildObject",
    "enemycamp_toolboxv1": "PalBuildObject",
    "enemycamp_miningtool": "PalBuildObject",
    "enemycamp_snowman": "PalBuildObject",
    "enemycamp_transmissiontower": "PalBuildObject",
    "enemycamp_walltorch02": "PalMapObjectTorchModel",
    "enemycamp_firestand": "PalMapObjectTorchModel",
    "enemycamp_candlestand": "PalMapObjectTorchModel",
    "enemycamp_itembooth": "PalBuildObject",
    "enemycamp_palbooth": "PalBuildObject",
    "enemycamp_wood_fence": "PalBuildObject",
    "enemycamp_stone_fence": "PalBuildObject",
    "enemycamp_iron_fence": "PalBuildObject",
    "enemycamp_glass_fence": "PalBuildObject",
    "enemycamp_japanesestyle_fence": "PalBuildObject",
    "enemycamp_sf_fence": "PalBuildObject",
    "enemycamp_wallsignboard_no101": "PalBuildObject",
    "enemycamp_wallsignboard_no102": "PalBuildObject",
    "enemycamp_wallsignboard_no103": "PalBuildObject",
    "enemycamp_wallsignboard_no104": "PalBuildObject",
    "enemycamp_wallsignboard_no105": "PalBuildObject",
    "enemycamp_wallsignboard_no106": "PalBuildObject",
    "enemycamp_wallsignboard_no107": "PalBuildObject",
    "enemycamp_wallsignboard_no108": "PalBuildObject",
    "enemycamp_wallsignboard_no109": "PalBuildObject",
    "enemycamp_wallsignboard_no110": "PalBuildObject",
    "enemycamp_globalpalstorage": "PalBuildObject",
    "enemycamp_factory_hard_02": "PalBuildObject",
    "enemycamp_factory_hard_03": "PalBuildObject",
    "enemycamp_weaponfactory_dirty_03": "PalBuildObject",
    "enemycamp_skinchange": "PalBuildObject",
    "enemycamp_monsterfarm": "PalBuildObjectMonsterFarm",
    "enemycamp_breedfarm": "PalBuildObjectBreedFarm",
    "enemycamp_displaycharacter": "PalBuildObject",
    "enemycamp_dimensionpalstorage": "PalBuildObject",
    "enemycamp_spherefactory_black_02": "PalBuildObject",
    "enemycamp_spherefactory_black_03": "PalBuildObject",
    "enemycamp_guildchest": "PalBuildObject",
    "enemycamp_coolerpalfoodbox": "PalBuildObject",
    "enemycamp_spa2": "PalBuildObject",
    "enemycamp_medicalpalbed_04": "PalBuildObject",
    "enemycamp_goalsoccer_iron": "PalBuildObject",
    "enemycamp_trafficsign03_iron": "PalBuildObject",
    "enemycamp_trafficsign04_iron": "PalBuildObject",
    "enemycamp_stonepit": "PalBuildObject",
    "enemycamp_stationdeforest2": "PalBuildObject",
    "enemycamp_copperpit": "PalBuildObject",
    "enemycamp_copperpit_2": "PalBuildObject",
    "enemycamp_farmblockv2_berries": "PalBuildObject",
    "enemycamp_farmblockv2_tomato": "PalBuildObject",
    "enemycamp_farmblockv2_lettuce": "PalBuildObject",
    "enemycamp_farmblockv2_carrot": "PalBuildObject",
    "enemycamp_farmblockv2_onion": "PalBuildObject",
    "enemycamp_farmblockv2_potato": "PalBuildObject",
    "enemycamp_altar": "PalBuildObjectRaidBossSummon",
    "enemycamp_lanterntop": "PalMapObjectLampModel",
    "enemycamp_shrine_lantern": "PalMapObjectLampModel",
    "enemycamp_guardiandogstatue": "PalBuildObject",
    "enemycamp_hunter_flag": "PalBuildObject",
    "enemycamp_hunter_banner": "PalBuildObject",
    "enemycamp_believer_flag": "PalBuildObject",
    "enemycamp_believer_banner": "PalBuildObject",
    "enemycamp_firecult_flag": "PalBuildObject",
    "enemycamp_firecult_banner": "PalBuildObject",
    "enemycamp_police_flag": "PalBuildObject",
    "enemycamp_police_banner": "PalBuildObject",
    "enemycamp_scientist_flag": "PalBuildObject",
    "enemycamp_scientist_banner": "PalBuildObject",
    "enemycamp_ninja_flag": "PalBuildObject",
    "enemycamp_ninja_banner": "PalBuildObject",
    "enemycamp_operatingtable": "PalBuildObject",
}


def decode_bytes(
    parent_reader: FArchiveReader, m_bytes: Sequence[int], object_id: str
) -> Optional[dict[str, Any]]:
    if len(m_bytes) == 0:
        return {"values": []}
    reader = parent_reader.internal_copy(bytes(m_bytes), debug=False)
    data: dict[str, Any] = {}

    if object_id.lower() not in MAP_OBJECT_NAME_TO_CONCRETE_MODEL_CLASS:
        logger.debug(f"Map object '{object_id}' not in database, skipping")
        return {"values": m_bytes}

    # Base handling
    data["instance_id"] = reader.guid()
    data["model_instance_id"] = reader.guid()

    map_object_concrete_model = MAP_OBJECT_NAME_TO_CONCRETE_MODEL_CLASS[
        object_id.lower()
    ]
    data["concrete_model_type"] = map_object_concrete_model
    match map_object_concrete_model:
        case "PalMapObjectCharacterTeamMissionModel":
            data["mission_id"] = reader.fstring()
            data["state"] = reader.byte()
            data["start_time"] = reader.i64()
            data["unknown_bytes"] = [int(b) for b in reader.read_to_end()]
        case "PalMapObjectFarmSkillFruitsModel":
            data["leading_bytes"] = reader.byte_list(4)
            data["skill_fruits_id"] = reader.fstring()
            data["current_state"] = reader.byte()
            data["progress_rate"] = reader.float()
            data["trailing_bytes"] = reader.byte_list(20)
        case "PalMapObjectSupplyStorageModel":
            data["created_at_real_time"] = reader.i64()
            data["trailing_bytes"] = reader.byte_list(8)
        case "PalMapObjectItemBoothModel":
            data["leading_bytes"] = reader.byte_list(4)
            data["private_lock_player_uid"] = reader.guid()
            data["trade_infos"] = reader.tarray(pal_item_booth_trade_info_read)
            data["trailing_bytes"] = reader.byte_list(20)
        case "PalMapObjectPalBoothModel":
            data["unknown_bytes"] = [int(b) for b in reader.read_to_end()]
        case "PalMapObjectMultiHatchingEggModel":
            data["unknown_bytes"] = [int(b) for b in reader.read_to_end()]
        case "PalMapObjectEnergyStorageModel":
            data["stored_energy_amount"] = reader.float()
            data["trailing_bytes"] = reader.byte_list(8)
        case "PalMapObjectDeathDroppedCharacterModel":
            data["stored_parameter_id"] = reader.guid()
            data["owner_player_uid"] = reader.guid()
            if not reader.eof():
                data["unknown_bytes"] = [int(b) for b in reader.read_to_end()]
        case "PalMapObjectConvertItemModel":
            data["leading_bytes"] = reader.byte_list(4)
            data["current_recipe_id"] = reader.fstring()
            data["requested_product_num"] = reader.i32()
            data["remain_product_num"] = reader.i32()
            data["work_speed_additional_rate"] = reader.float()
            data["trailing_bytes"] = reader.byte_list(8)
        case "PalMapObjectPickupItemOnLevelModel":
            data["auto_picked_up"] = reader.u32() > 0
        case "PalMapObjectDropItemModel":
            data["auto_picked_up"] = reader.u32() > 0
            data["pickupdable_player_uid"] = reader.guid()
            data["remove_pickup_guard_timer_handle"] = reader.i64()
            data["item_id"] = {
                "static_id": reader.fstring(),
                "dynamic_id": {
                    "created_world_id": reader.guid(),
                    "local_id_in_created_world": reader.guid(),
                },
            }
            data["trailing_bytes"] = reader.byte_list(4)
        case "PalMapObjectItemDropOnDamagModel":
            data["drop_item_infos"] = reader.tarray(pal_item_and_num_read)
            if not reader.eof():
                data["unknown_bytes"] = [int(b) for b in reader.read_to_end()]
        case "PalMapObjectDeathPenaltyStorageModel":
            data["auto_destroy_if_empty"] = reader.u32() > 0
            data["owner_player_uid"] = reader.guid()
            data["created_at"] = reader.u64()
            if not reader.eof():
                data["trailing_bytes"] = reader.byte_list(4)
        case "PalMapObjectDefenseBulletLauncherModel":
            data["leading_bytes"] = reader.byte_list(4)
            data["remaining_bullets"] = reader.i32()
            data["magazine_size"] = reader.i32()
            data["bullet_item_name"] = reader.fstring()
            data["trailing_bytes"] = reader.byte_list(4)
        case "PalMapObjectGenerateEnergyModel":
            data["generate_energy_rate_by_worker"] = reader.float()
            data["stored_energy_amount"] = reader.float()
            data["consume_energy_speed"] = reader.float()
        case "PalMapObjectFarmBlockV2Model":
            data["crop_progress_rate"] = reader.float()
            data["crop_data_id"] = reader.fstring()
            data["current_state"] = reader.byte()
            data["crop_progress_rate_value"] = reader.float()
            data["water_stack_rate_value"] = reader.float()
            data["state_machine"] = {
                "growup_required_time": reader.float(),
                "growup_progress_time": reader.float(),
            }
            data["trailing_bytes"] = reader.byte_list(8)
        case "PalMapObjectFastTravelPointModel":
            data["location_instance_id"] = reader.guid()
            if not reader.eof():
                data["unknown_bytes"] = [int(b) for b in reader.read_to_end()]
        case "PalMapObjectShippingItemModel":
            data["shipping_hours"] = reader.tarray(lambda r: r.i32())
        case "PalMapObjectProductItemModel":
            data["leading_bytes"] = reader.byte_list(4)
            data["work_speed_additional_rate"] = reader.float()
            data["product_item_id"] = reader.fstring()
            data["trailing_bytes"] = reader.byte_list(4)
        case "PalMapObjectRecoverOtomoModel":
            data["recover_amount_by_sec"] = reader.float()
        case "PalMapObjectHatchingEggModel":
            data["leading_bytes"] = reader.byte_list(4)
            data["hatched_character_save_parameter"] = reader.properties_until_end()
            data["current_pal_egg_temp_diff"] = reader.i32()
            data["hatched_character_guid"] = reader.guid()
            data["trailing_bytes"] = reader.byte_list(4)
        case "PalMapObjectTreasureBoxModel":
            data["treasure_grade_type"] = reader.byte()
            data["treasure_special_type"] = reader.byte()
            data["opened"] = reader.byte()
            data["long_hold_interaction_duration"] = reader.float()
            data["interact_player_action_type"] = reader.byte()
            data["is_lock_riding"] = reader.byte()
        case "PalMapObjectBreedFarmModel":
            data["leading_bytes"] = reader.byte_list(4)
            data["spawned_egg_instance_ids"] = reader.tarray(uuid_reader)
            data["trailing_bytes"] = reader.byte_list(4)
        case "PalMapObjectSignboardModel":
            data["leading_bytes"] = reader.byte_list(4)
            data["signboard_text"] = reader.fstring()
            data["last_modified_player_uid"] = reader.guid()
            data["trailing_bytes"] = reader.byte_list(4)
        case "PalMapObjectTorchModel":
            data["ignition_minutes"] = reader.i32()
            data["extinction_date_time"] = reader.i64()
            data["trailing_bytes"] = reader.byte_list(4)
        case "PalMapObjectPalEggModel":
            data["auto_picked_up"] = reader.u32() > 0
            data["pickupdable_player_uid"] = reader.guid()
            data["remove_pickup_guard_timer_handle"] = reader.i64()
        case "PalMapObjectBaseCampPoint":
            data["leading_bytes"] = reader.byte_list(4)
            data["base_camp_id"] = reader.guid()
            data["trailing_bytes"] = reader.byte_list(4)
        case "PalMapObjectItemChestModel" | "PalMapObjectItemChest_AffectCorruption":
            data["leading_bytes"] = reader.byte_list(4)
            data["private_lock_player_uid"] = reader.guid()
            data["trailing_bytes"] = reader.byte_list(4)
        case "PalMapObjectDimensionPalStorageModel":
            data["trailing_bytes"] = reader.byte_list(12)
        case (
            "PalMapObjectPlayerBedModel"
            | "PalBuildObject"
            | "PalMapObjectCharacterStatusOperatorModel"
            | "PalMapObjectRankUpCharacterModel"
            | "BlueprintGeneratedClass"
            | "PalMapObjectMedicalPalBedModel"
            | "PalMapObjectDoorModel"
            | "PalMapObjectMonsterFarmModel"
            | "PalMapObjectAmusementModel"
            | "PalMapObjectLampModel"
            | "PalMapObjectLabModel"
            | "PalMapObjectRepairItemModel"
            | "PalMapObjectBaseCampPassiveWorkHardModel"
            | "PalMapObjectBaseCampPassiveEffectModel"
            | "PalMapObjectBaseCampItemDispenserModel"
            | "PalMapObjectGuildChestModel"
            | "PalMapObjectCharacterMakeModel"
            | "PalMapObjectPalFoodBoxModel"
            | "PalMapObjectPlayerSitModel"
            | "PalMapObjectBaseCampWorkerDirectorModel"
            | "PalMapObjectPalMedicineBoxModel"
            | "PalMapObjectDefenseWaitModel"
            | "PalMapObjectHeatSourceModel"
            | "PalMapObjectDisplayCharacterModel"
            | "Default_PalMapObjectConcreteModelBase"
            | "PalMapObjectDamagedScarecrowModel"
            | "PalMapObjectGlobalPalStorageModel"
        ):
            data["trailing_bytes"] = reader.byte_list(4)
        case _:
            logger.debug(
                f"Unknown map object concrete model {map_object_concrete_model}, skipping"
            )
            return {"values": m_bytes}

    if not reader.eof():
        raise Exception(
            f"Warning: EOF not reached for {object_id} {map_object_concrete_model}: ori: {''.join(f'{b:02x}' for b in m_bytes)} remaining: {reader.size - reader.data.tell()}"
        )
    return data


def encode_bytes(p: Optional[dict[str, Any]]) -> bytes:
    if p is None:
        return b""

    writer = FArchiveWriter()

    map_object_concrete_model = p["concrete_model_type"]

    # Base handling
    writer.guid(p["instance_id"])
    writer.guid(p["model_instance_id"])

    match map_object_concrete_model:
        case "PalMapObjectCharacterTeamMissionModel":
            writer.fstring(p["mission_id"])
            writer.byte(p["state"])
            writer.i64(p["start_time"])
            writer.write(bytes(p["unknown_bytes"]))
        case "PalMapObjectFarmSkillFruitsModel":
            writer.write(bytes(p["leading_bytes"]))
            writer.fstring(p["skill_fruits_id"])
            writer.byte(p["current_state"])
            writer.float(p["progress_rate"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectSupplyStorageModel":
            writer.i64(p["created_at_real_time"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectItemBoothModel":
            writer.write(bytes(p["leading_bytes"]))
            writer.guid(p["private_lock_player_uid"])
            writer.tarray(pal_item_booth_trade_info_writer, p["trade_infos"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectPalBoothModel":
            writer.write(bytes(p["unknown_bytes"]))
        case "PalMapObjectMultiHatchingEggModel":
            writer.write(bytes(p["unknown_bytes"]))
        case "PalMapObjectEnergyStorageModel":
            writer.float(p["stored_energy_amount"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectDeathDroppedCharacterModel":
            writer.guid(p["stored_parameter_id"])
            writer.guid(p["owner_player_uid"])
            if "unknown_bytes" in p:
                writer.write(bytes(p["unknown_bytes"]))
        case "PalMapObjectConvertItemModel":
            writer.write(bytes(p["leading_bytes"]))
            writer.fstring(p["current_recipe_id"])
            writer.i32(p["requested_product_num"])
            writer.i32(p["remain_product_num"])
            writer.float(p["work_speed_additional_rate"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectPickupItemOnLevelModel":
            writer.u32(1 if p["auto_picked_up"] else 0)
        case "PalMapObjectDropItemModel":
            writer.u32(1 if p["auto_picked_up"] else 0)
            writer.guid(p["pickupdable_player_uid"])
            writer.i64(p["remove_pickup_guard_timer_handle"])
            writer.fstring(p["item_id"]["static_id"])
            writer.guid(p["item_id"]["dynamic_id"]["created_world_id"])
            writer.guid(p["item_id"]["dynamic_id"]["local_id_in_created_world"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectItemDropOnDamagModel":
            writer.tarray(pal_item_and_slot_writer, p["drop_item_infos"])
            if "unknown_bytes" in p:
                writer.write(bytes(p["unknown_bytes"]))
        case "PalMapObjectDeathPenaltyStorageModel":
            writer.u32(1 if p["auto_destroy_if_empty"] else 0)
            writer.guid(p["owner_player_uid"])
            writer.u64(p["created_at"])
            if "trailing_bytes" in p:
                writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectDefenseBulletLauncherModel":
            writer.write(bytes(p["leading_bytes"]))
            writer.i32(p["remaining_bullets"])
            writer.i32(p["magazine_size"])
            writer.fstring(p["bullet_item_name"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectGenerateEnergyModel":
            writer.float(p["generate_energy_rate_by_worker"])
            writer.float(p["stored_energy_amount"])
            writer.float(p["consume_energy_speed"])
        case "PalMapObjectFarmBlockV2Model":
            writer.float(p["crop_progress_rate"])
            writer.fstring(p["crop_data_id"])
            writer.byte(p["current_state"])
            writer.float(p["crop_progress_rate_value"])
            writer.float(p["water_stack_rate_value"])
            writer.float(p["state_machine"]["growup_required_time"])
            writer.float(p["state_machine"]["growup_progress_time"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectFastTravelPointModel":
            writer.guid(p["location_instance_id"])
            if "unknown_bytes" in p:
                writer.write(bytes(p["unknown_bytes"]))
        case "PalMapObjectShippingItemModel":
            writer.tarray(lambda w, x: w.i32(x), p["shipping_hours"])
        case "PalMapObjectProductItemModel":
            writer.write(bytes(p["leading_bytes"]))
            writer.float(p["work_speed_additional_rate"])
            writer.fstring(p["product_item_id"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectRecoverOtomoModel":
            writer.float(p["recover_amount_by_sec"])
        case "PalMapObjectHatchingEggModel":
            writer.write(bytes(p["leading_bytes"]))
            writer.properties(p["hatched_character_save_parameter"])
            writer.i32(p["current_pal_egg_temp_diff"])
            writer.guid(p["hatched_character_guid"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectTreasureBoxModel":
            writer.byte(p["treasure_grade_type"])
            writer.byte(p["treasure_special_type"])
            writer.byte(p["opened"])
            writer.float(p["long_hold_interaction_duration"])
            writer.byte(p["interact_player_action_type"])
            writer.byte(p["is_lock_riding"])
        case "PalMapObjectBreedFarmModel":
            writer.write(bytes(p["leading_bytes"]))
            writer.tarray(uuid_writer, p["spawned_egg_instance_ids"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectSignboardModel":
            writer.write(bytes(p["leading_bytes"]))
            writer.fstring(p["signboard_text"])
            writer.guid(p["last_modified_player_uid"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectTorchModel":
            writer.i32(p["ignition_minutes"])
            writer.i64(p["extinction_date_time"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectPalEggModel":
            writer.u32(1 if p["auto_picked_up"] else 0)
            writer.guid(p["pickupdable_player_uid"])
            writer.i64(p["remove_pickup_guard_timer_handle"])
        case "PalMapObjectBaseCampPoint":
            writer.write(bytes(p["leading_bytes"]))
            writer.guid(p["base_camp_id"])
            writer.write(bytes(p["trailing_bytes"]))
        case "PalMapObjectItemChestModel" | "PalMapObjectItemChest_AffectCorruption":
            writer.write(bytes(p["leading_bytes"]))
            writer.guid(p["private_lock_player_uid"])
            writer.write(bytes(p["trailing_bytes"]))
        case (
            "PalMapObjectPlayerBedModel"
            | "PalBuildObject"
            | "PalMapObjectCharacterStatusOperatorModel"
            | "PalMapObjectRankUpCharacterModel"
            | "BlueprintGeneratedClass"
            | "PalMapObjectMedicalPalBedModel"
            | "PalMapObjectDoorModel"
            | "PalMapObjectMonsterFarmModel"
            | "PalMapObjectAmusementModel"
            | "PalMapObjectLampModel"
            | "PalMapObjectLabModel"
            | "PalMapObjectRepairItemModel"
            | "PalMapObjectBaseCampPassiveWorkHardModel"
            | "PalMapObjectBaseCampPassiveEffectModel"
            | "PalMapObjectBaseCampItemDispenserModel"
            | "PalMapObjectGuildChestModel"
            | "PalMapObjectCharacterMakeModel"
            | "PalMapObjectPalFoodBoxModel"
            | "PalMapObjectPlayerSitModel"
            | "PalMapObjectDimensionPalStorageModel"
            | "PalMapObjectBaseCampWorkerDirectorModel"
            | "PalMapObjectPalMedicineBoxModel"
            | "PalMapObjectDefenseWaitModel"
            | "PalMapObjectHeatSourceModel"
            | "PalMapObjectDisplayCharacterModel"
            | "Default_PalMapObjectConcreteModelBase"
            | "PalMapObjectDamagedScarecrowModel"
            | "PalMapObjectGlobalPalStorageModel"
        ):
            writer.write(bytes(p["trailing_bytes"]))
        case _:
            raise Exception(
                f"Unknown map object concrete model {map_object_concrete_model}"
            )

    encoded_bytes = writer.bytes()
    return encoded_bytes
