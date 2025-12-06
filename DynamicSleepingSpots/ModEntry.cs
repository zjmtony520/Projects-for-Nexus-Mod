using System;
using System.Collections.Generic;
using System.Linq;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Buffs;
using StardewValley.Locations;

namespace DynamicSleepingSpots
{
    public class ModEntry : Mod
    {
        private readonly Random random = new();

        private ModConfig Config = new();
        private SaveData SaveData = new();
        private List<RescueProfile> Profiles = new();

        public override void Entry(IModHelper helper)
        {
            this.Config = helper.ReadConfig<ModConfig>();
            this.SaveData = helper.Data.ReadSaveData<SaveData>("collapse-data") ?? new SaveData();
            this.InitializeProfiles();

            helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
            helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;
            helper.Events.GameLoop.DayEnding += this.OnDayEnding;
            helper.Events.GameLoop.DayStarted += this.OnDayStarted;
            helper.Events.GameLoop.Saving += this.OnSaving;
        }

        private void OnGameLaunched(object? sender, GameLaunchedEventArgs e)
        {
            this.RegisterGmcm();
        }

        private void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
        {
            this.SaveData = this.Helper.Data.ReadSaveData<SaveData>("collapse-data") ?? new SaveData();
        }

        private void OnSaving(object? sender, SavingEventArgs e)
        {
            this.Helper.Data.WriteSaveData("collapse-data", this.SaveData);
        }

        private void OnDayEnding(object? sender, DayEndingEventArgs e)
        {
            if (!this.Config.EnableMod || !Context.IsWorldReady)
            {
                return;
            }

            foreach (Farmer farmer in Game1.getOnlineFarmers())
            {
                if (farmer.isInBed.Value)
                {
                    continue;
                }

                CollapseLocationType locationType = this.GetCollapseLocationType(farmer.currentLocation);
                CollapseSeverity severity = farmer.timeOfDay < 2600 ? CollapseSeverity.Mild : CollapseSeverity.Severe;

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
            {
                return;
            }

            foreach (Farmer farmer in Game1.getOnlineFarmers())
            {
                if (!this.SaveData.CollapseByFarmer.TryGetValue(farmer.UniqueMultiplayerID, out CollapseRecord? record))
                {
                    continue;
                }

                if (record.Processed || record.Day != Game1.Date.TotalDays - 1)
                {
                    continue;
                }

                this.ApplyRescueOutcome(farmer, record);
                record.Processed = true;
                this.SaveData.CollapseByFarmer[farmer.UniqueMultiplayerID] = record;
            }
        }

        private void RegisterGmcm()
        {
            var gmcm = this.Helper.ModRegistry.GetApi<IGenericModConfigMenuApi>("spacechase0.GenericModConfigMenu");
            if (gmcm is null)
            {
                return;
            }

            gmcm.Register(this.ModManifest, () => this.Config = new ModConfig(), () => this.Helper.WriteConfig(this.Config));

            gmcm.AddSectionTitle(this.ModManifest, () => this.Helper.Translation.Get("config.enableMod.name"));
            gmcm.AddBoolOption(this.ModManifest, () => this.Config.EnableMod, value => this.Config.EnableMod = value, () => this.Helper.Translation.Get("config.enableMod.name"), () => this.Helper.Translation.Get("config.enableMod.tooltip"));
            gmcm.AddTextOption(this.ModManifest, () => this.Config.Intensity.ToString(), value => this.Config.Intensity = Enum.TryParse<PenaltyIntensity>(value, out var parsed) ? parsed : PenaltyIntensity.Soft, () => this.Helper.Translation.Get("config.intensity.name"), () => this.Helper.Translation.Get("config.intensity.tooltip"), new[] { PenaltyIntensity.Soft.ToString(), PenaltyIntensity.Hard.ToString() });

            gmcm.AddSectionTitle(this.ModManifest, () => "Penalties");
            gmcm.AddBoolOption(this.ModManifest, () => this.Config.EnableGoldPenalties, value => this.Config.EnableGoldPenalties = value, () => this.Helper.Translation.Get("config.gold.name"));
            gmcm.AddBoolOption(this.ModManifest, () => this.Config.EnableItemPenalties, value => this.Config.EnableItemPenalties = value, () => this.Helper.Translation.Get("config.items.name"));
            gmcm.AddBoolOption(this.ModManifest, () => this.Config.EnableXPPenalties, value => this.Config.EnableXPPenalties = value, () => this.Helper.Translation.Get("config.xp.name"));
            gmcm.AddBoolOption(this.ModManifest, () => this.Config.EnableBuffs, value => this.Config.EnableBuffs = value, () => this.Helper.Translation.Get("config.buffs.name"));
            gmcm.AddBoolOption(this.ModManifest, () => this.Config.EnableFriendshipEffects, value => this.Config.EnableFriendshipEffects = value, () => this.Helper.Translation.Get("config.friendship.name"));

            gmcm.AddNumberOption(this.ModManifest, () => this.Config.MaxGoldLoss, value => this.Config.MaxGoldLoss = value, () => this.Helper.Translation.Get("config.maxgold.name"), null, 0, 100000, 100);
            gmcm.AddNumberOption(this.ModManifest, () => (int)(this.Config.BaseGoldLossFarm * 100), value => this.Config.BaseGoldLossFarm = value / 100f, () => this.Helper.Translation.Get("config.basegold.farm"), null, 0, 100);
            gmcm.AddNumberOption(this.ModManifest, () => (int)(this.Config.BaseGoldLossTown * 100), value => this.Config.BaseGoldLossTown = value / 100f, () => this.Helper.Translation.Get("config.basegold.town"), null, 0, 100);
            gmcm.AddNumberOption(this.ModManifest, () => (int)(this.Config.BaseGoldLossMines * 100), value => this.Config.BaseGoldLossMines = value / 100f, () => this.Helper.Translation.Get("config.basegold.mines"), null, 0, 100);
            gmcm.AddNumberOption(this.ModManifest, () => (int)(this.Config.BaseGoldLossDesert * 100), value => this.Config.BaseGoldLossDesert = value / 100f, () => this.Helper.Translation.Get("config.basegold.desert"), null, 0, 100);
            gmcm.AddNumberOption(this.ModManifest, () => (int)(this.Config.BaseGoldLossHome * 100), value => this.Config.BaseGoldLossHome = value / 100f, () => this.Helper.Translation.Get("config.basegold.home"), null, 0, 100);
            gmcm.AddNumberOption(this.ModManifest, () => (int)(this.Config.BaseGoldLossOther * 100), value => this.Config.BaseGoldLossOther = value / 100f, () => this.Helper.Translation.Get("config.basegold.other"), null, 0, 100);

            gmcm.AddNumberOption(this.ModManifest, () => this.Config.BaseXpLossFarming, value => this.Config.BaseXpLossFarming = value, () => this.Helper.Translation.Get("config.basexp.farming"), null, 0, 500);
            gmcm.AddNumberOption(this.ModManifest, () => this.Config.BaseXpLossCombat, value => this.Config.BaseXpLossCombat = value, () => this.Helper.Translation.Get("config.basexp.combat"), null, 0, 500);
            gmcm.AddNumberOption(this.ModManifest, () => this.Config.BaseXpLossForaging, value => this.Config.BaseXpLossForaging = value, () => this.Helper.Translation.Get("config.basexp.foraging"), null, 0, 500);
            gmcm.AddNumberOption(this.ModManifest, () => this.Config.BaseXpLossGeneric, value => this.Config.BaseXpLossGeneric = value, () => this.Helper.Translation.Get("config.basexp.generic"), null, 0, 500);

            gmcm.AddNumberOption(this.ModManifest, () => this.Config.BaseExtraItemsLostMines, value => this.Config.BaseExtraItemsLostMines = value, () => this.Helper.Translation.Get("config.baseitems.mines"), null, 0, 10);
            gmcm.AddNumberOption(this.ModManifest, () => this.Config.BaseExtraItemsLostDesert, value => this.Config.BaseExtraItemsLostDesert = value, () => this.Helper.Translation.Get("config.baseitems.desert"), null, 0, 10);
            gmcm.AddBoolOption(this.ModManifest, () => this.Config.LogToConsole, value => this.Config.LogToConsole = value, () => this.Helper.Translation.Get("config.log"));
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
                    AppliedBuff = new BuffDefinition
                    {
                        Id = "DynamicSleepingSpots/Harvey",
                        DurationMinutes = 240,
                        DescriptionKey = "buff.harvey",
                        MaxHealth = 10,
                        Speed = -1,
                    },
                    FriendshipEffect = new FriendshipEffectDefinition
                    {
                        NpcName = "Harvey",
                        AmountSoft = 15,
                        AmountHard = 0,
                    },
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
                    AppliedBuff = new BuffDefinition
                    {
                        Id = "DynamicSleepingSpots/Linus",
                        DurationMinutes = 360,
                        DescriptionKey = "buff.linus",
                        Foraging = 1,
                        Luck = 1,
                    },
                    FriendshipEffect = new FriendshipEffectDefinition
                    {
                        NpcName = "Linus",
                        AmountSoft = 40,
                        AmountHard = 25,
                    },
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
                    FriendshipEffect = new FriendshipEffectDefinition
                    {
                        NpcName = "Shane",
                        AmountSoft = -5,
                        AmountHard = -10,
                    },
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
                    AppliedBuff = new BuffDefinition
                    {
                        Id = "DynamicSleepingSpots/Guild",
                        DurationMinutes = 300,
                        DescriptionKey = "buff.guild",
                        Combat = 1,
                        Defense = 1,
                    },
                    FriendshipEffect = new FriendshipEffectDefinition
                    {
                        NpcName = "Marlon",
                        AmountSoft = 20,
                        AmountHard = 10,
                    },
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
                    AppliedBuff = new BuffDefinition
                    {
                        Id = "DynamicSleepingSpots/Spouse",
                        DurationMinutes = 360,
                        DescriptionKey = "buff.spouse",
                        Speed = 1,
                        Luck = 1,
                    },
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
                    AppliedBuff = new BuffDefinition
                    {
                        Id = "DynamicSleepingSpots/Junimos",
                        DurationMinutes = 240,
                        DescriptionKey = "buff.junimos",
                        Luck = 2,
                    },
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
                    AppliedBuff = new BuffDefinition
                    {
                        Id = "DynamicSleepingSpots/Wake",
                        DurationMinutes = 180,
                        DescriptionKey = "buff.wake",
                        Stamina = -20,
                    },
                }
            };
        }

        private void ApplyRescueOutcome(Farmer farmer, CollapseRecord record)
        {
            RescueProfile profile = this.ChooseRescueProfile(farmer, record);
            int goldLost = this.ApplyGoldPenalty(farmer, record, profile);
            int itemsLost = this.ApplyItemPenalty(farmer, record, profile);
            int xpLost = this.ApplyXpPenalty(farmer, record, profile);
            this.ApplyBuff(farmer, profile);
            this.ApplyFriendshipEffects(farmer, profile);

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
            {
                return this.Profiles.First(p => p.Id == "WakeWhereYouFell");
            }

            // simple weighting: favor Harvey in town, guild in mines
            if (record.LocationType == CollapseLocationType.Mines)
            {
                RescueProfile? guild = eligible.FirstOrDefault(p => p.Id == "AdventurersGuild");
                if (guild != null && this.random.NextDouble() < 0.6)
                {
                    return guild;
                }
            }

            if (record.LocationType == CollapseLocationType.Town)
            {
                RescueProfile? harvey = eligible.FirstOrDefault(p => p.Id == "HarveyClinic");
                if (harvey != null && this.random.NextDouble() < 0.6)
                {
                    return harvey;
                }
            }

            int index = this.random.Next(eligible.Count);
            return eligible[index];
        }

        private int ApplyGoldPenalty(Farmer farmer, CollapseRecord record, RescueProfile profile)
        {
            if (!this.Config.EnableGoldPenalties)
            {
                return 0;
            }

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
            float profileMultiplier = this.Config.Intensity == PenaltyIntensity.Soft ? profile.GoldLossMultiplierSoft : profile.GoldLossMultiplierHard;

            int loss = (int)Math.Round(farmer.Money * basePercent * severityFactor * profileMultiplier);
            loss = Math.Min(loss, this.Config.MaxGoldLoss);
            loss = Math.Max(0, loss);
            farmer.Money = Math.Max(0, farmer.Money - loss);
            return loss;
        }

        private int ApplyItemPenalty(Farmer farmer, CollapseRecord record, RescueProfile profile)
        {
            if (!this.Config.EnableItemPenalties)
            {
                return 0;
            }

            int baseLoss = record.LocationType switch
            {
                CollapseLocationType.Mines => this.Config.BaseExtraItemsLostMines,
                CollapseLocationType.Desert => this.Config.BaseExtraItemsLostDesert,
                _ => 0,
            };

            int profileLoss = this.Config.Intensity == PenaltyIntensity.Soft ? profile.ExtraItemsLostSoft : profile.ExtraItemsLostHard;
            if (record.Severity == CollapseSeverity.Severe)
            {
                baseLoss += 1;
            }

            int toLose = Math.Max(0, baseLoss + profileLoss);
            if (toLose <= 0)
            {
                return 0;
            }

            List<Item> removable = farmer.Items.Where(item => item != null && item.canBeTrashed.Value && item is not Tool).ToList();
            int lost = 0;
            for (int i = 0; i < toLose && removable.Count > 0; i++)
            {
                int index = this.random.Next(removable.Count);
                Item target = removable[index];
                int stackToRemove = target.Stack > 1 ? Math.Min(target.Stack, 1) : 1;
                target.Stack -= stackToRemove;
                if (target.Stack <= 0)
                {
                    farmer.removeItemFromInventory(target);
                }
                lost++;
                removable.RemoveAt(index);
            }

            return lost;
        }

        private int ApplyXpPenalty(Farmer farmer, CollapseRecord record, RescueProfile profile)
        {
            if (!this.Config.EnableXPPenalties)
            {
                return 0;
            }

            int baseLoss = record.LocationType switch
            {
                CollapseLocationType.Farm => this.Config.BaseXpLossFarming,
                CollapseLocationType.Mines or CollapseLocationType.Desert => this.Config.BaseXpLossCombat,
                CollapseLocationType.Town or CollapseLocationType.OtherOutdoors => this.Config.BaseXpLossForaging,
                _ => this.Config.BaseXpLossGeneric,
            };

            int profileLoss = this.Config.Intensity == PenaltyIntensity.Soft ? profile.XpLossSoft : profile.XpLossHard;
            float severityFactor = record.Severity == CollapseSeverity.Severe ? 1.3f : 1f;
            int totalLoss = (int)Math.Round((baseLoss + profileLoss) * severityFactor);
            if (totalLoss <= 0)
            {
                return 0;
            }

            int skillIndex = this.SelectSkillIndex(record.LocationType, profile);
            int currentXp = farmer.experiencePoints[skillIndex];
            int loss = Math.Min(totalLoss, currentXp);
            farmer.experiencePoints[skillIndex] = currentXp - loss;
            return loss;
        }

        private void ApplyBuff(Farmer farmer, RescueProfile profile)
        {
            if (!this.Config.EnableBuffs || profile.AppliedBuff is null)
            {
                return;
            }

            BuffDefinition def = profile.AppliedBuff;
            BuffEffects effects = new();

            if (def.Farming != 0)
            {
                effects.FarmingLevel.Add(def.Farming);
            }

            if (def.Fishing != 0)
            {
                effects.FishingLevel.Add(def.Fishing);
            }

            if (def.Foraging != 0)
            {
                effects.ForagingLevel.Add(def.Foraging);
            }

            if (def.Mining != 0)
            {
                effects.MiningLevel.Add(def.Mining);
            }

            if (def.Combat != 0)
            {
                effects.CombatLevel.Add(def.Combat);
            }

            if (def.Luck != 0)
            {
                effects.LuckLevel.Add(def.Luck);
            }

            if (def.Speed != 0)
            {
                effects.Speed.Add(def.Speed);
            }

            if (def.Defense != 0)
            {
                effects.Defense.Add(def.Defense);
            }

            if (def.MaxHealth != 0)
            {
                effects.MaxHealth.Add(def.MaxHealth);
            }

            if (def.Stamina != 0)
            {
                effects.Stamina.Add(def.Stamina);
            }

            Buff buff = new(
                id: def.Id,
                duration: def.DurationMinutes,
                source: this.ModManifest.Name,
                displaySource: this.Helper.Translation.Get(def.DescriptionKey),
                iconTexture: null,
                effects: effects);

            farmer.applyBuff(buff);
        }

        private void ApplyFriendshipEffects(Farmer farmer, RescueProfile profile)
        {
            if (!this.Config.EnableFriendshipEffects || profile.FriendshipEffect is null)
            {
                return;
            }

            FriendshipEffectDefinition def = profile.FriendshipEffect;
            int amount = this.Config.Intensity == PenaltyIntensity.Soft ? def.AmountSoft : def.AmountHard;
            if (amount == 0 || string.IsNullOrWhiteSpace(def.NpcName))
            {
                return;
            }

            farmer.changeFriendship(amount, Game1.getCharacterFromName(def.NpcName));
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
            {
                return CollapseLocationType.Home;
            }

            if (location is Farm)
            {
                return CollapseLocationType.Farm;
            }

            if (location is MineShaft or VolcanoDungeon)
            {
                return CollapseLocationType.Mines;
            }

            if (location.NameOrUniqueName.Equals("SkullCave", StringComparison.OrdinalIgnoreCase))
            {
                return CollapseLocationType.Mines;
            }

            if (location.Name == "Caldera")
            {
                return CollapseLocationType.Mines;
            }

            if (location.Name == "Desert")
            {
                return CollapseLocationType.Desert;
            }

            if (location.IsOutdoors && (location.Name == "Town" || location.Name == "Forest" || location.Name == "Mountain" || location.Name == "Beach" || location.Name == "Railroad" || location.Name == "Backwoods" || location.Name == "BusStop"))
            {
                return CollapseLocationType.Town;
            }

            if (location.IsOutdoors)
            {
                return CollapseLocationType.OtherOutdoors;
            }

            return CollapseLocationType.Town;
        }

        private int SelectSkillIndex(CollapseLocationType location, RescueProfile profile)
        {
            if (location == CollapseLocationType.Farm)
            {
                return Farmer.farmingSkill; // 0
            }

            if (location == CollapseLocationType.Mines || location == CollapseLocationType.Desert)
            {
                return Farmer.combatSkill; // 4
            }

            if (profile.Id == "Linus")
            {
                return Farmer.foragingSkill;
            }

            if (location == CollapseLocationType.Town || location == CollapseLocationType.OtherOutdoors)
            {
                return Farmer.foragingSkill;
            }

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
        public bool EnableBuffs { get; set; } = true;
        public bool EnableFriendshipEffects { get; set; } = true;
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
        public BuffDefinition? AppliedBuff { get; set; }
        public FriendshipEffectDefinition? FriendshipEffect { get; set; }

        public bool IsEligible(Farmer farmer, CollapseLocationType location)
        {
            if (!this.EligibleLocations.Contains(location))
            {
                return false;
            }

            if (this.RequiresSpouse && !farmer.isMarriedOrRoommates())
            {
                return false;
            }

            if (!string.IsNullOrWhiteSpace(this.NpcName))
            {
                NPC? npc = Game1.getCharacterFromName(this.NpcName, false);
                if (npc is null)
                {
                    return false;
                }
            }

            return true;
        }
    }

    public class BuffDefinition
    {
        public string Id { get; set; } = string.Empty;
        public string DescriptionKey { get; set; } = string.Empty;
        public int DurationMinutes { get; set; }
        public int Farming { get; set; }
        public int Fishing { get; set; }
        public int Foraging { get; set; }
        public int Mining { get; set; }
        public int Combat { get; set; }
        public int Luck { get; set; }
        public int Speed { get; set; }
        public int Defense { get; set; }
        public int MaxHealth { get; set; }
        public int Stamina { get; set; }
    }

    public class FriendshipEffectDefinition
    {
        public string? NpcName { get; set; }
        public int AmountSoft { get; set; }
        public int AmountHard { get; set; }
    }

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

        void AddTextOption(
            IManifest mod,
            Func<string> getValue,
            Action<string> setValue,
            Func<string> name,
            Func<string>? tooltip = null,
            IEnumerable<string>? allowedValues = null,
            Func<string, string>? formatValue = null,
            string? fieldId = null);
    }

    public static class FarmerExtensions
    {
        public static bool isMarriedOrRoommates(this Farmer farmer)
        {
            return farmer.isMarried() || farmer.isRoommate();
        }
    }
}
