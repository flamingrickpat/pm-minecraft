---
name: inventory-slots
description: How to read the current inventory slot layout with minecraft_inventory_slots before equipping, so you always know exactly which slot holds which item and never act on a wrong item in hand. Use before mining, crafting, eating, or selecting hotbar slots.
---

# Read the Slot Layout Before You Touch Anything

The state delta always includes the held slot; the full layout is one call away.

## Do this first

Before placing, mining, eating, or selecting a hotbar slot:

1. `minecraft_inventory_slots()` returns read-only JSON:
   - `slots`: map of `inventory slot index -> {name} | null` (empty slots are null)
   - `selectedHotbarSlot`: which hotbar slot is active
   - `heldItem`: the item currently in hand
   - `heldSlot`: the inventory slot index of the held item

2. Decide with facts, not guesses: which tool is where, and is it in the
   hotbar (selectable) or in the main inventory (needs equip)?

## Equip by exact name, then verify

- `minecraft_equip(item_name)` selects the item by exact Mineflayer name.
- Confirm the result and re-`minecraft_inventory_slots` when a subsequent action
  matters (mining, eating).

## Common mistakes this prevents

- Mining stone while holding cobblestone or an empty hand → the `unharvestable`
  error. Check the slot map, equip a pickaxe, retry.
- Eating from the wrong slot because you assumed the stack location.
- Selecting a hotbar slot by guesswork instead of reading `selectedHotbarSlot`.

## Rules

- The slot index is your ground truth for the hand. If you're unsure what a
  tool call will act on, read the slots first.
- `minecraft_inventory_slots` is read-only and makes no state changes — call it
  freely.
