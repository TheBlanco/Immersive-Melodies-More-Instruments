package immersive_electric_guitar;

import immersive_melodies.Items;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.neoforged.fml.common.Mod;
import org.joml.Vector3f;

import java.util.function.Supplier;

@Mod(ElectricGuitarAddon.MOD_ID)
public final class ElectricGuitarAddon {
    public static final String MOD_ID = "immersive_electric_guitar";

    public static final ResourceLocation ELECTRIC_GUITAR_ID = locate("electric_guitar");
    public static final ResourceLocation ACOUSTIC_GUITAR_ID = locate("acoustic_guitar");

    // Registering in the mod constructor is enough: Immersive Melodies registers every entry of its
    // item map (and the matching c1..c8 sound events) in its own RegisterEvent handler, and adds
    // them to its creative tab and hand-model loader.
    public static final Supplier<Item> ELECTRIC_GUITAR = Items.register(MOD_ID, ELECTRIC_GUITAR_ID.getPath(), 300, new Vector3f(0.0f, 0.0f, 0.5f));
    public static final Supplier<Item> ACOUSTIC_GUITAR = Items.register(MOD_ID, ACOUSTIC_GUITAR_ID.getPath(), 300, new Vector3f(0.0f, 0.0f, 0.5f));

    public ElectricGuitarAddon() {
        // Static initializers above do the work; referenced here so the class is fully loaded.
    }

    public static ResourceLocation locate(String path) {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }
}
