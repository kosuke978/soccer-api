const api = {
  overview: "/api/tournament/overview",
  groups: "/api/groups",
  matches: "/api/matches",
  storylines: "/api/storylines",
};

const fetchJson = async (url) => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
};

window.worldCupApi = {
  api,
  fetchJson,
};
