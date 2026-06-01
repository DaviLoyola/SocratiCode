const chatContainer = document.getElementById("chat-container");
const analyzeButton = document.getElementById("analyze-btn");
const clearCodeButton = document.getElementById("clear-code");
const newConversationButton = document.getElementById("new-conversation");
const questionTextarea = document.getElementById("question");
const questionCount = document.getElementById("question-count");
const languageHint = document.getElementById("language-hint");
const leftPanel = document.querySelector(".left-panel");

const loadingStates = [
  "🔍 Analisando seu código...",
  "🧠 Identificando padrões de raciocínio...",
  "✍️  Formulando orientações...",
];

const editor = CodeMirror(document.getElementById("code-editor"), {
  value: "",
  mode: "text/plain",
  theme: "neo",
  lineNumbers: true,
  styleActiveLine: true,
  viewportMargin: Infinity,
  placeholder: "Cole aqui o seu código...",
});

function detectLanguage(code) {
  const text = code.toLowerCase();

  if (/def\s+\w+\(|print\(|import\s+\w+/.test(text)) {
    return { label: "Python", mode: "python" };
  }
  if (/function\s+\w+\(|console\.log\(|=>/.test(text)) {
    return { label: "JavaScript", mode: "javascript" };
  }
  if (/#include\s*<|int\s+main\s*\(/.test(text)) {
    return { label: "C", mode: "text/x-csrc" };
  }
  if (/public\s+class\s+\w+|system\.out\.println/.test(text)) {
    return { label: "Java", mode: "text/x-java" };
  }
  return { label: "texto", mode: "text/plain" };
}

function autoResizeQuestion() {
  questionTextarea.style.height = "auto";
  questionTextarea.style.height = `${Math.min(questionTextarea.scrollHeight, 220)}px`;
}

function updateQuestionCount() {
  const length = questionTextarea.value.length;
  questionCount.textContent = `${length}/500`;
}

function addMessage(role, content, code = null) {
  const message = document.createElement("div");
  message.className = `message ${role}`;

  let messageHtml = "";
  if (code) {
    messageHtml += `<p><strong>Código:</strong></p><pre><code>${escapeHtml(code)}</code></pre>`;
  }

  if (role === "assistant") {
    const rendered = marked.parse(content || "");
    messageHtml += DOMPurify.sanitize(rendered);
  } else {
    messageHtml += `<p>${escapeHtml(content || "")}</p>`;
  }

  message.innerHTML = messageHtml;
  chatContainer.appendChild(message);
  scrollChatToBottom();
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function scrollChatToBottom() {
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function createLoadingBubble() {
  const wrapper = document.createElement("div");
  wrapper.className = "loading";
  wrapper.innerHTML = `
    <div class="typing-dots"><span></span><span></span><span></span></div>
    <span id="loading-text">${loadingStates[0]}</span>
  `;
  chatContainer.appendChild(wrapper);
  scrollChatToBottom();
  return wrapper;
}

function cycleLoadingStates(wrapper) {
  const textNode = wrapper.querySelector("#loading-text");
  const timeouts = [2000, 4000];

  const handles = timeouts.map((delay, index) =>
    setTimeout(() => {
      if (textNode) {
        textNode.textContent = loadingStates[index + 1];
      }
    }, delay)
  );

  return () => handles.forEach((handle) => clearTimeout(handle));
}

async function fetchHistory() {
  const response = await fetch("/api/history");
  const data = await response.json();

  chatContainer.innerHTML = "";
  (data.messages || []).forEach((message) => {
    addMessage(message.role, message.content, message.role === "user" ? message.code : null);
  });
}

async function sendToTutor() {
  const code = editor.getValue().trim();
  const question = questionTextarea.value.trim();

  if (!code && !question) {
    alert("Preencha o código ou a dúvida antes de enviar.");
    return;
  }

  const language = detectLanguage(code);
  editor.setOption("mode", language.mode);
  languageHint.textContent = `Linguagem detectada: ${language.label}`;

  analyzeButton.disabled = true;
  analyzeButton.textContent = "Analisando...";

  addMessage("user", question, code);
  const loadingBubble = createLoadingBubble();
  const stopCycle = cycleLoadingStates(loadingBubble);

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, question }),
    });

    const payload = await response.json();
    loadingBubble.remove();
    stopCycle();

    if (!response.ok) {
      addMessage("assistant", payload.error || "Não foi possível processar sua solicitação.");
      return;
    }

    addMessage("assistant", payload.reply || "Não houve resposta do tutor.");
    if (window.innerWidth <= 980) {
      leftPanel.classList.add("mobile-collapsed");
      document.querySelector(".right-panel").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } catch (error) {
    loadingBubble.remove();
    stopCycle();
    addMessage("assistant", "O tutor está temporariamente indisponível. Tente novamente em instantes.");
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.textContent = "Enviar para o Tutor";
  }
}

async function resetConversation() {
  const confirmed = window.confirm("Tem certeza? Seu progresso será perdido.");
  if (!confirmed) {
    return;
  }

  await fetch("/api/new-conversation", { method: "POST" });
  chatContainer.innerHTML = "";
}

clearCodeButton.addEventListener("click", () => {
  leftPanel.classList.remove("mobile-collapsed");
  editor.setValue("");
  editor.setOption("mode", "text/plain");
  languageHint.textContent = "Linguagem detectada: texto";
});

analyzeButton.addEventListener("click", sendToTutor);
newConversationButton.addEventListener("click", resetConversation);

questionTextarea.addEventListener("focus", () => {
  leftPanel.classList.remove("mobile-collapsed");
});

questionTextarea.addEventListener("input", () => {
  autoResizeQuestion();
  updateQuestionCount();
});

window.addEventListener("load", async () => {
  autoResizeQuestion();
  updateQuestionCount();
  await fetchHistory();
});
