class PortugalFootballCard extends HTMLElement {
  setConfig(config) {
    this.config = {
      view: "live",
      live_entity: "sensor.portugal_football_jogos_ao_vivo",
      table_entity: "sensor.portugal_football_classificacao",
      fixtures_entity: "sensor.portugal_football_proximos_jogos",
      scorers_entity: "sensor.portugal_football_melhores_marcadores",
      stats_entity: "sensor.portugal_football_estatisticas",
      ...config,
    };
    if (!["live", "table", "fixtures", "scorers", "stats"].includes(this.config.view)) {
      throw new Error("view must be live, table, fixtures, scorers or stats");
    }
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return this.config?.view === "table" ? 8 : 5;
  }

  esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[c]));
  }

  fmtDate(value) {
    if (!value) return "";
    try {
      return new Intl.DateTimeFormat("pt-PT", {
        weekday: "short", day: "2-digit", month: "2-digit",
        hour: "2-digit", minute: "2-digit"
      }).format(new Date(value));
    } catch (_) {
      return value;
    }
  }

  crest(url, name) {
    return url ? `<img class="crest" src="${this.esc(url)}" alt="${this.esc(name)}">` : "";
  }

  render() {
    if (!this._hass || !this.config) return;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });

    const css = `
      :host { display:block; }
      ha-card { padding:16px; overflow:hidden; }
      .head { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:14px; }
      .title { font-size:1.25rem; font-weight:700; }
      .badge { font-size:.78rem; padding:4px 9px; border-radius:999px; background:var(--primary-color); color:var(--text-primary-color); }
      .muted { color:var(--secondary-text-color); }
      .game { padding:12px 0; border-top:1px solid var(--divider-color); }
      .teams { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:10px; }
      .team { display:flex; align-items:center; gap:8px; min-width:0; }
      .team.right { justify-content:flex-end; text-align:right; }
      .crest { width:28px; height:28px; object-fit:contain; flex:0 0 auto; }
      .score { font-weight:800; font-size:1.3rem; white-space:nowrap; }
      table { width:100%; border-collapse:collapse; font-size:.9rem; }
      th, td { padding:7px 5px; border-bottom:1px solid var(--divider-color); text-align:center; }
      th:nth-child(2), td:nth-child(2) { text-align:left; }
      tr:first-child td { font-weight:700; }
      .row-team { display:flex; align-items:center; gap:7px; }
      .row-team .crest { width:22px; height:22px; }
      .statgrid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
      .stat { padding:12px; border:1px solid var(--divider-color); border-radius:12px; }
      .stat strong { display:block; font-size:1.05rem; margin-top:3px; }
      .scorer { display:grid; grid-template-columns:auto 1fr auto; align-items:center; gap:9px; padding:9px 0; border-top:1px solid var(--divider-color); }
      .empty { padding:22px 0; text-align:center; color:var(--secondary-text-color); }
      @media (max-width:460px) {
        ha-card { padding:12px; }
        .statgrid { grid-template-columns:1fr; }
        th:nth-child(5), td:nth-child(5), th:nth-child(6), td:nth-child(6), th:nth-child(7), td:nth-child(7) { display:none; }
      }
    `;

    let body = "";
    if (this.config.view === "live") body = this.renderLive();
    if (this.config.view === "table") body = this.renderTable();
    if (this.config.view === "fixtures") body = this.renderFixtures();
    if (this.config.view === "scorers") body = this.renderScorers();
    if (this.config.view === "stats") body = this.renderStats();

    this.shadowRoot.innerHTML = `<style>${css}</style><ha-card>${body}</ha-card>`;
  }

  entity(id) {
    return this._hass.states[id];
  }

  renderLive() {
    const e = this.entity(this.config.live_entity);
    const games = e?.attributes?.matches || [];
    return `
      <div class="head"><div class="title">⚽ Liga Portugal — Ao vivo</div><div class="badge">${games.length} LIVE</div></div>
      ${games.length ? games.map(g => `
        <div class="game">
          <div class="muted">${this.esc(g.status)} ${g.minute ? "• " + this.esc(g.minute) + "'" : ""}</div>
          <div class="teams">
            <div class="team">${this.crest(g.home_crest,g.home_team)}<span>${this.esc(g.home_team)}</span></div>
            <div class="score">${this.esc(g.home_score ?? "-")} – ${this.esc(g.away_score ?? "-")}</div>
            <div class="team right"><span>${this.esc(g.away_team)}</span>${this.crest(g.away_crest,g.away_team)}</div>
          </div>
        </div>
      `).join("") : '<div class="empty">Não há jogos da Liga Portugal ao vivo neste momento.</div>'}
    `;
  }

  renderTable() {
    const e = this.entity(this.config.table_entity);
    const rows = e?.attributes?.table || [];
    return `
      <div class="head"><div class="title">🇵🇹 Liga Portugal — Classificação</div></div>
      ${rows.length ? `<table>
        <thead><tr><th>#</th><th>Equipa</th><th>J</th><th>Pts</th><th>V</th><th>E</th><th>D</th><th>DG</th></tr></thead>
        <tbody>${rows.map(r => `<tr>
          <td>${this.esc(r.position)}</td>
          <td><div class="row-team">${this.crest(r.crest,r.team)}<span>${this.esc(r.team)}</span></div></td>
          <td>${this.esc(r.played)}</td><td><strong>${this.esc(r.points)}</strong></td>
          <td>${this.esc(r.won)}</td><td>${this.esc(r.draw)}</td><td>${this.esc(r.lost)}</td>
          <td>${this.esc(r.goal_difference)}</td>
        </tr>`).join("")}</tbody>
      </table>` : '<div class="empty">Classificação ainda indisponível.</div>'}
    `;
  }

  renderFixtures() {
    const e = this.entity(this.config.fixtures_entity);
    const games = e?.attributes?.matches || [];
    return `
      <div class="head"><div class="title">📅 Próximos jogos</div></div>
      ${games.length ? games.map(g => `
        <div class="game">
          <div class="muted">${this.esc(this.fmtDate(g.utc_date))} • Jornada ${this.esc(g.matchday ?? "-")}</div>
          <div class="teams">
            <div class="team">${this.crest(g.home_crest,g.home_team)}<span>${this.esc(g.home_team)}</span></div>
            <div class="score">–</div>
            <div class="team right"><span>${this.esc(g.away_team)}</span>${this.crest(g.away_crest,g.away_team)}</div>
          </div>
        </div>
      `).join("") : '<div class="empty">Sem jogos agendados no intervalo atual.</div>'}
    `;
  }

  renderScorers() {
    const e = this.entity(this.config.scorers_entity);
    const scorers = e?.attributes?.scorers || [];
    return `
      <div class="head"><div class="title">🥅 Melhores marcadores</div></div>
      ${scorers.length ? scorers.map((s,i) => `
        <div class="scorer"><strong>${i+1}</strong><div class="team">${this.crest(s.crest,s.team)}<div><div>${this.esc(s.player)}</div><div class="muted">${this.esc(s.team)}</div></div></div><strong>${this.esc(s.goals ?? 0)} ⚽</strong></div>
      `).join("") : '<div class="empty">Sem dados de marcadores.</div>'}
    `;
  }

  renderStats() {
    const e = this.entity(this.config.stats_entity);
    const a = e?.attributes || {};
    return `
      <div class="head"><div class="title">📊 Estatísticas</div></div>
      <div class="statgrid">
        <div class="stat"><span class="muted">Líder</span><strong>${this.esc(a.leader || "-")}</strong><span>${this.esc(a.leader_points ?? "-")} pts</span></div>
        <div class="stat"><span class="muted">Melhor ataque</span><strong>${this.esc(a.best_attack || "-")}</strong><span>${this.esc(a.best_attack_goals ?? "-")} golos</span></div>
        <div class="stat"><span class="muted">Melhor defesa</span><strong>${this.esc(a.best_defence || "-")}</strong><span>${this.esc(a.best_defence_goals_against ?? "-")} sofridos</span></div>
      </div>
    `;
  }
}

customElements.define("portugal-football-card", PortugalFootballCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "portugal-football-card",
  name: "Portugal Football Card",
  description: "Liga Portugal: ao vivo, classificação, jogos, marcadores e estatísticas.",
  preview: false,
});
