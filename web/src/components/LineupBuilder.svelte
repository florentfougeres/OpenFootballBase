<script lang="ts">
  import { untrack } from "svelte";
  import { q } from "../lib/db";
  import { app, route, t } from "../lib/app.svelte";
  import type { Row } from "../lib/app.svelte";
  import { notify } from "../lib/toast.svelte";
  import { DISPLAYS, FORMATION_NAMES, FORMATIONS, PATTERNS, decodeLineup, defaultStyle, emptyLineup, encodeLineup, roleLabel, type Display, type Line, type Lineup, type Style } from "../lib/lineup";
  import { clubName, clubOf } from "../lib/format";
  import PosPill from "./PosPill.svelte";
  import Segmented from "./Segmented.svelte";
  import Sheet from "./Sheet.svelte";

  // Créateur de composition : on choisit une formation, puis un joueur de l'effectif pour chaque poste. La composition se partage par un lien (formation + joueurs dans l'adresse, sans compte) et s'exporte en image.
  // `rows` : les joueurs proposés (effectif d'un club) ; `find` : à défaut, une recherche dans toute la base ; `seed` : les joueurs déjà placés par le lien ouvert. `logo` et `colors` : le blason et les couleurs du club
  // (le club décide du style de départ). `base` : l'adresse (sans la composition) pour le lien de partage et la sauvegarde locale.
  let { rows = [], find, seed = [], caption, logo = null, colors = [], base }: { rows?: Row[]; find?: (term: string, line: Line) => Promise<Row[]>; seed?: Row[]; caption: string; logo?: string | null; colors?: string[]; base: string } = $props();

  // Tous les joueurs rencontrés (proposés, trouvés, ou venus du lien) : la composition ne garde que leurs clés.
  // Le parent recrée le composant quand le club, la saison ou le lien changent : on ne lit donc ces listes qu'au départ.
  let known = $state<Record<string, Row>>(untrack(() => Object.fromEntries([...rows, ...seed].map((r) => [r.key as string, r]))));
  const byKey = { get: (k: string) => known[k] };
  const fromUrl = () => { const l = decodeLineup(route.query); return l ? { ...l, players: l.players.map((k) => (k && known[k] ? k : null)) } : null; };

  /** Style de départ : en mode « par club », les maillots aux couleurs du club ; sinon des ronds blancs avec les initiales (pas de numéro de maillot quand on pioche dans toute la base). */
  const clubStyle = (): Style => ({ ...defaultStyle(), marker: "jersey", color: colors[0], color2: colors[1] ?? "#ffffff" });
  const firstDisplay: Display = untrack(() => (find ? "initials" : "number"));
  const firstStyle = (): Style => untrack(() => (!find && colors.length ? clubStyle() : defaultStyle()));

  // Sauvegarde locale (par adresse) : on retrouve sa composition après un rechargement ou une interruption. Un lien ouvert prime toujours.
  const storeKey = untrack(() => `ofb.lineup.${base}`);
  const restore = (): Lineup | null => {
    try {
      const raw = localStorage.getItem(storeKey); if (!raw) return null;
      const { lineup: l, rows: saved } = JSON.parse(raw);
      for (const r of saved ?? []) if (r?.key && !known[r.key]) known[r.key] = r;
      const back = decodeLineup(new URLSearchParams(l));
      return back ? { ...back, players: back.players.map((k) => (k && known[k] ? k : null)) } : null;
    } catch { return null; }
  };
  let restored = false;
  const start = (): Lineup => {
    const url = fromUrl(); if (url) return url;
    const saved = restore(); if (saved && saved.players.some(Boolean)) { restored = true; return saved; }
    return { ...emptyLineup(undefined, firstDisplay), style: firstStyle() };
  };
  let lineup = $state<Lineup>(start());
  $effect(() => { if (restored) { restored = false; notify(t("lineupRestored")); } });

  const slots = $derived(FORMATIONS[lineup.formation]);
  const placed = $derived(new Set(lineup.players.filter(Boolean) as string[]));
  const filled = $derived(placed.size);

  // Annuler / rétablir : chaque changement de composition ou de style est un état mémorisé ; une rafale de changements (un curseur, une couleur) ne compte que pour un pas. Le titre et le sous-titre, frappés lettre par lettre, n'y entrent pas.
  const snap = (l: Lineup) => JSON.stringify({ ...l, title: "", subtitle: "" });
  let cur = untrack(() => snap(lineup)), lastAt = 0, restoring = false;
  let past = $state<string[]>([]), future = $state<string[]>([]);
  $effect(() => {
    const s = snap(lineup);
    if (s === cur) return;
    if (!restoring) { if (Date.now() - lastAt > 500 || !past.length) past = [...past.slice(-49), cur]; future = []; lastAt = Date.now(); }
    restoring = false; cur = s;
  });
  const sameKeys = (l: Lineup) => ({ ...l, title: lineup.title, subtitle: lineup.subtitle });
  function undo() { if (!past.length) return; const prev = past[past.length - 1]; past = past.slice(0, -1); future = [cur, ...future]; restoring = true; lineup = sameKeys(JSON.parse(prev)); }
  function redo() { if (!future.length) return; const next = future[0]; future = future.slice(1); past = [...past, cur]; restoring = true; lineup = sameKeys(JSON.parse(next)); }

  // Sauvegarde locale, un peu après le dernier changement.
  $effect(() => {
    const body = { lineup: encodeLineup(lineup), rows: lineup.players.filter(Boolean).map((k) => known[k!]).filter(Boolean) };
    const id = setTimeout(() => { try { if (filled) localStorage.setItem(storeKey, JSON.stringify(body)); else localStorage.removeItem(storeKey); } catch { /* stockage indisponible : tant pis */ } }, 400);
    return () => clearTimeout(id);
  });

  function setFormation(f: string) {
    // Aucun joueur n'est retiré (les deux formations ont 11 postes) : chacun garde sa ligne (défense, milieu, attaque) tant qu'il reste un poste libre dans cette ligne,
    // sinon il prend le poste libre de la ligne la plus proche. Son numéro libre le suit.
    const cur = FORMATIONS[lineup.formation], to = FORMATIONS[f], ORDER = ["GK", "DF", "MF", "FW"];
    const next = to.map(() => null as string | null), nums = to.map(() => null as number | null), left: { k: string; line: string; n: number | null }[] = [];
    lineup.players.forEach((k, i) => {
      if (!k) return;
      const j = to.findIndex((s, x) => s.line === cur[i].line && !next[x]);
      if (j >= 0) { next[j] = k; nums[j] = lineup.nums[i]; } else left.push({ k, line: cur[i].line, n: lineup.nums[i] });
    });
    for (const x of left) {
      let best = -1, dist = 9;
      to.forEach((s, j) => { if (!next[j]) { const d = Math.abs(ORDER.indexOf(s.line) - ORDER.indexOf(x.line)); if (d < dist) { dist = d; best = j; } } });
      if (best >= 0) { next[best] = x.k; nums[best] = x.n; }
    }
    lineup = { ...lineup, formation: f, players: next, nums };
  }

  function autoFill() {
    const used = new Set<string>();
    if (find) return;
    const players = slots.map((s) => {
      const pick = rows.find((r) => r.position === s.line && !used.has(r.key as string)) ?? null;
      if (pick) used.add(pick.key as string);
      return (pick?.key as string | undefined) ?? null;
    });
    lineup = { ...lineup, players };
  }

  // Photos : celles des fiches Wikipedia (`player_profile`), cherchées une fois pour les joueurs placés quand on choisit l'affichage « photo ».
  let photos = $state<Record<string, string>>({});
  $effect(() => {
    if (lineup.display !== "photo" || !app.has.player_profile) return;
    const todo = lineup.players.filter((k): k is string => !!k && /^Q\d+$/.test(k) && !(k in photos));
    if (!todo.length) return;
    q(`SELECT player_qid, photo_url FROM player_profile WHERE player_qid IN (${todo.map(() => "?").join(",")})`, todo)
      .then((r) => { const next = { ...photos }; for (const k of todo) next[k] = ""; for (const x of r) if (x.photo_url) next[x.player_qid as string] = x.photo_url as string; photos = next; })
      .catch(() => {});
  });
  /** Texte du rond selon l'affichage choisi. */
  const badge = (i: number, r: Row) =>
    lineup.display === "number" ? String(r.shirt_number ?? initials(String(r.player)))
    : lineup.display === "free" ? String(lineup.nums[i] ?? i + 1)
    : lineup.display === "position" ? roleLabel(slots[i].role, app.lang)
    : lineup.display === "none" ? ""
    : initials(String(r.player));
  const photoOf = (i: number) => (lineup.display === "photo" && lineup.players[i] ? photos[lineup.players[i]!] || "" : "");
  const PALETTE = ["#ffffff", "#111827", "#b91c1c", "#ea580c", "#eab308", "#15803d", "#1d4ed8", "#7c3aed"];
  const JERSEY = "M-0.36 -0.9 L-0.98 -0.5 L-0.78 0 L-0.52 -0.18 L-0.52 0.92 L0.52 0.92 L0.52 -0.18 L0.78 0 L0.98 -0.5 L0.36 -0.9 Q0 -0.62 -0.36 -0.9 Z";
  const ms = $derived(lineup.style.size / 100), ls = $derived(lineup.style.label / 100), ns = $derived(lineup.style.name / 100);
  const isJersey = $derived(lineup.style.marker === "jersey" && lineup.display !== "photo");          // avec les photos, le marqueur reste un rond
  /** Encre lisible sur une couleur de fond. */
  const ink = (hex: string) => { const n = parseInt(hex.replace("#", "").padEnd(6, "0").slice(0, 6), 16); return 0.299 * ((n >> 16) & 255) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255) > 150 ? "#111827" : "#ffffff"; };
  const R = 2.8, Z = 1.3;          // Z : zoom des photos, calées sur le haut (le visage est le plus souvent en haut de l'image)
  /** Taille du texte d'un marqueur : celle demandée (curseur « numéro »), réduite pour que le texte tienne toujours dans le maillot (unités du maillot) ou dans le rond. */
  const fitJersey = (txt: string, ls: number) => Math.min(0.9 * ls, 0.76 / (0.66 * Math.max(1, txt.length)));
  const fitCircle = (txt: string, ms: number, ls: number) => Math.min(2.7 * ms * ls, (R * ms * 1.4) / (0.66 * Math.max(1, txt.length)));

  const W = 68, H = 105;          // le terrain en unités (68 × 105 : rapport des vraies dimensions)
  // Lisibilité : aucun texte du terrain ne descend sous 8 px à l'écran, quelle que soit la largeur du terrain (en unités du terrain : 8 px ÷ pixels par unité).
  let pitchPx = $state(0);
  const minU = $derived(pitchPx > 0 ? 8 / (pitchPx / W) : 0);
  const unit = $derived(Math.max(ns, minU / 1.8));          // échelle des plaques de nom
  const floorF = $derived(Math.max(0.5, Math.min(1, minU / (1.8 * unit))));

  /** Plaques des noms sous les ronds (comme à la télé) : nom en capitales sur fond sombre ; avec les nationalités, un petit drapeau rond est dans la plaque.
   *  Chaque plaque reste centrée sous son marqueur ; si elle déborde du terrain ou touche sa voisine, son texte rétrécit (le plus large d'abord) sans passer sous 8 px à l'écran ;
   *  en dernier recours seulement, les plaques s'écartent l'une de l'autre. */
  const GAP = 0.8;
  /** Largeur réelle d'un texte, mesurée par un texte invisible placé dans le SVG et rendu à la taille réelle : même police, mêmes arrondis (à 10 px les lettres sont environ 13 % plus larges qu'à grande taille,
   *  ce qui faisait déborder les noms larges comme MARQUINHOS). */
  let probe: SVGTextElement | undefined = $state();
  let measured = $state(0);          // change quand les mesures sont à refaire (SVG monté, polices chargées)
  const widths = new Map<string, number>();
  $effect(() => {
    if (!probe) return;
    const redo = () => { widths.clear(); untrack(() => { measured++; }); };          // la lecture du compteur est isolée : l'effet ne dépend que du texte de mesure
    redo();
    document.fonts?.ready.then(redo);
  });
  const textW = (str: string, fs: number) => {
    const key = `${fs.toFixed(3)}|${str}`;
    let w = widths.get(key); if (w !== undefined) return w;
    if (!probe) return str.length * 0.78 * fs;
    probe.setAttribute("font-size", String(fs)); probe.textContent = str; w = probe.getComputedTextLength();
    widths.set(key, w); return w;
  };
  const plates = $derived.by(() => {
    measured;
    const info = slots.map((s, i) => ({ i, name: shortName(String(known[lineup.players[i] ?? ""]?.player ?? "")).toUpperCase(), fl: lineup.opts.nat && !!flagCode(i), cx: px(s.x), y: py(s.y) }))
      .filter((o) => lineup.players[o.i] && o.name).sort((a, b) => a.y - b.y);
    const rowsOf: (typeof info)[] = [];
    for (const o of info) { const row = rowsOf[rowsOf.length - 1]; if (row && o.y - row[0].y < 8) row.push(o); else rowsOf.push([o]); }
    const ext = isJersey ? R * 1.15 * 0.95 * ms : R * ms;          // demi-hauteur du marqueur
    const u = unit, out: Record<number, { fs: number; label: string; f: number; x0: number; y0: number; w: number; h: number; fx: number; fy: number; fr: number; tx: number; anchor: string; ty: number }> = {};
    for (const row of rowsOf) {
      row.sort((a, b) => a.cx - b.cx);
      const f = row.map(() => 1), nat = row.map((o) => textW(o.name, 1.8 * u) * 1.03 + (o.fl ? 5 : 3) * u), wd = (n: number) => nat[n] * f[n];
      for (let it = 0; it < 400; it++) {
        let changed = false;
        row.forEach((o, n) => { if ((o.cx - wd(n) / 2 < 1 || o.cx + wd(n) / 2 > W - 1) && f[n] > floorF) { f[n] -= 0.03; changed = true; } });
        for (let n = 0; n + 1 < row.length; n++) {
          if (row[n + 1].cx - wd(n + 1) / 2 - (row[n].cx + wd(n) / 2) >= GAP) continue;
          const wide = wd(n) >= wd(n + 1) ? n : n + 1, m = f[wide] > floorF ? wide : wide === n ? n + 1 : n;
          if (f[m] > floorF) { f[m] -= 0.03; changed = true; }
        }
        if (!changed) break;
      }
      const w = row.map((_, n) => wd(n)), L = row.map((o, n) => o.cx - w[n] / 2);
      for (let n = 1; n < L.length; n++) L[n] = Math.max(L[n], L[n - 1] + w[n - 1] + GAP);
      let limit = W - 1;
      for (let n = L.length - 1; n >= 0; n--) { L[n] = Math.min(L[n], limit - w[n]); limit = L[n] - GAP; }
      row.forEach((o, n) => {
        const x0 = Math.max(L[n], 1), y0 = o.y + ext + 0.5, h = 3.1 * u, g = Math.max(f[n], floorF);
        out[o.i] = { fs: 1.8 * g * u, label: o.name, f: g, x0, y0, w: w[n], h, fx: x0 + 1.75 * g * u, fy: y0 + h / 2, fr: 1.25 * g * u, tx: o.fl ? x0 + 3.5 * g * u : x0 + w[n] / 2, anchor: o.fl ? "start" : "middle", ty: y0 + h / 2 + 0.68 * g * u };
      });
    }
    return out;
  });
  const flagCode = (i: number) => (lineup.players[i] ? (byKey.get(lineup.players[i]!)?.nat_flag as string | null | undefined) ?? null : null);

  // Choix du joueur : sur grand écran dans le panneau, sur téléphone dans un tiroir en bas (le terrain reste visible au-dessus, décalé pour que le poste choisi ne soit jamais caché).
  let open = $state<number | null>(null), search = $state("");
  const slotRole = $derived(open === null ? null : slots[open]);
  let found = $state<Row[]>([]), searching = $state(false);
  // Recherche dans toute la base : courte attente après la frappe ; une réponse tardive d'une frappe précédente est ignorée.
  $effect(() => {
    const term = search.trim(), line = slotRole?.line;
    if (!find || open === null || !line) return;
    if (term.length < 2) { found = []; searching = false; return; }
    searching = true;
    let alive = true;
    const id = setTimeout(() => find(term, line).then((r) => { if (alive) { found = r; searching = false; } }).catch(() => { if (alive) searching = false; }), 200);
    return () => { alive = false; clearTimeout(id); };
  });
  const candidates = $derived.by(() => {
    if (!slotRole) return [] as Row[];
    if (find) return found;
    const q = search.trim().toLocaleLowerCase();
    const list = q ? rows.filter((r) => String(r.player).toLocaleLowerCase().includes(q)) : rows;
    const rank = (r: Row) => (r.position === slotRole.line ? 0 : 1);
    return [...list].sort((a, b) => rank(a) - rank(b));
  });
  /** Poste libre suivant (après `i`, en bouclant) : après un joueur posé sur un poste vide, on enchaîne. */
  const nextEmpty = (i: number, players: (string | null)[]) => {
    for (let d = 1; d < players.length; d++) { const j = (i + d) % players.length; if (!players[j]) return j; }
    return null;
  };
  function assign(i: number, key: string | null) {
    const players = [...lineup.players], wasEmpty = !players[i];
    if (key) {
      if (!known[key]) { const r = found.find((x) => x.key === key); if (r) known[key] = r; }
      const from = players.indexOf(key);
      if (from >= 0) players[from] = players[i];          // le joueur change de poste : l'occupant précédent prend sa place
      players[i] = key;
    } else players[i] = null;
    lineup = { ...lineup, players };
    open = key && wasEmpty ? nextEmpty(i, players) : null;
    search = "";
  }
  const closePicker = () => { open = null; search = ""; };

  // Téléphone : le tiroir occupe le bas de l'écran ; le terrain monte juste assez pour que le poste choisi (et son nom) reste au-dessus.
  let shift = $state(0), pitchBox: HTMLDivElement | undefined = $state();
  $effect(() => {
    const i = open; desktop; ms;
    if (i === null || desktop || !svg || !pitchBox) { shift = 0; return; }
    const raf = requestAnimationFrame(() => {
      const slot = svg!.querySelectorAll("g[role=button]")[i]?.getBoundingClientRect(); if (!slot) return;
      const natural = slot.bottom + shift, trayTop = innerHeight * 0.56, topRoom = pitchBox!.getBoundingClientRect().top + shift - 8;
      shift = Math.round(Math.min(Math.max(0, natural + 36 - trayTop), Math.max(0, topRoom)));
    });
    return () => cancelAnimationFrame(raf);
  });

  /** Titre de la composition : celui qu'on a saisi, sinon la légende du club. */
  const heading = $derived(lineup.title.trim() || caption);
  const cleared = (): Lineup => ({ ...emptyLineup(lineup.formation, lineup.display), title: lineup.title, subtitle: lineup.subtitle, opts: lineup.opts, style: lineup.style });
  const initials = (name: string) => name.split(/\s+/).filter(Boolean).map((w) => w[0]).join("").slice(0, 2).toUpperCase();
  const shortName = (name: string) => (name.length <= 11 ? name : name.split(" ").slice(-1)[0]);
  const px = (x: number) => (x / 100) * W;
  const py = (y: number) => ((lineup.opts.gkTop ? 100 - y : y) / 100) * H;          // « gardien en haut » : le terrain est retourné
  const pts = (list: [number, number][]) => list.map(([u, v]) => `${u.toFixed(2)},${v.toFixed(2)}`).join(" ");
  const rect = (x: number, y: number, w: number, h: number): [number, number][] => [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
  const circle = (cx: number, cy: number, r: number): [number, number][] => Array.from({ length: 64 }, (_, i) => [cx + r * Math.cos((i / 64) * 2 * Math.PI), cy + r * Math.sin((i / 64) * 2 * Math.PI)]);
  const at = (s: { x: number; y: number }) => ({ x: px(s.x), y: py(s.y) });
  const flagSrc = (code: string) => `${import.meta.env.BASE_URL}flags/${code}.svg`;
  let tab = $state<"formation" | "style" | "options">("formation");
  // Téléphone : tout tient sur un écran. Le terrain prend la hauteur disponible et les réglages s'ouvrent dans une feuille ; sur grand écran ils restent à côté du terrain.
  let desktop = $state(typeof matchMedia !== "undefined" && matchMedia("(min-width: 1024px)").matches);
  let settings = $state(false);
  $effect(() => {
    const mq = matchMedia("(min-width: 1024px)"), on = () => (desktop = mq.matches);
    mq.addEventListener("change", on); on();
    return () => mq.removeEventListener("change", on);
  });

  // Styles prêts à l'emploi (un tap) ; les réglages fins sont repliés sous « Personnaliser ».
  const presets = $derived([
    ...(!find && colors.length ? [{ key: "club", label: t("lineupPresetClub"), run: () => { lineup = { ...lineup, display: "number", style: clubStyle() }; } }] : []),
    { key: "classic", label: t("lineupPresetClassic"), run: () => { lineup = { ...lineup, display: find ? "initials" : "number", style: defaultStyle() }; } },
    { key: "minimal", label: t("lineupPresetMinimal"), run: () => { lineup = { ...lineup, display: "none", style: { ...defaultStyle(), color: "#111827", size: 90 } }; } },
  ]);

  async function share() {
    const url = `${location.origin}${location.pathname}${base}&${encodeLineup(lineup)}`;
    // Téléphone : la feuille de partage du système ; ailleurs (ou à défaut) le lien est copié.
    if (!desktop && typeof navigator.share === "function") {
      try { await navigator.share({ title: heading, url }); return; } catch (e: any) { if (e?.name === "AbortError") return; }
    }
    try { await navigator.clipboard.writeText(url); notify(t("lineupCopied")); } catch { prompt(t("lineupShare"), url); }
  }

  let svg: SVGSVGElement | undefined = $state();
  /** Image PNG : le terrain est un SVG aux couleurs fixes, dessiné tel quel sur un canvas (aucune bibliothèque). */
  async function exportPng() {
    if (!svg) return;
    const clone = svg.cloneNode(true) as SVGSVGElement;
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clone.querySelectorAll("[data-ui], [data-logo], [data-photo], [data-flag], clipPath[data-ext]").forEach((n) => n.remove());          // l'interface (zones de tap, poste actif) n'est pas dans l'image ; une image externe ne se charge pas dans un SVG exporté : on la dessine sur le canvas
    const scale = 12;
    clone.setAttribute("width", String(W * scale)); clone.setAttribute("height", String(H * scale));
    const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(clone)], { type: "image/svg+xml" }));
    try {
      const img = new Image();
      await new Promise<void>((ok, ko) => { img.onload = () => ok(); img.onerror = () => ko(new Error("svg")); img.src = url; });
      const c = document.createElement("canvas"); c.width = W * scale; c.height = H * scale;
      const ctx = c.getContext("2d")!;
      ctx.drawImage(img, 0, 0);
      if (logo) {
        try {
          const lg = new Image(); lg.crossOrigin = "anonymous";
          await new Promise<void>((ok, ko) => { lg.onload = () => ok(); lg.onerror = () => ko(new Error("logo")); lg.src = logo; });
          const f = Math.min(8 / lg.naturalWidth, 8 / lg.naturalHeight) * scale;
          ctx.drawImage(lg, 8.5 * scale - (lg.naturalWidth * f) / 2, 8.5 * scale - (lg.naturalHeight * f) / 2, lg.naturalWidth * f, lg.naturalHeight * f);
        } catch { /* sans blason si l'image ne se charge pas */ }
      }
      // Photos des joueurs : dessinées sur le canvas, rognées en rond et alignées sur le haut (le visage).
      await Promise.all(slots.map(async (s, i) => {
        const src = photoOf(i); if (!src) return;
        try {
          const ph = new Image(); ph.crossOrigin = "anonymous";
          await new Promise<void>((ok, ko) => { ph.onload = () => ok(); ph.onerror = () => ko(new Error("photo")); ph.src = src; });
          const side = Math.min(ph.naturalWidth, ph.naturalHeight) / Z, p = at(s), cx = p.x * scale, cy = p.y * scale, rr = (R * ms - 0.25) * scale;
          ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, rr, 0, Math.PI * 2); ctx.clip();
          ctx.drawImage(ph, (ph.naturalWidth - side) / 2, 0, side, side, cx - rr, cy - rr, rr * 2, rr * 2);
          ctx.restore();
        } catch { /* les initiales restent si la photo ne se charge pas */ }
      }));
      // Drapeaux (fichiers du site, même origine) : dessinés sur le canvas aux mêmes places.
      if (lineup.opts.nat) await Promise.all(slots.map(async (s, i) => {
        const code = flagCode(i); if (!code) return;
        try {
          const fl = new Image();
          await new Promise<void>((ok, ko) => { fl.onload = () => ok(); fl.onerror = () => ko(new Error("flag")); fl.src = flagSrc(code); });
          const pl = plates[i]; if (!pl) return;
          const d = fl.naturalWidth && fl.naturalHeight ? Math.min(fl.naturalWidth, fl.naturalHeight) : 1, rr = (pl.fr - 0.15) * scale;
          ctx.save(); ctx.beginPath(); ctx.arc(pl.fx * scale, pl.fy * scale, rr, 0, Math.PI * 2); ctx.clip();
          ctx.drawImage(fl, (fl.naturalWidth - d) / 2, (fl.naturalHeight - d) / 2, d, d, pl.fx * scale - rr, pl.fy * scale - rr, rr * 2, rr * 2);
          ctx.restore();
        } catch { /* sans drapeau */ }
      }));
      const blob = await new Promise<Blob | null>((ok) => c.toBlob(ok, "image/png"));
      if (!blob) throw new Error("png");
      const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
      a.download = `${heading.replace(/[^\w-]+/g, "_")}-${lineup.formation}.png`; a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      notify(t("lineupPngDone"));
    } catch { notify(t("lineupPngError")); } finally { URL.revokeObjectURL(url); }
  }

  const BTN = "flex h-14 min-w-0 flex-col items-center justify-center gap-0.5 rounded-xl border px-1 text-[0.6875rem] font-semibold transition disabled:opacity-50 lg:h-10 lg:flex-row lg:gap-2 lg:px-3 lg:text-sm";
  const GHOST = `${BTN} border-line bg-surface hover:bg-surface-2`;
</script>

{#snippet icon(d: string)}<svg viewBox="0 0 24 24" class="size-5 shrink-0 lg:size-4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d={d} /></svg>{/snippet}

{#snippet toggle(label: string, on: boolean, set: (v: boolean) => void)}
  <li>
    <button type="button" role="switch" aria-checked={on} class="flex min-h-11 w-full items-center justify-between gap-3 px-3.5 text-left transition hover:bg-surface-2" onclick={() => set(!on)}>
      <span class="text-sm font-medium">{label}</span>
      <span class="relative h-6 w-11 shrink-0 rounded-full transition {on ? 'bg-accent' : 'bg-line'}" aria-hidden="true"><span class="absolute top-0.5 size-5 rounded-full bg-white shadow transition-all {on ? 'left-[1.375rem]' : 'left-0.5'}"></span></span>
    </button>
  </li>
{/snippet}

{#snippet swatches(value: string, set: (c: string) => void)}
  <div class="mt-1.5 flex flex-wrap items-center gap-1.5" role="group" aria-label={t("lineupColor")}>
    {#each [...new Set([...colors.map((c) => c.toLowerCase()), ...PALETTE])] as c (c)}
      <button type="button" class="size-6 rounded-full border-2 transition {value.toLowerCase() === c ? 'border-accent ring-2 ring-accent/40' : 'border-line'}" style="background:{c}" aria-label={c} aria-pressed={value.toLowerCase() === c} onclick={() => set(c)}></button>
    {/each}
    <label class="relative grid size-6 cursor-pointer place-items-center overflow-hidden rounded-full border-2 border-line bg-surface text-lg font-bold leading-none text-muted" title={t("lineupCustomColor")}>
      <input type="color" class="absolute -inset-2 size-[200%] cursor-pointer opacity-0" {value} aria-label={t("lineupCustomColor")} oninput={(e) => set(e.currentTarget.value)} /><span aria-hidden="true">+</span>
    </label>
  </div>
{/snippet}

{#snippet slider(label: string, value: number, set: (v: number) => void)}
  <label class="mt-2 flex items-center gap-3 text-sm">
    <span class="w-24 shrink-0 text-muted">{label}</span>
    <input type="range" min="60" max="150" step="5" {value} class="min-w-0 flex-1 accent-accent" oninput={(e) => set(+e.currentTarget.value)} />
    <span class="w-11 shrink-0 text-right tabular-nums text-muted">{value}%</span>
  </label>
{/snippet}

{#snippet panel()}
  <Segmented class="sm:w-full! sm:[&>button]:flex-1" label={t("lineupPanel")} idPrefix="lup" value={tab} onselect={(k) => (tab = k)}
    items={[{ key: "formation", label: t("lineupTabFormation") }, { key: "style", label: t("lineupTabStyle") }, { key: "options", label: t("lineupTabOptions") }]} />

  <div class="card mt-2 p-3 lg:mt-3">
    {#if tab === "formation"}
      <div class="grid grid-cols-3 gap-2 sm:grid-cols-4 lg:grid-cols-3" role="group" aria-label={t("lineupFormation")}>
        {#each FORMATION_NAMES as f (f)}
          <button type="button" class="min-h-10 whitespace-nowrap rounded-lg border px-1 text-[0.8125rem] font-semibold tabular-nums transition {lineup.formation === f ? 'border-accent bg-accent text-accent-fg' : 'border-line bg-surface hover:bg-surface-2'}" aria-pressed={lineup.formation === f} onclick={() => setFormation(f)}>{f}</button>
        {/each}
      </div>
      <div class="mt-3 flex flex-wrap gap-2">
        {#if !find}<button type="button" class="h-10 rounded-xl border border-line bg-surface px-3.5 text-sm font-semibold transition hover:bg-surface-2" onclick={autoFill}>{t("lineupAuto")}</button>{/if}
        <button type="button" class="h-10 rounded-xl border border-line bg-surface px-3.5 text-sm font-semibold text-warn transition hover:bg-surface-2 disabled:opacity-50" disabled={!filled} onclick={() => (lineup = cleared())}>{t("lineupClearAll")}</button>
      </div>
    {:else if tab === "style"}
      <p class="eyebrow">{t("lineupPresets")}</p>
      <div class="mt-2 grid grid-cols-{presets.length} gap-2" role="group" aria-label={t("lineupPresets")}>
        {#each presets as p (p.key)}
          <button type="button" class="min-h-10 rounded-lg border border-line bg-surface px-1 text-xs font-semibold transition hover:bg-surface-2" onclick={p.run}>{p.label}</button>
        {/each}
      </div>

      <p class="eyebrow mt-3">{t("lineupContent")}</p>
      <div class="mt-2 grid grid-cols-3 gap-2" role="group" aria-label={t("lineupContent")}>
        {#each DISPLAYS as d (d)}
          <button type="button" class="min-h-10 rounded-lg border px-1 text-xs font-semibold transition {lineup.display === d ? 'border-accent bg-accent text-accent-fg' : 'border-line bg-surface hover:bg-surface-2'}" aria-pressed={lineup.display === d} onclick={() => (lineup.display = d)}>{t("disp_" + d)}</button>
        {/each}
      </div>
      {#if lineup.display === "photo"}<p class="mt-2 text-xs text-muted">{t("lineupPhotoNote")}</p>{/if}

      <details class="group mt-3 rounded-xl border border-line">
        <summary class="flex min-h-11 cursor-pointer list-none items-center justify-between px-3.5 text-sm font-semibold [&::-webkit-details-marker]:hidden">
          {t("lineupCustomize")}<svg viewBox="0 0 24 24" class="size-4 text-muted transition group-open:rotate-180" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
        </summary>
        <div class="border-t border-line/60 p-3.5 pt-1">
          <p class="eyebrow mt-2">{t("lineupMarker")}</p>
          <div class="mt-2 grid grid-cols-2 gap-2" role="group" aria-label={t("lineupMarker")}>
            {#each ["circle", "jersey"] as const as m (m)}
              <button type="button" class="min-h-10 rounded-lg border px-2 text-sm font-semibold transition {lineup.style.marker === m ? 'border-accent bg-accent text-accent-fg' : 'border-line bg-surface hover:bg-surface-2'}" aria-pressed={lineup.style.marker === m} onclick={() => (lineup.style.marker = m)}>{t("mk_" + m)}</button>
            {/each}
          </div>
          {#if lineup.style.marker === "jersey" && lineup.display === "photo"}<p class="mt-2 text-xs text-muted">{t("lineupJerseyPhoto")}</p>{/if}

          <p class="eyebrow mt-3">{t("lineupColor")}</p>
          {@render swatches(lineup.style.color, (c) => (lineup.style.color = c))}
          {#if lineup.style.marker === "jersey"}
            <p class="eyebrow mt-3">{t("lineupPattern")}</p>
            <div class="mt-2 grid grid-cols-4 gap-2" role="group" aria-label={t("lineupPattern")}>
              {#each PATTERNS as pt (pt)}
                <button type="button" class="min-h-9 rounded-lg border px-1 text-xs font-semibold transition {lineup.style.pattern === pt ? 'border-accent bg-accent text-accent-fg' : 'border-line bg-surface hover:bg-surface-2'}" aria-pressed={lineup.style.pattern === pt} onclick={() => (lineup.style.pattern = pt)}>{t("pt_" + pt)}</button>
              {/each}
            </div>
            {#if lineup.style.pattern !== "plain"}
              <p class="eyebrow mt-3">{t("lineupColor2")}</p>
              {@render swatches(lineup.style.color2, (c) => (lineup.style.color2 = c))}
            {/if}
          {/if}
          <p class="eyebrow mt-3">{t("lineupGkColor")}</p>
          {@render swatches(lineup.style.gk, (c) => (lineup.style.gk = c))}

          <p class="eyebrow mt-3">{t("lineupSizes")}</p>
          {@render slider(t("lineupSizeMarker"), lineup.style.size, (v) => (lineup.style.size = v))}
          {@render slider(t("lineupSizeLabel"), lineup.style.label, (v) => (lineup.style.label = v))}
          {@render slider(t("lineupSizeName"), lineup.style.name, (v) => (lineup.style.name = v))}
        </div>
      </details>
    {:else}
      <label class="eyebrow" for="lineup-title">{t("lineupTitleLabel")}</label>
      <input id="lineup-title" type="text" maxlength="40" class="mb-2.5 mt-1 h-10 w-full rounded-xl border border-line bg-bg px-3 text-base" placeholder={caption} bind:value={lineup.title} />
      <label class="eyebrow" for="lineup-subtitle">{t("lineupSubtitle")}</label>
      <input id="lineup-subtitle" type="text" maxlength="60" class="mb-3 mt-1 h-10 w-full rounded-xl border border-line bg-bg px-3 text-base" placeholder={t("lineupSubtitlePh")} bind:value={lineup.subtitle} />
      <ul class="divide-y divide-line/60 overflow-hidden rounded-xl border border-line">
        {@render toggle(t("lineupShowFormation"), lineup.opts.formation, (v) => (lineup.opts.formation = v))}
        {#if logo}{@render toggle(t("lineupShowBadge"), lineup.opts.badge, (v) => (lineup.opts.badge = v))}{/if}
        {@render toggle(t("lineupShowPhotos"), lineup.display === "photo", (v) => (lineup.display = v ? "photo" : find ? "initials" : "number"))}
        {@render toggle(t("lineupShowNat"), lineup.opts.nat, (v) => (lineup.opts.nat = v))}
        {@render toggle(t("lineupGkTop"), lineup.opts.gkTop, (v) => (lineup.opts.gkTop = v))}
      </ul>
    {/if}
  </div>
{/snippet}

<!-- Choix du joueur d'un poste : la liste de l'effectif (ou une recherche dans toute la base), avec le numéro libre quand il est choisi. -->
{#snippet picker()}
  {#if open !== null}
    <div class="flex items-center justify-between gap-3 px-4 pb-2 pt-3">
      <h2 class="min-w-0 truncate text-base font-bold">{t("lineupPick")} · {slotRole ? roleLabel(slotRole.role, app.lang) : ""} <span class="font-semibold tabular-nums text-muted">{filled}/{slots.length}</span></h2>
      <button type="button" class="grid size-10 shrink-0 place-items-center rounded-xl text-muted transition hover:bg-surface-2 hover:text-fg" aria-label={t("close")} onclick={closePicker}>
        <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg>
      </button>
    </div>
    <div class="px-4 pb-2">
      <input type="search" class="h-11 w-full rounded-xl border border-line bg-bg px-3 text-base" placeholder={t("lineupSearch")} aria-label={t("lineupSearch")} bind:value={search} />
    </div>
    {#if lineup.display === "free"}
      <div class="flex items-center gap-3 px-4 pb-2">
        <label class="text-sm font-semibold text-muted" for="lineup-num">{t("lineupFreeNumber")}</label>
        <input id="lineup-num" type="number" min="0" max="99" inputmode="numeric" class="h-11 w-20 rounded-xl border border-line bg-bg px-3 text-base tabular-nums" placeholder={String(open + 1)}
          value={lineup.nums[open] ?? ""} oninput={(e) => { const n = parseInt(e.currentTarget.value, 10); const nums = [...lineup.nums]; nums[open!] = n >= 0 && n <= 99 ? n : null; lineup = { ...lineup, nums }; }} />
      </div>
    {/if}
    <ul class="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
      {#if lineup.players[open]}
        <li><button type="button" class="flex min-h-11 w-full items-center rounded-xl px-3 text-left text-sm font-semibold text-warn hover:bg-surface-2" onclick={() => assign(open!, null)}>{t("lineupRemove")}</button></li>
      {/if}
      {#each candidates as r (r.key)}
        {@const here = lineup.players[open] === r.key}
        <li>
          <button type="button" class="flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-left hover:bg-surface-2 {here ? 'bg-accent-soft' : ''}" onclick={() => assign(open!, r.key as string)}>
            <span class="w-6 shrink-0 text-right text-sm tabular-nums text-muted">{r.shirt_number ?? ""}</span>
            <span class="min-w-0 flex-1 truncate font-medium">{r.player}{#if find && r.club}<span class="block truncate text-xs font-normal text-muted">{clubName(clubOf(r.club))}{r.last ? ` · ${r.last}` : ""}</span>{/if}</span>
            {#if placed.has(r.key as string) && !here}<span class="shrink-0 text-xs text-muted">{t("lineupPlaced")}</span>{/if}
            <PosPill pos={r.position} small />
          </button>
        </li>
      {:else}
        <li class="px-3 py-4 text-sm text-muted">{find && search.trim().length < 2 ? t("lineupTypeName") : searching ? t("loading") : t("sqNoMatch")}</li>
      {/each}
    </ul>
  {/if}
{/snippet}

<svelte:window onkeydown={(e) => { if (e.key === "Escape" && open !== null) closePicker(); }} />

<p class="sr-only" role="status" aria-live="polite">{filled}/{slots.length}</p>

<div class="mt-2 grid items-start gap-3 lg:mt-4 lg:grid-cols-[minmax(0,1fr)_20rem] lg:gap-6">
  <div bind:this={pitchBox} bind:clientWidth={pitchPx} class="relative mx-auto aspect-[68/105] w-[min(100%,calc((100dvh-var(--lu-chrome,24.5rem))*0.6476))] min-w-40 transition-transform duration-200 motion-reduce:transition-none lg:mx-0 lg:w-[min(100%,calc((100dvh-18rem)*0.6476))] lg:min-w-72 {shift ? 'z-[60]' : ''}" style={shift ? `transform: translateY(-${shift}px)` : ""}>
    <svg bind:this={svg} viewBox="0 0 {W} {H}" class="block size-full rounded-2xl" role="group" aria-label={t("lineupPitch")} font-family="system-ui, -apple-system, 'Segoe UI', sans-serif">
      <rect width={W} height={H} fill="#2f7d4a" />
      {#each [0, 1, 2, 3, 4, 5, 6] as i (i)}<polygon points={pts(rect(0, i * 15, W, 7.5))} fill="#fff" fill-opacity="0.05" />{/each}
      <g fill="none" stroke="#fff" stroke-opacity="0.7" stroke-width="0.35" stroke-linejoin="round">
        <polygon points={pts(rect(1, 1, W - 2, H - 2))} />
        <polyline points={pts([[1, H / 2], [W - 1, H / 2]])} />
        <polygon points={pts(circle(W / 2, H / 2, 9.15))} />
        <polygon points={pts(rect(W / 2 - 20.16, 1, 40.32, 16.5))} /><polygon points={pts(rect(W / 2 - 9.16, 1, 18.32, 5.5))} />
        <polygon points={pts(rect(W / 2 - 20.16, H - 17.5, 40.32, 16.5))} /><polygon points={pts(rect(W / 2 - 9.16, H - 6.5, 18.32, 5.5))} />
      </g>
      {#if logo && lineup.opts.badge}
        <circle cx="8.5" cy="8.5" r="6.2" fill="#fff" fill-opacity="0.92" />
        <image data-logo href={logo} x="4.5" y="4.5" width="8" height="8" preserveAspectRatio="xMidYMid meet" />
      {/if}
      <g stroke="#14532d" stroke-width="0.7" paint-order="stroke" stroke-linejoin="round" text-anchor="end">
        <text x={W - 3} y="5" font-size="2.6" font-weight="800" fill="#fff">{heading}</text>
        {#if lineup.subtitle.trim()}<text x={W - 3} y="8.2" font-size="2.1" fill="#fff">{lineup.subtitle.trim()}</text>{/if}
        {#if lineup.opts.formation}<text x={W - 3} y={lineup.subtitle.trim() ? 11.2 : 8.2} font-size="2.1" fill="#fff">{lineup.formation}</text>{/if}
      </g>
      <text bind:this={probe} data-ui aria-hidden="true" x="0" y="0" font-size="100" font-weight="800" visibility="hidden"> </text>
      {#each slots as s, i (i)}
        {@const p = at(s)}
        {@const r = lineup.players[i] ? byKey.get(lineup.players[i]!) : null}
        <g role="button" tabindex="0" class="cursor-pointer outline-none [&:focus-visible_.lu-hit]:stroke-[#ffd54a] [&:focus-visible_.lu-hit]:stroke-[0.7]" aria-label="{roleLabel(s.role, app.lang)} — {r ? r.player : t('lineupEmpty')}" aria-pressed={open === i}
          onclick={() => (open = i)} onkeydown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open = i; } }}>
          <!-- zone de tap de 44 px minimum (≈ 6,4 unités de rayon sur un terrain de téléphone), visible au clavier par son contour -->
          <circle data-ui class="lu-hit" cx={p.x} cy={p.y} r="6.4" fill="#000" fill-opacity="0" stroke="transparent" />
          {#if open === i}<circle data-ui cx={p.x} cy={p.y} r={(isJersey ? R * 1.15 : R) * ms + 1.2} fill="#ffd54a" fill-opacity="0.18" stroke="#ffd54a" stroke-width="0.7" />{/if}
          {#if r}
            {@const txt = badge(i, r)}
            {@const gk = s.line === "GK"}
            {@const col = gk ? lineup.style.gk : lineup.style.color}
            {#if isJersey}
              <g transform="translate({p.x} {p.y}) scale({R * 1.15 * ms})">
                <clipPath id="lu-jc-{i}"><path d={JERSEY} /></clipPath>
                <g clip-path="url(#lu-jc-{i})">
                  <rect x="-1" y="-1" width="2" height="2" fill={col} />
                  {#if !gk && lineup.style.pattern === "halves"}<rect x="0" y="-1" width="1" height="2" fill={lineup.style.color2} />{/if}
                  {#if !gk && lineup.style.pattern === "stripes"}{#each [1, 3] as b (b)}<rect x={-1 + b * 0.4} y="-1" width="0.4" height="2" fill={lineup.style.color2} />{/each}{/if}
                  {#if !gk && lineup.style.pattern === "hoops"}{#each [1, 3] as b (b)}<rect x="-1" y={-1 + b * 0.4} width="2" height="0.4" fill={lineup.style.color2} />{/each}{/if}
                </g>
                <path d={JERSEY} fill="none" stroke="#111827" stroke-width="0.09" stroke-linejoin="round" />
                {#if txt}{@const fs = fitJersey(txt, ls)}<text x="0" y={0.22 + fs * 0.36} text-anchor="middle" font-size={fs} font-weight="800" fill={ink(col)} stroke={ink(col) === "#ffffff" ? "#111827" : "#ffffff"} stroke-width="0.07" paint-order="stroke">{txt}</text>{/if}
              </g>
            {:else}
              <circle cx={p.x} cy={p.y} r={R * ms} fill={col} stroke="#14532d" stroke-width="0.5" />
              {#if txt}{@const fs = fitCircle(txt, ms, ls)}<text x={p.x} y={p.y + fs * 0.36} text-anchor="middle" font-size={fs} font-weight="800" fill={ink(col)}>{txt}</text>{/if}
            {/if}
            {#if photoOf(i)}
              <clipPath data-ext id="lu-clip-{i}"><circle cx={p.x} cy={p.y} r={R * ms - 0.25} /></clipPath>
              <image data-photo={i} href={photoOf(i)} x={p.x - (R * ms - 0.25) * Z} y={p.y - (R * ms - 0.25)} width={(R * ms - 0.25) * 2 * Z} height={(R * ms - 0.25) * 2 * Z} preserveAspectRatio="xMidYMin slice" clip-path="url(#lu-clip-{i})" />
            {/if}
            {@const fl = lineup.opts.nat && !!flagCode(i)}
            {@const pl = plates[i]}
            <rect x={pl.x0} y={pl.y0} width={pl.w} height={pl.h} rx={pl.h / 2} fill="#101a14" fill-opacity="0.9" />
            <text x={pl.tx} y={pl.ty} text-anchor={pl.anchor} font-size={pl.fs} font-weight="800" fill="#fff">{pl.label}</text>
            {#if fl}
              <circle cx={pl.fx} cy={pl.fy} r={pl.fr} fill="#fff" stroke="#fff" stroke-width="0.2" />
              <clipPath data-ext id="lu-flag-{i}"><circle cx={pl.fx} cy={pl.fy} r={pl.fr - 0.15} /></clipPath>
              <image data-flag href={flagSrc(flagCode(i)!)} x={pl.fx - pl.fr} y={pl.fy - pl.fr} width={pl.fr * 2} height={pl.fr * 2} preserveAspectRatio="xMidYMid slice" clip-path="url(#lu-flag-{i})" />
            {/if}
          {:else}
            <circle cx={p.x} cy={p.y} r={R * ms} fill="#000" fill-opacity="0.25" stroke="#fff" stroke-opacity="0.9" stroke-width="0.4" stroke-dasharray="1.2 0.9" />
            <path d="M{p.x - ms} {p.y}h{2 * ms}M{p.x} {p.y - ms}v{2 * ms}" stroke="#fff" stroke-width="0.6" stroke-linecap="round" />
            <text x={p.x} y={p.y + R * ms + 0.8 + Math.max(1.9, minU)} text-anchor="middle" font-size={Math.max(1.9, minU)} font-weight="700" fill="#fff" stroke="#14532d" stroke-width="0.5" paint-order="stroke">{roleLabel(s.role, app.lang)}</text>
          {/if}
        </g>
      {/each}
    </svg>

    <!-- Terrain vide : dire quoi faire, et offrir le raccourci -->
    {#if filled === 0 && open === null}
      <div class="pointer-events-none absolute left-1/2 top-1/2 flex w-max max-w-[calc(100%-1.5rem)] -translate-x-1/2 -translate-y-1/2 items-center justify-center gap-3 rounded-2xl bg-bg/95 px-3 py-2 shadow-lg">
        <p class="min-w-0 text-xs font-semibold leading-snug">{t("lineupEmptyHint")}</p>
        {#if !find}<button type="button" class="pointer-events-auto h-9 shrink-0 rounded-xl bg-accent px-3 text-xs font-bold text-accent-fg transition hover:opacity-90" onclick={autoFill}>{t("lineupAuto")}</button>{/if}
      </div>
    {/if}
  </div>

  <div class="min-w-0">
    {#if desktop}
      {#if open !== null}
        <div class="card flex max-h-[calc(100dvh-14rem)] min-h-64 flex-col overflow-hidden">{@render picker()}</div>
      {:else}
        {@render panel()}
      {/if}
    {/if}
    <div class="grid grid-cols-4 gap-2 lg:mt-3 lg:flex lg:flex-wrap lg:items-center">
      <button type="button" class="{GHOST} lg:hidden" onclick={() => (settings = true)}>{@render icon("M4 7h10M18 7h2M4 17h2M10 17h10M16 7m-2 0a2 2 0 1 0 4 0 2 2 0 1 0-4 0M8 17m-2 0a2 2 0 1 0 4 0 2 2 0 1 0-4 0")}<span>{t("lineupSettings")}</span></button>
      <button type="button" class="{BTN} border-accent bg-accent text-accent-fg hover:opacity-90 disabled:border-line disabled:bg-surface-2 disabled:text-muted disabled:opacity-100 lg:basis-full lg:font-bold" disabled={!filled} onclick={share}>{@render icon("M12 16V4m0 0-4 4m4-4 4 4M5 14v5h14v-5")}<span class="lg:hidden">{t("lineupShareShort")}</span><span class="hidden lg:inline">{t("lineupShare")}</span></button>
      <button type="button" class={GHOST} disabled={!filled} onclick={exportPng}>{@render icon("M4 5h16v14H4zM4 15l5-5 4 4 3-3 4 4")}<span class="lg:hidden">{t("lineupPngShort")}</span><span class="hidden lg:inline">{t("lineupPng")}</span></button>
      <button type="button" class={GHOST} disabled={!past.length} onclick={undo} aria-label={t("lineupUndo")}>{@render icon("M9 14 4 9l5-5M4 9h10a6 6 0 0 1 0 12h-3")}<span class="lg:sr-only">{t("lineupUndo")}</span></button>
      <button type="button" class="{GHOST} max-lg:hidden" disabled={!future.length} onclick={redo} aria-label={t("lineupRedo")}>{@render icon("m15 14 5-5-5-5M20 9H10a6 6 0 0 0 0 12h3")}<span class="sr-only">{t("lineupRedo")}</span></button>
      <span class="ml-auto hidden text-sm tabular-nums text-muted lg:inline">{filled}/{slots.length}</span>
    </div>

    <p class="mt-2 hidden text-xs text-muted lg:block">{t("lineupNote")}</p>
  </div>
</div>

<!-- Téléphone : réglages dans une feuille ; choix du joueur dans un tiroir bas qui laisse le terrain visible -->
<Sheet open={settings && !desktop} onclose={() => (settings = false)} title={t("lineupPanel")}>
  <div class="overflow-y-auto px-5 pb-5">
    {@render panel()}
  </div>
</Sheet>

{#if open !== null && !desktop}
  <div class="fixed inset-x-0 bottom-0 z-[70] flex h-[44dvh] flex-col rounded-t-3xl border border-line bg-surface pb-[env(safe-area-inset-bottom)] shadow-2xl" role="region" aria-label={t("lineupPick")}>
    {@render picker()}
  </div>
{/if}
