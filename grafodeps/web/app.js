const state = {
  graph: null,
  selectedModule: null,
  selectedCycle: null,
  positions: new Map(),
};

const elements = {
  form: document.querySelector("#project-form"),
  projectPath: document.querySelector("#project-path"),
  analyzeButton: document.querySelector("#analyze-button"),
  demoButton: document.querySelector("#demo-button"),
  exportButton: document.querySelector("#export-button"),
  clearFocus: document.querySelector("#clear-focus"),
  search: document.querySelector("#module-search"),
  status: document.querySelector("#status"),
  modules: document.querySelector("#module-list"),
  cycles: document.querySelector("#cycle-list"),
  visibleCount: document.querySelector("#visible-count"),
  cycleListCount: document.querySelector("#cycle-list-count"),
  moduleCount: document.querySelector("#module-count"),
  edgeCount: document.querySelector("#edge-count"),
  cycleCount: document.querySelector("#cycle-count"),
  projectName: document.querySelector("#project-name"),
  graph: document.querySelector("#graph"),
  graphWrap: document.querySelector("#graph-wrap"),
  graphEmpty: document.querySelector("#graph-empty"),
  detailEmpty: document.querySelector("#detail-empty"),
  detailContent: document.querySelector("#detail-content"),
  detailKind: document.querySelector("#detail-kind"),
  detailName: document.querySelector("#detail-name"),
  codeAnalysis: document.querySelector("#code-analysis"),
  moduleSummary: document.querySelector("#module-summary"),
  definitionList: document.querySelector("#definition-list"),
  analysisNote: document.querySelector("#analysis-note"),
  directImportList: document.querySelector("#direct-import-list"),
  importedByList: document.querySelector("#imported-by-list"),
  moduleStats: document.querySelector("#module-stats"),
  inDegree: document.querySelector("#in-degree"),
  outDegree: document.querySelector("#out-degree"),
  relationTitle: document.querySelector("#relation-title"),
  relationSummary: document.querySelector("#relation-summary"),
  relationList: document.querySelector("#relation-list"),
};

const SVG_NS = "http://www.w3.org/2000/svg";
const VIEW_WIDTH = 1000;
const VIEW_HEIGHT = 680;

function setStatus(message, kind = "") {
  elements.status.textContent = message;
  elements.status.className = `status ${kind}`.trim();
}

async function analyzeProject(projectPath) {
  const project = projectPath.trim();
  if (!project) {
    setStatus("Escribe la ruta de una carpeta Python para analizarla.", "error");
    elements.projectPath.focus();
    return;
  }

  elements.analyzeButton.disabled = true;
  elements.demoButton.disabled = true;
  setStatus("Analizando archivos Python…");

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project }),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error?.message || "No se pudo analizar la carpeta.");
    }

    state.graph = result;
    state.selectedModule = null;
    state.selectedCycle = null;
    state.positions = layoutNodes(result.modules);
    updateSummary();
    renderModuleList();
    renderCycleList();
    drawGraph();
    showNoSelection();
    elements.search.disabled = false;
    elements.exportButton.disabled = false;
    elements.clearFocus.disabled = false;
    setStatus(`Análisis completado: ${result.modules.length} módulos y ${result.edges.length} dependencias.`, "success");
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Error inesperado durante el análisis.", "error");
  } finally {
    elements.analyzeButton.disabled = false;
    elements.demoButton.disabled = false;
  }
}

function updateSummary() {
  elements.moduleCount.textContent = state.graph.modules.length;
  elements.edgeCount.textContent = state.graph.edges.length;
  elements.cycleCount.textContent = state.graph.cycles.length;
  elements.projectName.textContent = state.graph.project;
  elements.projectName.title = state.graph.project;
}

function layoutNodes(modules) {
  const positions = new Map();
  const count = modules.length;
  if (!count) return positions;

  const columns = Math.max(1, Math.ceil(Math.sqrt(count * 1.35)));
  const rows = Math.ceil(count / columns);
  const xGap = Math.min(850 / columns, 180);
  const yGap = Math.min(560 / rows, 130);
  const usedWidth = xGap * (columns - 1);
  const usedHeight = yGap * (rows - 1);
  const startX = (VIEW_WIDTH - usedWidth) / 2;
  const startY = (VIEW_HEIGHT - usedHeight) / 2;

  modules.forEach((module, index) => {
    const row = Math.floor(index / columns);
    const rowStart = row * columns;
    const rowCount = Math.min(columns, count - rowStart);
    const rowWidth = xGap * (rowCount - 1);
    positions.set(module, {
      x: (VIEW_WIDTH - rowWidth) / 2 + (index - rowStart) * xGap,
      y: startY + row * yGap,
    });
  });
  return positions;
}

function renderModuleList() {
  const query = elements.search.value.trim().toLowerCase();
  const matches = state.graph.modules.filter((module) => module.toLowerCase().includes(query));
  elements.visibleCount.textContent = `${matches.length}/${state.graph.modules.length}`;
  elements.modules.replaceChildren();

  if (!matches.length) {
    elements.modules.append(makeEmptyItem("No hay módulos que coincidan."));
    return;
  }

  const cyclicModules = new Set(state.graph.cycles.flat());
  for (const module of matches) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "module-button";
    button.setAttribute("aria-current", state.selectedModule === module ? "true" : "false");
    button.title = module;
    const dot = document.createElement("span");
    dot.className = `module-dot${cyclicModules.has(module) ? " is-cyclic" : ""}`;
    dot.setAttribute("aria-hidden", "true");
    button.append(dot, document.createTextNode(module));
    button.addEventListener("click", () => selectModule(module));
    item.append(button);
    elements.modules.append(item);
  }
}

function renderCycleList() {
  elements.cycleListCount.textContent = state.graph.cycles.length;
  elements.cycles.replaceChildren();
  if (!state.graph.cycles.length) {
    elements.cycles.append(makeEmptyItem("No se detectaron circuitos simples."));
    return;
  }

  state.graph.cycles.forEach((cycle, index) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "cycle-button";
    button.textContent = `${cycle.join(" → ")} → ${cycle[0]}`;
    button.setAttribute("aria-pressed", String(state.selectedCycle === index));
    button.addEventListener("click", () => selectCycle(index));
    item.append(button);
    elements.cycles.append(item);
  });
}

function makeEmptyItem(message) {
  const item = document.createElement("li");
  item.className = "empty-list";
  item.textContent = message;
  return item;
}

function appendSvg(tag, attributes = {}, parent = elements.graph) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  parent.append(node);
  return node;
}

function drawGraph() {
  if (!state.graph) return;
  elements.graph.replaceChildren();
  elements.graphWrap.hidden = false;
  elements.graphEmpty.hidden = true;
  addMarkers();

  const selectedCycle = state.selectedCycle === null ? null : state.graph.cycles[state.selectedCycle];
  const cycleEdges = new Set();
  if (selectedCycle) {
    for (let index = 0; index < selectedCycle.length; index += 1) {
      cycleEdges.add(edgeKey(selectedCycle[index], selectedCycle[(index + 1) % selectedCycle.length]));
    }
  }

  const reachable = state.selectedModule ? reachableFrom(state.selectedModule) : new Set();
  const hasFocus = Boolean(state.selectedModule || selectedCycle);

  for (const edge of state.graph.edges) {
    const group = appendSvg("g", { "aria-hidden": "true" });
    const start = state.positions.get(edge.source);
    const end = state.positions.get(edge.target);
    const key = edgeKey(edge.source, edge.target);
    const isCycleEdge = cycleEdges.has(key);
    const isHighlighted = state.selectedModule && reachable.has(edge.target) &&
      (edge.source === state.selectedModule || reachable.has(edge.source));
    const isDimmed = hasFocus && !isCycleEdge && !isHighlighted;
    appendSvg("line", {
      x1: start.x,
      y1: start.y,
      x2: end.x,
      y2: end.y,
      class: `edge${isCycleEdge ? " is-cycle" : isHighlighted ? " is-highlighted" : ""}${isDimmed ? " is-dimmed" : ""}`,
    }, group);
  }

  const selectedNodes = new Set(selectedCycle || []);
  if (state.selectedModule) {
    selectedNodes.add(state.selectedModule);
    for (const node of reachable) selectedNodes.add(node);
  }
  const cyclicNodes = new Set(state.graph.cycles.flat());
  for (const module of state.graph.modules) {
    const position = state.positions.get(module);
    const selected = module === state.selectedModule;
    const inSelectedCycle = selectedCycle?.includes(module) || false;
    const relevant = selectedNodes.has(module) || inSelectedCycle;
    const group = appendSvg("g", {
      class: `node${selected ? " is-selected" : ""}${cyclicNodes.has(module) ? " is-cyclic" : ""}${hasFocus && !relevant ? " is-dimmed" : ""}`,
      tabindex: "0",
      role: "button",
      "aria-label": nodeLabel(module),
      "aria-pressed": String(selected || inSelectedCycle),
      transform: `translate(${position.x} ${position.y})`,
    });
    const circle = appendSvg("circle", { r: 19 }, group);
    const title = appendSvg("title", {}, group);
    title.textContent = nodeLabel(module);
    const label = appendSvg("text", { x: 25, y: 4 }, group);
    label.textContent = module;
    group.addEventListener("click", () => selectModule(module));
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectModule(module);
      }
    });
    circle.setAttribute("aria-hidden", "true");
  }
}

function addMarkers() {
  const defs = appendSvg("defs");
  const regular = appendSvg("marker", {
    id: "arrow",
    viewBox: "0 0 10 10",
    refX: "9",
    refY: "5",
    markerWidth: "6",
    markerHeight: "6",
    orient: "auto-start-reverse",
  }, defs);
  appendSvg("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: "#b8c5c1" }, regular);
  const cycle = appendSvg("marker", {
    id: "arrow-cycle",
    viewBox: "0 0 10 10",
    refX: "9",
    refY: "5",
    markerWidth: "7",
    markerHeight: "7",
    orient: "auto-start-reverse",
  }, defs);
  appendSvg("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: "#c94f43" }, cycle);
}

function nodeLabel(module) {
  const degree = state.graph.degrees[module];
  const importedBy = degree.in === 1 ? "módulo" : "módulos";
  const imports = degree.out === 1 ? "módulo" : "módulos";
  return `${module}: importado por ${degree.in} ${importedBy}; importa ${degree.out} ${imports}.`;
}

function edgeKey(source, target) {
  return `${source}\u0000${target}`;
}

function reachableFrom(root) {
  const adjacency = new Map(state.graph.modules.map((module) => [module, []]));
  for (const edge of state.graph.edges) adjacency.get(edge.source).push(edge.target);
  const visited = new Set();
  const queue = [...(adjacency.get(root) || [])];
  while (queue.length) {
    const current = queue.shift();
    if (visited.has(current)) continue;
    visited.add(current);
    queue.push(...(adjacency.get(current) || []));
  }
  return visited;
}

function selectModule(module) {
  state.selectedModule = module;
  state.selectedCycle = null;
  renderModuleList();
  renderCycleList();
  drawGraph();
  showModuleDetails(module);
}

function selectCycle(index) {
  state.selectedModule = null;
  state.selectedCycle = index;
  renderModuleList();
  renderCycleList();
  drawGraph();
  showCycleDetails(state.graph.cycles[index]);
}

function showNoSelection() {
  elements.detailEmpty.hidden = false;
  elements.detailContent.hidden = true;
}

function showModuleDetails(module) {
  const degree = state.graph.degrees[module];
  const dependencies = [...reachableFrom(module)].filter((dependency) => dependency !== module).sort();
  elements.detailEmpty.hidden = true;
  elements.detailContent.hidden = false;
  elements.codeAnalysis.hidden = false;
  elements.moduleStats.hidden = false;
  elements.detailKind.textContent = "MÓDULO SELECCIONADO";
  elements.detailName.textContent = module;
  renderModuleAnalysis(module);
  renderRelationList(
    state.graph.analysis[module].imports,
    elements.directImportList,
    "No se detectaron importaciones directas a otros módulos del proyecto.",
  );
  renderRelationList(
    state.graph.analysis[module].imported_by,
    elements.importedByList,
    "Ningún otro módulo del proyecto lo importa directamente.",
  );
  elements.inDegree.textContent = degree.in;
  elements.outDegree.textContent = degree.out;
  elements.relationTitle.textContent = "Dependencias alcanzables";
  elements.relationSummary.textContent = `${dependencies.length} módulo(s), contando las dependencias transitivas.`;
  renderRelationList(dependencies, elements.relationList, "No tiene otras dependencias transitivas.");
}

function showCycleDetails(cycle) {
  elements.detailEmpty.hidden = true;
  elements.detailContent.hidden = false;
  elements.codeAnalysis.hidden = true;
  elements.moduleStats.hidden = true;
  elements.detailKind.textContent = "CIRCUITO DIRIGIDO";
  elements.detailName.textContent = `${cycle.join(" → ")} → ${cycle[0]}`;
  elements.relationTitle.textContent = "Módulos del ciclo";
  elements.relationSummary.textContent = `Circuito simple de longitud ${cycle.length}; cada flecha es una dependencia dirigida.`;
  renderRelationList(cycle, elements.relationList, "No hay módulos en este ciclo.");
}

function renderModuleAnalysis(module) {
  const analysis = state.graph.analysis[module];
  elements.moduleSummary.textContent = analysis.summary;
  elements.definitionList.replaceChildren();

  for (const definition of analysis.definitions) {
    const item = document.createElement("li");
    const heading = document.createElement("strong");
    heading.textContent = `${definition.kind} ${definition.name}${definition.signature}`;
    item.append(heading);

    if (definition.description) {
      const description = document.createElement("p");
      description.textContent = definition.description;
      item.append(description);
    } else {
      const missingDescription = document.createElement("p");
      missingDescription.className = "definition-muted";
      missingDescription.textContent = `Sin docstring; definida en la línea ${definition.line}.`;
      item.append(missingDescription);
    }

    if (definition.decorators.length) {
      const decorators = document.createElement("p");
      decorators.className = "definition-muted";
      decorators.textContent = `Decoradores: ${definition.decorators.map((decorator) => `@${decorator}`).join(", ")}`;
      item.append(decorators);
    }

    for (const method of definition.methods) {
      const methodItem = document.createElement("p");
      methodItem.className = "definition-method";
      methodItem.textContent = `Método ${method.name}${method.signature}${method.description ? `: ${method.description}` : ""}`;
      item.append(methodItem);
    }
    if (definition.omitted_methods) {
      const omittedMethods = document.createElement("p");
      omittedMethods.className = "definition-muted";
      omittedMethods.textContent = `${definition.omitted_methods} métodos más omitidos.`;
      item.append(omittedMethods);
    }
    elements.definitionList.append(item);
  }

  if (!analysis.definitions.length) {
    const item = makeEmptyItem("No se encontraron funciones ni clases a nivel de módulo.");
    elements.definitionList.append(item);
  }
  elements.analysisNote.textContent = analysis.omitted_definitions
    ? `Análisis estructural: se omitieron ${analysis.omitted_definitions} definiciones adicionales.`
    : "Resumen basado en docstrings y definiciones del archivo; no ejecuta ni interpreta el flujo del programa.";
}

function renderRelationList(items, list, emptyMessage) {
  list.replaceChildren();
  if (!items.length) {
    list.append(makeEmptyItem(emptyMessage));
    return;
  }
  for (const item of items) {
    const row = document.createElement("li");
    row.textContent = item;
    list.append(row);
  }
}

function resetFocus() {
  state.selectedModule = null;
  state.selectedCycle = null;
  renderModuleList();
  renderCycleList();
  drawGraph();
  showNoSelection();
}

async function exportPng() {
  const source = elements.graph.cloneNode(true);
  source.setAttribute("xmlns", SVG_NS);
  source.setAttribute("width", VIEW_WIDTH);
  source.setAttribute("height", VIEW_HEIGHT);
  for (const edge of source.querySelectorAll(".edge")) {
    edge.setAttribute("stroke", edge.classList.contains("is-cycle") ? "#c94f43" :
      edge.classList.contains("is-highlighted") ? "#0c9b7a" : "#b8c5c1");
    edge.setAttribute("stroke-width", edge.classList.contains("is-cycle") ? "3" :
      edge.classList.contains("is-highlighted") ? "2.6" : "1.5");
    edge.setAttribute("marker-end", edge.classList.contains("is-cycle") ? "url(#arrow-cycle)" : "url(#arrow)");
    if (edge.classList.contains("is-dimmed")) edge.setAttribute("opacity", ".17");
  }
  for (const node of source.querySelectorAll(".node")) {
    const circle = node.querySelector("circle");
    const text = node.querySelector("text");
    circle.setAttribute("fill", node.classList.contains("is-selected") ? "#d7f0e7" : "#fff");
    circle.setAttribute("stroke", node.classList.contains("is-cyclic") ? "#c94f43" :
      node.classList.contains("is-selected") ? "#087f70" : "#839b94");
    circle.setAttribute("stroke-width", node.classList.contains("is-selected") || node.classList.contains("is-cyclic") ? "3" : "2");
    text.setAttribute("fill", "#33464b");
    text.setAttribute("font-family", "Consolas, monospace");
    text.setAttribute("font-size", "11");
    if (node.classList.contains("is-dimmed")) node.setAttribute("opacity", ".17");
  }
  const svgBlob = new Blob([new XMLSerializer().serializeToString(source)], { type: "image/svg+xml;charset=utf-8" });
  const imageUrl = URL.createObjectURL(svgBlob);
  const image = new Image();
  image.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = VIEW_WIDTH * 2;
    canvas.height = VIEW_HEIGHT * 2;
    const context = canvas.getContext("2d");
    context.fillStyle = "#fbfcfb";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.scale(2, 2);
    context.drawImage(image, 0, 0, VIEW_WIDTH, VIEW_HEIGHT);
    URL.revokeObjectURL(imageUrl);
    canvas.toBlob((blob) => {
      if (!blob) {
        setStatus("El navegador no pudo exportar la imagen PNG.", "error");
        return;
      }
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${safeFilename(state.graph.project)}-grafo.png`;
      link.click();
      URL.revokeObjectURL(link.href);
      setStatus("Imagen PNG exportada.", "success");
    }, "image/png");
  };
  image.onerror = () => {
    URL.revokeObjectURL(imageUrl);
    setStatus("No se pudo preparar la imagen PNG.", "error");
  };
  image.src = imageUrl;
}

function safeFilename(name) {
  return name.replace(/[^a-z0-9_-]+/gi, "-").replace(/^-|-$/g, "") || "proyecto";
}

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  analyzeProject(elements.projectPath.value);
});
elements.demoButton.addEventListener("click", () => {
  elements.projectPath.value = "examples";
  analyzeProject("examples");
});
elements.search.addEventListener("input", renderModuleList);
elements.clearFocus.addEventListener("click", resetFocus);
elements.exportButton.addEventListener("click", exportPng);
analyzeProject(elements.projectPath.value);
