import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";

export function initMarkdownEditors() {
  document.querySelectorAll(".markdown-editor").forEach((editorEl) => {
    const textarea = editorEl.querySelector(".markdown-input");
    const preview = editorEl.querySelector(".markdown-preview");
    const toggleBtn = editorEl.querySelector(".preview-toggle");
    const toolbarButtons = editorEl.querySelectorAll("[data-md]");
    let previewVisible = false;

    toolbarButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const syntax = btn.getAttribute("data-md");
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = textarea.value.substring(start, end);

        let newText = "";
        if (syntax.includes("\n")) {
          // For block syntaxes (code blocks, blockquotes)
          const cleanText = selectedText || "code";
          newText = syntax.replace("code", cleanText);
        } else if (syntax.trim().endsWith(" ")) {
          // Prefix formats like "- ", "# ", "> "
          newText = syntax + selectedText;
        } else {
          // Inline formats like **bold**, *italic*
          const cleanText = selectedText.trim() || "text";
          newText = `${syntax}${cleanText}${syntax}`;
        }

        textarea.setRangeText(newText, start, end, "end");
        textarea.focus();
      });
    });

    toggleBtn.addEventListener("click", () => {
      previewVisible = !previewVisible;
      if (previewVisible) {
        preview.innerHTML = marked.parse(textarea.value); // ❌ don't trim!
        textarea.style.display = "none";
        preview.style.display = "block";
        toggleBtn.innerHTML = `<i data-lucide="pencil" class="me-1"></i> Edit`;
      } else {
        textarea.style.display = "block";
        preview.style.display = "none";
        toggleBtn.innerHTML = `<i data-lucide="eye" class="me-1"></i> Preview`;
      }
      lucide.createIcons();
    });
  });
}

initMarkdownEditors();
