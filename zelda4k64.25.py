"""Simple text-based adventure inspired by classic hero games."""

from __future__ import annotations

import random


def title_screen() -> None:
    """Display the game title and basic instructions."""
    print("=" * 40)
    print("  The Quest of the Tiny Hero")
    print("=" * 40)
    print("Commands: look, go <direction>, take <item>, attack, inventory, quit")
    print()


class Player:
    """Player with hit points and inventory."""

    def __init__(self) -> None:
        self.hp = 10
        self.inventory: list[str] = []

    def has(self, item: str) -> bool:
        return item in self.inventory


class Enemy:
    """Simple enemy with a name and hit points."""

    def __init__(self, name: str, hp: int, damage: int) -> None:
        self.name = name
        self.hp = hp
        self.damage = damage

    def is_alive(self) -> bool:
        return self.hp > 0


class Location:
    """A place in the world."""

    def __init__(
        self, description: str, items: list[str] | None = None, enemy: Enemy | None = None
    ) -> None:
        self.description = description
        self.items = items or []
        self.enemy = enemy
        self.neighbors: dict[str, str] = {}

    def connect(self, direction: str, dest: str) -> None:
        self.neighbors[direction] = dest


class Game:
    """Main game logic."""

    def __init__(self) -> None:
        self.player = Player()
        self.locations: dict[str, Location] = {}
        self.current = "village"
        self.boss_defeated = False
        self.setup_world()

    def setup_world(self) -> None:
        """Create locations and connections."""
        self.locations[
            "village"
        ] = Location(
            "You are in a peaceful village with cobblestone paths.",
            ["shield"],
        )
        self.locations[
            "forest"
        ] = Location(
            "Tall trees surround you. You hear rustling leaves.",
            ["sword"],
            Enemy("Octorok", 5, 1),
        )
        self.locations[
            "cave"
        ] = Location(
            "A dark, damp cave. Something gleams on the ground.",
            ["key"],
            Enemy("Moblin", 6, 2),
        )
        self.locations[
            "dungeon"
        ] = Location(
            "Stone walls close in around you. A locked door blocks the way east.",
            [],
            Enemy("Darknut", 8, 2),
        )
        self.locations[
            "boss_room"
        ] = Location(
            "The lair of the fearsome beast!", [], Enemy("Dungeon Boss", 12, 3)
        )

        self.locations["village"].connect("north", "forest")
        self.locations["forest"].connect("south", "village")
        self.locations["forest"].connect("east", "cave")
        self.locations["cave"].connect("west", "forest")
        self.locations["village"].connect("east", "dungeon")
        self.locations["dungeon"].connect("west", "village")
        # boss_room is east of dungeon behind locked door
        self.locations["dungeon"].connect("east", "boss_room")
        self.locations["boss_room"].connect("west", "dungeon")

    def look(self) -> None:
        """Describe the current location."""
        loc = self.locations[self.current]
        print(loc.description)
        if loc.items:
            print("You see:", ", ".join(loc.items))
        if loc.enemy and loc.enemy.is_alive():
            print(f"A {loc.enemy.name} blocks your path!")
        print("Exits:", ", ".join(loc.neighbors.keys()))

    def take(self, item: str) -> None:
        """Pick up an item if present."""
        loc = self.locations[self.current]
        if item in loc.items:
            self.player.inventory.append(item)
            loc.items.remove(item)
            print(f"You found a {item}!")
        else:
            print("There is no such item here.")

    def go(self, direction: str) -> None:
        """Move to a neighboring location, if possible."""
        loc = self.locations[self.current]
        if direction not in loc.neighbors:
            print("You can't go that way.")
            return
        if self.current == "dungeon" and direction == "east":
            if not self.player.has("key"):
                print("The door is locked. You need a key.")
                return
        self.current = loc.neighbors[direction]
        self.look()

    def attack(self) -> None:
        """Handle combat with the enemy in the location."""
        loc = self.locations[self.current]
        enemy = loc.enemy
        if not enemy or not enemy.is_alive():
            print("There is nothing to fight here.")
            return
        sword_bonus = 2 if self.player.has("sword") else 1
        enemy.hp -= sword_bonus
        print(f"You strike the {enemy.name}! ({enemy.hp} HP left)")
        if enemy.is_alive():
            damage = enemy.damage - (1 if self.player.has("shield") else 0)
            damage = max(0, damage)
            self.player.hp -= damage
            print(f"The {enemy.name} hits you! (You have {self.player.hp} HP)")
            if self.player.hp <= 0:
                print("You have been defeated!")
        else:
            print(f"You defeated the {enemy.name}!")
            if enemy.name == "Dungeon Boss":
                self.boss_defeated = True

    def show_inventory(self) -> None:
        items = self.player.inventory
        print("Inventory:", ", ".join(items) if items else "(empty)")

    def game_loop(self) -> None:
        self.look()
        while self.player.hp > 0 and not self.boss_defeated:
            cmd = input("\n> ").strip().lower()
            if cmd == "quit":
                break
            if cmd == "look":
                self.look()
            elif cmd.startswith("go "):
                self.go(cmd[3:])
            elif cmd.startswith("take "):
                self.take(cmd[5:])
            elif cmd == "inventory":
                self.show_inventory()
            elif cmd == "attack":
                self.attack()
            else:
                print("I don't understand that command.")
        if self.boss_defeated:
            print("\nYou rescued the kingdom! Victory is yours!")
        elif self.player.hp <= 0:
            print("\nYour journey ends here.")


def main() -> None:
    title_screen()
    game = Game()
    game.game_loop()


if __name__ == "__main__":
    main()
