using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Characters;
using StardewValley.Objects;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Xml.Linq;

namespace TalkingHorse
{
    public sealed class ModEntry : Mod
    {
        // how often the horse is allowed to speak (in seconds)
        private const int SpeechCooldownSeconds = 12;

        // how often we check riding state (in ticks)
        private const int TicksBetweenChecks = 12;

        private readonly Random _random = new();
        private readonly List<string> _lines = new();

        private bool _wasRidingLastTick;
        private int _quietDay = -1;
        private double _lastSpeechTime;

        private ITranslationHelper T => Helper.Translation;

        public override void Entry(IModHelper helper)
        {
            helper.Events.GameLoop.DayStarted += OnDayStarted;
            helper.Events.GameLoop.UpdateTicked += OnUpdateTicked;
            helper.Events.Input.ButtonPressed += OnButtonPressed;

            Monitor.Log("Talking Horse loaded.", LogLevel.Info);
        }

        // ===================== Events =====================

        private void OnDayStarted(object? sender, DayStartedEventArgs e)
        {
            _quietDay = -1;
            _lastSpeechTime = 0;
            _wasRidingLastTick = false;

            LoadLines();

            Monitor.Log("New day: reset quiet state & cooldown.", LogLevel.Trace);
        }

        private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
        {
            if (!Context.IsWorldReady)
                return;

            // only run this logic every N ticks
            if (!e.IsMultipleOf(TicksBetweenChecks))
                return;

            bool isRiding = Game1.player?.mount is Horse;

            // detect mount / dismount transitions
            if (Game1.player?.mount is Horse && !_wasRidingLastTick)
            {
                Monitor.Log("Detected mount: player just started riding.", LogLevel.Trace);
                SayGreetingLineToPlayer();
            }
            else if (!isRiding && _wasRidingLastTick)
            {
                Monitor.Log("Player stopped riding.", LogLevel.Trace);
            }

            _wasRidingLastTick = isRiding;

            // talk while riding
            if (isRiding && !IsQuietToday() && CanSpeakNow())
                SayRandomLineToPlayer();
        }

        private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
        {
            if (!Context.IsWorldReady)
                return;

            // left- or right-click only
            if (!e.Button.IsUseToolButton() && !e.Button.IsActionButton())
                return;

            GameLocation? loc = Game1.currentLocation;
            if (loc is null)
                return;

            Vector2 tile = e.Cursor.GrabTile;

            // find a horse whose tile matches the clicked tile
            Horse? horse = loc.characters
                .OfType<Horse>()
                .FirstOrDefault(h =>
                    (int)(h.Position.X / Game1.tileSize) == (int)tile.X &&
                    (int)(h.Position.Y / Game1.tileSize) == (int)tile.Y);

            if (horse is null)
                return;

            Monitor.Log($"Horse clicked at tile {tile}.", LogLevel.Trace);

            // if holding mayonnaise, bribe horse to be quiet for the day
            if (TryConsumeMayonnaise(Game1.player))
            {
                QuietHorseForDay();
            }
        }

        // ===================== Core logic =====================

        private void LoadLines()
        {
            _lines.Clear();

            // load horse lines from i18n; stop when a key is missing
            for (int i = 1; i <= 50; i++)
            {
                string key = $"horse.line{i}";
                string text = T.Get(key);

                if (text == key) // missing translation → stop
                    break;

                _lines.Add(text);
            }

            Monitor.Log($"Loaded {_lines.Count} horse lines.", LogLevel.Trace);
        }

        private bool IsQuietToday()
        {
            return _quietDay == Game1.dayOfMonth;
        }

        private void QuietHorseForDay()
        {
            _quietDay = Game1.dayOfMonth;

            Monitor.Log("Horse bribed with mayonnaise. It will stay quiet today.", LogLevel.Info);

            // short confirmation to the player
            ShowHud(T.Get("horse.quiet")); // add this key in i18n
        }

        private bool CanSpeakNow()
        {
            double now = Game1.currentGameTime?.TotalGameTime.TotalSeconds ?? 0;
            return now - _lastSpeechTime >= SpeechCooldownSeconds;
        }

        private void TouchCooldown()
        {
            _lastSpeechTime = Game1.currentGameTime?.TotalGameTime.TotalSeconds ?? 0;
        }

        private void SayGreetingLineToPlayer()
        {
            // separate greeting key; if missing, fall back to a random line
            string text = T.Get("horse.greeting");
            if (text == "horse.greeting" || string.IsNullOrWhiteSpace(text))
            {
                SayRandomLineToPlayer();
                return;
            }

            TouchCooldown();
            Monitor.Log("Spoke greeting line on mount.", LogLevel.Trace);

            ShowHud(text);
        }

        private void SayRandomLineToPlayer()
        {
            if (_lines.Count == 0)
                return;

            int index = _random.Next(_lines.Count);
            string text = _lines[index];

            TouchCooldown();
            Monitor.Log("Spoke random riding line.", LogLevel.Trace);

            ShowHud(text);
        }

        private void ShowHud(string text)
        {
            // simple text popup; no icon
            Game1.addHUDMessage(new HUDMessage(text)
            {
                noIcon = true
            });
        }

        private bool TryConsumeMayonnaise(Farmer player)
        {
            // Mayo object ID: 306 (vanilla)
            const int MayonnaiseId = 306;

            for (int i = 0; i < player.Items.Count; i++)
            {
                if (player.Items[i] is SObject obj && obj.ParentSheetIndex == MayonnaiseId)
                {
                    obj.Stack--;
                    if (obj.Stack <= 0)
                        player.Items[i] = null;

                    Monitor.Log("Consumed mayonnaise to bribe horse.", LogLevel.Trace);
                    return true;
                }
            }

            ShowHud(T.Get("horse.need-mayo")); // “You need mayonnaise to bribe your horse!” etc.
            return false;
        }
    }
}
