from __future__ import annotations

import dataclasses
import enum
from typing import List, Tuple, cast


class WeaponType(enum.Enum):
    AXE = "Axe"
    BOW = "Bow"
    CLAW = "Claw"
    CROSSBOW = "Crossbow"
    CURVED_GREATSWORD = "Curved Greatsword"
    CURVED_SWORD = "Curved Sword"
    DAGGER = "Dagger"
    FIST = "Fist"
    FLAME = "Flame"
    GREAT_HAMMER = "Great Hammer"
    GREATAXE = "Greataxe"
    GREATBOW = "Greatbow"
    GREATSWORD = "Greatsword"
    HALBERD = "Halberd"
    HAMMER = "Hammer"
    KATANA = "Katana"
    PIERCING_SWORD = "Piercing Sword"
    REAPER = "Reaper"
    SACRED_CHIME = "Sacred Chime"
    SHIELD = "Shield"
    SPEAR = "Spear"
    STAFF = "Staff"
    STRAIGHT_SWORD = "Straight Sword"
    TALISMAN = "Talisman"
    ULTRA_GREATSWORD = "Ultra Greatsword"
    WHIP = "Whip"


class WeaponInfusion(enum.Enum):
    NONE = None
    HEAVY = "Heavy"
    SHARP = "Sharp"
    REFINED = "Refined"
    SIMPLE = "Simple"
    CRYSTAL = "Crystal"
    FIRE = "Fire"
    CHAOS = "Chaos"
    LIGHTNING = "Lightning"
    DEEP = "Deep"
    DARK = "Dark"
    POISON = "Poison"
    BLOOD = "Blood"
    RAW = "Raw"
    BLESSED = "Blessed"
    HOLLOW = "Hollow"


@dataclasses.dataclass
class Damage:
    physical: float
    magic: float
    fire: float
    lightning: float
    dark: float


@dataclasses.dataclass
class ScalingCoefficients:
    str: float
    dex: float
    int: float
    faith: float
    luck: float

    def __init__(
        self, str: float, dex: float, faith: float, luck: float, int: float
    ) -> None:
        self.str = str
        self.dex = dex
        self.int = int
        self.faith = faith
        self.luck = luck


@dataclasses.dataclass
class SaturationCurve:
    physical: List[float]
    magic: List[float]
    fire: List[float]
    lightning: List[float]
    dark: List[float]


@dataclasses.dataclass
class Requirements:
    str: int
    dex: int
    int: int
    faith: int


@dataclasses.dataclass
class Defence:
    physical: int
    magic: int
    fire: int
    lightning: int
    dark: int


@dataclasses.dataclass
class Infusion:
    weapon: Weapon = dataclasses.field(repr=False)
    infusion: WeaponInfusion
    scaling: ScalingCoefficients
    damage: Damage
    saturation: SaturationCurve

    @property
    def physical_blessed(self) -> bool:
        return self.infusion == WeaponInfusion.BLESSED or self.weapon.name in {
            "Anri’s Straight Sword",
            "Saint Bident",
            "Lothric’s Holy Sword",
            "Wolnir’s Holy Blade",
            "Morne’s Great Hammer",
        }

    @property
    def magic_blessed(self) -> bool:
        return self.weapon.name == "Golden Ritual Spear"

    def damage_increases(self) -> Tuple[bool, bool, bool, bool, bool]:
        increases = [False, False, False, False, False]
        str, dex, int, faith, luck = 0, 1, 2, 3, 4
        if self.damage.physical:
            increases[str] = True
            increases[dex] = True
            increases[luck] = True
            increases[faith] = self.physical_blessed

        if self.damage.magic:
            increases[int] = True
            increases[faith] = self.magic_blessed

        if self.damage.fire:
            increases[int] = True
            increases[faith] = True

        if self.damage.lightning:
            increases[faith] = True

        if self.damage.dark:
            increases[int] = True
            increases[faith] = True

        if not self.scaling.str:
            increases[str] = False

        if not self.scaling.dex:
            increases[dex] = False

        if not self.scaling.int:
            increases[int] = False

        if not self.scaling.faith:
            increases[faith] = False

        if not self.scaling.luck:
            increases[luck] = False

        return cast(Tuple[bool, bool, bool, bool, bool], tuple(increases))

    def damages(
        self, str: int, dex: int, int_: int, faith: int, luck: int
    ) -> Tuple[int, int, int, int, int]:
        requirements = self.weapon.requirements
        if (
            str < requirements.str
            or dex < requirements.dex
            or int_ < requirements.int
            or faith < requirements.faith
        ):
            return 0, 0, 0, 0, 0
        return (
            int(
                self.damage.physical
                * (
                    1
                    + self.scaling.str * self.saturation.physical[str]
                    + self.scaling.dex * self.saturation.physical[dex]
                    + self.scaling.luck * self.saturation.physical[luck]
                    + (
                        self.scaling.faith * self.saturation.physical[faith]
                        if self.physical_blessed
                        else 0
                    )
                )
            ),
            int(
                self.damage.magic
                * (
                    1
                    + self.scaling.int * self.saturation.magic[int_]
                    + (
                        self.scaling.faith * self.saturation.magic[faith]
                        if self.magic_blessed
                        else 0
                    )
                )
            ),
            int(
                self.damage.fire
                * (
                    1
                    + self.scaling.int * self.saturation.fire[int_]
                    + self.scaling.faith * self.saturation.fire[faith]
                )
            ),
            int(
                self.damage.lightning
                * (1 + self.scaling.faith * self.saturation.lightning[faith])
            ),
            int(
                self.damage.dark
                * (
                    1
                    + self.scaling.int * self.saturation.dark[int_]
                    + self.scaling.faith * self.saturation.dark[faith]
                )
            ),
        )

    def _levels(self, levels, points):
        links = [
            i
            for i, (v, d) in enumerate(zip(levels, self.damage_increases()))
            if v and d
        ]
        requirements = self.weapon.requirements
        levels = list(levels)
        if levels[0] < requirements.str:
            points -= requirements.str - levels[0]
            levels[0] = requirements.str
        if levels[1] < requirements.dex:
            points -= requirements.dex - levels[1]
            levels[1] = requirements.dex
        if levels[2] < requirements.int:
            points -= requirements.int - levels[2]
            levels[2] = requirements.int
        if levels[3] < requirements.faith:
            points -= requirements.faith - levels[3]
            levels[3] = requirements.faith
        try:
            limit_delta = min(levels[i] for i in links)
        except ValueError:
            limit_delta = 0
        for level in sigma_combinations(points, len(links), 99 - limit_delta):
            levels_ = list(levels)
            for i, value in zip(links, level):
                levels_[i] += value
            if any(i > 99 for i in levels_):
                continue
            yield levels_

    def level(self, levels, points):
        for level in self._levels(levels, points):
            yield self.damages(*level), level

    def max_level(self, levels, points):
        values = sorted(
            self.level(levels, points), key=lambda i: sum(i[0]), reverse=True
        )
        max_ar = None
        for value in values:
            ar = sum(value[0])
            if max_ar is None:
                max_ar = ar
            if ar != max_ar:
                break
            yield value


def sigma_combinations(points, n, limit=None):
    if limit is None:
        limit = points
    if n <= 1:
        if points <= limit:
            yield points,
    else:
        for i in range(min(points, limit) + 1):
            for t in sigma_combinations(points - i, n - 1, limit):
                yield (i,) + t


@dataclasses.dataclass
class Infusions:
    none: Infusion
    heavy: Infusion
    sharp: Infusion
    refined: Infusion
    simple: Infusion
    crystal: Infusion
    fire: Infusion
    chaos: Infusion
    lightning: Infusion
    deep: Infusion
    dark: Infusion
    poison: Infusion
    blood: Infusion
    raw: Infusion
    blessed: Infusion
    hollow: Infusion

    def __iter__(self):
        return iter(
            [
                self.none,
                self.heavy,
                self.sharp,
                self.refined,
                self.simple,
                self.crystal,
                self.fire,
                self.chaos,
                self.lightning,
                self.deep,
                self.dark,
                self.poison,
                self.blood,
                self.raw,
                self.blessed,
                self.hollow,
            ]
        )


@dataclasses.dataclass
class Weapon:
    name: str
    id: str
    type: WeaponType
    weight: float
    bleed: float
    poison: float
    frost: float
    requirements: Requirements
    defence: Damage
    infusable: bool
    dual_wield: bool
    infusions: Infusions

    def max_level(self, level: Tuple[int, int, int, int, int], n: int):
        for infusion in self.infusions:
            if infusion is None:
                continue
            ls = list(infusion.max_level(level, n))
            if ls:
                yield sum(ls[0][0]), ls, infusion
            else:
                yield 0, ls, infusion
