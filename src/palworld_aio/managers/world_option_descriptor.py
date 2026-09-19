# ---------------------------------------------------------------------------
# Adapter class for unifying interactions among different parsed data sources
# ---------------------------------------------------------------------------
#
# This class acts as an adapter for loadable formats (currently .sav and .ini)
# and provides an externally unified interface for get/set-ing the values of
# each option separately. As part of the initialization process it adds
# corresponding wrapping metadata for the individual option as defined in a json schema.

from __future__ import annotations
from typing import Any, List, Optional, TypedDict
from resource_resolver import resource_path, get_base_dir
from palsav import json_tools
from .unreal_ini_parser import META_VALUE_KEY

# The config formats naming/resolve_name can bridge between. Kept as a
# single alias so they stay in sync if another format is ever added.
# PropertyDescriptor.__required_naming_keys is derived from it.
class NamingMap(TypedDict):
    """Documenting class for type hinting/checking the `naming` dict in templates"""
    sav: str
    ini: str

class PropertyDescriptorException(RuntimeError):
    "For explicit ID'ing of PropertyDescriptor errors"

SAVEDATA_DESCRIPTOR_TEMPLATE = json_tools.load( resource_path(get_base_dir(), "game_data", "world_options_schema_struct.json") )

# Initializes certain template elements with values that are more practical to generate on the fly
SPECIALLY_HANDLED_KEYS = {
    "DenyTechnologyList":{
        "key": "allowed_values",
        "value": [{"data":item["asset"], "text":item["name"]} for item in json_tools.load( resource_path(get_base_dir(), "game_data", "world.json") )["technology"]]
    },
    "AdditionalDropItemWhenPlayerKillingInPvPMode": {
        "key": "allowed_values",
        "value": [[{"data":item["asset"], "text":f"{item["name"]}: {item["description"]}"} for item in json_tools.load( resource_path(get_base_dir(), "game_data", "items.json") )["items"]]]
    }
}

def get_property_descriptor_template(property_name, descriptor_template):
    for property_key in descriptor_template.keys():
        if property_name == property_key or (
            descriptor_template[property_key].get("naming")
            and property_name in descriptor_template[property_key]["naming"].values()
        ):
            return descriptor_template[property_key]

class PropertyDescriptor:
    """
    One entry of the reference-mapping format:

        {
            # MANDATORY values for every property. Relevant for initialization of descriptor
            "value": ...,           # primitive, or nested dict/list of
                                    # PropertyDescriptor for struct/array
            "type": "...",          # bool | int | float | string | enum |
                                    # name | array | struct | object | ...
            "description": "...",

            # OPTIONAL extras (omitted from JSON when unset):
            "default": ...,
            "allowed_values": [...],# choice list for enum/name;
                                    # [min, max] for numeric range constraints
            "array_type": "...",    # element type, only when type == "array"
            "deprecated": False,
            "naming": {             # cross-format name mapping, for .sav
                "sav": "...",       # tooling that reads/writes the same
                "ini": "...",       # logical setting under a different key
                "json":"..."        # per format. Optional as a whole, but
                },                  # if present ALL format keys are
                                    # mandatory (even where the name is
                                    # identical to the canonical one) --
                                    # this disambiguates "same name" from
                                    # "not specified" once there could be
                                    # more than two formats.
            "enumType": "...",      # the enum prefix/namespace used by the
                                    # .sav-side representation of this value
                                    # (may differ from "engineType", which
                                    # is the .ini/reflection-side path).
            "children_template": {} # sub-template for struct properties, 
                                    # with the same structure
        }
    """

    __required_naming_keys = frozenset(NamingMap.__annotations__)

    def __init__(self, property_name_from_settings: str, property_struct_from_settings: dict, source_type: str, source_descriptor_template = SAVEDATA_DESCRIPTOR_TEMPLATE):

        template_data = get_property_descriptor_template(property_name_from_settings, source_descriptor_template)

        if special_key_data := SPECIALLY_HANDLED_KEYS.get(property_name_from_settings):
            for k, v in special_key_data.items():
                template_data[k] = v

        if not template_data:
            raise PropertyDescriptorException(f"Could not find property name '{property_name_from_settings}' in list while initializing PropertyDescriptor")
        self.property_name = property_name_from_settings
        self.setting_data = property_struct_from_settings
        self.type: str = template_data.get("type")
        if not self.type:
            raise PropertyDescriptorException(f"'Type' property not set in template of property '{property_name_from_settings}'.")
        self.array_type: Optional[str] = template_data.get("array_type")
        self.default: Optional[Any] = template_data.get("default")
        self.allowed_values: Optional[List[Any]] = template_data.get("allowed_values")
        self.description: Optional[str] = template_data.get("description")
        self.deprecated: Optional[bool] = template_data.get("deprecated")
        self.naming: Optional[NamingMap] = template_data.get("naming")
        self.enum_type: Optional[str] = template_data.get("enum_type")
        self.source_type: str = source_type
        self.children_template: dict = template_data.get("children_template")
        self.__post_init__()

    def __post_init__(self) -> None:
        # Enforce the existence of all `naming` keys if the property descriptor has a `naming` field
        if self.naming is not None:
            got = set(self.naming.keys())
            if got != self.__required_naming_keys:
                missing = self.__required_naming_keys - got
                extra = got - self.__required_naming_keys
                parts = []
                if missing:
                    parts.append(f"missing {sorted(missing)}")
                if extra:
                    parts.append(f"unrecognized {sorted(extra)}")
                exact_keys = ', '.join(sorted(self.__required_naming_keys))
                conflict = ', '.join(parts)
                raise PropertyDescriptorException(f"PropertyDescriptor.naming, when specified, must include exactly the keys {exact_keys}. Conflict: {conflict}, found when parsing property {self.property_name}.")

        #recursive initialization for inner properties of struct-types
        if self.type == "StructProperty":
            if not self.children_template:
                raise PropertyDescriptorException(f"Could not find a defined children_template for property {self.property_name}")
            _children: dict[str, PropertyDescriptor] = {}
            for key, value in self.value.items():
                if isinstance(value, dict):
                    _children[key] = self.init_inner(key,value,self.source_type, self.children_template)
            self._children = _children

    @property
    def value(self):
        if self.source_type == "sav":
            if self.type == "ArrayProperty":
                if self.array_type == "EnumProperty":
                    value_list = []
                    for value in self.setting_data["value"]["values"]:
                        pref, val = value.split("::")
                        if not pref == self.enum_type:
                            raise PropertyDescriptorException( f"Property '{self.property_name}' is of type EnumProperty, but has mismatching prefix of '{pref}'. Expected {self.enum_type}." )
                        value_list.append(val)
                    return value_list
                return self.setting_data["value"]["values"]
            elif self.type == "EnumProperty":
                pref, val = self.setting_data["value"]["value"].split("::")
                if not pref == self.enum_type:
                    raise PropertyDescriptorException( f"Property '{self.property_name}' is of type EnumProperty, but has mismatching prefix of '{pref}'. Expected {self.enum_type}." )
                return val
            elif self.type in ("NameProperty", "StrProperty", "IntProperty", "BoolProperty", "FloatProperty", "StructProperty"):
                return self.setting_data["value"]
        elif self.source_type == "ini":
            return self.setting_data[META_VALUE_KEY]
        else:
            raise PropertyDescriptorException(f"Could not determine source type ({"|".join(self.__required_naming_keys)}) for {self.property_name} while attepting to get value")

    @value.setter
    def value(self,v):
        if self.source_type == "sav":
            if self.type == "ArrayProperty":
                if self.array_type == "EnumProperty":
                    if not self.enum_type:
                        raise RuntimeError(f"No enum_type for property {self.property_name} though defined in template as ArrayProperty of EnumProperty.")
                    value_list = []
                    for value in v:
                        value_list.append(self.enum_type+"::"+value)
                    self.setting_data["value"]["values"] = value_list
                else:
                    self.setting_data["value"]["values"] = v
            elif self.type == "EnumProperty":
                if not self.enum_type:
                    raise RuntimeError(f"No enum_type for property {self.property_name} though defined in template as type EnumProperty.")
                self.setting_data["value"]["value"] = self.enum_type+"::"+v
            elif self.type in ("NameProperty", "StrProperty", "IntProperty", "BoolProperty", "FloatProperty"):
                self.setting_data["value"] = v
        elif self.source_type == "ini":
            self.setting_data[META_VALUE_KEY] = v
        else:
            raise PropertyDescriptorException(f"Could not determine source type ({"|".join(self.__required_naming_keys)}) for {self.property_name} while attepting to get value")

    @property
    def children(self):
        if hasattr(self, '_children'):
            return self._children

    @classmethod
    def init_inner(cls, property_name_from_settings, property_struct_from_settings, source_type, source_descriptor_template) -> "PropertyDescriptor":
        """Classname-agnostic classmethod for children of structs"""
        return cls(property_name_from_settings, property_struct_from_settings, source_type, source_descriptor_template)

    def resolve_format_name(self, fmt) -> str:
        """Gets the appropriate setting keyname for a format"""
        if self.naming and self.naming.get(fmt):
            return self.naming[fmt]
        return self.property_name
