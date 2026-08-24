// Front-end: carrega/mostra procedimentos, lida com formulário de contato (chamada ao backend) e chat widget.
// Observação: endpoints (/procedures, /contact, /assistant) são esperados no backend.
// Se ainda não tiver backend, a função loadProcedures usa procedimentos padrão como fallback.

document.addEventListener('DOMContentLoaded', () => {
  const proceduresList = document.getElementById('procedures-list');
  const yearEl = document.getElementById('year');
  const chatToggleBtn = document.getElementById('toggleChat');
  const chatPanel = document.getElementById('chatPanel');
  const openChatBtn = document.getElementById('openChat');
  yearEl && (yearEl.textContent = new Date().getFullYear());

  // Fetch procedures from backend, fallback to static list if fails
  async function loadProcedures(){
    try{
      const res = await fetch('/procedures');
      if(!res.ok) throw new Error('Falha ao buscar procedimentos');
      const data = await res.json();
      renderProcedures(data);
    }catch(e){
      renderProcedures(defaultProcedures());
    }
  }

  function renderProcedures(items){
    proceduresList.innerHTML = '';
    items.forEach((p, idx) => {
      const id = p.id || ('p' + idx);
      const card = document.createElement('article');
      card.className = 'proc-card';
      card.innerHTML = `
        <h4>${escapeHtml(p.name)}</h4>
        <p>${escapeHtml(p.summary)}</p>
        <div class="more" data-id="${id}" role="button" tabindex="0">Saiba mais</div>
        <div class="full" id="full-${id}" style="display:none;margin-top:0.5rem;color:#555">${escapeHtml(p.details)}</div>
      `;
      proceduresList.appendChild(card);
    });
  }

  // Toggle "Saiba mais"
  proceduresList.addEventListener('click', e => {
    if(e.target.matches('.more')){
      toggleFull(e.target.dataset.id);
    }
  });
  proceduresList.addEventListener('keydown', e => {
    if(e.key === 'Enter' && e.target.matches('.more')) toggleFull(e.target.dataset.id);
  });

  function toggleFull(id){
    const el = document.getElementById('full-' + id);
    if(!el) return;
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
  }

  // Contact form handling
  const contactForm = document.getElementById('contact-form');
  if(contactForm){
    contactForm.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const btn = contactForm.querySelector('button[type="submit"]');
      btn.disabled = true;
      const payload = {
        name: contactForm.name.value,
        email: contactForm.email.value,
        message: contactForm.message.value
      };
      try{
        const res = await fetch('/contact', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify(payload)
        });
        if(!res.ok) throw new Error('Erro envio');
        document.getElementById('contact-result').textContent = 'Mensagem enviada com sucesso!';
        contactForm.reset();
      }catch(err){
        document.getElementById('contact-result').textContent = 'Erro ao enviar. Tente novamente.';
      } finally { btn.disabled = false; }
    });

    const clearBtn = document.getElementById('clearContact');
    clearBtn && clearBtn.addEventListener('click', () => contactForm.reset());
  }

  // Chat widget logic
  const chatForm = document.getElementById('chatForm');
  const chatMessages = document.getElementById('chatMessages');
  const chatInput = document.getElementById('chatInput');

  function appendMessage(text, who='bot'){
    const div = document.createElement('div');
    div.className = 'msg ' + (who === 'user' ? 'user' : 'bot');
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
  }

  // Open/close chat
  chatToggleBtn && chatToggleBtn.addEventListener('click', () => {
    if(chatPanel) {
      chatPanel.hidden = !chatPanel.hidden;
      if(!chatPanel.hidden) chatInput && chatInput.focus();
    }
  });
  openChatBtn && openChatBtn.addEventListener('click', () => {
    if(chatPanel){
      chatPanel.hidden = false;
      chatInput && chatInput.focus();
    }
  });
  const closeChatBtn = document.getElementById('closeChat');
  closeChatBtn && closeChatBtn.addEventListener('click', () => chatPanel.hidden = true);

  if(chatForm){
    chatForm.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const msg = chatInput.value.trim();
      if(!msg) return;
      appendMessage(msg, 'user');
      chatInput.value = '';

      // temporary loading message
      const temp = appendMessage('...', 'bot');

      try{
        const res = await fetch('/assistant', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({message: msg})
        });
        const json = await res.json();
        temp.remove();
        const reply = json.reply || 'Desculpe, não entendi. Pode reformular?';
        appendMessage(reply, 'bot');
      }catch(err){
        temp.remove();
        appendMessage('Erro ao acessar o assistente. Tente novamente mais tarde.', 'bot');
      }
    });
  }

  // Helpers
  function escapeHtml(text){
    if(text === undefined || text === null) return '';
    return String(text).replace(/[&<>"']/g, function(m){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]; });
  }

  function defaultProcedures(){
    return [
      {id: 'p1', name: 'Preenchimento facial', summary: 'Correção de volumes e harmonização facial.', details: 'Utilizamos ácido hialurônico para repor volumes com segurança. Sessões de avaliação e resultados temporários.'},
      {id: 'p2', name: 'Toxina botulínica (Botox)', summary: 'Redução de linhas de expressão.', details: 'Toxina botulínica para suavizar rugas dinâmicas. Procedimento rápido, com efeito em dias.'},
      {id: 'p3', name: 'Peeling químico', summary: 'Renovação da pele.', details: 'Peelings para clareamento, textura e rejuvenescimento. Vários níveis: superficial, médio.'},
      {id: 'p4', name: 'Microagulhamento', summary: 'Estimula produção de colágeno.', details: 'Técnica que melhora textura e cicatrizes, com sessões espaçadas conforme avaliação.'}
    ];
  }

  // Inicializa
  loadProcedures();
});
