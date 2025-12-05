using HarmonyLib;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;

namespace SafeLightning
{
    public sealed class ModEntry : Mod
    {
        private Harmony? harmony;

        public override void Entry(IModHelper helper)
        {
            this.harmony = new Harmony(this.ModManifest.UniqueID);
            this.harmony.Patch(
                original: AccessTools.Method(typeof(GameLocation), nameof(GameLocation.lightningStrike)),
                prefix: new HarmonyMethod(typeof(ModEntry), nameof(ModEntry.BeforeLightningStrike))
            );

            this.Monitor.Log(this.Helper.Translation.Get("log.patched"), LogLevel.Info);
        }

        private static bool BeforeLightningStrike(GameLocation __instance, Vector2 tileLocation, ref bool __result)
        {
            if (__instance.objects.TryGetValue(tileLocation, out var obj) && obj.bigCraftable.Value && obj.ParentSheetIndex == 9)
            {
                return true;
            }

            __result = false;
            return false;
        }
    }
}
