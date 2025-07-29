# Palworld XGP Save Importer

An experimental tool to import Steam Palworld savefiles into XGP savefile container.

Directly forked from the Starfield XGP Save Importer. Probably I should create a single tool for different games if this continues.

## Usage

```
$ python3 main.py <path to save folder>
```

Or just drop the save folder (the folder with long hex string name) onto the executable from releases.

**NOTE**: The cloud sync feature of Xbox app might interfere with outside modifications to the savefile containers. After shutting down the game, please wait a minute or two before trying to import savefiles to give Xbox app some time to sync the containers. 

## Path references

Steam version: `%LOCALAPPDATA%\Pal\Saved\SaveGames\<steamid64>\`

Xbox version: `%LOCALAPPDATA%\Packages\PocketpairInc.Palworld_ad4psfrxyesvt\SystemAppData\wgs`