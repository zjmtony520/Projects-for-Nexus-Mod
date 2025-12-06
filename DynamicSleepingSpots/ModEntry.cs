using System;
using System.Collections.Generic;
using System.Linq;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Locations;
using StardewValley.Tools;

namespace DynamicSleepingSpots
{
    public class ModEntry : Mod
    {
        private readonly Random random = new();

        private ModConfig Config = new();
        private SaveData SaveData = new();
        private List<RescueProfile> Profiles = new();

        /// <summary>
        /// Tracks the last known location type for each farmer before 2:00 AM.
        /// This is used as the 'collapse location' instead of where they wake up (home).
        /// </summary>
        private readonly Dictionary<long, CollapseLocationType> LastPrePassOutLocationByFarmer = new();

        public override void Entry(IModHelper helper)
        {
            this.Config = helper.ReadConfig<ModConfig>();
            this.SaveData = new SaveData(); // real save data is loaded after a save is loaded
            this.InitializeProfiles();

            helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
            helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;
            helper.Events.GameLoop.DayEnding += this.OnDayEnding;
            helper.Events.GameLoop.DayStarted += this.OnDayStarted;
            helper.Events.GameLoop.Saving += this.OnSaving;
            helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;
        }

        private void OnGameLaunched(object? sender, GameLaunchedEventArgs e)
        {
            this.RegisterGmcm();
        }

        private void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
        {
            this.SaveData = this.Helper.Data.ReadSaveData<SaveData>("collapse-data") ?? new SaveData();
            this.LastPrePassOutLocationByFarmer.Clear();
        }

        private void OnSaving(object? sender, SavingEventArgs e)
        {
            this.Helper.Data.WriteSaveData("collapse-data", this.SaveData);
        }

        /// <summary>
        /// Every tick before 2:00 AM, remember each farmer's current location type.
        /// After 2:00 AM, we stop updating so we keep the last "real" location where they were awake.
        /// </summary>
        private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
        {
            if (!Context.IsWorldReady)
                return;

            // Once time hits 2:00 (2600), we don't want to overwrite the last pre-pass-out location.
            if (Game1.timeOfDay >= 2600)
                return;

            foreach (Farmer farmer in Game1.getOnlineFarmers())
            {
                CollapseLocationType type = this.GetCollapseLocationType(farmer.currentLocation);
                this.LastPrePassOutLocationByFarmer[farmer.UniqueMultiplayerID] = type;
            }
        }

        private void OnDayEnding(object? sender, DayEndingEventArgs e)
        {
            if (!this.Config.EnableMod || !Context.IsWorldReady)
                return;

            foreach (Farmer farmer in Game1.getOnlineFarmers())
            {
                // if the farmer is in bed at day end, we treat it as a normal sleep (no collapse)
                if (farmer.isInBed.Value)
                    continue;

                // Prefer the last pre-pass-out location we tracked earlier in the night.
                CollapseLocationType locationType;
                if (!this.LastPrePassOutLocationByFarmer.TryGetValue(farmer.UniqueMultiplayerID, out locationType))
                {
                    // Fallback: use their current location if we somehow didn't track them earlier.
                    locationType = this.GetCollapseLocationType(farmer.currentLocation);
                }

                CollapseSeverity severity = Game1.timeOfDay < 2600
                    ? CollapseSeverity.Mild
                    : CollapseSeverity.Severe;

                this.SaveData.CollapseByFarmer[farmer.UniqueMultiplayerID] = new CollapseRecord
                {
                    LocationType = locationType,
                    Severity = severity,
                    Day = Game1.Date.TotalDays,
                    Processed = false,
                };
            }
        }

        private void OnDayStarted(object? sender, DayStartedEventArgs e)
        {
            if (!this.Config.EnableMod || !Context.IsWorldReady)
                return;

            // new day, reset tracking for pre-pass-out locations
            this.LastPrePassOutLocationByFarmer.Clear();

            foreach (Farmer farmer in Game1.getOnlineFarmers())
            {
                if (!this.SaveData.CollapseByFarmer.TryGetValue(farmer.UniqueMultiplayerID, out CollapseRecord? record))
                    continue;

                if (record.Processed || record.Day != Game1.Date.TotalDays - 1)
                    continue;

                this.ApplyRescueOutcome(farmer, record);
                record.Processed = true;
                this.SaveData.CollapseByFarmer[farmer.UniqueMultiplayerID] = record;
            }
        }

        private void RegisterGmcm()
        {
            var gmcm = this.Helper.ModRegistry.GetApi<IGenericModConfigMenuApi>("spacechase0.GenericModConfigMenu");
            if (gmcm is null)
                return;

            gmcm.Register(this.ModManifest, () => this.Config = new ModConfig(), () => this.Helper.WriteConfig(this.Config));

            // --- Main toggle + intensity ---
            gmcm.AddSectionTitle(
                this.ModManifest,
                () => this.Helper.Translation.Get("config.enableMod.name"),
                () => this.Helper.Translation.Get("config.enableMod.tooltip")
            );

            gmcm.AddBoolOption(
                this.ModManifest,
                () => this.Config.EnableMod,
                value => this.Config.EnableMod = value,
                () => this.Helper.Translation.Get("config.enableMod.name"),
                () => this.Helper.Translation.Get("config.enableMod.tooltip")
            );

            // Intensity as a number option: 0 = Soft, 1 = Hard
            gmcm.AddNumberOption(
                this.ModManifest,
                () => this.Config.Intensity == PenaltyIntensity.Soft ? 0 : 1,
                value => this.Config.Intensity = value <= 0 ? PenaltyIntensity.Soft : PenaltyIntensity.Hard,
                () => this.Helper.Translation.Get("config.intensity.name"),
                () => this.Helper.Translation.Get("config.intensity.tooltip"),
                min: 0,
                max: 1,
                interval: 1,
                formatValue: value => value == 0 ? PenaltyIntensity.Soft.ToString() : PenaltyIntensity.Hard.ToString()
            );

            // --- Penalty toggles ---
            gmcm.AddSectionTitle(
                this.ModManifest,
                () => "Penalties",
                () => this.Helper.Translation.Get("config.penalties.tooltip")
            );

            gmcm.AddBoolOption(
                this.ModManifest,
                () => this.Config.EnableGoldPenalties,
                value => this.Config.EnableGoldPenalties = value,
                () => this.Helper.Translation.Get("config.gold.name"),
                () => this.Helper.Translation.Get("config.gold.tooltip")
            );

            gmcm.AddBoolOption(
                this.ModManifest,
                () => this.Config.EnableItemPenalties,
                value => this.Config.EnableItemPenalties = value,
                () => this.Helper.Translation.Get("config.items.name"),
                () => this.Helper.Translation.Get("config.items.tooltip")
            );

            gmcm.AddBoolOption(
                this.ModManifest,
                () => this.Config.EnableXPPenalties,
                value => this.Config.EnableXPPenalties = value,
                () => this.Helper.Translation.Get("config.xp.name"),
                () => this.Helper.Translation.Get("config.xp.tooltip")
            );

            // --- Gold settings ---
            gmcm.AddNumberOption(
                this.ModManifest,
                () => this.Config.MaxGoldLoss,
                value => this.Config.MaxGoldLoss = value,
                () => this.Helper.Translation.Get("config.maxgold.name"),
                () => this.Helper.Translation.Get("config.maxgold.tooltip"),
                min: 0,
                max: 100000,
                interval: 100
            );

            gmcm.AddNumberOption(
                this.ModManifest,
                () => (int)(this.Config.BaseGoldLossFarm * 100),
                value => this.Config.BaseGoldLossFarm = value / 100f,
                () => this.Helper.Translation.Get("config.basegold.farm"),
                () => this.Helper.Translation.Get("config.basegold.farm.tooltip"),
                min: 0,
                max: 100
            );

            gmcm.AddNumberOption(
                this.ModManifest,
                () => (int)(this.Config.BaseGoldLossTown * 100),
                value => this.Config.BaseGoldLossTown = value / 100f,
                () => this.Helper.Translation.Get("config.basegold.town"),
                () => this.Helper.Translation.Get("config.basegold.town.tooltip"),
                min: 0,
                max: 100
            );

            gmcm.AddNumberOption(
                this.ModManifest,
                () => (int)(this.Config.BaseGoldLossMines * 100),
                value => this.Config.BaseGoldLossMines = value / 100f,
                () => this.Helper.Translation.Get("config.basegold.mines"),
                () => this.Helper.Translation.Get("config.basegold.mines.tooltip"),
                min: 0,
                max: 100
            );

            gmcm.AddNumberOption(
                this.ModManifest,
                () => (int)(this.Config.BaseGoldLossDesert * 100),
                value => this.Config.BaseGoldLossDesert = value / 100f,
                () => this.Helper.Translation.Get("config.basegold.desert"),
                () => this.Helper.Translation.Get("config.basegold.desert.tooltip"),
                min: 0,
                max: 100
            );

            gmcm.AddNumberOption(
                this.ModManifest,
                () => (int)(this.Config.BaseGoldLossHome * 100),
                value => this.Config.BaseGoldLossHome = value / 100f,
                () => this.Helper.Translation.Get("config.basegold.home"),
                () => this.Helper.Translation.Get("config.basegold.home.tooltip"),
                min: 0,
                max: 100
            );

            gmcm.AddNumberOption(
                this.ModManifest,
                () => (int)(this.Config.BaseGoldLossOther * 100),
                value => this.Config.BaseGoldLossOther = value / 100f,
                () => this.Helper.Translation.Get("config.basegold.other"),
                () => this.Helper.Translation.Get("config.basegold.other.tooltip"),
                min: 0,
                max: 100
            );

            // --- XP settings ---
            gmcm.AddNumberOption(
                this.ModManifest,
                () => this.Config.BaseXpLossFarming,
                value => this.Config.BaseXpLossFarming = value,
                () => this.Helper.Translation.Get("config.basexp.farming"),
                () => this.Helper.Translation.Get("config.basexp.farming.tooltip"),
                min: 0,
                max: 500
            );

            gmcm.AddNumberOption(
                this.ModManifest,
                () => this.Config.BaseXpLossCombat,
                value => this.Config.BaseXpLossCombat = value,
                () => this.Helper.Translation.Get("config.basexp.combat"),
                () => this.Helper.Translation.Get("config.basexp.combat.tooltip"),
                min: 0,
                max: 500
            );

            gmcm.AddNumberOption(
                this.ModManifest,
                () => this.Config.BaseXpLossForaging,
                value => this.Config.BaseXpLossForaging = value,
                () => this.Helper.Translation.Get("config.basexp.foraging"),
                () => this.Helper.Translation.Get("config.basexp.foraging.tooltip"),
                min: 0,
                max: 500
            );

            gmcm.AddNumberOption(
                this.ModManifest,
                () => this.Config.BaseXpLossGeneric,
                value => this.Config.BaseXpLossGeneric = value,
                () => this.Helper.Translation.Get("config.basexp.generic"),
                () => this.Helper.Translation.Get("config.basexp.generic.tooltip"),
                min: 0,
                max: 500
            );

            // --- Item loss settings ---
            gmcm.AddNumberOption(
                this.ModManifest,
                () => this.Config.BaseExtraItemsLostMines,
                value => this.Config.BaseExtraItemsLostMines = value,
                () => this.Helper.Translation.Get("config.baseitems.mines"),
                () => this.Helper.Translation.Get("config.baseitems.mines.tooltip"),
                min: 0,
                max: 10
            );

            gmcm.AddNumberOption(
                this.ModManifest,
                () => this.Config.BaseExtraItemsLostDesert,
                value => this.Config.BaseExtraItemsLostDesert = value,
                () => this.Helper.Translation.Get("config.baseitems.desert"),
                () => this.Helper.Translation.Get("config.baseitems.desert.tooltip"),
                min: 0,
                max: 10
            );

            // --- Misc ---
            gmcm.AddBoolOption(
                this.ModManifest,
                () => this.Config.LogToConsole,
                value => this.Config.LogToConsole = value,
                () => this.Helper.Translation.Get("config.log"),
                () => this.Helper.Translation.Get("config.log.tooltip")
            );
        }

        private void InitializeProfiles()
        {
            this.Profiles = new List<RescueProfile>
            {
                new RescueProfile
                {
                    Id = "HarveyClinic",
                    DisplayName = "Harvey & Clinic",
                    FlavorKey = "rescuer.harvey",
                    EligibleLocations = new HashSet<CollapseLocationType>
                    {
                        CollapseLocationType.Town,
                        CollapseLocationType.OtherOutdoors,
                        CollapseLocationType.Mines,
                        CollapseLocationType.Desert
                    },
                    NpcName = "Harvey",
                    GoldLossMultiplierSoft = 1.2f,
                    GoldLossMultiplierHard = 1.5f,
                    ExtraItemsLostSoft = 0,
                    ExtraItemsLostHard = 0,
                    XpLossSoft = 5,
                    XpLossHard = 10,
                },
                new RescueProfile
                {
                    Id = "Linus",
                    DisplayName = "Linus",
                    FlavorKey = "rescuer.linus",
                    EligibleLocations = new HashSet<CollapseLocationType>
                    {
                        CollapseLocationType.Town,
                        CollapseLocationType.OtherOutdoors,
                        CollapseLocationType.Mines,
                    },
                    NpcName = "Linus",
                    GoldLossMultiplierSoft = 0.2f,
                    GoldLossMultiplierHard = 0.4f,
                    ExtraItemsLostSoft = 0,
                    ExtraItemsLostHard = 0,
                    XpLossSoft = 0,
                    XpLossHard = 5,
                },
                new RescueProfile
                {
                    Id = "JojaSecurity",
                    DisplayName = "Joja Security",
                    FlavorKey = "rescuer.joja",
                    EligibleLocations = new HashSet<CollapseLocationType>
                    {
                        CollapseLocationType.Town,
                        CollapseLocationType.Desert,
                        CollapseLocationType.OtherOutdoors
                    },
                    NpcName = null,
                    GoldLossMultiplierSoft = 0.9f,
                    GoldLossMultiplierHard = 1.1f,
                    ExtraItemsLostSoft = 0,
                    ExtraItemsLostHard = 1,
                    XpLossSoft = 8,
                    XpLossHard = 15,
                },
                new RescueProfile
                {
                    Id = "AdventurersGuild",
                    DisplayName = "Adventurer's Guild",
                    FlavorKey = "rescuer.guild",
                    EligibleLocations = new HashSet<CollapseLocationType>
                    {
                        CollapseLocationType.Mines,
                        CollapseLocationType.Desert
                    },
                    NpcName = "Marlon",
                    GoldLossMultiplierSoft = 0.8f,
                    GoldLossMultiplierHard = 1.0f,
                    ExtraItemsLostSoft = 1,
                    ExtraItemsLostHard = 2,
                    XpLossSoft = 15,
                    XpLossHard = 25,
                },
                new RescueProfile
                {
                    Id = "SpouseRescue",
                    DisplayName = "Spouse",
                    FlavorKey = "rescuer.spouse",
                    EligibleLocations = new HashSet<CollapseLocationType>
                    {
                        CollapseLocationType.Farm,
                        CollapseLocationType.Home
                    },
                    RequiresSpouse = true,
                    NpcName = null,
                    GoldLossMultiplierSoft = 0.0f,
                    GoldLossMultiplierHard = 0.1f,
                    ExtraItemsLostSoft = 0,
                    ExtraItemsLostHard = 0,
                    XpLossSoft = 0,
                    XpLossHard = 5,
                },
                new RescueProfile
                {
                    Id = "Junimos",
                    DisplayName = "Junimos",
                    FlavorKey = "rescuer.junimos",
                    EligibleLocations = new HashSet<CollapseLocationType>
                    {
                        CollapseLocationType.Farm,
                        CollapseLocationType.Town,
                        CollapseLocationType.OtherOutdoors
                    },
                    NpcName = null,
                    GoldLossMultiplierSoft = 0.0f,
                    GoldLossMultiplierHard = 0.2f,
                    ExtraItemsLostSoft = 0,
                    ExtraItemsLostHard = 0,
                    XpLossSoft = 0,
                    XpLossHard = 5,
                },
                new RescueProfile
                {
                    Id = "WakeWhereYouFell",
                    DisplayName = "Where You Fell",
                    FlavorKey = "rescuer.wake",
                    EligibleLocations = new HashSet<CollapseLocationType>
                    {
                        CollapseLocationType.Farm,
                        CollapseLocationType.Home,
                        CollapseLocationType.Town,
                        CollapseLocationType.Mines,
                        CollapseLocationType.Desert,
                        CollapseLocationType.OtherOutdoors
                    },
                    NpcName = null,
                    GoldLossMultiplierSoft = 0.2f,
                    GoldLossMultiplierHard = 0.5f,
                    ExtraItemsLostSoft = 0,
                    ExtraItemsLostHard = 1,
                    XpLossSoft = 15,
                    XpLossHard = 30,
                }
            };
        }

        private void ApplyRescueOutcome(Farmer farmer, CollapseRecord record)
        {
            RescueProfile profile = this.ChooseRescueProfile(farmer, record);
            int goldLost = this.ApplyGoldPenalty(farmer, record, profile);
            int itemsLost = this.ApplyItemPenalty(farmer, record, profile);
            int xpLost = this.ApplyXpPenalty(farmer, record, profile);

            string message = this.BuildMessage(profile, goldLost, itemsLost, xpLost, record.Severity);
            Game1.addHUDMessage(new HUDMessage(message, HUDMessage.newQuest_type) { timeLeft = 5000 });

            if (this.Config.LogToConsole)
            {
                this.Monitor.Log($"Collapse story for {farmer.Name}: {profile.Id} at {record.LocationType}, severity {record.Severity}, -{goldLost}g, -{itemsLost} items, -{xpLost} XP.", LogLevel.Info);
            }
        }

        private RescueProfile ChooseRescueProfile(Farmer farmer, CollapseRecord record)
        {
            List<RescueProfile> eligible = this.Profiles
                .Where(p => p.IsEligible(farmer, record.LocationType))
                .ToList();

            if (eligible.Count == 0)
                return this.Profiles.First(p => p.Id == "WakeWhereYouFell");

            // simple weighting: favor Harvey in town, guild in mines
            if (record.LocationType == CollapseLocationType.Mines)
            {
                RescueProfile? guild = eligible.FirstOrDefault(p => p.Id == "AdventurersGuild");
                if (guild != null && this.random.NextDouble() < 0.6)
                    return guild;
            }

            if (record.LocationType == CollapseLocationType.Town)
            {
                RescueProfile? harvey = eligible.FirstOrDefault(p => p.Id == "HarveyClinic");
                if (harvey != null && this.random.NextDouble() < 0.6)
                    return harvey;
            }

            int index = this.random.Next(eligible.Count);
            return eligible[index];
        }

        private int ApplyGoldPenalty(Farmer farmer, CollapseRecord record, RescueProfile profile)
        {
            if (!this.Config.EnableGoldPenalties)
                return 0;

            float basePercent = record.LocationType switch
            {
                CollapseLocationType.Farm => this.Config.BaseGoldLossFarm,
                CollapseLocationType.Home => this.Config.BaseGoldLossHome,
                CollapseLocationType.Mines => this.Config.BaseGoldLossMines,
                CollapseLocationType.Desert => this.Config.BaseGoldLossDesert,
                CollapseLocationType.Town => this.Config.BaseGoldLossTown,
                _ => this.Config.BaseGoldLossOther,
            };

            float severityFactor = record.Severity == CollapseSeverity.Severe ? 1.5f : 1f;
            float profileMultiplier = this.Config.Intensity == PenaltyIntensity.Soft
                ? profile.GoldLossMultiplierSoft
                : profile.GoldLossMultiplierHard;

            int loss = (int)Math.Round(farmer.Money * basePercent * severityFactor * profileMultiplier);
            loss = Math.Min(loss, this.Config.MaxGoldLoss);
            loss = Math.Max(0, loss);
            farmer.Money = Math.Max(0, farmer.Money - loss);
            return loss;
        }

        private int ApplyItemPenalty(Farmer farmer, CollapseRecord record, RescueProfile profile)
        {
            if (!this.Config.EnableItemPenalties)
                return 0;

            int baseLoss = record.LocationType switch
            {
                CollapseLocationType.Mines => this.Config.BaseExtraItemsLostMines,
                CollapseLocationType.Desert => this.Config.BaseExtraItemsLostDesert,
                _ => 0,
            };

            int profileLoss = this.Config.Intensity == PenaltyIntensity.Soft
                ? profile.ExtraItemsLostSoft
                : profile.ExtraItemsLostHard;

            if (record.Severity == CollapseSeverity.Severe)
                baseLoss += 1;

            int toLose = Math.Max(0, baseLoss + profileLoss);
            if (toLose <= 0)
                return 0;

            List<Item> removable = farmer.Items
                .Where(item => item != null && item.canBeTrashed() && item is not Tool)
                .ToList();

            int lost = 0;
            for (int i = 0; i < toLose && removable.Count > 0; i++)
            {
                int index = this.random.Next(removable.Count);
                Item target = removable[index];
                int stackToRemove = target.Stack > 1 ? Math.Min(target.Stack, 1) : 1;
                target.Stack -= stackToRemove;
                if (target.Stack <= 0)
                    farmer.removeItemFromInventory(target);

                lost++;
                removable.RemoveAt(index);
            }

            return lost;
        }

        private int ApplyXpPenalty(Farmer farmer, CollapseRecord record, RescueProfile profile)
        {
            if (!this.Config.EnableXPPenalties)
                return 0;

            int baseLoss = record.LocationType switch
            {
                CollapseLocationType.Farm => this.Config.BaseXpLossFarming,
                CollapseLocationType.Mines or CollapseLocationType.Desert => this.Config.BaseXpLossCombat,
                CollapseLocationType.Town or CollapseLocationType.OtherOutdoors => this.Config.BaseXpLossForaging,
                _ => this.Config.BaseXpLossGeneric,
            };

            int profileLoss = this.Config.Intensity == PenaltyIntensity.Soft
                ? profile.XpLossSoft
                : profile.XpLossHard;

            float severityFactor = record.Severity == CollapseSeverity.Severe ? 1.3f : 1f;
            int totalLoss = (int)Math.Round((baseLoss + profileLoss) * severityFactor);
            if (totalLoss <= 0)
                return 0;

            int skillIndex = this.SelectSkillIndex(record.LocationType, profile);
            int currentXp = farmer.experiencePoints[skillIndex];
            int loss = Math.Min(totalLoss, currentXp);
            farmer.experiencePoints[skillIndex] = currentXp - loss;
            return loss;
        }

        private string BuildMessage(RescueProfile profile, int gold, int items, int xp, CollapseSeverity severity)
        {
            return this.Helper.Translation.Get("message.summary", new
            {
                rescuer = this.Helper.Translation.Get(profile.FlavorKey),
                gold = gold,
                items = items,
                xp = xp,
                severity = this.Helper.Translation.Get(severity == CollapseSeverity.Severe ? "severity.severe" : "severity.mild"),
            });
        }

        private CollapseLocationType GetCollapseLocationType(GameLocation location)
        {
            if (location is FarmHouse or IslandFarmHouse)
                return CollapseLocationType.Home;

            if (location is Farm)
                return CollapseLocationType.Farm;

            if (location is MineShaft or VolcanoDungeon)
                return CollapseLocationType.Mines;

            if (location.NameOrUniqueName.Equals("SkullCave", StringComparison.OrdinalIgnoreCase))
                return CollapseLocationType.Mines;

            if (location.Name == "Caldera")
                return CollapseLocationType.Mines;

            if (location.Name == "Desert")
                return CollapseLocationType.Desert;

            if (location.IsOutdoors && (location.Name == "Town" || location.Name == "Forest" || location.Name == "Mountain" || location.Name == "Beach" || location.Name == "Railroad" || location.Name == "Backwoods" || location.Name == "BusStop"))
                return CollapseLocationType.Town;

            if (location.IsOutdoors)
                return CollapseLocationType.OtherOutdoors;

            return CollapseLocationType.Town;
        }

        private int SelectSkillIndex(CollapseLocationType location, RescueProfile profile)
        {
            if (location == CollapseLocationType.Farm)
                return Farmer.farmingSkill;

            if (location == CollapseLocationType.Mines || location == CollapseLocationType.Desert)
                return Farmer.combatSkill;

            if (profile.Id == "Linus")
                return Farmer.foragingSkill;

            if (location == CollapseLocationType.Town || location == CollapseLocationType.OtherOutdoors)
                return Farmer.foragingSkill;

            return Farmer.farmingSkill;
        }
    }

    public enum CollapseLocationType
    {
        None,
        Farm,
        Home,
        Town,
        Mines,
        Desert,
        OtherOutdoors
    }

    public enum CollapseSeverity
    {
        Mild,
        Severe
    }

    public enum PenaltyIntensity
    {
        Soft,
        Hard
    }

    public class ModConfig
    {
        public bool EnableMod { get; set; } = true;
        public PenaltyIntensity Intensity { get; set; } = PenaltyIntensity.Soft;
        public bool EnableGoldPenalties { get; set; } = true;
        public bool EnableItemPenalties { get; set; } = true;
        public bool EnableXPPenalties { get; set; } = true;
        public int MaxGoldLoss { get; set; } = 5000;
        public float BaseGoldLossFarm { get; set; } = 0.03f;
        public float BaseGoldLossTown { get; set; } = 0.04f;
        public float BaseGoldLossMines { get; set; } = 0.06f;
        public float BaseGoldLossDesert { get; set; } = 0.08f;
        public float BaseGoldLossHome { get; set; } = 0.00f;
        public float BaseGoldLossOther { get; set; } = 0.04f;
        public int BaseXpLossFarming { get; set; } = 15;
        public int BaseXpLossCombat { get; set; } = 25;
        public int BaseXpLossForaging { get; set; } = 15;
        public int BaseXpLossGeneric { get; set; } = 10;
        public int BaseExtraItemsLostMines { get; set; } = 1;
        public int BaseExtraItemsLostDesert { get; set; } = 1;
        public bool LogToConsole { get; set; } = true;
    }

    public class SaveData
    {
        public Dictionary<long, CollapseRecord> CollapseByFarmer { get; set; } = new();
    }

    public class CollapseRecord
    {
        public CollapseLocationType LocationType { get; set; }
        public CollapseSeverity Severity { get; set; }
        public int Day { get; set; }
        public bool Processed { get; set; }
    }

    public class RescueProfile
    {
        public string Id { get; set; } = string.Empty;
        public string DisplayName { get; set; } = string.Empty;
        public string FlavorKey { get; set; } = string.Empty;
        public HashSet<CollapseLocationType> EligibleLocations { get; set; } = new();
        public bool RequiresSpouse { get; set; }
        public string? NpcName { get; set; }
        public float GoldLossMultiplierSoft { get; set; } = 1f;
        public float GoldLossMultiplierHard { get; set; } = 1f;
        public int ExtraItemsLostSoft { get; set; }
        public int ExtraItemsLostHard { get; set; }
        public int XpLossSoft { get; set; }
        public int XpLossHard { get; set; }

        public bool IsEligible(Farmer farmer, CollapseLocationType location)
        {
            if (!this.EligibleLocations.Contains(location))
                return false;

            if (this.RequiresSpouse && !farmer.HasSpouseOrRoommate())
                return false;

            if (!string.IsNullOrWhiteSpace(this.NpcName))
            {
                NPC? npc = Game1.getCharacterFromName(this.NpcName, false);
                if (npc is null)
                    return false;
            }

            return true;
        }
    }

    /// <summary>Extension helpers for Farmer.</summary>
    public static class FarmerExtensions
    {
        /// <summary>Returns true if the farmer has a spouse or roommate (Krobus).</summary>
        public static bool HasSpouseOrRoommate(this Farmer farmer)
        {
            if (farmer is null)
                return false;

            // In practice, this returns either the spouse or Krobus roommate.
            return farmer.getSpouse() != null;
        }
    }

    // Minimal GMCM API interface – only the methods we actually use.
    public interface IGenericModConfigMenuApi
    {
        void Register(IManifest mod, Action reset, Action save, bool titleScreenOnly = false);

        void AddSectionTitle(IManifest mod, Func<string> text, Func<string>? tooltip = null);

        void AddBoolOption(
            IManifest mod,
            Func<bool> getValue,
            Action<bool> setValue,
            Func<string> name,
            Func<string>? tooltip = null,
            string? fieldId = null);

        void AddNumberOption(
            IManifest mod,
            Func<int> getValue,
            Action<int> setValue,
            Func<string> name,
            Func<string>? tooltip = null,
            int? min = null,
            int? max = null,
            int? interval = null,
            Func<int, string>? formatValue = null,
            string? fieldId = null);
    }
}
