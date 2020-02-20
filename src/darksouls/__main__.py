import pathlib

from typing import List, Iterable, Any, Dict, Iterator, Tuple, Union, Callable, NoReturn

import matplotlib.pyplot as plt

from .loaders import Loader
from .weapons import Weapon, WeaponType, WeaponInfusion

CATEGORY20 = tuple('#1f77b4 #aec7e8 #ff7f0e #ffbb78 #2ca02c #98df8a #d62728 #ff9896 #9467bd #c5b0d5 '
                   '#8c564b #c49c94 #e377c2 #f7b6d2 #7f7f7f #c7c7c7 #bcbd22 #dbdb8d #17becf #9edae5'.split())


def infusions(weapons: Iterable[Weapon], level: Tuple[int, int, int, int, int], n: int):
    return [
        i
        for weapon in weapons
        for i in weapon.max_level(level, n)
    ]


def _old(weapons):
    for ar, levels, infusion in sorted(infusions(weapons, (10, 10, 10, 10, 10), 70), key=lambda v: v[0]):
        ls = [l[1] for l in levels]
        weapon = infusion.weapon
        if weapon.type is None:
            print(f'{ar}: {weapon.name}[{infusion.infusion.value}] -> {ls}')
        else:
            print(f'{ar}: {weapon.name}[{infusion.infusion.value}][{weapon.type.value}] -> {ls}')


WeaponInfusions = Dict[str, List[int]]
WeaponsRange = Dict[str, List[Tuple[int, int]]]
Levels = Dict[str, Dict[str, WeaponInfusions]]


def find_levels(weapons: List[Weapon], levels: Any) -> Levels:
    default = [None] * len(levels)
    weapon_ars = {}
    for i, level in enumerate(levels):
        for ar, _, infusion in infusions(weapons, (10, 10, 10, 10, 10), level):
            if ar == 0:
                ar = None
            (
                weapon_ars
                    .setdefault(infusion.weapon.type.name, {})
                    .setdefault(infusion.weapon.name, {})
                    .setdefault(infusion.infusion.name, list(default))
                    [i]
            ) = ar
    return weapon_ars


def extract_item_data(levels: Levels) -> Iterator[Tuple[str, WeaponInfusions]]:
    for weapon_type_key, weapons in levels.items():
        for weapon_name, weapon in weapons.items():
            yield weapon_name, weapon


def extract_groups_data(levels: Levels) -> Iterator[Tuple[str, WeaponsRange]]:
    for weapon_type_key, weapons in levels.items():
        values = {
            weapon_name: [
                (max([a for a in ars if a is not None], default=None), min([a for a in ars if a is not None], default=None))
                for ars in zip(*weapon.values())
            ]
            for weapon_name, weapon in weapons.items()
        }
        yield WeaponType[weapon_type_key].value, values


def plot(domain: Any, levels: Iterator[Tuple[str, Union[WeaponsRange, WeaponInfusions]]],
         get_color: Callable[[int, str], str], base_path: pathlib.Path
         ) -> NoReturn:
    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)
    for name, values in levels:
        fig, axs = plt.subplots()
        axs.set_xlabel('Level Increase')
        axs.set_ylabel('AR')
        axs.set_title(name)
        lines = []
        for i, (key, value) in enumerate(values.items()):
            color = get_color(i, key)
            if isinstance(value[0], list):
                upper, lower = zip(*value)
                axs.fill_between(domain, upper, lower, facecolor=color, edgecolor=color, alpha=0.1)
                lines.append(axs.plot(domain, upper, '-', color=color)[0])
                axs.plot(domain, lower, '-', color=color)
            else:
                lines.append(axs.plot(domain, value, '-', color=color)[0])
        axs.legend(lines, values.keys(), loc=0)
        fig.savefig(base_path / name)
        plt.close(fig)


def main():
    inf_colors = {
        infusion.name: CATEGORY20[i]
        for i, infusion in enumerate(WeaponInfusion)
    }

    weapons = list(Loader.load_weapons())
    domain = range(0, 20)
    levels = find_levels(weapons, domain)
    plot(
        domain,
        extract_groups_data(levels),
        lambda i, _: CATEGORY20[i % 20],
        pathlib.Path('./.darksouls/images/categories/')
    )
    plot(
        domain,
        extract_item_data(levels),
        lambda _, inf: inf_colors[inf],
        pathlib.Path('./.darksouls/images/weapons/')
    )


if __name__ == '__main__':
    main()
