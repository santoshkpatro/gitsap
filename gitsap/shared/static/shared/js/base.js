document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".toast").forEach((el) => {
    new bootstrap.Toast(el).show();
  });
});

class SmartMultiSelect {
  constructor(root) {
    this.root = root;
    this.dropdown = document.querySelector(root.dataset.dropdown);
    this.pills = document.querySelector(root.dataset.pills);
    this.select = document.querySelector(root.dataset.select);
    this.selected = new Map();

    this.init();
  }

  init() {
    this.dropdown.addEventListener("click", (e) => {
      const item = e.target.closest("a");
      if (!item) return;
      e.preventDefault();

      const id = item.dataset.id;
      const name = item.dataset.name;

      if (!this.selected.has(id)) {
        this.selected.set(id, name);
        this.addOption(id);
        this.renderPills();
      }
    });

    this.pills.addEventListener("click", (e) => {
      if (e.target.classList.contains("btn-close")) {
        const id = e.target.dataset.id;
        this.selected.delete(id);
        this.removeOption(id);
        this.renderPills();
      }
    });
  }

  addOption(id) {
    const option = document.createElement("option");
    option.value = id;
    option.selected = true;
    option.setAttribute("data-dynamic", "true");
    this.select.appendChild(option);
  }

  removeOption(id) {
    const option = this.select.querySelector(`option[value="${id}"]`);
    if (option) {
      option.remove();
    }
  }

  renderPills() {
    this.pills.innerHTML = "";
    this.selected.forEach((name, id) => {
      const pill = document.createElement("span");
      pill.className =
        "badge bg-light text-dark border rounded-pill d-flex align-items-center me-1";
      pill.innerHTML = `
        <span class="me-1">${name}</span>
        <button type="button" class="btn-close btn-close-sm ms-1" aria-label="Remove" data-id="${id}"></button>
      `;
      this.pills.appendChild(pill);
    });
  }
}

document.querySelectorAll(".smart-multiselect").forEach((el) => {
  new SmartMultiSelect(el);
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
