# Immersive Melodies: Electric Guitar

A NeoForge 1.21.1 addon for [Immersive Melodies](https://modrinth.com/mod/immersive-melodies) 0.8.0+ that adds an
**Electric Guitar** instrument. It shows up in the Immersive Melodies creative tab and plays every melody like the
built-in instruments.

## Recipe

```
. . I      I = Iron Ingot
R S .      S = String
R N .      R = Redstone, N = Note Block
```

## How it hooks in

- `ElectricGuitarAddon` calls `immersive_melodies.Items.register(...)` from the mod constructor. Immersive Melodies
  then registers the item, its `electric_guitar.c1`…`c8` sound events, the creative tab entry, and loads the
  `electric_guitar_hand` 3D model.
- `client/ElectricGuitarClient` registers `ElectricGuitarAnimator` (fretting hand follows pitch, picking hand strums
  on each note). It only loads on the client because animators use client-only model classes.

## Building

```bash
./gradlew build
```

The jar ends up in `build/libs/`. Install it next to Immersive Melodies (NeoForge, 0.8.0+1.21.1 or newer).

## Model and textures

The in-hand model is a plain Blockbench model in the same style as the built-in instruments: 25 cubes and a
hand-painted 32x32 texture. Open `blockbench/electric_guitar.bbmodel` in Blockbench to edit it, then use
File > Export > Java Block/Item Model to overwrite
`src/main/resources/assets/immersive_electric_guitar/models/item/electric_guitar_hand.json` (and save the
texture to `textures/item/electric_guitar.png`). The 16x16 inventory icon is `textures/item/icon/electric_guitar.png`.

## Sounds

`python tools/generate_sounds.py` synthesizes the c1–c8 guitar samples (Python standard library plus `ffmpeg` on
PATH). To use recorded samples instead, drop `c1.ogg` … `c8.ogg` (mono, each a C note in that octave) into
`src/main/resources/assets/immersive_electric_guitar/sounds/instruments/electric_guitar/`.

## License

GPL-3.0, matching Immersive Melodies, whose API it links against.
