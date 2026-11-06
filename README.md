# Immersive Melodies: More Instruments

A NeoForge 1.21.1 addon for [Immersive Melodies](https://modrinth.com/mod/immersive-melodies) 0.8.0+ that adds new
instruments. They show up in the Immersive Melodies creative tab and play every melody like the built-in instruments.

- **Electric Guitar**
- **Acoustic Guitar**

## Recipes

Electric Guitar:

```
. . I      I = Iron Ingot
R S .      S = String
R N .      R = Redstone, N = Note Block
```

Acoustic Guitar:

```
. T .      T = Stick
S P S      S = String
P P P      P = any Planks
```

## How it hooks in

- `ElectricGuitarAddon` calls `immersive_melodies.Items.register(...)` for each instrument from the mod constructor.
  Immersive Melodies then registers the item, its `<name>.c1`…`c8` sound events, the creative tab entry, and loads the
  `<name>_hand` 3D model.
- `client/ElectricGuitarClient` registers `ElectricGuitarAnimator` for both guitars (fretting hand follows pitch,
  picking hand strums on each note). It only loads on the client because animators use client-only model classes.

The mod id stays `immersive_electric_guitar` so items in existing worlds keep working.

## Building

```bash
./gradlew build
```

The jar ends up in `build/libs/`. Install it next to Immersive Melodies (NeoForge, 0.8.0+1.21.1 or newer).

## Models and textures

The in-hand models are plain Blockbench models in the same style as the built-in instruments, each with a
hand-painted 32x32 texture. Open `blockbench/electric_guitar.bbmodel` or `blockbench/acoustic_guitar.bbmodel` in
Blockbench to edit them, then use File > Export > Java Block/Item Model to overwrite
`src/main/resources/assets/immersive_electric_guitar/models/item/<name>_hand.json` (and save the texture to
`textures/item/<name>.png`). The 16x16 inventory icons are in `textures/item/icon/`.

## Sounds

Each instrument has `c1.ogg` … `c8.ogg` (mono, a C note in each octave) in
`src/main/resources/assets/immersive_electric_guitar/sounds/instruments/<name>/`. These tools need `ffmpeg` on PATH:

- `python tools/generate_sounds.py` synthesizes the Electric Guitar samples (Python standard library only).
- `python tools/import_acoustic_samples.py <folder>` builds the Acoustic Guitar samples from recorded notes; the
  script lists which files to download.
- `python tools/preview_melody.py <instrument> <song.mid> <out.mp3>` renders a MIDI file the way the mod plays it,
  to judge a sound without starting Minecraft.

## Credits

Acoustic Guitar samples: "Shinyguitar" by Karoryfer Samples (played and mapped by D. Smolken), released under
CC0 1.0 — https://github.com/sfzinstruments/karoryfer.shinyguitar

## License

GPL-3.0, matching Immersive Melodies, whose API it links against.
