using System;
using System.Linq;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Characters;
using StardewValley.Locations;
using StardewValley.Monsters;
using StardewValley.Pathfinding;

namespace PetGuardian
{
    /// <summary>
    /// Makes the farm pet automatically hunt monsters on the farm:
    /// - detects monsters anywhere on the farm
    /// - walks toward the nearest one using pathfinding
    /// - attacks only in a small configurable range
    /// - has its own HP bar and simple HP system
    /// </summary>
    public class ModEntry : Mod
    {
        private ModConfig _config = null!;
        private int _currentHealth;
        private int _attackCooldown;
        private Texture2D? _pixel; // 1x1 texture for HP bar

        // Remember current target so we don't repath every tick
        private Monster? _currentTarget;

        public override void Entry(IModHelper helper)
        {
            _config = helper.ReadConfig<ModConfig>();
            _currentHealth = _config.MaxHealth;

            helper.Events.GameLoop.DayStarted += OnDayStarted;
            helper.Events.GameLoop.UpdateTicked += OnUpdateTicked;
            helper.Events.Display.RenderedWorld += OnRenderedWorld;
        }

        /*********
        ** Helpers
        *********/
        private void EnsurePixelTexture()
        {
            if (_pixel != null)
                return;

            if (Game1.graphics is null)
                return;

            _pixel = new Texture2D(Game1.graphics.GraphicsDevice, 1, 1);
            _pixel.SetData(new[] { Color.White });
        }

        private static bool IsMonsterValid(Monster? m)
        {
            return m is not null && !m.IsInvisible && !m.isInvincible() && m.Health > 0;
        }

        /*********
        ** Events
        *********/
        private void OnDayStarted(object? sender, DayStartedEventArgs e)
        {
            // heal pet at the start of each day
            _currentHealth = _config.MaxHealth;
            _currentTarget = null;
        }

        private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
        {
            if (!Context.IsWorldReady)
                return;

            // tick down attack cooldown
            if (_attackCooldown > 0)
                _attackCooldown--;

            if (_currentHealth <= 0)
                return; // pet is "knocked out"

            if (_config.OnlyAtNight && Game1.timeOfDay < 1800)
                return;

            // always guard the main farm, regardless of where the player is
            GameLocation farmLocation = Game1.getFarm();
            if (farmLocation is not Farm farm)
                return;

            // find the pet on the farm
            Pet? pet = farm.characters.OfType<Pet>().FirstOrDefault();
            if (pet is null)
                return;

            // choose or validate current target (long-range awareness)
            Monster? target = ChooseTarget(farm, pet);
            if (target is null)
                return;

            // handle walking toward the target
            HandlePetMovement(farm, pet, target);

            // check distance in tiles for attack
            float distance = Vector2.Distance(pet.Tile, target.Tile);
            if (distance > _config.AttackRange)
                return;

            if (_attackCooldown > 0)
                return;

            // bite!
            int damage = _config.AttackDamage;
            target.takeDamage(
                damage,
                0,
                0,
                isBomb: false,
                addedPrecision: 0,
                who: Game1.player
            );

            // tiny self-chip so HP bar actually moves
            _currentHealth = Math.Max(0, _currentHealth - 1);

            _attackCooldown = _config.AttackCooldownTicks;
        }

        private void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
        {
            if (!Context.IsWorldReady)
                return;

            EnsurePixelTexture();
            if (_pixel is null)
                return;

            GameLocation farmLocation = Game1.getFarm();
            if (farmLocation is not Farm farm)
                return;

            Pet? pet = farm.characters.OfType<Pet>().FirstOrDefault();
            if (pet is null)
                return;

            if (_currentHealth <= 0)
                return;

            float ratio = Math.Clamp((float)_currentHealth / _config.MaxHealth, 0f, 1f);

            // draw just above the pet
            Vector2 worldPos = pet.Position + new Vector2(0, -Game1.tileSize / 2);
            Vector2 screenPos = Game1.GlobalToLocal(Game1.viewport, worldPos);

            const int barWidth = 40;
            const int barHeight = 6;
            int x = (int)screenPos.X - barWidth / 2;
            int y = (int)screenPos.Y;

            SpriteBatch spriteBatch = e.SpriteBatch;

            // background
            spriteBatch.Draw(
                texture: _pixel,
                destinationRectangle: new Rectangle(x, y, barWidth, barHeight),
                color: Color.Black * 0.6f
            );

            // current HP
            spriteBatch.Draw(
                texture: _pixel,
                destinationRectangle: new Rectangle(
                    x + 1,
                    y + 1,
                    (int)((barWidth - 2) * ratio),
                    barHeight - 2
                ),
                color: Color.LimeGreen
            );
        }

        /*********
        ** Targeting + movement
        *********/
        /// <summary>
        /// Pick or update the current monster target for the pet.
        /// Long-range awareness: no distance cap, pet can see any monster on the farm.
        /// </summary>
        private Monster? ChooseTarget(Farm farm, Pet pet)
        {
            // if we already have a target, check if it's still valid & on the farm
            if (IsMonsterValid(_currentTarget) && _currentTarget!.currentLocation == farm)
                return _currentTarget;

            // pick the nearest valid monster anywhere on the farm
            Monster? nearest = farm.characters
                .OfType<Monster>()
                .Where(IsMonsterValid)
                .OrderBy(m => Vector2.Distance(m.Tile, pet.Tile))
                .FirstOrDefault();

            if (nearest is null)
            {
                _currentTarget = null;
                pet.controller = null; // stop walking if there are no monsters
                return null;
            }

            _currentTarget = nearest;
            return _currentTarget;
        }

        /// <summary>
        /// Make the pet walk toward the current target using a simple pathfinder.
        /// Attack range remains small: pet must get close to attack.
        /// </summary>
        private void HandlePetMovement(Farm farm, Pet pet, Monster target)
        {
            // if close enough already, no need to re-path
            float distance = Vector2.Distance(pet.Tile, target.Tile);
            if (distance <= _config.AttackRange * 0.6f)
            {
                // let pet stop or shuffle a bit
                pet.controller = null;
                return;
            }

            // if we already have a controller heading somewhere, let it run
            if (pet.controller is not null)
                return;

            // start a new path toward the target's tile
            var targetPoint = new Point((int)target.Tile.X, (int)target.Tile.Y);

            // use positional arguments to match the PathFindController constructor
            pet.controller = new PathFindController(
                pet,        // character to move
                farm,       // location
                targetPoint,
                -1,         // finalFacingDirection
                null,       // endBehaviorFunction
                200         // limit
            );
        }
    }
}
