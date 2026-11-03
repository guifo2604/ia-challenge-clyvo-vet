const estado = { clinicas: [], clinicaId: null, tutores: [], pets: [], aba: "prioridade" };
const tutorNome = (id) => (estado.tutores.find((t) => t.id === id) || {}).nome || "";
const vazio = (titulo, texto) => `<div class="vazio"><strong>${esc(titulo)}</strong>${esc(texto)}</div>`;

async function init() {
  try {
    [estado.clinicas, estado.tutores, estado.pets] = await Promise.all([api("/clinicas"), api("/tutores"), api("/pets")]);
  } catch (e) { $("#painel-prioridade").innerHTML = `<div class="painel"><div class="erro">${esc(e.message)}</div></div>`; return; }
  const sel = $("#sel-clinica");
  sel.innerHTML = estado.clinicas.map((c) => `<option value="${c.id}">${esc(c.nome)}</option>`).join("");
  const lembrada = Number(lembrar("clinicaId"));
  estado.clinicaId = estado.clinicas.some((c) => c.id === lembrada) ? lembrada : (estado.clinicas[0] || {}).id;
  sel.value = estado.clinicaId;
  sel.addEventListener("change", () => { estado.clinicaId = Number(sel.value); guardar("clinicaId", sel.value); abrirAba(estado.aba); });
  $$(".aba").forEach((b) => b.addEventListener("click", () => abrirAba(b.id.replace("aba-", ""))));
  $("#btn-novo-tutor").addEventListener("click", async () => {
    const t = await abrirDialogoTutor(); if (!t) return;
    estado.tutores.push(t); aviso(`Tutor ${t.nome} cadastrado.`);
  });
  $("#btn-novo-pet").addEventListener("click", async () => {
    if (!estado.tutores.length) return aviso("Cadastre um tutor primeiro.");
    const p = await abrirDialogoPet({ tutores: estado.tutores, tutorId: estado.tutores[0].id }); if (!p) return;
    estado.pets.push(p); aviso(`${p.nome} cadastrado.`);
    if (estado.aba === "nova") abrirAba("nova", p.id);
  });
  abrirAba("prioridade");
}

function abrirAba(nome, petId) {
  estado.aba = nome;
  $$(".aba").forEach((b) => b.setAttribute("aria-selected", String(b.id === `aba-${nome}`)));
  ["prioridade", "nova", "consultas"].forEach((n) => { $(`#painel-${n}`).hidden = n !== nome; });
  if (nome === "prioridade") desenharPrioridade();
  if (nome === "nova") desenharNova(petId);
  if (nome === "consultas") desenharConsultas();
}

/* ---------- Prioridade ---------- */
async function desenharPrioridade() {
  const alvo = $("#painel-prioridade");
  alvo.innerHTML = `<div class="painel"><p class="mudo">Carregando…</p></div>`;
  try {
    const lista = await api(`/clinicas/${estado.clinicaId}/alto-risco`);
    alvo.innerHTML = `<div class="painel"><div class="painel__titulo"><h2>Pets para atender primeiro</h2>
      <span class="mudo pequeno">Consulta mais recente de cada pet, do maior para o menor risco</span></div>
      ${lista.length ? `<ol class="fila">${lista.map((p, i) => `<li class="fila__item">
        <span class="fila__ordem">${i + 1}</span>
        <div><div class="fila__nome">${esc(p.pet_nome)} <span class="mudo pequeno" style="font-family:var(--sans);font-weight:400">${esc(p.especie)}, tutor ${esc(p.tutor_nome)}</span></div>
          <p>${esc(p.recomendacao)}</p><p class="mudo pequeno">Última consulta em ${dataBR(p.data_consulta)}</p>
          <details data-pet="${p.pet_id}"><summary>Ver histórico</summary><div class="hist"></div></details></div>
        <div class="fila__medidor"><div class="fila__score">${num(p.score_pct)}%</div>${termometro(p.score_pct, 1)}</div></li>`).join("")}</ol>`
      : vazio("Nenhum pet em alto risco nesta clínica", "Quando uma consulta for avaliada como alto risco, o pet aparece aqui.")}</div>`;
    $$("details[data-pet]", alvo).forEach((d) => d.addEventListener("toggle", () => historicoResumido(d), { once: true }));
  } catch (e) { alvo.innerHTML = `<div class="painel"><div class="erro">${esc(e.message)}</div></div>`; }
}
async function historicoResumido(d) {
  const alvo = $(".hist", d);
  try {
    const cs = await api(`/pets/${d.dataset.pet}/consultas`);
    alvo.innerHTML = `<ul class="historico">${cs.map((c) => `<li><span class="data">${dataBR(c.data_consulta)}</span>
      <span>${esc(c.sintomas || "Sem sintomas")}<small>${esc(c.diagnostico || "Sem diagnóstico")}</small></span>
      <span>${c.predicao ? termometro(c.predicao.score_pct, c.predicao.risco) + `<small>${num(c.predicao.score_pct)}%</small>` : ""}</span></li>`).join("")}</ul>`;
  } catch (e) { alvo.innerHTML = `<div class="erro">${esc(e.message)}</div>`; }
}

/* ---------- Nova consulta ---------- */
function desenharNova(petIdInicial) {
  const alvo = $("#painel-nova");
  if (!estado.pets.length) { alvo.innerHTML = `<div class="painel">${vazio("Nenhum pet cadastrado", "Use “Novo pet” para cadastrar o primeiro.")}</div>`; return; }
  const opcoes = [...estado.pets].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))
    .map((p) => `<option value="${p.id}">${esc(p.nome)} (${esc(tutorNome(p.tutor_id))})</option>`).join("");
  alvo.innerHTML = `<div class="nova">
    <form class="painel" id="form-consulta" novalidate>
      <h2 style="margin-bottom:14px">Registrar consulta</h2>
      <div class="erro" role="alert" hidden></div>
      <div class="campo"><label for="c-pet">Pet</label><select id="c-pet" name="pet" required>${opcoes}</select></div>
      <dl class="ficha" id="ficha"></dl>
      <div class="grade2">
        <div class="campo"><label for="c-data">Data da consulta</label><input id="c-data" name="data" type="date" required max="${hojeISO()}" value="${hojeISO()}"></div>
        <div class="campo"><label for="c-peso">Peso (kg)</label><input id="c-peso" name="peso" type="number" step="any" min="0.1" max="120" required></div>
      </div>
      <div class="campo"><label for="c-sint">Sintomas</label><textarea id="c-sint" name="sintomas" maxlength="500"></textarea></div>
      <div class="campo"><label for="c-diag">Diagnóstico</label><textarea id="c-diag" name="diagnostico" maxlength="500"></textarea></div>
      <button class="btn" type="submit">Registrar e calcular risco</button>
    </form>
    <div id="resultado" aria-live="polite"><div class="painel">${vazio("O risco aparece aqui", "Ao registrar a consulta, a IA avalia o pet com os dados do prontuário.")}</div></div></div>`;
  const form = $("#form-consulta"), selPet = $("#c-pet");
  if (petIdInicial) selPet.value = petIdInicial;
  selPet.addEventListener("change", () => fichaDoPet(selPet.value));
  fichaDoPet(selPet.value);
  form.addEventListener("submit", enviarConsulta);
}

async function fichaDoPet(id) {
  const pet = estado.pets.find((p) => p.id === Number(id)); if (!pet) return;
  const ficha = $("#ficha");
  ficha.innerHTML = `<dt>Idade</dt><dd>${idadeTexto(pet.data_nascimento)}</dd><dt>Castrado</dt><dd>${pet.castrado ? "Sim" : "Não"}</dd>
    <dt>Alergia</dt><dd>${esc(pet.alergia || "Nenhuma")}</dd><dt>Doença crônica</dt><dd>${esc(pet.doenca_cronica || "Nenhuma")}</dd>
    <dt>Vacinas registradas</dt><dd>${pet.total_vacinas}</dd>`;
  try {
    const cs = await api(`/pets/${pet.id}/consultas`);
    if (Number($("#c-pet").value) === pet.id && cs[0] && !$("#c-peso").value) $("#c-peso").value = cs[0].peso_kg;
  } catch (_) { /* o peso é opcional aqui */ }
}

async function enviarConsulta(e) {
  e.preventDefault();
  const f = e.target, erro = $(".erro", f), btn = $("[type=submit]", f);
  if (!f.reportValidity()) return;
  erro.hidden = true; btn.disabled = true;
  try {
    const c = await api("/consultas", { method: "POST", body: {
      pet_id: Number(f.pet.value), clinica_id: estado.clinicaId, data_consulta: f.data.value,
      peso_kg: Number(f.peso.value), sintomas: f.sintomas.value.trim(), diagnostico: f.diagnostico.value.trim() } });
    mostrarResultado(c);
    f.sintomas.value = ""; f.diagnostico.value = "";
    const pet = estado.pets.find((p) => p.id === c.pet_id);
    aviso(`Consulta de ${c.pet_nome} registrada.`);
    if (pet) fichaDoPet(pet.id);
  } catch (err) { erro.textContent = err.message; erro.hidden = false; }
  finally { btn.disabled = false; }
}

function mostrarResultado(c) {
  const p = c.predicao, alto = p.risco === 1;
  $("#resultado").innerHTML = `<div class="painel resultado">
    <p class="mudo">${esc(c.pet_nome)}, consulta de ${dataBR(c.data_consulta)}</p>
    <div class="leitura ${alto ? "leitura--alto" : "leitura--baixo"}" style="margin:12px 0 0">
      <div class="leitura__linha"><h3 style="margin:0">${alto ? "Alto risco" : "Baixo risco"}</h3><span class="leitura__numero">${num(p.score_pct)}%</span></div>
      ${termometro(p.score_pct, p.risco, { grande: true, anima: true })}
      <div class="termo-legenda"><span>0%</span><span>50%: limite de alto risco</span><span>100%</span></div>
      <p><strong>Conduta sugerida:</strong> ${esc(p.recomendacao)}</p></div>
    <p class="aviso" style="margin-top:12px">Apoio à decisão clínica: a avaliação final é do veterinário. Modelo ${esc(p.modelo_versao)}.</p></div>`;
  acionarAnimacoes($("#resultado"));
}

/* ---------- Consultas da clínica ---------- */
async function desenharConsultas() {
  const alvo = $("#painel-consultas");
  alvo.innerHTML = `<div class="painel"><p class="mudo">Carregando…</p></div>`;
  try {
    const cs = (await api(`/clinicas/${estado.clinicaId}/consultas`)).slice(0, 100);
    alvo.innerHTML = `<div class="painel"><div class="painel__titulo"><h2>Consultas da clínica</h2><span class="mudo pequeno">${cs.length} mais recentes</span></div>
      ${cs.length ? `<div class="rolagem"><table><thead><tr><th>Data</th><th>Pet</th><th>Sintomas</th><th>Diagnóstico</th><th>Peso</th><th>Risco</th></tr></thead><tbody>${cs.map((c) => `<tr>
        <td>${dataBR(c.data_consulta)}</td><td>${esc(c.pet_nome)}</td><td>${esc(c.sintomas || "")}</td><td>${esc(c.diagnostico || "")}</td><td>${num(c.peso_kg)} kg</td>
        <td>${c.predicao ? `<span class="etiqueta ${c.predicao.risco ? "etiqueta--alto" : "etiqueta--ok"}">${c.predicao.risco ? "Alto" : "Baixo"} ${num(c.predicao.score_pct)}%</span>` : `<span class="mudo">Sem avaliação</span>`}</td></tr>`).join("")}</tbody></table></div>`
      : vazio("Nenhuma consulta nesta clínica", "Registre a primeira em “Nova consulta”.")}</div>`;
  } catch (e) { alvo.innerHTML = `<div class="painel"><div class="erro">${esc(e.message)}</div></div>`; }
}

init();
