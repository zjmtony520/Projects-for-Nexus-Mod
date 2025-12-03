namespace PetGuardian
{
    /// <summary>Config for the Pet Guardian mod.</summary>
    public class ModConfig
    {
        /// <summary>Max HP for the pet.</summary>
        public int MaxHealth { get; set; } = 100;

        /// <summary>Damage per hit when the pet attacks a monster.</summary>
        public int AttackDamage { get; set; } = 15;

        /// <summary>
        /// Attack range in tiles.
        /// The pet must get within this distance to actually deal damage.
        /// (Detection is farm-wide; this only controls bite distance.)
        /// </summary>
        public float AttackRange { get; set; } = 1.5f;

        /// <summary>Cooldown between attacks in ticks (60 ticks = 1 second).</summary>
        public int AttackCooldownTicks { get; set; } = 30;

        /// <summary>If true, pet only guards at night (after 6 pm).</summary>
        public bool OnlyAtNight { get; set; } = false;
    }
}
