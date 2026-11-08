// Play Room v111: online 2-player from the game's own Multiplayer menu (title screen, cursor 2) instead of a Host
// button on the setup screen. Picking Host or Join stores the choice and reloads; Play then hosts or joins.
  $("mpCancel").addEventListener("click", () => { mpReset(); $("mpField").hidden = true; $("play").hidden = false; $("play").textContent = "Play game"; });
  window.__onlineStart = async (o) => {
    mpStatus("Getting 2-player ready…");
    for (let i = 0; i < 60 && (!lobby || !romBytes); i++) await new Promise((r) => setTimeout(r, 250));
    if (!lobby) { mpStatus("2-player games need you signed in to Claude on this page.", "bad"); return; }
    if (o.host) hostGame(); else joinGame(o.join);
  };
  // The game's Multiplayer menu (title screen) opens this list: host a game, or join one a friend is hosting.
  window.__onlineMenu = () => {
    if (!lobby || (window.__mp && !window.__mp.wide)) return false;
    let el = document.getElementById("mpPick");
    if (!el) { el = document.createElement("div"); el.id = "mpPick"; const host = $("p2Pick"); (host ? host.parentElement : document.body).appendChild(el); }
    el.innerHTML = ""; el.hidden = false;
    const add = (label, fn, cls) => { const b = document.createElement("button"); b.type = "button"; b.textContent = label; if (cls) b.className = cls; b.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); fn(); }); el.appendChild(b); };
    const h = document.createElement("div"); h.className = "p2-title"; h.textContent = "Play together online"; el.appendChild(h);
    const n = document.createElement("div"); n.className = "p2-note"; n.textContent = "Save first: the page restarts into the 2-player game. Your friend needs access to this Play Room."; el.appendChild(n);
    const go = (o) => { try { sessionStorage.setItem("rotk-online", JSON.stringify(o)); } catch (e) {} location.reload(); };
    add("Host a game", () => go({ host: 1 }), "p2-main");
    const hosts = lobby.peers().filter((p) => !p.sameTab && p.presence && p.presence.host && typeof p.presence.host.room === "string" && /^rotk-[a-z0-9]{4,20}$/.test(p.presence.host.room));
    (async () => {
      let profs = {}; try { const ids = hosts.map((p) => p.by).filter(Boolean); if (ids.length) profs = await userApi.profiles(ids); } catch (e) {}
      for (const p of hosts) { const nm = (p.by && profs[p.by] && profs[p.by].name) || "a friend"; add("Join " + nm + "’s game", () => go({ join: p.presence.host.room, name: nm }), "p2-hero"); }
      add("Cancel", () => { el.hidden = true; });
    })();
    return true;
  };
  $("mpHost").addEventListener("click", () => hostGame());
  async function hostGame() {
    if (!romBytes || mpBusy || !lobby) return;
    mpBusy = true; unlockAudio(); $("mpHost").disabled = true;
