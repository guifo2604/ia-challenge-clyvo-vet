/* Utilidades compartilhadas pelas telas do tutor e do veterinário. */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ---- API ---- */
async function erroDaApi(res) {
  try {
    const d = (await res.json()).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d.map((e) => `${(e.loc || []).slice(1).join(".") || "campo"}: ${String(e.msg).replace(/^Value error, /, "")}`).join("; ");
    }
  } catch (_) { /* resposta sem JSON */ }
  return `Algo deu errado (erro ${res.status}). Tente de novo.`;
}
async function api(path, { method = "GET", body } = {}) {
  let res;
  try {
    res = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (_) {
    throw new Error("Não consegui falar com o servidor. Confira se a API está rodando.");
  }
  if (!res.ok) throw new Error(await erroDaApi(res));
  return res.json();
}

/* ---- preferências leves (nunca quebram se o navegador bloquear) ---- */
const lembrar = (k) => { try { return localStorage.getItem(k); } catch (_) { return null; } };
const guardar = (k, v) => { try { localStorage.setItem(k, v); } catch (_) { /* ignora */ } };

/* ---- formatação ---- */
const dataBR = (iso) => (iso ? iso.slice(0, 10).split("-").reverse().join("/") : "");
const hojeISO = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
const num = (n, casas = 1) => Number(n).toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
function idadeTexto(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  const n = new Date();
  let meses = (n.getFullYear() - y) * 12 + (n.getMonth() + 1 - m);
  if (n.getDate() < d) meses--;
  meses = Math.max(meses, 0);
  if (meses < 12) return `${meses} ${meses === 1 ? "mês" : "meses"}`;
  const a = Math.floor(meses / 12);
  return `${a} ${a === 1 ? "ano" : "anos"}`;
}
function fichaPet(p) {
  const sexo = p.sexo === "Macho" ? (p.castrado ? "macho castrado" : "macho") : (p.castrado ? "fêmea castrada" : "fêmea");
  return `${p.especie}${p.raca ? ", " + p.raca : ""}, ${idadeTexto(p.data_nascimento)}, ${sexo}`;
}

/* ---- termômetro de risco ---- */
function termometro(score, alto, { grande = false, anima = false } = {}) {
  const s = Math.max(0, Math.min(100, Number(score)));
  return `<div class="termo ${alto ? "termo--alto" : ""} ${grande ? "termo--grande" : ""} ${anima ? "termo--anima" : ""}"
    role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${s}"
    aria-label="Índice de risco ${num(s)}% (limite de alto risco: 50%)" style="--p:${s}">
    <span class="termo__bulbo"></span><span class="termo__trilho"><span class="termo__merc"></span><span class="termo__limiar"></span></span></div>`;
}
function acionarAnimacoes(raiz = document) {
  requestAnimationFrame(() => requestAnimationFrame(() => $$(".termo--anima", raiz).forEach((t) => t.classList.add("on"))));
}

/* ---- aviso rápido ---- */
let _toast;
function aviso(texto) {
  let t = $("#toast");
  if (!t) { t = document.createElement("div"); t.id = "toast"; t.className = "toast"; t.setAttribute("role", "status"); document.body.append(t); }
  t.textContent = texto; t.hidden = false;
  clearTimeout(_toast); _toast = setTimeout(() => { t.hidden = true; }, 3500);
}

/* ---- diálogos com formulário ---- */
function dialogoForm({ titulo, corpo, botao, aoAbrir, aoEnviar }) {
  return new Promise((resolve) => {
    const d = document.createElement("dialog");
    d.className = "dlg";
    d.innerHTML = `<form class="dlg__form" novalidate>
      <h2>${esc(titulo)}</h2>
      <div class="erro" role="alert" hidden></div>
      ${corpo}
      <div class="dlg__acoes"><button type="button" class="btn btn--claro" data-cancelar>Cancelar</button>
      <button type="submit" class="btn">${esc(botao)}</button></div></form>`;
    document.body.append(d);
    let resultado = null;
    const form = $("form", d), erro = $(".erro", d), enviar = $("[type=submit]", d);
    $("[data-cancelar]", d).addEventListener("click", () => d.close());
    d.addEventListener("close", () => { d.remove(); resolve(resultado); });
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!form.reportValidity()) return;
      erro.hidden = true; enviar.disabled = true;
      try { resultado = await aoEnviar(form); d.close(); }
      catch (err) { erro.textContent = err.message; erro.hidden = false; enviar.disabled = false; }
    });
    if (aoAbrir) aoAbrir(form);
    d.showModal();
    const primeiro = form.querySelector("input:not([type=hidden]),select,textarea");
    if (primeiro) primeiro.focus();
  });
}

const SANGUE = {
  Cachorro: ["DEA 1.1+", "DEA 1.1-", "DEA 4+"],
  Gato: ["A", "AB", "B"],
};

function abrirDialogoTutor() {
  return dialogoForm({
    titulo: "Novo tutor", botao: "Cadastrar tutor",
    corpo: `<div class="campo"><label for="t-nome">Nome</label><input id="t-nome" name="nome" required minlength="2" maxlength="150"></div>
            <div class="campo"><label for="t-email">E-mail (opcional)</label><input id="t-email" name="email" type="email" maxlength="150"></div>`,
    aoEnviar: (f) => api("/tutores", { method: "POST", body: { nome: f.nome.value.trim(), email: f.email.value.trim() } }),
  });
}

function abrirDialogoPet({ tutores, tutorId }) {
  const opcoesTutor = tutores.map((t) => `<option value="${t.id}" ${t.id === tutorId ? "selected" : ""}>${esc(t.nome)}</option>`).join("");
  return dialogoForm({
    titulo: "Novo pet", botao: "Cadastrar pet",
    corpo: `<div class="campo"><label for="p-tutor">Tutor</label><select id="p-tutor" name="tutor_id" required>${opcoesTutor}</select></div>
      <div class="grade2">
        <div class="campo"><label for="p-nome">Nome do pet</label><input id="p-nome" name="nome" required maxlength="100"></div>
        <div class="campo"><label for="p-especie">Espécie</label><select id="p-especie" name="especie" required><option>Cachorro</option><option>Gato</option></select></div>
        <div class="campo"><label for="p-raca">Raça (opcional)</label><input id="p-raca" name="raca" maxlength="100"></div>
        <div class="campo"><label for="p-nasc">Data de nascimento</label><input id="p-nasc" name="data_nascimento" type="date" required max="${hojeISO()}"></div>
        <div class="campo"><label for="p-sexo">Sexo</label><select id="p-sexo" name="sexo" required><option>Macho</option><option>Fêmea</option></select></div>
        <div class="campo"><label for="p-sangue">Tipo sanguíneo</label><select id="p-sangue" name="tipo_sanguineo" required></select></div>
      </div>
      <div class="campo campo--check"><label><input type="checkbox" name="castrado"> Castrado</label></div>
      <div class="campo"><label for="p-alergia">Alergias (deixe vazio se não houver)</label><input id="p-alergia" name="alergia" maxlength="255"></div>
      <div class="campo"><label for="p-cronica">Doença crônica (deixe vazio se não houver)</label><input id="p-cronica" name="doenca_cronica" maxlength="255"></div>`,
    aoAbrir: (f) => {
      const trocar = () => { f.tipo_sanguineo.innerHTML = SANGUE[f.especie.value].map((s) => `<option>${esc(s)}</option>`).join(""); };
      f.especie.addEventListener("change", trocar); trocar();
    },
    aoEnviar: (f) => api("/pets", { method: "POST", body: {
      tutor_id: Number(f.tutor_id.value), nome: f.nome.value.trim(), especie: f.especie.value,
      raca: f.raca.value.trim(), data_nascimento: f.data_nascimento.value, sexo: f.sexo.value,
      tipo_sanguineo: f.tipo_sanguineo.value, castrado: f.castrado.checked,
      alergia: f.alergia.value.trim(), doenca_cronica: f.doenca_cronica.value.trim(),
    } }),
  });
}

function abrirDialogoVacina(pet) {
  return dialogoForm({
    titulo: `Registrar vacina de ${pet.nome}`, botao: "Registrar vacina",
    corpo: `<div class="campo"><label for="v-nome">Vacina</label><input id="v-nome" name="nome" required minlength="2" maxlength="100" placeholder="Ex.: V10, Antirrábica"></div>
      <div class="grade2">
        <div class="campo"><label for="v-ap">Data da aplicação</label><input id="v-ap" name="data_aplicacao" type="date" required max="${hojeISO()}"></div>
        <div class="campo"><label for="v-val">Validade (opcional)</label><input id="v-val" name="data_validade" type="date"></div>
      </div>`,
    aoEnviar: (f) => api(`/pets/${pet.id}/vacinas`, { method: "POST", body: {
      nome: f.nome.value.trim(), data_aplicacao: f.data_aplicacao.value, data_validade: f.data_validade.value || null } }),
  });
}
