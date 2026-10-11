const config = window.PRODUCT_RESEARCH_CONFIG || {};
let rows = [];

const els = {
  statusText: document.querySelector("#statusText"),
  productRows: document.querySelector("#productRows"),
  totalProducts: document.querySelector("#totalProducts"),
  completedToday: document.querySelector("#completedToday"),
  highOpportunity: document.querySelector("#highOpportunity"),
  averageMargin: document.querySelector("#averageMargin"),
  lastRun: document.querySelector("#lastRun"),
  searchInput: document.querySelector("#searchInput"),
  categoryFilter: document.querySelector("#categoryFilter"),
  confidenceFilter: document.querySelector("#confidenceFilter"),
  detailsPanel: document.querySelector("#detailsPanel"),
  detailTitle: document.querySelector("#detailTitle"),
  detailLink: document.querySelector("#detailLink"),
  detailAssessment: document.querySelector("#detailAssessment"),
  detailRisks: document.querySelector("#detailRisks"),
  detailActions: document.querySelector("#detailActions"),
  detailVerification: document.querySelector("#detailVerification"),
};

document.querySelector("#refreshButton").addEventListener("click", loadDashboard);
els.searchInput.addEventListener("input", renderTable);
els.categoryFilter.addEventListener("change", renderTable);
els.confidenceFilter.addEventListener("change", renderTable);
document.querySelector("#manualForm").addEventListener("submit", (event) => event.preventDefault());

loadDashboard();

async function loadDashboard() {
  if (!config.supabaseUrl || !config.supabaseAnonKey || config.supabaseAnonKey.includes("YOUR_")) {
    els.statusText.textContent = "Configure dashboard/config.js with Supabase URL and anon key.";
    rows = [];
    renderTable();
    return;
  }
  els.statusText.textContent = "Loading...";
  const client = supabase.createClient(config.supabaseUrl, config.supabaseAnonKey);
  const { data, error } = await client
    .from("research_results")
    .select("id,status,opportunity_score,data_confidence,analysis,created_at,products(id,asin,name,category,product_url,latest_price)");
  if (error) {
    els.statusText.textContent = error.message;
    return;
  }
  rows = data || [];
  populateCategories();
  renderMetrics();
  renderTable();
  els.statusText.textContent = `${rows.length} results`;
}

function populateCategories() {
  const categories = [...new Set(rows.map((row) => row.products?.category).filter(Boolean))].sort();
  els.categoryFilter.innerHTML = '<option value="">All categories</option>';
  for (const category of categories) {
    const option = document.createElement("option");
    option.value = category;
    option.textContent = category;
    els.categoryFilter.appendChild(option);
  }
}

function renderMetrics() {
  els.totalProducts.textContent = new Set(rows.map((row) => row.products?.id)).size;
  const today = new Date().toISOString().slice(0, 10);
  els.completedToday.textContent = rows.filter((row) => (row.created_at || "").startsWith(today)).length;
  els.highOpportunity.textContent = rows.filter((row) => Number(row.opportunity_score) >= 8 && row.data_confidence !== "low").length;
  els.lastRun.textContent = rows[0]?.created_at ? new Date(rows[0].created_at).toLocaleString() : "--";
  els.averageMargin.textContent = "--";
}

function renderTable() {
  const query = els.searchInput.value.trim().toLowerCase();
  const category = els.categoryFilter.value;
  const confidence = els.confidenceFilter.value;
  const filtered = rows.filter((row) => {
    const product = row.products || {};
    return (!query || product.name?.toLowerCase().includes(query)) &&
      (!category || product.category === category) &&
      (!confidence || row.data_confidence === confidence);
  });
  els.productRows.innerHTML = "";
  for (const row of filtered) {
    const product = row.products || {};
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(product.name || "Unknown")}</strong><br>${escapeHtml(product.category || "")}</td>
      <td>${formatMoney(product.latest_price)}</td>
      <td>${escapeHtml(row.analysis?.demand_assessment || "Unknown")}</td>
      <td>${escapeHtml(row.analysis?.competition_assessment || "Unknown")}</td>
      <td>See report</td>
      <td>${Number(row.opportunity_score).toFixed(1)}</td>
      <td><span class="badge ${row.data_confidence === "low" ? "low" : ""}">${escapeHtml(row.data_confidence)}</span></td>
    `;
    tr.addEventListener("click", () => showDetails(row));
    els.productRows.appendChild(tr);
  }
}

function showDetails(row) {
  const product = row.products || {};
  els.detailsPanel.hidden = false;
  els.detailTitle.textContent = product.name || "Product details";
  els.detailLink.href = product.product_url || "#";
  els.detailAssessment.textContent = row.analysis?.profitability_assessment || "No assessment available.";
  fillList(els.detailRisks, row.analysis?.main_risks || []);
  fillList(els.detailActions, row.analysis?.recommended_next_actions || []);
  fillList(els.detailVerification, row.analysis?.verification_notes || []);
}

function fillList(node, items) {
  node.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    node.appendChild(li);
  }
}

function formatMoney(value) {
  if (value === null || value === undefined) return "--";
  return `AED ${Number(value).toFixed(2)}`;
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

