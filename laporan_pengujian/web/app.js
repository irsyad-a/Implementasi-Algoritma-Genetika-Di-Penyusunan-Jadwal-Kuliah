/**
 * app.js - Logika Interaktif Konsol Telemetri & Riset Algoritma Genetika
 * Membaca telemetri dari window.BENCHMARK_DATA dan merender tabel serta grafik analitis
 * Mengikuti prinsip antislop: bebas emoji dekoratif, tipografi bersih, dan penanda status semantik.
 */

document.addEventListener("DOMContentLoaded", () => {
  const data = window.BENCHMARK_DATA || {};
  initTabs();
  renderKPIs(data);
  renderCharts(data);

  // Ambil data dengan fallback key
  const list18 = data.riset_18core ? (data.riset_18core.results || []) : [];
  const list12 = data.mega_12core ? (data.mega_12core.detail_tasks || data.mega_12core.results || []) : [];
  const listCross = data.komparasi_lintas ? (data.komparasi_lintas.detail_kasus || data.komparasi_lintas.results || []) : [];
  const listStress = data.stress_test ? (data.stress_test.detail_runs || data.stress_test.results || []) : [];
  const listGenap = data.optimasi_genap ? (data.optimasi_genap.detail_pengujian || []) : [];

  renderTable18Core(list18);
  renderTable12Core(list12);
  renderTableCrossCase(listCross);
  renderTableStressTest(listStress);
  renderTableGenap(listGenap);
  initCalculator();
});

// ==============================================================================
// 1. Navigasi Tab
// ==============================================================================
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");

      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add("active");
      }
    });
  });
}

// ==============================================================================
// 2. Metrik Kunci Ringkasan
// ==============================================================================
function renderKPIs(data) {
  const r18 = data.riset_18core ? (data.riset_18core.results || []) : [];
  const hardZeroCount = r18.filter((r) => r.hard_violations === 0).length;
  const bestFit = r18.length ? Math.max(...r18.map((r) => r.fitness)) : 1.5;

  const elHardZero = document.getElementById("kpi-hard-zero");
  if (elHardZero) elHardZero.innerText = `${hardZeroCount} / ${r18.length} Kasus`;

  const elBestFit = document.getElementById("kpi-best-fit");
  if (elBestFit) elBestFit.innerText = bestFit.toFixed(4);

  const elFastZero = document.getElementById("kpi-fast-zero");
  if (elFastZero) elFastZero.innerText = "Generasi 2 (18.6s)";
}

// ==============================================================================
// 3. Tabel Riset 18 Core Paralel
// ==============================================================================
function renderTable18Core(results) {
  const tbody = document.getElementById("tbody-18core");
  const filterCat = document.getElementById("filter-cat-18core");
  const searchInput = document.getElementById("search-18core");
  if (!tbody || !results) return;

  function update() {
    const q = (searchInput ? searchInput.value : "").toLowerCase();
    const cat = filterCat ? filterCat.value : "ALL";

    tbody.innerHTML = "";
    results
      .filter((r) => {
        const matchCat = cat === "ALL" || r.kategori === cat;
        const matchQ =
          (r.nama_uji || "").toLowerCase().includes(q) ||
          (r.kategori || "").toLowerCase().includes(q);
        return matchCat && matchQ;
      })
      .forEach((r) => {
        const tr = document.createElement("tr");
        const statusChip =
          r.hard_violations === 0
            ? '<span class="chip chip-success">TERPENUHI (HARD = 0)</span>'
            : `<span class="chip chip-danger">BENTROK: ${r.hard_violations}</span>`;

        const zeroGen =
          r.first_hard_zero_gen !== null && r.first_hard_zero_gen !== undefined
            ? `<span class="mono" style="color:var(--accent-green); font-weight:600;">Gen ${r.first_hard_zero_gen}</span>`
            : '<span class="mono" style="color:var(--text-tertiary);">-</span>';

        tr.innerHTML = `
          <td class="mono" style="text-align:center;">${r.core_id}</td>
          <td><span class="chip chip-neutral">${r.kategori}</span></td>
          <td><strong>${r.nama_uji}</strong></td>
          <td class="mono" style="text-align:center;">${r.total_mk}</td>
          <td class="mono" style="text-align:center;">${r.pop_size}</td>
          <td class="mono" style="text-align:center;">${r.generasi}</td>
          <td class="mono" style="text-align:center;">${r.mutation_rate}</td>
          <td class="mono" style="text-align:center;">${r.seed}</td>
          <td class="mono" style="text-align:center; font-weight:700; color:${r.hard_violations === 0 ? "var(--accent-green)" : "var(--accent-red)"};">${r.hard_violations}</td>
          <td class="mono" style="text-align:center;">${r.soft_violations}</td>
          <td class="mono" style="color:var(--accent-cyan); font-weight:700;">${Number(r.fitness).toFixed(6)}</td>
          <td style="text-align:center;">${zeroGen}</td>
          <td class="mono" style="text-align:right;">${r.durasi_detik}s</td>
          <td style="text-align:center;">${statusChip}</td>
        `;
        tbody.appendChild(tr);
      });
  }

  if (filterCat) filterCat.addEventListener("change", update);
  if (searchInput) searchInput.addEventListener("input", update);
  update();
}

// ==============================================================================
// 4. Tabel Mega Benchmark 12 Core
// ==============================================================================
function renderTable12Core(results) {
  const tbody = document.getElementById("tbody-12core");
  if (!tbody || !results) return;

  tbody.innerHTML = "";
  results.forEach((r) => {
    const tr = document.createElement("tr");
    const taskId = r.task_id || r.core_idx || "-";
    const desc = r.kategori || r.deskripsi || r.config_name || `Task ${taskId}`;
    const pop = r.pop_size || r.populasi_size || "-";
    const gen = r.generasi_target || r.generasi || "-";
    const mut = r.mutation_rate !== undefined ? r.mutation_rate : "-";
    const seed = r.seed !== undefined ? r.seed : (r.random_seed !== undefined ? r.random_seed : "-");
    const hard = r.hard_violations !== undefined ? r.hard_violations : "-";
    const soft = r.soft_violations !== undefined ? r.soft_violations : "-";
    const fit = r.fitness !== undefined ? Number(r.fitness).toFixed(6) : "-";
    const time = r.durasi_detik !== undefined ? `${r.durasi_detik}s` : "-";

    const isRecord = hard <= 2;

    tr.innerHTML = `
      <td class="mono" style="text-align:center;">${taskId}</td>
      <td><strong>${desc}</strong></td>
      <td class="mono" style="text-align:center;">${pop}</td>
      <td class="mono" style="text-align:center;">${gen}</td>
      <td class="mono" style="text-align:center;">${mut}</td>
      <td class="mono" style="text-align:center;">${seed}</td>
      <td class="mono" style="text-align:center; font-weight:700; color:${isRecord ? "var(--accent-cyan)" : "var(--accent-red)"};">${hard}</td>
      <td class="mono" style="text-align:center;">${soft}</td>
      <td class="mono" style="color:var(--accent-cyan); font-weight:700;">${fit}</td>
      <td class="mono" style="text-align:right;">${time}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ==============================================================================
// 5. Tabel Komparasi Lintas Kasus
// ==============================================================================
function renderTableCrossCase(results) {
  const tbody = document.getElementById("tbody-crosscase");
  if (!tbody || !results) return;

  tbody.innerHTML = "";
  results.forEach((r) => {
    const tr = document.createElement("tr");
    const coreIdx = r.core_idx || "-";
    const name = r.case_name || "-";
    const desc = r.deskripsi || "-";
    const mk = r.total_mk !== undefined ? r.total_mk : "-";
    const hard = r.hard_violations !== undefined ? r.hard_violations : "-";
    const soft = r.soft_violations !== undefined ? r.soft_violations : "-";
    const fit = r.fitness !== undefined ? Number(r.fitness).toFixed(6) : "-";
    const time = r.durasi_detik !== undefined ? `${r.durasi_detik}s` : "-";

    const isZero = hard === 0;
    tr.innerHTML = `
      <td class="mono" style="text-align:center;">${coreIdx}</td>
      <td><strong>${name}</strong></td>
      <td>${desc}</td>
      <td class="mono" style="text-align:center;">${mk}</td>
      <td class="mono" style="text-align:center; font-weight:700; color:${isZero ? "var(--accent-green)" : "var(--accent-red)"};">${hard}</td>
      <td class="mono" style="text-align:center;">${soft}</td>
      <td class="mono" style="color:var(--accent-cyan); font-weight:700;">${fit}</td>
      <td class="mono" style="text-align:right;">${time}</td>
      <td style="text-align:center;">${isZero ? '<span class="chip chip-success">KONVERGEN</span>' : '<span class="chip chip-danger">DEFISIT KAPASITAS</span>'}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ==============================================================================
// 6. Tabel Stress Test
// ==============================================================================
function renderTableStressTest(results) {
  const tbody = document.getElementById("tbody-stresstest");
  if (!tbody || !results) return;

  tbody.innerHTML = "";
  results.forEach((r, idx) => {
    const tr = document.createElement("tr");
    const runId = r.run !== undefined ? r.run : (r.core_id !== undefined ? r.core_id : idx + 1);
    const seed = r.seed !== undefined ? r.seed : "-";
    const pop = r.populasi_size || r.pop_size || 200;
    const gen = r.generasi_target || r.generasi || 1200;
    const mut = r.mutation_rate !== undefined ? r.mutation_rate : 0.08;
    const hard = r.hard_violations !== undefined ? r.hard_violations : "-";
    const soft = r.soft_violations !== undefined ? r.soft_violations : "-";
    const fit = r.fitness !== undefined ? Number(r.fitness).toFixed(6) : "-";
    const time = r.durasi_detik !== undefined ? `${r.durasi_detik}s` : "-";

    const isWinner = hard === 3 && (seed === 44 || seed === 45);

    tr.innerHTML = `
      <td class="mono" style="text-align:center;">${runId}</td>
      <td class="mono" style="font-weight:700; color:${isWinner ? "var(--accent-cyan)" : "var(--text-primary)"};">Seed ${seed} ${isWinner ? "(Optimal)" : ""}</td>
      <td class="mono" style="text-align:center;">${pop}</td>
      <td class="mono" style="text-align:center;">${gen}</td>
      <td class="mono" style="text-align:center;">${mut}</td>
      <td class="mono" style="text-align:center; font-weight:700; color:var(--accent-green);">${hard}</td>
      <td class="mono" style="text-align:center;">${soft}</td>
      <td class="mono" style="color:var(--accent-cyan); font-weight:700;">${fit}</td>
      <td class="mono" style="text-align:right;">${time}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ==============================================================================
// 7. Tabel Optimasi Semester Genap
// ==============================================================================
function renderTableGenap(results) {
  const tbody = document.getElementById("tbody-genap");
  if (!tbody || !results) return;

  tbody.innerHTML = "";
  results.forEach((r) => {
    const tr = document.createElement("tr");
    const coreIdx = r.core_idx || "-";
    const label = r.label || "-";
    const tipe = r.tipe || "-";
    const pop = r.populasi || "-";
    const gen = r.generasi || "-";
    const mut = r.mutasi !== undefined ? r.mutasi : "-";
    const seed = r.seed !== undefined ? r.seed : "-";
    const hard = r.hard_violations !== undefined ? r.hard_violations : "-";
    const soft = r.soft_violations !== undefined ? r.soft_violations : "-";
    const fit = r.fitness !== undefined ? Number(r.fitness).toFixed(6) : "-";
    const time = r.durasi_detik !== undefined ? `${r.durasi_detik}s` : "-";

    const isWinner = hard <= 12;

    tr.innerHTML = `
      <td class="mono" style="text-align:center;">${coreIdx}</td>
      <td><strong>${label}</strong></td>
      <td><span class="chip chip-neutral">${tipe}</span></td>
      <td class="mono" style="text-align:center;">${pop}</td>
      <td class="mono" style="text-align:center;">${gen}</td>
      <td class="mono" style="text-align:center;">${mut}</td>
      <td class="mono" style="text-align:center;">${seed}</td>
      <td class="mono" style="text-align:center; font-weight:700; color:${isWinner ? "var(--accent-cyan)" : "var(--accent-red)"};">${hard}</td>
      <td class="mono" style="text-align:center;">${soft}</td>
      <td class="mono" style="color:var(--accent-cyan); font-weight:700;">${fit}</td>
      <td class="mono" style="text-align:right;">${time}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ==============================================================================
// 8. Grafik Visualisasi Analitis (Chart.js v4)
// ==============================================================================
function renderCharts(data) {
  if (typeof Chart === "undefined") return;

  Chart.defaults.color = "#A1A1AA";
  Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
  Chart.defaults.borderColor = "#27272A";

  const r18 = (data.riset_18core && (data.riset_18core.results || [])) || [];
  const r12 = (data.mega_12core && (data.mega_12core.detail_tasks || data.mega_12core.results || [])) || [];

  // Chart 1: 18 Core Hard Violations
  const ctx1 = document.getElementById("chart-18core-hard");
  if (ctx1 && r18.length) {
    new Chart(ctx1, {
      type: "bar",
      data: {
        labels: r18.map((r) => `C${r.core_id}: ${(r.nama_uji || "").split("(")[0].trim()}`),
        datasets: [
          {
            label: "Hard Violations",
            data: r18.map((r) => r.hard_violations),
            backgroundColor: r18.map((r) =>
              r.hard_violations === 0 ? "rgba(48, 209, 88, 0.75)" : "rgba(255, 69, 58, 0.75)"
            ),
            borderColor: r18.map((r) =>
              r.hard_violations === 0 ? "#30D158" : "#FF453A"
            ),
            borderWidth: 1,
            borderRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: (ctx) => {
                const item = r18[ctx.dataIndex];
                return `Fitness: ${Number(item.fitness).toFixed(4)} | Waktu: ${item.durasi_detik}s`;
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: "Jumlah Pelanggaran Keras (Hard)", color: "#A1A1AA" },
            grid: { color: "#202024" },
          },
          x: {
            grid: { display: false },
            ticks: {
              maxRotation: 45,
              minRotation: 30,
              font: { size: 10 },
            },
          },
        },
      },
    });
  }

  // Chart 2: Fitness vs Ukuran Populasi
  const ctx2 = document.getElementById("chart-fitness-pop");
  if (ctx2 && r18.length) {
    const sortedByPop = [...r18].sort((a, b) => a.pop_size - b.pop_size);
    new Chart(ctx2, {
      type: "line",
      data: {
        labels: sortedByPop.map((r) => `Pop ${r.pop_size}`),
        datasets: [
          {
            label: "Nilai Fitness",
            data: sortedByPop.map((r) => r.fitness),
            borderColor: "#00E5FF",
            backgroundColor: "rgba(0, 229, 255, 0.08)",
            fill: true,
            tension: 0.2,
            pointBackgroundColor: sortedByPop.map((r) =>
              r.hard_violations === 0 ? "#30D158" : "#00E5FF"
            ),
            pointRadius: 4,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: {
            beginAtZero: false,
            title: { display: true, text: "Nilai Fitness (Target > 1.0)", color: "#A1A1AA" },
            grid: { color: "#202024" },
          },
          x: {
            grid: { color: "#202024" },
          },
        },
      },
    });
  }

  // Chart 3: Mega Benchmark 12 Core
  const ctx3 = document.getElementById("chart-mega-12core");
  if (ctx3 && r12.length) {
    new Chart(ctx3, {
      type: "bar",
      data: {
        labels: r12.map((r) => `Task ${r.task_id || r.core_idx}: Pop ${r.pop_size || r.populasi_size} (Mut ${Math.round((r.mutation_rate || 0)*100)}%)`),
        datasets: [
          {
            label: "Hard Violations",
            data: r12.map((r) => r.hard_violations),
            backgroundColor: r12.map((r) =>
              r.hard_violations <= 2 ? "rgba(0, 229, 255, 0.75)" : "rgba(255, 69, 58, 0.75)"
            ),
            borderColor: r12.map((r) =>
              r.hard_violations <= 2 ? "#00E5FF" : "#FF453A"
            ),
            borderWidth: 1,
            borderRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: "Hard Violations", color: "#A1A1AA" },
            grid: { color: "#202024" },
          },
          x: {
            grid: { display: false },
            ticks: { font: { size: 10 }, maxRotation: 45 },
          },
        },
      },
    });
  }
}

// ==============================================================================
// 9. Kalkulator Interaktif Kelayakan Rombel
// ==============================================================================
function initCalculator() {
  const calcBtn = document.getElementById("btn-calc-pigeon");
  const inCourses = document.getElementById("calc-courses");
  const inSlots = document.getElementById("calc-slots");
  const resDiv = document.getElementById("calc-result");

  if (!calcBtn || !inCourses || !inSlots || !resDiv) return;

  calcBtn.addEventListener("click", () => {
    const N = parseInt(inCourses.value) || 0;
    const T = parseInt(inSlots.value) || 25;

    if (N <= 0 || T <= 0) {
      resDiv.innerHTML = '<div class="calc-feedback-box fail">Harap masukkan angka bilangan bulat positif.</div>';
      return;
    }

    const saturation = ((N / T) * 100).toFixed(1);
    const minCollision = Math.max(0, N - T);
    const neededClasses = Math.ceil(N / T);

    if (N <= T) {
      resDiv.innerHTML = `
        <div class="calc-feedback-box pass">
          <div style="font-weight: 700; margin-bottom: 4px;">KONDISI FEASIBLE: HARD = 0 DAPAT DICAPAI SECARA MATEMATIS</div>
          <div>• Saturasi Slot: <span class="mono" style="font-weight:700;">${saturation}%</span> (${N} MK dari total ${T} slot operasional mingguan).</div>
          <div>• Slot Kosong Tersedia: <span class="mono">${T - N} slot</span>.</div>
          <div>• Minimum Bentrok Tak Terhindarkan: <span class="mono" style="font-weight:700;">0 bentrok</span>.</div>
          <div>• Konfigurasi Rekomendasi GA: Populasi 100 - 150, Generasi 400 - 500, Laju Mutasi 0.07.</div>
        </div>
      `;
    } else {
      resDiv.innerHTML = `
        <div class="calc-feedback-box fail">
          <div style="font-weight: 700; margin-bottom: 4px;">KONDISI INFEASIBLE: PRINSIP SARANG MERPATI TERLANGGAR (DEFISIT KAPASITAS FISIK)</div>
          <div>• Tingkat Saturasi Waktu: <span class="mono" style="font-weight:700;">${saturation}%</span> (${N} mata kuliah dipadatkan pada ${T} slot waktu).</div>
          <div>• Bentrok Minimum Fisik Pasti Terjadi: <span class="mono" style="font-weight:700;">${minCollision} bentrok</span>.</div>
          <div>• Solusi Rekayasa Kurikulum: Bagi rombel menjadi minimal <span class="mono" style="font-weight:700;">${neededClasses} Kelas Paralel</span> agar beban per kelas &le; ${T} slot.</div>
        </div>
      `;
    }
  });
}
