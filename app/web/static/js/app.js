const overviewUrl = "/api/overview";
const teamSearchInput = document.getElementById("team-search");
const teamResults = document.getElementById("team-results");
const teamMatches = document.getElementById("team-matches");
const groupsGrid = document.getElementById("groups-grid");
const upcomingList = document.getElementById("upcoming-list");
const recentList = document.getElementById("recent-list");

const formatDate = (isoDate) => {
  if (!isoDate) {
    return "";
  }
  const date = new Date(isoDate);
  return new Intl.DateTimeFormat("ja-JP", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Tokyo",
  }).format(date);
};

const renderMatches = (container, matches) => {
  container.innerHTML = "";
  if (!matches || matches.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "該当する試合がありません。";
    container.appendChild(empty);
    return;
  }
  matches.forEach((match) => {
    const card = document.createElement("div");
    card.className = "match-card";
    card.innerHTML = `
      <div class="match-meta">
        <span>${match.stage || ""}${match.group ? ` / Group ${match.group}` : ""}</span>
        <span>${formatDate(match.date)}</span>
      </div>
      <div class="match-teams">
        ${match.home.name} ${match.home_goals ?? ""} - ${
      match.away_goals ?? ""
    } ${match.away.name}
      </div>
      <div class="match-meta">
        <span>${match.venue || "TBD"}</span>
        <span>${match.status || "scheduled"}</span>
      </div>
    `;
    container.appendChild(card);
  });
};

const renderGroups = (groups) => {
  groupsGrid.innerHTML = "";
  groups.forEach((group) => {
    const card = document.createElement("div");
    card.className = "group-card";
    card.innerHTML = `
      <div class="group-title">${group.name}</div>
      ${group.teams
        .map(
          (team) => `
            <div class="group-team">
              <span>${team.name}</span>
              <span class="muted">${team.confederation || ""}</span>
            </div>
          `
        )
        .join("")}
    `;
    groupsGrid.appendChild(card);
  });
};

const renderTeams = (teams) => {
  teamResults.innerHTML = "";
  if (!teams || teams.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "検索結果がありません。";
    teamResults.appendChild(empty);
    return;
  }
  teams.forEach((team) => {
    const card = document.createElement("div");
    card.className = "result-card";
    card.textContent = team.name;
    card.addEventListener("click", async () => {
      const response = await fetch(`/api/teams/${team.id}/matches`);
      const payload = await response.json();
      renderMatches(teamMatches, payload.matches);
    });
    teamResults.appendChild(card);
  });
};

const fetchOverview = async () => {
  const response = await fetch(overviewUrl);
  const payload = await response.json();
  renderGroups(payload.groups);
  renderMatches(upcomingList, payload.upcoming_matches);
  renderMatches(recentList, payload.recent_results);
};

const searchTeams = async (query) => {
  if (!query) {
    teamResults.innerHTML = "";
    teamMatches.innerHTML = "";
    return;
  }
  const response = await fetch(`/api/teams?query=${encodeURIComponent(query)}`);
  const payload = await response.json();
  renderTeams(payload.teams);
};

let searchTimeout = null;
teamSearchInput.addEventListener("input", (event) => {
  const query = event.target.value;
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => searchTeams(query), 300);
});

fetchOverview();
