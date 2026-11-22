<script lang="ts">
  import { app, countryOf, nav, page, route, readRoute, t } from "./lib/app.svelte";
  import { clubName, clubOf, compName } from "./lib/format";
  import { boot } from "./lib/db";
  import { applyTheme } from "./lib/theme.svelte";
  import Footer from "./components/Footer.svelte";
  import BottomNav from "./components/BottomNav.svelte";
  import Header from "./components/Header.svelte";
  import Sidebar from "./components/Sidebar.svelte";
  import SearchOverlay from "./components/SearchOverlay.svelte";
  import Toast from "./components/Toast.svelte";
  import ErrorBox from "./components/ErrorBox.svelte";
  import Spinner from "./components/Spinner.svelte";
  import About from "./routes/About.svelte";
  import BallonDor from "./routes/BallonDor.svelte";
  import Club from "./routes/Club.svelte";
  import Clubs from "./routes/Clubs.svelte";
  import Competition from "./routes/Competition.svelte";
  import Competitions from "./routes/Competitions.svelte";
  import Country from "./routes/Country.svelte";
  import Coverage from "./routes/Coverage.svelte";
  import Home from "./routes/Home.svelte";
  import OfCompetition from "./routes/OfCompetition.svelte";
  import Player from "./routes/Player.svelte";
  import Players from "./routes/Players.svelte";
  import Explore from "./routes/Explore.svelte";
  import Follows from "./routes/Follows.svelte";
  import Settings from "./routes/Settings.svelte";

  readRoute();
  applyTheme();
  boot();

  const head = $derived(route.parts[0]);
  // Un titre par page (WCAG 2.4.2) : « Arsenal FC · 2026/27 · OpenFootballBase ». Un joueur pose son nom (`page.name`) quand ses données sont lues.
  const pageName = $derived.by(() => {
    const [h, a, b] = route.parts;
    switch (h) {
      case "explore": return t("explore");
      case "follows": return t("follows");
      case "settings": return t("settings");
      case "clubs": return t("clubs");
      case "players": return t("players");
      case "competitions": return t("allComps");
      case "coverage": return t("coverage");
      case "about": return t("about");
      case "ballon-dor": return t("balloon");
      case "competition": return a ? compName(a) : "";
      case "country": return a ? countryOf(a).name : "";
      case "club": return a ? [clubName(clubOf(a)), b?.replace("-", "/")].filter(Boolean).join(" · ") : "";
      default: return "";
    }
  });
  $effect(() => { document.title = [page.name ?? pageName, t("title")].filter(Boolean).join(" · "); });
  // Remonte en haut de page à chaque changement de route (hors changement de saison sur l'accueil).
  $effect(() => { route.parts.join("/"); scrollTo({ top: 0 }); });
  // Transition de page sur mobile : un glissement court dans le sens de la navigation (avant : depuis la droite ; arrière : depuis la gauche), jamais avec « réduire les animations ».
  let shell: HTMLElement | undefined = $state();
  let last = "";
  $effect(() => {
    const k = route.parts.slice(0, 2).join("/"); const dir = nav.dir;
    if (k === last) return;
    last = k;
    if (!shell || !matchMedia("(max-width: 1023px)").matches || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    shell.animate([{ opacity: 0, transform: `translateX(${dir === "back" ? -28 : 28}px)` }, { opacity: 1, transform: "none" }], { duration: 250, easing: "cubic-bezier(0.2, 0.8, 0.2, 1)" });
  });
</script>

<svelte:window onhashchange={readRoute} />

<a class="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-surface focus:px-3 focus:py-2" href="#main">{t("skip")}</a>
<Sidebar />
<div class="lg:pl-60">
<Header />
<main id="main" tabindex="-1" bind:this={shell}>
  {#if app.error}
    <div class="mx-auto max-w-6xl px-4 py-10"><ErrorBox message={app.error} /></div>
  {:else if !app.manifest}
    <div class="mx-auto max-w-6xl px-4"><Spinner /></div>
  {:else if !head}
    <Home />
  {:else if !app.ready}
    <div class="mx-auto max-w-6xl px-4"><Spinner /><p class="text-sm text-muted">{t("loading")}</p></div>
  {:else}
    <div class="mx-auto px-4 py-8 {head === 'competition' || head === 'competitions' || head === 'club' || head === 'coverage' || head === 'players' || head === 'explore' ? 'max-w-[88rem]' : 'max-w-6xl'}">
      {#if head === "club"}
        <Club key={route.parts[1]} slug={route.parts[2]} />
      {:else if head === "explore"}
        <Explore />
      {:else if head === "follows"}
        <Follows />
      {:else if head === "settings"}
        <Settings />
      {:else if head === "clubs"}
        <Clubs />
      {:else if head === "country"}
        <Country code={route.parts[1]} />
      {:else if head === "competitions"}
        <Competitions />
      {:else if head === "competition" && route.parts[1]?.startsWith("OF:")}
        <OfCompetition code={route.parts[1]} />
      {:else if head === "competition"}
        <Competition code={route.parts[1]} slug={route.parts[2]} />
      {:else if head === "players"}
        <Players />
      {:else if head === "player"}
        <Player key={route.parts[1]} />
      {:else if head === "coverage"}
        <Coverage slug={route.parts[1]} />
      {:else if head === "ballon-dor"}
        <BallonDor />
      {:else if head === "about"}
        <About />
      {:else}
        <p class="text-warn">{t("noResult")}</p>
      {/if}
    </div>
  {/if}
</main>
<Footer />
<div class="h-[calc(5.25rem+env(safe-area-inset-bottom))] lg:hidden" aria-hidden="true"></div>
</div>
<BottomNav />
<SearchOverlay />
<Toast />
