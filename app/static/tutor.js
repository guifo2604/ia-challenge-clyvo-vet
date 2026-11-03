const estado = { tutores: [], tutorId: null, pets: [], hist: new Map(), petId: null };

function ultima(petId) { return (estado.hist.get(petId) || [])[0] || null; }

function textoTutor(pred) {
  return pred.risco
    ? { titulo: "Atenção recomendada", msg: "Vale agendar um retorno com a clínica em breve. Isso não é um diagnóstico: é um aviso para acompanhar de perto." }
    : { titulo: "Tudo em ordem", msg: "Mantenha os check-ups e as vacinas em dia." };
}

async function init() {
  try { estado.tutores = await api("/tutores"); }
  catch (e) { $("#detalhe").innerHTML = `<div class="painel"><div class="erro">${esc(e.message)}</div></div>`; return; }
  const sel = $("#sel-tutor");
  sel.innerHTML = estado.tutores.map((t) => `<option value="${t.id}">${esc(t.nome)}</option>`).join("");
  const lembrado = Number(lembrar("tutorId"));
  estado.tutorId = estado.tutores.some((t) => t.id === lembrado) ? lembrado : (estado.tutores[0] || {}).id;
  sel.value = estado.tutorId;
  sel.addEventListener("change", () => { estado.tutorId = Number(sel.value); guardar("tutorId", sel.value); estado.petId = null; carregarPets(); });
  $("#btn-novo-tutor").addEventListener("click", async () => {
    const t = await abrirDialogoTutor(); if (!t) return;
    estado.tutores.push(t);
    sel.innerHTML = estado.tutores.map((x) => `<option value="${x.id}">${esc(x.nome)}</option>`).join("");
    sel.value = t.id; sel.dispatchEvent(new Event("change")); aviso(`Tutor ${t.nome} cadastrado.`);
  });
  $("#btn-novo-pet").addEventListener("click", async () => {
    if (!estado.tutorId) return aviso("Cadastre um tutor primeiro.");
    const p = await abrirDialogoPet({ tutores: estado.tutores, tutorId: estado.tutorId }); if (!p) return;
    aviso(`${p.nome} cadastrado.`);
    if (p.tutor_id !== estado.tutorId) { sel.value = p.tutor_id; estado.tutorId = p.tutor_id; guardar("tutorId", String(p.tutor_id)); }
    estado.petId = p.id; carregarPets();
  });
  carregarPets();
}

async function carregarPets() {
  const lista = $("#lista-pets");
  if (!estado.tutorId) { lista.innerHTML = ""; $("#detalhe").innerHTML = vazio("Nenhum tutor cadastrado", "Use “Novo tutor” para começar."); return; }
  try {
    estado.pets = await api(`/pets?tutor_id=${estado.tutorId}`);
    const hs = await Promise.all(estado.pets.map((p) => api(`/pets/${p.id}/consultas`)));
    estado.hist = new Map(estado.pets.map((p, i) => [p.id, hs[i].filter((c) => c.predicao)]));  // só consultas já avaliadas pela IA
  } catch (e) { lista.innerHTML = `<li class="erro">${esc(e.message)}</li>`; return; }
  if (!estado.pets.length) {
    lista.innerHTML = `<li class="vazio"><strong>Nenhum pet ainda</strong>Cadastre o primeiro com o botão acima.</li>`;
    $("#detalhe").innerHTML = ""; return;
  }
  if (!estado.pets.some((p) => p.id === estado.petId)) estado.petId = estado.pets[0].id;
  desenharLista(); desenharDetalhe();
}

function desenharLista() {
  $("#lista-pets").innerHTML = estado.pets.map((p) => {
    const u = ultima(p.id);
    const estadoHtml = u
      ? `${termometro(u.predicao.score_pct, u.predicao.risco)}<span>${esc(textoTutor(u.predicao).titulo)}</span>`
      : `<span class="mudo">Sem consultas ainda</span>`;
    return `<li><button class="pet-linha" type="button" data-id="${p.id}" aria-current="${p.id === estado.petId}">
      <span class="pet-linha__nome">${esc(p.nome)}</span><span class="pet-linha__sub">${esc(fichaPet(p))}</span>
      <span class="pet-linha__estado">${estadoHtml}</span></button></li>`;
  }).join("");
  $$(".pet-linha").forEach((b) => b.addEventListener("click", () => { estado.petId = Number(b.dataset.id); desenharLista(); desenharDetalhe(); }));
}

function vazio(titulo, texto) { return `<div class="vazio"><strong>${esc(titulo)}</strong>${esc(texto)}</div>`; }

function graficoEvolucao(consultas) {
  const cron = [...consultas].reverse();
  const W = 640, H = 210, L = 38, R = 34, T = 14, B = 34;
  const x = (i) => (cron.length === 1 ? (L + W - R) / 2 : L + (i * (W - L - R)) / (cron.length - 1));
  const y = (s) => T + (1 - s / 100) * (H - T - B);
  const pts = cron.map((c, i) => `${x(i).toFixed(1)},${y(c.predicao.score_pct).toFixed(1)}`).join(" ");
  const marcas = cron.map((c, i) => `<circle cx="${x(i).toFixed(1)}" cy="${y(c.predicao.score_pct).toFixed(1)}" r="5" fill="${c.predicao.risco ? "#C0342B" : "#3F7D4E"}" stroke="#fff" stroke-width="2"><title>${dataBR(c.data_consulta)}: ${num(c.predicao.score_pct)}%</title></circle>`).join("");
  const rotulos = cron.map((c, i) => (cron.length <= 7 || i === 0 || i === cron.length - 1)
    ? `<text x="${x(i).toFixed(1)}" y="${H - 10}" text-anchor="middle">${dataBR(c.data_consulta).slice(0, 5)}/${dataBR(c.data_consulta).slice(8)}</text>` : "").join("");
  return `<svg class="grafico" viewBox="0 0 ${W} ${H}" role="img" aria-label="Evolução do índice de risco do pet ao longo das consultas">
    <line x1="${L}" x2="${W - R}" y1="${y(0)}" y2="${y(0)}" stroke="#D5DDDB"/><text x="${L - 8}" y="${y(0) + 4}" text-anchor="end">0%</text>
    <line x1="${L}" x2="${W - R}" y1="${y(100)}" y2="${y(100)}" stroke="#D5DDDB"/><text x="${L - 8}" y="${y(100) + 4}" text-anchor="end">100%</text>
    <line x1="${L}" x2="${W - R}" y1="${y(50)}" y2="${y(50)}" stroke="#14222A" stroke-dasharray="5 4"/><text x="${L - 8}" y="${y(50) + 4}" text-anchor="end">50%</text>
    <polyline points="${pts}" fill="none" stroke="#0E4F5C" stroke-width="2.5" stroke-linejoin="round"/>${marcas}${rotulos}</svg>`;
}

async function desenharDetalhe() {
  const pet = estado.pets.find((p) => p.id === estado.petId); if (!pet) return;
  const cons = estado.hist.get(pet.id) || [];
  const u = cons[0];
  let leitura;
  if (u) {
    const t = textoTutor(u.predicao);
    leitura = `<div class="leitura ${u.predicao.risco ? "leitura--alto" : "leitura--baixo"}">
      <div class="leitura__linha"><h3>${esc(t.titulo)}</h3><span class="leitura__numero">${num(u.predicao.score_pct)}%</span><span class="mudo pequeno">índice de atenção em ${dataBR(u.data_consulta)}</span></div>
      ${termometro(u.predicao.score_pct, u.predicao.risco, { grande: true, anima: true })}
      <div class="termo-legenda"><span>0%</span><span>50%: ponto de atenção</span><span>100%</span></div>
      <p>${esc(t.msg)}</p></div>`;
  } else {
    leitura = `<div class="leitura leitura--vazio">${vazio("Ainda não há consultas", "Quando a clínica registrar a primeira consulta, o índice de atenção do " + pet.nome + " aparece aqui.")}</div>`;
  }
  const evolucao = cons.length >= 2
    ? `<div class="secao"><h3>Evolução do índice</h3>${graficoEvolucao(cons)}</div>` : "";
  const historico = cons.length
    ? `<div class="secao"><h3>Histórico de consultas</h3><ul class="historico">${cons.map((c) => `<li>
        <span class="data">${dataBR(c.data_consulta)}</span>
        <span>${esc(c.sintomas || "Sem sintomas registrados")}<small>${esc(c.diagnostico || "Sem diagnóstico registrado")}, ${num(c.peso_kg)} kg</small></span>
        <span>${termometro(c.predicao.score_pct, c.predicao.risco)}<small>${num(c.predicao.score_pct)}%</small></span></li>`).join("")}</ul></div>` : "";
  $("#detalhe").innerHTML = `<div class="painel">
    <div class="pet-cab"><h2>${esc(pet.nome)}</h2><p class="mudo">${esc(fichaPet(pet))}</p>
      <p class="pequeno">${pet.alergia ? "Alergia: " + esc(pet.alergia) + ". " : ""}${pet.doenca_cronica ? "Doença crônica: " + esc(pet.doenca_cronica) + "." : ""}</p></div>
    ${leitura}${evolucao}${historico}
    <div class="secao"><div class="painel__titulo"><h3 style="margin:0">Carteirinha de vacinas</h3>
      <button class="btn btn--claro btn--pequeno" id="btn-vacina" type="button">Registrar vacina</button></div><div id="vacinas"></div></div>
    <p class="aviso secao">O índice vem de um modelo de IA que apoia a decisão da clínica. Ele não substitui o diagnóstico do veterinário.</p></div>`;
  acionarAnimacoes($("#detalhe"));
  $("#btn-vacina").addEventListener("click", async () => {
    const v = await abrirDialogoVacina(pet); if (!v) return;
    pet.total_vacinas += 1; aviso("Vacina registrada."); carregarVacinas(pet);
  });
  carregarVacinas(pet);
}

async function carregarVacinas(pet) {
  const alvo = $("#vacinas");
  try {
    const vs = await api(`/pets/${pet.id}/vacinas`);
    if (pet.id !== estado.petId) return;
    alvo.innerHTML = vs.length ? `<div class="rolagem"><table><thead><tr><th>Vacina</th><th>Aplicada em</th><th>Validade</th><th>Situação</th></tr></thead><tbody>${vs.map((v) => {
      const vencida = v.data_validade && v.data_validade < hojeISO();
      return `<tr><td>${esc(v.nome)}</td><td>${dataBR(v.data_aplicacao)}</td><td>${v.data_validade ? dataBR(v.data_validade) : "Sem validade"}</td>
        <td><span class="etiqueta ${vencida ? "etiqueta--vencida" : "etiqueta--ok"}">${vencida ? "Vencida" : "Em dia"}</span></td></tr>`; }).join("")}</tbody></table></div>`
      : vazio("Nenhuma vacina registrada", "Use “Registrar vacina” para começar a carteirinha.");
  } catch (e) { alvo.innerHTML = `<div class="erro">${esc(e.message)}</div>`; }
}

init();
