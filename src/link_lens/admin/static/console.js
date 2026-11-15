// The operations console. It calls the admin API under /admin and nothing
// else: no database, no other service. What a person may do is decided by the
// API; hiding a menu entry here is a convenience, not a control.
"use strict";

const view = document.getElementById("view");
let me = null;

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function api(method, path, body) {
  const response = await fetch("/admin" + path, {
    method,
    credentials: "same-origin",
    headers: { "content-type": "application/json", "x-linklens-console": "1" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => null);
  if (response.status === 401 && path !== "/session") {
    me = null;
    signInScreen();
    throw new ApiError("Sign in", 401);
  }
  if (!response.ok) {
    throw new ApiError((data && (data.detail || data.title)) || response.statusText, response.status);
  }
  return data;
}

// Building the page from values, never from markup, so a dataset's title
// cannot become part of the page's code.
function h(tag, attributes, ...children) {
  const element = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (name.startsWith("on")) element.addEventListener(name.slice(2), value);
    else if (name === "class") element.className = value;
    else if (value === true) element.setAttribute(name, "");
    else element.setAttribute(name, value);
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    element.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return element;
}

// Replace an element's content, leaving out whatever a condition turned off.
const put = (element, ...nodes) => element.replaceChildren(...nodes.flat(Infinity).filter((node) => node !== null && node !== undefined && node !== false));
const show = (...nodes) => put(view, ...nodes);
const notice = (text, kind) => h("div", { class: "notice " + (kind || ""), role: kind === "bad" ? "alert" : "status" }, text);
const badge = (text, kind) => h("span", { class: "badge " + (kind || "") }, text);
// A link out of the console. An address comes from settings or from a
// publisher's metadata, so anything that is not a web address is not linked.
const link = (text, href) => (href && /^https?:\/\//i.test(href) ? h("a", { href, target: "_blank", rel: "noopener noreferrer" }, text) : null);
const short = (value, length = 12) => (value ? h("code", { title: value }, String(value).slice(0, length)) : "–");
const number = (value) => (value === null || value === undefined ? "–" : Number(value).toLocaleString("en"));
const money = (value) => (value === null || value === undefined ? "unknown" : "US$" + Number(value).toFixed(2));

function when(value) {
  if (!value) return "–";
  const date = new Date(value);
  return h("time", { datetime: value, title: value }, date.toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" }));
}

function daysSince(value) {
  return value ? Math.max(0, (Date.now() - new Date(value).getTime()) / 86400000) : null;
}

function table(columns, rows, empty) {
  if (!rows.length) return h("p", { class: "muted" }, empty || "Nothing to show.");
  return h(
    "div",
    { class: "scroll" },
    h(
      "table",
      {},
      h("thead", {}, h("tr", {}, columns.map((column) => h("th", { class: column.num ? "num" : "" }, column.title)))),
      h("tbody", {}, rows.map((row) => h("tr", {}, columns.map((column) => h("td", { class: column.num ? "num" : "" }, column.cell(row))))))
    )
  );
}

function facts(pairs) {
  return h("dl", { class: "facts" }, pairs.filter(Boolean).map(([name, value]) => [h("dt", {}, name), h("dd", {}, value)]));
}

// Run a change, show how it ended, and say so if it failed.
async function act(button, work, target) {
  const isButton = button.tagName === "BUTTON";
  const label = button.textContent;
  button.disabled = true;
  if (isButton) button.textContent = "Working…";
  try {
    await work();
  } catch (error) {
    (target || view).prepend(notice(error.message, "bad"));
  } finally {
    button.disabled = false;
    if (isButton) button.textContent = label;
  }
}

const may = (role) => me && me.roles.indexOf(me.role) >= me.roles.indexOf(role);

// Status of a source: three facts kept apart, as the reporting model has them.
function sourceBadges(row) {
  const refresh = {
    fresh: ["fresh", "good"],
    stale: ["overdue", "warn"],
    failing: ["checks failing", "bad"],
    paused: ["paused", ""],
    no_cadence: ["no cadence", ""],
    never_checked: ["never checked", "warn"],
  }[row.refresh_status] || [row.refresh_status, ""];
  const drift = {
    blocked: ["drifted", "bad"],
    changed: ["shape changed", "warn"],
    no_mapping: ["no approved mapping", "warn"],
  }[row.drift_status];
  return [
    row.waiting_for_review && badge("waiting for review", "warn"),
    drift && badge(drift[0], drift[1]),
    badge(refresh[0], refresh[1]),
  ];
}

const FILTERS = {
  All: () => true,
  "Waiting for review": (row) => row.waiting_for_review,
  Drifted: (row) => row.drift_status === "blocked",
  Failing: (row) => row.refresh_status === "failing",
  Overdue: (row) => row.refresh_status === "stale",
  Fresh: (row) => row.refresh_status === "fresh",
  Paused: (row) => row.paused,
  "No cadence": (row) => row.refresh_status === "no_cadence",
};

// Screens

function signInScreen(message) {
  document.getElementById("bar").hidden = true;
  const token = h("input", { type: "password", name: "token", autocomplete: "current-password", required: true });
  const form = h(
    "form",
    {
      class: "panel sign-in",
      onsubmit: async (event) => {
        event.preventDefault();
        try {
          await api("POST", "/session", { token: token.value });
          await start();
        } catch (error) {
          signInScreen(error.message);
        }
      },
    },
    h("h1", {}, "Link Lens console"),
    h("p", { class: "lead" }, "Sign in with the token you were given."),
    message && notice(message, "bad"),
    h("div", { class: "row" }, h("label", { class: "grow" }, "Token", token), h("button", {}, "Sign in"))
  );
  show(form);
  token.focus();
}

async function homeScreen() {
  const home = await api("GET", "/home");
  const budget = home.budget;
  show(
    h("h1", {}, "What needs attention"),
    h("p", { class: "lead" }, "Sources that wait for a person. Reviewing a mapping happens in the Agent Inbox; running and scheduling in Dagster; the numbers are on the dashboards."),
    home.attention.length
      ? h(
          "div",
          { class: "panel" },
          table(
            [
              { title: "Source", cell: (row) => h("a", { href: "#/sources/" + encodeURIComponent(row.source_id) }, row.source_title) },
              { title: "Why", cell: (row) => row.reasons.map((reason) => badge(reason, "warn")) },
              { title: "Waiting", cell: (row) => (row.waiting_since ? daysSince(row.waiting_since).toFixed(1) + " days" : "–") },
              { title: "Go to", cell: (row) => [link("Agent Inbox", row.links.inbox), row.links.inbox && " · ", link("Dagster", row.links.dagster)] },
            ],
            home.attention
          )
        )
      : notice("Nothing waits for a person right now.", "good"),
    h(
      "div",
      { class: "tiles" },
      h("div", { class: "tile" }, h("b", {}, number(home.sources.registered)), h("span", {}, "registered sources")),
      h("div", { class: "tile" }, h("b", {}, number(home.sources.with_cadence)), h("span", {}, "with a refresh cadence")),
      h("div", { class: "tile" }, h("b", {}, home.latest_release ? "#" + home.latest_release.release_id : "none"), h("span", {}, home.latest_release ? ["latest release, ", when(home.latest_release.released_at)] : "no release recorded yet")),
      h("div", { class: "tile" }, h("b", {}, money(budget.remaining_usd)), h("span", {}, "left of the " + money(budget.cap_usd) + " model budget"))
    ),
    h("h2", {}, "Look further"),
    h(
      "div",
      { class: "row" },
      h("a", { class: "button quiet", href: home.links.source_health, target: "_blank", rel: "noopener noreferrer" }, "Source health dashboard"),
      h("a", { class: "button quiet", href: home.links.data_quality, target: "_blank", rel: "noopener noreferrer" }, "Data quality dashboard"),
      h("a", { class: "button quiet", href: home.links.product_overview, target: "_blank", rel: "noopener noreferrer" }, "Product overview dashboard"),
      h("a", { class: "button quiet", href: home.links.dagster, target: "_blank", rel: "noopener noreferrer" }, "Dagster"),
      h("a", { class: "button quiet", href: home.links.inbox, target: "_blank", rel: "noopener noreferrer" }, "Agent Inbox")
    )
  );
}

async function sourcesScreen() {
  const rows = await api("GET", "/sources");
  let chosen = "All";
  const body = h("div", {});
  const chips = h("div", { class: "chips", role: "group", "aria-label": "Filter by status" });
  const draw = () => {
    chips.replaceChildren(
      ...Object.keys(FILTERS).map((name) =>
        h("button", { "aria-pressed": String(name === chosen), onclick: () => { chosen = name; draw(); } }, name + " " + rows.filter(FILTERS[name]).length)
      )
    );
    put(body, 
      table(
        [
          { title: "Source", cell: (row) => h("a", { href: "#/sources/" + encodeURIComponent(row.source_id) }, row.source_title || row.source_id) },
          { title: "Publisher", cell: (row) => row.publisher || "–" },
          { title: "Status", cell: sourceBadges },
          { title: "Last checked", cell: (row) => when(row.last_checked_at) },
          { title: "Next check due", cell: (row) => when(row.next_check_due_at) },
          { title: "Cadence", num: true, cell: (row) => (row.cadence_days ? row.cadence_days + " d" : "–") },
        ],
        rows.filter(FILTERS[chosen]),
        "No source has this status."
      )
    );
  };
  draw();
  show(
    h("div", { class: "row" }, h("h1", { class: "grow" }, "Sources"), may("product_owner") && h("a", { class: "button", href: "#/sources/add" }, "Add a source")),
    h("p", { class: "lead" }, "Registered sources and whether each is fresh, overdue, drifted or waiting for a review."),
    chips,
    h("div", { class: "panel" }, body)
  );
}

function previewTable(inspection) {
  if (inspection && Array.isArray(inspection.preview) && inspection.preview.length) {
    const [header, ...sample] = inspection.preview;
    return h(
      "div",
      { class: "scroll" },
      h("table", {}, h("thead", {}, h("tr", {}, header.map((name) => h("th", {}, name)))), h("tbody", {}, sample.map((row) => h("tr", {}, row.map((value) => h("td", {}, value))))))
    );
  }
  return h("pre", {}, JSON.stringify(inspection, null, 2));
}

async function addSourceScreen() {
  const steps = (here) => h("ol", { class: "steps" }, ["Search", "Preview", "Confirm"].map((name, index) => h("li", { class: index === here ? "here" : "" }, name)));
  const stage = h("div", {});
  const query = h("input", { type: "search", name: "q", placeholder: "business names, licence register, charities…", size: 40 });

  const search = async () => {
    const found = await api("GET", "/catalogue?q=" + encodeURIComponent(query.value));
    put(stage, 
      steps(0),
      h("p", { class: "muted" }, (found.matches === 1 ? "1 dataset of the saved catalogue matches" : found.matches + " datasets of the saved catalogue match") + "; the best ranked are shown first. Relevance is an uncalibrated score, not a measured probability."),
      table(
        [
          { title: "Dataset", cell: (row) => [row.title || row.slug, row.registered && [" ", badge("already a source", "good")]] },
          { title: "Publisher", cell: (row) => row.publisher || "–" },
          { title: "Formats", cell: (row) => (row.formats || []).join(", ") || "–" },
          { title: "Licence", cell: (row) => row.licence || "unknown" },
          { title: "Relevance", num: true, cell: (row) => (row.relevance === null || row.relevance === undefined ? "not scored" : Number(row.relevance).toFixed(2)) },
          { title: "", cell: (row) => h("button", { class: "quiet", onclick: (event) => act(event.target, () => preview(row), stage) }, "Preview") },
        ],
        found.datasets,
        "No dataset of the saved catalogue matches."
      )
    );
  };

  const preview = async (dataset) => {
    const found = await api("POST", "/sources/preview", { dataset_id: dataset.dataset_id });
    const budget = found.budget;
    const agreed = h("input", { type: "checkbox" });
    const confirm = h("button", { disabled: true, onclick: (event) => act(event.target, () => add(found), stage) }, "Add this source and start onboarding");
    agreed.addEventListener("change", () => { confirm.disabled = !(agreed.checked && budget.affordable); });
    put(stage, 
      steps(1),
      h("h2", {}, found.title),
      found.already_registered && notice("This dataset is already a source. Adding it again checks for a new file and starts onboarding only if its snapshot has no run.", "warn"),
      facts([
        ["Publisher", found.publisher || "–"],
        ["Licence", [found.licence, found.licence_url && [" · ", link("terms", found.licence_url)]]],
        ["File", [found.resource.name || found.resource.id, " (", found.resource.format.toUpperCase(), ")"]],
        ["Downloaded for this preview", number(found.bytes) + " bytes" + (found.partial ? " (fetched as a byte range; the file may be larger)" : "")],
        ["Publisher's last change", found.resource.last_modified ? when(found.resource.last_modified) : "not stated"],
      ]),
      h("h2", {}, "Header and first rows"),
      previewTable(found.inspection),
      h("h2", {}, "Cost of onboarding"),
      h("p", { class: "muted" }, "Adding the source starts onboarding, which makes paid model calls within the run's own limits. The estimate is history, not a quote."),
      facts([
        ["Estimate", [money(budget.estimate_usd), " (", budget.basis, budget.highest_usd ? "; highest " + money(budget.highest_usd) : "", ")"]],
        ["Budget cap", money(budget.cap_usd)],
        ["Charged so far", money(budget.charged_usd)],
        ["Remaining", money(budget.remaining_usd)],
      ]),
      !budget.affordable && notice("The estimate would take the budget over its cap, so this source cannot be added now. Raising the cap is the owner's decision.", "bad"),
      h("label", { class: "check" }, agreed, "I have read the preview and want onboarding to start."),
      h("div", { class: "row" }, confirm, h("button", { class: "quiet", onclick: search }, "Back to the results"))
    );
  };

  const add = async (found) => {
    const added = await api("POST", "/sources", { dataset_id: found.dataset_id, resource_id: found.resource.id, confirm_paid_calls: true });
    put(stage, 
      steps(2),
      notice(added.onboarding_started ? "The source is registered and onboarding has started. It will wait for a review in the Agent Inbox." : "The source is registered. Its snapshot already had an onboarding run, so nothing new was started.", "good"),
      facts([["Source", short(added.source_id, 40)], ["Snapshot", short(added.snapshot_id)], ["Onboarding run", short(added.run_id, 40)]]),
      h("p", {}, h("a", { class: "button", href: "#/sources/" + encodeURIComponent(added.source_id) }, "Open the source"))
    );
  };

  show(
    h("h1", {}, "Add a source"),
    h("p", { class: "lead" }, "Find a dataset in the saved catalogue, look at what would be downloaded and what onboarding is likely to cost, then confirm."),
    h("form", { class: "panel row", onsubmit: (event) => { event.preventDefault(); act(event.submitter, search, stage); } }, h("label", { class: "grow" }, "Search the catalogue", query), h("button", {}, "Search")),
    h("div", { class: "panel" }, stage)
  );
  put(stage, steps(0), h("p", { class: "muted" }, "Search by title, publisher or name."));
  query.focus();
}

async function sourceScreen(sourceId) {
  const row = await api("GET", "/sources/" + encodeURIComponent(sourceId));
  const change = (changes) => async () => {
    await api("PATCH", "/sources/" + encodeURIComponent(sourceId), changes);
    await sourceScreen(sourceId);
  };
  const days = h("input", { type: "number", min: "0.01", step: "any", value: row.cadence_days || "", size: 6, name: "days" });
  const waited = daysSince(row.waiting_since);
  show(
    h("p", {}, h("a", { href: "#/sources" }, "← Sources")),
    h("h1", {}, row.source_title || row.source_id),
    h("p", { class: "lead" }, row.publisher || ""),
    h("div", {}, sourceBadges(row)),
    row.waiting_for_review && notice(["This source has waited " + waited.toFixed(1) + " days for a review. ", link("Review it in the Agent Inbox", row.links.inbox), "."], "warn"),
    row.drift_status === "blocked" && notice("The publisher's new file cannot be read under the approved mapping. Extraction of that snapshot waits for a newly approved mapping; earlier snapshots and every release are unaffected.", "bad"),
    row.last_error && notice("Last failed check: " + row.last_error, "bad"),
    h(
      "div",
      { class: "panel" },
      facts([
        ["Source ID", h("code", {}, row.source_id)],
        ["Last checked", when(row.last_checked_at)],
        ["Last changed", when(row.last_changed_at)],
        ["Next check due", when(row.next_check_due_at)],
        ["Approved mapping", row.approved_config_hash ? [short(row.approved_config_hash), " approved ", when(row.approved_at)] : "none yet"],
        ["Latest run", row.latest_run_id ? [short(row.latest_run_id, 40), " ", badge(row.latest_run_status || "unknown")] : "none"],
        row.paused && ["Paused by", row.paused_by],
        ["Elsewhere", [link("Dataset on the portal", row.links.portal), " · ", link("Dagster", row.links.dagster), " · ", link("Dashboard", row.links.dashboard), " · ", link("OKF page (needs an API key)", row.links.okf)]],
      ])
    ),
    may("product_owner") &&
      h(
        "div",
        { class: "panel" },
        h("h2", {}, "Refresh"),
        h("p", { class: "muted" }, "The cadence is how often Dagster checks the publisher for a new file. A refresh downloads, checks drift and extracts; it makes no model call."),
        h(
          "form",
          { class: "row", onsubmit: (event) => { event.preventDefault(); act(event.submitter, change({ cadence_days: Number(days.value) })); } },
          h("label", {}, "Check every (days)", days),
          h("button", {}, "Save cadence"),
          row.cadence_days && h("button", { type: "button", class: "quiet", onclick: (event) => act(event.target, change({ cadence_days: null })) }, "Clear cadence"),
          row.paused
            ? h("button", { type: "button", class: "quiet", onclick: (event) => act(event.target, change({ paused: false })) }, "Resume checks")
            : h("button", { type: "button", class: "quiet", onclick: (event) => act(event.target, change({ paused: true })) }, "Pause checks")
        )
      ),
    h("h2", {}, "Snapshots"),
    h("div", { class: "panel" }, table(
      [
        { title: "Snapshot", cell: (item) => short(item.snapshot_id) },
        { title: "Retrieved", cell: (item) => when(item.retrieved_at) },
        { title: "Format", cell: (item) => item.format || "–" },
        { title: "Licence", cell: (item) => item.licence || "unknown" },
        { title: "Bytes", num: true, cell: (item) => number(item.bytes) },
      ],
      row.snapshots,
      "No snapshot yet."
    )),
    h("h2", {}, "Runs"),
    h("div", { class: "panel" }, table(
      [
        { title: "Run", cell: (item) => short(item.run_id, 40) },
        { title: "Kind", cell: (item) => item.kind },
        { title: "Status", cell: (item) => badge(item.status || "unknown", item.status === "needs_review" ? "warn" : item.status === "failed" ? "bad" : "") },
        { title: "Snapshot", cell: (item) => short(item.snapshot_id) },
        { title: "Created", cell: (item) => when(item.created_at) },
        { title: "Model calls", num: true, cell: (item) => number(item.model_calls) },
      ],
      row.runs,
      "No run yet."
    )),
    h("h2", {}, "Drift checks"),
    h("div", { class: "panel" }, table(
      [
        { title: "Checked", cell: (item) => when(item.checked_at) },
        { title: "Snapshot", cell: (item) => short(item.snapshot_id) },
        { title: "Result", cell: (item) => badge(item.blocking ? "blocked" : item.status, item.blocking ? "bad" : item.status === "unchanged" ? "good" : "warn") },
        { title: "Reasons", cell: (item) => (Array.isArray(item.reasons) ? item.reasons.map((reason) => (typeof reason === "string" ? reason : JSON.stringify(reason))).join("; ") : JSON.stringify(item.reasons)) || "–" },
      ],
      row.drift_checks,
      "No drift check recorded."
    )),
    h("h2", {}, "What people did here"),
    h("div", { class: "panel" }, actionsTable(row.actions))
  );
}

async function releasesScreen() {
  const found = await api("GET", "/releases");
  const stage = h("div", {});
  const compare = async (batch) => {
    const preview = await api("GET", "/releases/preview?batch_id=" + encodeURIComponent(batch.batch_id));
    const notes = h("input", { type: "text", name: "notes", size: 50 });
    const anyway = h("input", { type: "checkbox" });
    const create = h("button", {
      disabled: !preview.ready,
      onclick: (event) =>
        act(event.target, async () => {
          const release = await api("POST", "/releases", { batch_id: batch.batch_id, notes: notes.value || null });
          await releasesScreen();
          view.prepend(notice("Release #" + release.release_id + " is recorded in your name. Dagster builds the models for it.", "good"));
        }, stage),
    }, "Record this release");
    anyway.addEventListener("change", () => { create.disabled = !(preview.ready || anyway.checked); });
    put(stage, 
      h("div", { class: "panel" },
        h("h2", {}, "Batch " + batch.batch_id + (preview.current_release_id ? " against release #" + preview.current_release_id : ": the first release")),
        h("div", { class: "tiles" },
          h("div", { class: "tile" }, h("b", {}, number(preview.profiles)), h("span", {}, "profiles in the batch")),
          h("div", { class: "tile" }, h("b", {}, number(preview.profiles_added)), h("span", {}, "added")),
          h("div", { class: "tile" }, h("b", {}, number(preview.profiles_changed)), h("span", {}, "changed")),
          h("div", { class: "tile" }, h("b", {}, number(preview.profiles_removed)), h("span", {}, "removed")),
          h("div", { class: "tile" }, h("b", {}, number(preview.profiles_unchanged)), h("span", {}, "unchanged"))
        ),
        preview.refreshed_sources > 0 && notice(preview.refreshed_sources + " of the batch's sources were refreshed. A batch is a sample chosen again after a refresh, so part of this difference is resampling, not change at the publishers.", "warn"),
        h("h2", {}, "Checks"),
        table([{ title: "Check", cell: (check) => check.check }, { title: "Result", cell: (check) => badge(check.passed ? "passed" : "failed", check.passed ? "good" : "bad") }], preview.checks),
        h("p", { class: "muted" }, "Recording a release is your decision and is stored in your name. Clients see it at once, within their tier."),
        h("div", { class: "row" }, h("label", { class: "grow" }, "Notes (optional)", notes)),
        !preview.ready && h("p", {}, h("label", { class: "check" }, anyway, "Record it although a check failed.")),
        h("div", { class: "row" }, create)
      )
    );
    stage.scrollIntoView({ behavior: "smooth" });
  };
  show(
    h("h1", {}, "Releases"),
    h("p", { class: "lead" }, "A release is what clients are served. Only a person records one; compare a batch with the current release first."),
    h("h2", {}, "Recorded"),
    h("div", { class: "panel" }, table(
      [
        { title: "Release", cell: (row) => "#" + row.release_id },
        { title: "Batch", cell: (row) => short(row.batch_id) },
        { title: "Ontology", cell: (row) => short(row.ontology_hash) },
        { title: "Recorded by", cell: (row) => row.released_by },
        { title: "When", cell: (row) => when(row.released_at) },
        { title: "Notes", cell: (row) => row.notes || "–" },
      ],
      found.releases,
      "No release has been recorded, so clients are served nothing yet."
    )),
    h("h2", {}, "Batches"),
    h("div", { class: "panel" }, table(
      [
        { title: "Batch", cell: (row) => h("code", {}, row.batch_id) },
        { title: "Kind", cell: (row) => row.batch_kind },
        { title: "Recorded", cell: (row) => when(row.recorded_at) },
        { title: "Runs", num: true, cell: (row) => number(row.runs) },
        { title: "Profiles", num: true, cell: (row) => number(row.counted_profiles) },
        { title: "Released as", cell: (row) => ((row.release_ids || []).length ? row.release_ids.map((id) => "#" + id).join(", ") : "–") },
        { title: "", cell: (row) => may("product_owner") && h("button", { class: "quiet", onclick: (event) => act(event.target, () => compare(row), stage) }, "Compare and release") },
      ],
      found.batches,
      "No batch has been assembled."
    )),
    stage
  );
}

async function clientsScreen() {
  const found = await api("GET", "/clients");
  const again = () => clientsScreen();
  const shown = h("div", {});
  const tierOptions = (chosen) => found.tiers.map((tier) => h("option", { value: tier.id, selected: tier.id === chosen }, tier.id));

  const name = h("input", { type: "text", name: "name", required: true });
  const tier = h("select", { name: "tier" }, tierOptions());
  const newClient = h(
    "form",
    { class: "row", onsubmit: (event) => { event.preventDefault(); act(event.submitter, async () => { await api("POST", "/clients", { name: name.value, tier_id: tier.value }); await again(); }); } },
    h("label", {}, "Name", name), h("label", {}, "Tier", tier), h("button", { disabled: !found.tiers.length }, "Create client")
  );

  const issue = async (client, label) => {
    const key = await api("POST", "/clients/" + client.client_id + "/keys", { label: label || null });
    await again();
    view.prepend(
      h("div", { class: "notice warn", role: "alert" },
        h("p", {}, "This is the key for " + client.name + ". It is shown this once and cannot be shown again; copy it now and hand it over safely."),
        h("div", { class: "secret" }, key.key))
    );
    window.scrollTo(0, 0);
  };

  const tierForm = (existing) => {
    const field = (label, attributes) => { const input = h("input", attributes); return [h("label", {}, label, input), input]; };
    const [idLabel, id] = field("Tier", { type: "text", required: true, value: existing ? existing.id : "", readonly: Boolean(existing), size: 10 });
    const [rateLabel, rate] = field("Calls per minute", { type: "number", min: "1", required: true, value: existing ? existing.rate_per_minute : 60, size: 6 });
    const [quotaLabel, quota] = field("Monthly quota (empty: none)", { type: "number", min: "1", value: existing && existing.monthly_quota ? existing.monthly_quota : "", size: 8 });
    const [interfacesLabel, interfaces] = field("Interfaces", { type: "text", value: existing ? existing.interfaces.join(", ") : "rest" });
    const [toolsetsLabel, toolsets] = field("MCP toolsets", { type: "text", value: existing ? existing.toolsets.join(", ") : "" });
    const [scopeLabel, scope] = field("Sources (empty: all)", { type: "text", value: existing && existing.source_scope ? existing.source_scope.join(", ") : "" });
    const [lagLabel, lag] = field("Releases behind", { type: "number", min: "0", value: existing ? existing.release_lag : 0, size: 4 });
    const [depthLabel, depth] = field("History depth (empty: all)", { type: "number", min: "0", value: existing && existing.history_depth !== null ? existing.history_depth : "", size: 4 });
    const bundles = h("input", { type: "checkbox", checked: existing ? existing.bundle_downloads : false });
    const list = (input) => input.value.split(",").map((item) => item.trim()).filter(Boolean);
    put(shown, 
      h("form",
        { class: "panel", onsubmit: (event) => { event.preventDefault(); act(event.submitter, async () => {
          await api("PUT", "/tiers/" + encodeURIComponent(id.value), {
            rate_per_minute: Number(rate.value),
            monthly_quota: quota.value ? Number(quota.value) : null,
            interfaces: list(interfaces),
            toolsets: list(toolsets),
            source_scope: list(scope).length ? list(scope) : null,
            bundle_downloads: bundles.checked,
            release_lag: Number(lag.value || 0),
            history_depth: depth.value === "" ? null : Number(depth.value),
          });
          await again();
        }, shown); } },
        h("h2", {}, existing ? "Edit tier " + existing.id : "New tier"),
        h("p", { class: "muted" }, "A tier limits how much and through which interface a client reads. It never hides evidence: every answer keeps its provenance, alternatives and licence."),
        h("div", { class: "row" }, idLabel, rateLabel, quotaLabel, lagLabel, depthLabel),
        h("div", { class: "row" }, interfacesLabel, toolsetsLabel, scopeLabel, h("label", { class: "check" }, bundles, "Bundle downloads")),
        h("p", {}, h("button", {}, "Save tier"))
      )
    );
  };

  show(
    h("h1", {}, "Clients, tiers and keys"),
    h("p", { class: "lead" }, "Who may read the product service, how much, and with which keys. A key's secret is shown once, when it is issued."),
    h("h2", {}, "Tiers"),
    h("div", { class: "panel" },
      table(
        [
          { title: "Tier", cell: (row) => row.id },
          { title: "Calls/min", num: true, cell: (row) => number(row.rate_per_minute) },
          { title: "Monthly quota", num: true, cell: (row) => (row.monthly_quota ? number(row.monthly_quota) : "none") },
          { title: "Interfaces", cell: (row) => row.interfaces.join(", ") },
          { title: "Toolsets", cell: (row) => row.toolsets.join(", ") || "–" },
          { title: "Sources", cell: (row) => (row.source_scope ? row.source_scope.length + " named" : "all") },
          { title: "Bundles", cell: (row) => (row.bundle_downloads ? "yes" : "no") },
          { title: "", cell: (row) => h("button", { class: "quiet", onclick: () => tierForm(row) }, "Edit") },
        ],
        found.tiers,
        "No tier yet. Create one before the first client."
      ),
      h("p", {}, h("button", { class: "quiet", onclick: () => tierForm(null) }, "New tier"))
    ),
    shown,
    h("h2", {}, "Clients"),
    h("div", { class: "panel" }, newClient),
    found.clients.map((client) => {
      const keyLabel = h("input", { type: "text", name: "label", size: 18 });
      const move = h("select", { "aria-label": "Tier of " + client.name }, tierOptions(client.tier_id));
      move.addEventListener("change", () => act(move, async () => { await api("PATCH", "/clients/" + client.client_id, { tier_id: move.value }); await again(); }));
      return h("div", { class: "panel" },
        h("div", { class: "row" },
          h("h2", { class: "grow" }, client.name, " ", badge(client.status, client.status === "active" ? "good" : "bad")),
          h("label", {}, "Tier", move),
          h("button", { class: "quiet", onclick: (event) => act(event.target, async () => { await api("PATCH", "/clients/" + client.client_id, { status: client.status === "active" ? "suspended" : "active" }); await again(); }) }, client.status === "active" ? "Suspend" : "Reactivate"),
          h("form", { class: "row", onsubmit: (event) => { event.preventDefault(); act(event.submitter, () => issue(client, keyLabel.value)); } }, h("label", {}, "Label of a new key (optional)", keyLabel), h("button", {}, "Issue a key"))
        ),
        table(
          [
            { title: "Key", cell: (key) => h("code", {}, "ll_" + key.prefix + "_…") },
            { title: "Label", cell: (key) => key.label || "–" },
            { title: "Created", cell: (key) => when(key.created_at) },
            { title: "Expires", cell: (key) => (key.expires_at ? when(key.expires_at) : "never") },
            { title: "State", cell: (key) => (key.revoked_at ? [badge("revoked", "bad"), " ", when(key.revoked_at)] : badge("active", "good")) },
            { title: "", cell: (key) => !key.revoked_at && h("button", { class: "danger", onclick: (event) => {
              // Asked twice: the first press only arms the button.
              if (event.target.dataset.armed) act(event.target, async () => { await api("DELETE", "/keys/" + key.prefix); await again(); });
              else { event.target.dataset.armed = "yes"; event.target.textContent = "Revoke now? It stops working at once"; }
            } }, "Revoke") },
          ],
          client.keys,
          "No key issued."
        )
      );
    })
  );
}

async function ontologyScreen() {
  const versions = await api("GET", "/ontology/versions");
  show(
    h("h1", {}, "Ontology versions"),
    h("p", { class: "lead" }, "Read-only here. Promoting a version is a person's decision made with the command line (link-lens ontology promote), and needs a recorded gate run with no failed check."),
    versions.length
      ? versions.map((version) =>
          h("div", { class: "panel" },
            h("div", { class: "row" },
              h("h2", { class: "grow" }, version.label, " ", short(version.ontology_hash)),
              version.activations.length ? badge(version.activations[0].status + " for " + version.activations[0].experiment_id, "good") : badge("never activated"),
              version.gate ? badge(version.gate.passed ? "gate passed" : "gate failed", version.gate.passed ? "good" : "bad") : badge("not gated")
            ),
            facts([
              ["Created", when(version.created_at)],
              ["Parent", version.parent_hash ? short(version.parent_hash) : "none"],
              version.gate && ["Gate run", when(version.gate.run_at)],
            ]),
            version.gate && table([{ title: "Check", cell: (check) => check.check }, { title: "Result", cell: (check) => badge(check.result, check.result === "fail" ? "bad" : check.result === "pass" ? "good" : "") }], version.gate.checks),
            version.activations.length > 0 && table(
              [
                { title: "Activation", cell: (row) => row.status },
                { title: "Experiment", cell: (row) => row.experiment_id },
                { title: "By", cell: (row) => row.reviewer || "–" },
                { title: "When", cell: (row) => when(row.created_at) },
              ],
              version.activations
            )
          )
        )
      : notice("No ontology version is registered.")
  );
}

function actionsTable(actions) {
  const kinds = { done: "good", failed: "bad", refused: "warn", unfinished: "warn" };
  return table(
    [
      { title: "When", cell: (row) => when(row.at) },
      { title: "Who", cell: (row) => [row.actor, " ", h("span", { class: "muted" }, "(" + row.role + ")")] },
      { title: "Action", cell: (row) => h("code", { class: "whole" }, row.action) },
      { title: "Target", cell: (row) => h("span", { class: "mono" }, row.target) },
      { title: "Outcome", cell: (row) => badge(row.outcome, kinds[row.outcome]) },
      { title: "Details", cell: (row) => h("span", { class: "mono" }, JSON.stringify({ request: row.request, result: row.result })) },
    ],
    actions,
    "Nothing recorded."
  );
}

async function auditScreen() {
  const actions = await api("GET", "/actions?limit=200");
  show(
    h("h1", {}, "Audit log"),
    h("p", { class: "lead" }, "Every change made through this console: who, in which role, to what, and how it ended. A request is written before the change it asks for. No key or secret is ever stored here."),
    h("div", { class: "panel" }, actionsTable(actions))
  );
}

// Routing

const SCREENS = [
  { path: "", title: "Home", role: "engineer", screen: homeScreen },
  { path: "sources", title: "Sources", role: "engineer", screen: sourcesScreen },
  { path: "releases", title: "Releases", role: "engineer", screen: releasesScreen },
  { path: "ontology", title: "Ontology", role: "engineer", screen: ontologyScreen },
  { path: "clients", title: "Clients", role: "admin", screen: clientsScreen },
  { path: "audit", title: "Audit log", role: "admin", screen: auditScreen },
];

async function route() {
  if (!me) return;
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean).map(decodeURIComponent);
  const first = parts[0] || "";
  document.getElementById("nav").replaceChildren(
    ...SCREENS.filter((item) => may(item.role)).map((item) => h("a", { href: "#/" + item.path, class: item.path === first ? "here" : "", "aria-current": item.path === first ? "page" : null }, item.title))
  );
  show(h("p", { class: "muted" }, "Loading…"));
  try {
    if (first === "sources" && parts[1] === "add") await addSourceScreen();
    else if (first === "sources" && parts[1]) await sourceScreen(parts.slice(1).join("/"));
    else {
      const found = SCREENS.find((item) => item.path === first);
      if (!found) show(notice("There is no such page.", "bad"));
      else await found.screen();
    }
  } catch (error) {
    if (error.status !== 401) show(notice(error.message, "bad"));
  }
}

async function start() {
  try {
    me = await api("GET", "/me");
  } catch (error) {
    return;
  }
  document.getElementById("bar").hidden = false;
  document.getElementById("who").textContent = me.name + " · " + me.role.replace("_", " ");
  await route();
}

document.getElementById("sign-out").addEventListener("click", async () => {
  await api("DELETE", "/session").catch(() => null);
  me = null;
  signInScreen();
});
window.addEventListener("hashchange", route);
start();
