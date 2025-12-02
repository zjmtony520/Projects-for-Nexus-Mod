using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace WeatherAlertMod
{
    /// <summary>
    /// Main entry point for the Weather Alert mod.
    /// </summary>
    public class ModEntry : Mod
    {
        private ModConfig Config;

        public override void Entry(IModHelper helper)
        {
            // load config (or create default)
            this.Config = this.Helper.ReadConfig<ModConfig>();

            // run every morning
            helper.Events.GameLoop.DayStarted += this.OnDayStarted;
        }

        /// <summary>Helper for translations.</summary>
        private string T(string key)
        {
            return this.Helper.Translation.Get(key);
        }

        /// <summary>
        /// Called at the start of each in-game day.
        /// Checks tomorrow's weather and shows an alert if enabled.
        /// </summary>
        private void OnDayStarted(object sender, DayStartedEventArgs e)
        {
            if (!this.Config.EnableMod || !Context.IsWorldReady)
                return;

            // In Stardew 1.6+, weatherForTomorrow & weather_* are STRINGS
            string weather = Game1.weatherForTomorrow;
            string msgKey = null;

            switch (weather)
            {
                case string w when w == Game1.weather_rain:
                    if (!this.Config.AlertOnRain)
                        return;
                    msgKey = "weather.rain";
                    break;

                case string w when w == Game1.weather_lightning:
                    if (!this.Config.AlertOnStorm)
                        return;
                    msgKey = "weather.storm";
                    break;

                case string w when w == Game1.weather_snow:
                    if (!this.Config.AlertOnSnow)
                        return;
                    msgKey = "weather.snow";
                    break;

                case string w when w == Game1.weather_debris:
                    if (!this.Config.AlertOnWind)
                        return;
                    msgKey = "weather.wind";
                    break;

                case string w when w == Game1.weather_festival:
                    if (!this.Config.AlertOnFestival)
                        return;
                    msgKey = "weather.festival";
                    break;

                default:
                    // sunny / wedding / unknown -> no alert
                    return;
            }

            string msg = this.T(msgKey);
            this.ShowMessage(msg);
        }

        /// <summary>Shows the message as HUD toast or popup dialogue.</summary>
        private void ShowMessage(string text)
        {
            if (this.Config.UsePopupDialogue)
            {
                Game1.drawObjectDialogue(text);
            }
            else
            {
                Game1.addHUDMessage(new HUDMessage(text, HUDMessage.newQuest_type));
            }

            this.Monitor.Log($"Weather alert shown: {text}", LogLevel.Info);
        }
    }

    /// <summary>
    /// Configuration options saved to config.json.
    /// </summary>
    public class ModConfig
    {
        /// <summary>Master on/off switch.</summary>
        public bool EnableMod { get; set; } = true;

        /// <summary>Show alert if it will rain tomorrow.</summary>
        public bool AlertOnRain { get; set; } = true;

        /// <summary>Show alert if there will be a storm (lightning) tomorrow.</summary>
        public bool AlertOnStorm { get; set; } = true;

        /// <summary>Show alert if it will snow tomorrow.</summary>
        public bool AlertOnSnow { get; set; } = true;

        /// <summary>Show alert if it will be windy / debris tomorrow.</summary>
        public bool AlertOnWind { get; set; } = false;

        /// <summary>Show alert if tomorrow is a festival.</summary>
        public bool AlertOnFestival { get; set; } = false;

        /// <summary>If true, use a big dialogue popup. If false, use a small HUD toast.</summary>
        public bool UsePopupDialogue { get; set; } = false;
    }
}
