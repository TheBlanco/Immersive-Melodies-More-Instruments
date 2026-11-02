package immersive_electric_guitar.client;

import immersive_melodies.client.MelodyProgress;
import immersive_melodies.client.animation.accessors.ModelAccessor;
import immersive_melodies.client.animation.animators.Animator;
import net.minecraft.world.entity.Entity;

public class ElectricGuitarAnimator implements Animator {
    @Override
    public <T extends Entity> void setAngles(ModelAccessor<T> accessor, MelodyProgress progress, float time) {
        // Free hand slides along the neck with the current pitch and presses in a little on each note
        float press = (1.0f - Math.min(progress.delta(), 200) / 200.0f) * progress.getCurrentVolume() * 0.1f;
        accessor.leftArmPitch(-0.6f - press);
        accessor.leftArmRoll(-0.2f);
        accessor.leftArmYaw((progress.getCurrentPitch() - 0.5f) * 0.8f - 0.5f);

        // The arm holding the guitar stays fixed, otherwise the whole instrument bobs with it
        accessor.rightArmPitch(-0.75f);
        accessor.rightArmYaw(0.1f);
        accessor.rightArmRoll(-0.2f);
    }
}
