document.addEventListener("DOMContentLoaded", () => {
  const leagueSelect = document.getElementById("leagueSelect");
  const tableBody = document.getElementById("matches-body");
  const pagination = document.getElementById("pagination");
  const loading = document.getElementById("loading");

  let currentLeague = leagueSelect.value;
  let currentPage = 1;

  // Cargar partidos al inicio
  loadMatches();

  // Cuando cambia la liga
  leagueSelect.addEventListener("change", () => {
    currentLeague = leagueSelect.value;
    currentPage = 1;
    loadMatches();
  });

  // Función principal
  function loadMatches(page = 1) {
    loading.classList.remove("d-none");
    tableBody.innerHTML = `<tr><td colspan="7" class="text-muted">Cargando...</td></tr>`;
    pagination.innerHTML = "";

    fetch(`/get-matches/?league_id=${currentLeague}&page=${page}`)
      .then(res => res.json())
      .then(data => {
        loading.classList.add("d-none");
        if (data.error) {
          tableBody.innerHTML = `<tr><td colspan="7" class="text-danger">${data.error}</td></tr>`;
          return;
        }

        if (data.matches.length === 0) {
          tableBody.innerHTML = `<tr><td colspan="7" class="text-muted">No hay partidos programados.</td></tr>`;
          return;
        }

        // Rellenar tabla
        tableBody.innerHTML = "";
        data.matches.forEach(it => {
          const row = `
            <tr>
              <td>${new Date(it.date).toLocaleString()}</td>
              <td><strong>${it.home_team}</strong> vs <strong>${it.away_team}</strong></td>
              <td>${it.competition}</td>
              <td class="text-success">${it.home_win.toFixed(2)}</td>
              <td class="text-warning">${it.draw.toFixed(2)}</td>
              <td class="text-danger">${it.away_win.toFixed(2)}</td>
              <td><span class="badge bg-primary">${it.likely_score[0]} - ${it.likely_score[1]}</span></td>
            </tr>`;
          tableBody.innerHTML += row;
        });

        // Generar paginación
        pagination.innerHTML = "";
        for (let i = 1; i <= data.num_pages; i++) {
          pagination.innerHTML += `
            <li class="page-item ${i === data.page_number ? 'active' : ''}">
              <a class="page-link" href="#">${i}</a>
            </li>`;
        }

        // Escuchar clics de página
        document.querySelectorAll(".page-item a").forEach(link => {
          link.addEventListener("click", e => {
            e.preventDefault();
            const page = parseInt(e.target.textContent);
            currentPage = page;
            loadMatches(page);
          });
        });
      })
      .catch(() => {
        loading.classList.add("d-none");
        tableBody.innerHTML = `<tr><td colspan="7" class="text-danger">Error al cargar los datos.</td></tr>`;
      });
  }
});
