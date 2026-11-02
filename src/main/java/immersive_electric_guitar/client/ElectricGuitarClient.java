package immersive_electric_guitar.client;

import immersive_electric_guitar.ElectricGuitarAddon;
import immersive_melodies.client.animation.ItemAnimators;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.common.Mod;

@Mod(value = ElectricGuitarAddon.MOD_ID, dist = Dist.CLIENT)
public final class ElectricGuitarClient {
    public ElectricGuitarClient() {
        // Animators touch client-only model classes, so they are registered from the client entrypoint only
        ItemAnimators.register(ElectricGuitarAddon.ELECTRIC_GUITAR_ID, new ElectricGuitarAnimator());
    }
}
