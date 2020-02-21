import itertools
import json
import pathlib
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    NoReturn,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import requests

from .weapons import (
    Damage,
    Infusion,
    Infusions,
    Requirements,
    SaturationCurve,
    ScalingCoefficients,
    Weapon,
    WeaponInfusion,
    WeaponType,
)

T = TypeVar("T")


class Cache:
    PATH = pathlib.Path("./.darksouls/cache")

    @classmethod
    def weapons_path(cls) -> pathlib.Path:
        return cls.PATH / "weapons.json"

    @classmethod
    def misc_path(cls) -> pathlib.Path:
        return cls.PATH / "misc.json"

    @classmethod
    def ensure_path(cls) -> NoReturn:
        if not cls.PATH.exists():
            cls.PATH.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_weapons(cls) -> dict:
        with cls.weapons_path().open() as f:
            return json.load(f)

    @classmethod
    def save_weapons(cls, weapons) -> NoReturn:
        cls.ensure_path()
        with cls.weapons_path().open("w") as f:
            json.dump(weapons, f)

    @classmethod
    def load_misc_data(cls) -> dict:
        with cls.misc_path().open() as f:
            return json.load(f)

    @classmethod
    def save_misc_data(cls, misc_data) -> NoReturn:
        cls.ensure_path()
        with cls.misc_path().open("w") as f:
            json.dump(misc_data, f)


class Web:
    @staticmethod
    def _gets(
        url: str, per_page: int, per_page_limit: int, key: Callable[[dict], int]
    ) -> Iterator[dict]:
        if per_page > per_page_limit:
            raise ValueError("`per_page` can be a max of {per_page_limit}")
        for page in itertools.count(0):
            r = requests.get(url, params={"per_page": per_page, "page": page})
            data = r.json()
            yield data
            if key(data) < per_page:
                break

    @classmethod
    def load_weapons(cls, per_page: int = 500) -> List[dict]:
        results = cls._gets(
            "https://mugenmonkey.com/api/v0/ds3_weapons",
            per_page,
            500,
            lambda d: len(d["results"]),
        )
        weapons = []
        for result in results:
            for r in result["results"]:
                w = result[r["key"]][r["id"]]
                if isinstance(w["base_damage"], str):
                    w["base_damage"] = json.loads(w["base_damage"])
                if isinstance(w["scaling_coefficients"], str):
                    w["scaling_coefficients"] = json.loads(w["scaling_coefficients"])
                if isinstance(w["stat_funcs"], str):
                    w["stat_funcs"] = json.loads(w["stat_funcs"])
                weapons.append(w)
        return weapons

    @classmethod
    def load_misc_data(cls, per_page: int = 500) -> Dict[Any, List[Union[int, float]]]:
        results = cls._gets(
            "https://mugenmonkey.com/api/v0/misc_data",
            per_page,
            500,
            lambda d: len(d["dark_souls_3"]["scaling_saturation_curves"]),
        )
        misc_data = {}
        for result in results:
            for k, v in result["dark_souls_3"]["scaling_saturation_curves"].items():
                misc_data[k] = [i / 100 for i in v]
        return misc_data


def grouper(it: Iterator[T], n: int) -> Iterator[Tuple[T]]:
    return zip(*[iter(it)] * n)


def enum_by_value(enum: Type[T]) -> Dict[Any, T]:
    return {i.value: i for i in enum}


class Loader:
    @staticmethod
    def _load(load_cache, save_cache, load_web, cache, force):
        if not force:
            try:
                return load_cache()
            except FileNotFoundError:
                pass
        data = load_web()
        if cache:
            save_cache(data)
        return data

    @classmethod
    def _load_infusions(cls, curves, w, weapon) -> Iterator[Optional[Infusion]]:
        for inf, d, s, s_, c in zip(
            [i for i in WeaponInfusion],
            grouper(weapon["base_damage"], 5),
            grouper(weapon["scaling_coefficients"], 4),
            weapon["scaling_coefficients"][-16:],
            grouper(weapon["stat_funcs"], 5),
        ):
            c = [int(v) for v in c]
            d = [float(v) for v in d]
            s = [float(v) / 100 for v in s] + [float(s_) / 100]
            if any(c) or any(d) or any(s):
                yield Infusion(
                    weapon=w,
                    infusion=inf,
                    scaling=ScalingCoefficients(*s),
                    damage=Damage(*d),
                    saturation=SaturationCurve(*[curves[str(v)] for v in c]),
                )
            else:
                yield None

    @classmethod
    def load_weapons(
        cls,
        *,
        cache: bool = True,
        force: bool = False,
        misc_cache: bool = True,
        misc_force: bool = False
    ) -> Iterator[Weapon]:
        weapons = cls._load(
            Cache.load_weapons, Cache.save_weapons, Web.load_weapons, cache, force
        )
        ts = set()
        curves = cls.load_misc_data(cache=misc_cache, force=misc_force)
        for weapon in weapons:
            ts.add(weapon["weapon_type"])
            w = Weapon(
                name=weapon["name"],
                id=weapon["id"],
                type=enum_by_value(WeaponType)[weapon["weapon_type"]],
                weight=float(weapon["weight"]),
                bleed=float(weapon["bleed"]),
                poison=float(weapon["poison"]),
                frost=float(weapon["frost"]),
                requirements=Requirements(
                    str=int(weapon["strength_req"]),
                    dex=int(weapon["dex_req"]),
                    int=int(weapon["intelligence_req"]),
                    faith=int(weapon["faith_req"]),
                ),
                defence=Damage(
                    physical=float(weapon["physical_def"]),
                    magic=float(weapon["magic_def"]),
                    fire=float(weapon["fire_def"]),
                    lightning=float(weapon["lightning_def"]),
                    dark=float(weapon["dark_def"]),
                ),
                infusable=bool(weapon["infusable"]),
                dual_wield=bool(weapon["dual_wield"]),
                infusions=...,
            )
            infusions = list(cls._load_infusions(curves, w, weapon))
            if not infusions:
                infusions = [None] * 16
            w.infusions = Infusions(*infusions)
            yield w

    @classmethod
    def load_misc_data(cls, *, cache: bool = True, force: bool = False):
        return cls._load(
            Cache.load_misc_data, Cache.save_misc_data, Web.load_misc_data, cache, force
        )
