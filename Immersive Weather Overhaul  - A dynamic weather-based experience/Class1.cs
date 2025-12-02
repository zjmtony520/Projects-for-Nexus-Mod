using System;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Buffs;
using StardewValley.Menus;

namespace WeatherBuffs
{
    internal enum WeatherBuffType
    {
        None,
        Rain,
        Storm,
        SunnySummer,
        Snow,
        Windy
    }

    public class ModEntry : Mod
    {
        // match your manifest UniqueID prefix
        private const string WeatherBuffId = "ZeroXPatch.WeatherBuffs/WeatherBuff";

        private WeatherBuffType _currentBuffType = WeatherBuffType.None;
        private int _ticksSinceLastWeatherCheck;
        private Rectangle _iconRect;

        public override void Entry(IModHelper helper)
        {
            helper.Events.GameLoop.SaveLoaded += OnSaveLoaded;
            helper.Events.GameLoop.DayStarted += OnDayStarted;
            helper.Events.GameLoop.UpdateTicked += OnUpdateTicked;
            helper.Events.Display.RenderedHud += OnRenderedHud;
        }

        private void OnSaveLoaded(object sender, SaveLoadedEventArgs e)
        {
            _currentBuffType = WeatherBuffType.None;
            _ticksSinceLastWeatherCheck = 0;
            RefreshWeatherBuff();
        }

        private void OnDayStarted(object sender, DayStartedEventArgs e)
        {
            _currentBuffType = WeatherBuffType.None;
            _ticksSinceLastWeatherCheck = 0;
            RefreshWeatherBuff();
        }

        private void OnUpdateTicked(object sender, UpdateTickedEventArgs e)
        {
            if (!Context.IsWorldReady)
                return;

            _ticksSinceLastWeatherCheck++;

            // check for weather changes roughly once per second (handles Rain Totem etc.)
            if (_ticksSinceLastWeatherCheck >= 60)
            {
                _ticksSinceLastWeatherCheck = 0;
                RefreshWeatherBuff();
            }
        }

        /// <summary>Recalculate which weather buff should be active and apply it if needed.</summary>
        private void RefreshWeatherBuff()
        {
            if (!Context.IsWorldReady || Game1.player == null)
                return;

            WeatherBuffType newType = DetermineWeatherBuffType();
            if (newType == _currentBuffType)
                return;

            _currentBuffType = newType;
            ApplyBuffForCurrentWeather();
        }

        /// <summary>Decide which buff type should be active based on current weather.</summary>
        private WeatherBuffType DetermineWeatherBuffType()
        {
            // priority: Storm > Rain > Snow > Windy > SunnySummer > None

            if (Game1.isLightning)
                return WeatherBuffType.Storm;

            if (Game1.isRaining)
                return WeatherBuffType.Rain;

            if (Game1.isSnowing)
                return WeatherBuffType.Snow;

            if (Game1.isDebrisWeather)
                return WeatherBuffType.Windy;

            bool isSunnySummer =
                string.Equals(Game1.currentSeason, "summer", StringComparison.OrdinalIgnoreCase)
                && !Game1.isRaining
                && !Game1.isLightning
                && !Game1.isSnowing
                && !Game1.isDebrisWeather;

            if (isSunnySummer)
                return WeatherBuffType.SunnySummer;

            return WeatherBuffType.None;
        }

        /// <summary>Apply the actual stat buff (via BuffEffects) for the current weather.</summary>
        private void ApplyBuffForCurrentWeather()
        {
            if (!Context.IsWorldReady || Game1.player == null)
                return;

            BuffEffects effects = new BuffEffects();
            string displayName;
            string description;

            switch (_currentBuffType)
            {
                case WeatherBuffType.Rain:
                    // Rain: +2 Fishing, +1 Farming, -2 Foraging
                    effects.FishingLevel.Add(2);
                    effects.FarmingLevel.Add(1);
                    effects.ForagingLevel.Add(-2);

                    displayName = Helper.Translation.Get("buff.rain.name");
                    description = Helper.Translation.Get("buff.rain.description");
                    break;

                case WeatherBuffType.Storm:
                    // Storm: +2 Mining, +1 Combat, -2 Farming
                    effects.MiningLevel.Add(2);
                    effects.CombatLevel.Add(1);
                    effects.FarmingLevel.Add(-2);

                    displayName = Helper.Translation.Get("buff.storm.name");
                    description = Helper.Translation.Get("buff.storm.description");
                    break;

                case WeatherBuffType.SunnySummer:
                    // Sunny Summer: +2 Farming, +1 Foraging, -2 Fishing
                    effects.FarmingLevel.Add(2);
                    effects.ForagingLevel.Add(1);
                    effects.FishingLevel.Add(-2);

                    displayName = Helper.Translation.Get("buff.sunny.name");
                    description = Helper.Translation.Get("buff.sunny.description");
                    break;

                case WeatherBuffType.Snow:
                    // Snow: +1 Mining, +1 Luck, -1 Fishing
                    effects.MiningLevel.Add(1);
                    effects.LuckLevel.Add(1);
                    effects.FishingLevel.Add(-1);

                    displayName = Helper.Translation.Get("buff.snow.name");
                    description = Helper.Translation.Get("buff.snow.description");
                    break;

                case WeatherBuffType.Windy:
                    // Windy: +2 Foraging, -1 Combat
                    effects.ForagingLevel.Add(2);
                    effects.CombatLevel.Add(-1);

                    displayName = Helper.Translation.Get("buff.windy.name");
                    description = Helper.Translation.Get("buff.windy.description");
                    break;

                case WeatherBuffType.None:
                default:
                    displayName = Helper.Translation.Get("buff.none.name");
                    description = Helper.Translation.Get("buff.none.description");
                    break;
            }

            Buff buff = CreateWeatherBuff(displayName, description, effects);
            Game1.player.applyBuff(buff);
        }

        /// <summary>Create a hidden buff instance with our shared ID for this mod.</summary>
        private Buff CreateWeatherBuff(string displayName, string description, BuffEffects effects)
        {
            Buff buff = new Buff(
                id: WeatherBuffId,
                displayName: displayName,
                description: description,
                iconTexture: Game1.mouseCursors,
                iconSheetIndex: 0,
                duration: Buff.ENDLESS,
                effects: effects
            );

            // we draw our own HUD icon, so hide the default vanilla buff icon
            buff.visible = false;
            return buff;
        }

        /// <summary>Draw the small weather buff icon & tooltip near the clock.</summary>
        private void OnRenderedHud(object sender, RenderedHudEventArgs e)
        {
            if (!Context.IsWorldReady || Game1.player == null)
                return;

            if (_currentBuffType == WeatherBuffType.None)
                return;

            if (Game1.eventUp || Game1.currentLocation == null)
                return;

            SpriteBatch spriteBatch = e.SpriteBatch;

            float scale = Game1.options.uiScale;
            int iconSize = (int)(32 * scale);
            int margin = (int)(8 * scale);

            int x = Game1.uiViewport.Width - iconSize - margin;
            int y = margin; // near the clock

            _iconRect = new Rectangle(x, y, iconSize, iconSize);

            // Background square (slightly transparent)
            spriteBatch.Draw(Game1.fadeToBlackRect, _iconRect, Color.Black * 0.35f);

            // Inner square
            Rectangle inner = new Rectangle(
                x + iconSize / 8,
                y + iconSize / 8,
                iconSize * 3 / 4,
                iconSize * 3 / 4
            );
            spriteBatch.Draw(Game1.fadeToBlackRect, inner, Color.White * 0.8f);

            // Label (R / ⚡ / ☀ / ❄ / W)
            string label = GetBuffIconLabel();
            Vector2 textSize = Game1.smallFont.MeasureString(label);
            Vector2 textPos = new Vector2(
                x + (iconSize - textSize.X) / 2f,
                y + (iconSize - textSize.Y) / 2f
            );
            spriteBatch.DrawString(Game1.smallFont, label, textPos, Color.Black);

            // Tooltip when hovered
            Point mouse = Game1.getMousePosition();
            if (_iconRect.Contains(mouse))
            {
                string tooltip = GetBuffTooltip();
                IClickableMenu.drawHoverText(spriteBatch, tooltip, Game1.smallFont);
            }
        }

        private string GetBuffIconLabel()
        {
            switch (_currentBuffType)
            {
                case WeatherBuffType.Rain:
                    return "R";     // Rain
                case WeatherBuffType.Storm:
                    return "⚡";    // Storm
                case WeatherBuffType.SunnySummer:
                    return "☀";    // Sunny
                case WeatherBuffType.Snow:
                    return "❄";    // Snow
                case WeatherBuffType.Windy:
                    return "W";    // Windy
                default:
                    return "";
            }
        }

        private string GetBuffTooltip()
        {
            switch (_currentBuffType)
            {
                case WeatherBuffType.Rain:
                    return Helper.Translation.Get("tooltip.rain");

                case WeatherBuffType.Storm:
                    return Helper.Translation.Get("tooltip.storm");

                case WeatherBuffType.SunnySummer:
                    return Helper.Translation.Get("tooltip.sunny");

                case WeatherBuffType.Snow:
                    return Helper.Translation.Get("tooltip.snow");

                case WeatherBuffType.Windy:
                    return Helper.Translation.Get("tooltip.windy");

                default:
                    return Helper.Translation.Get("tooltip.none");
            }
        }
    }
}
