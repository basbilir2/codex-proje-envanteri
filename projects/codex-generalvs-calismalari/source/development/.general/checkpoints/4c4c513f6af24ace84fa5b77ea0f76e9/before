(function (root) {
  'use strict';

  const STORAGE_KEY = 'generalvs-habits-v1';

  function normalizeText(value) {
    return String(value || '').trim().replace(/\s+/g, ' ');
  }

  function addHabit(habits, text, id) {
    const name = normalizeText(text);
    if (!name) throw new Error('Alışkanlık adı boş olamaz.');
    return [...habits, { id: String(id), name, done: false }];
  }

  function toggleHabit(habits, id) {
    return habits.map((habit) => habit.id === String(id) ? { ...habit, done: !habit.done } : habit);
  }

  function deleteHabit(habits, id) {
    return habits.filter((habit) => habit.id !== String(id));
  }

  function counts(habits) {
    const completed = habits.filter((habit) => habit.done).length;
    return { total: habits.length, completed, remaining: habits.length - completed };
  }

  function serializeHabits(habits) {
    return JSON.stringify(habits);
  }

  function parseHabits(raw) {
    try {
      const value = JSON.parse(raw || '[]');
      if (!Array.isArray(value)) return [];
      return value.filter((item) => item && typeof item.id === 'string' && typeof item.name === 'string' && typeof item.done === 'boolean');
    } catch (_) {
      return [];
    }
  }

  function saveHabits(storage, habits) {
    storage.setItem(STORAGE_KEY, serializeHabits(habits));
  }

  function loadHabits(storage) {
    return parseHabits(storage.getItem(STORAGE_KEY));
  }

  const api = { STORAGE_KEY, normalizeText, addHabit, toggleHabit, deleteHabit, counts, serializeHabits, parseHabits, saveHabits, loadHabits };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;

  if (!root || !root.document) return;
  const document = root.document;
  const form = document.querySelector('#habit-form');
  const input = document.querySelector('#habit-input');
  const list = document.querySelector('#habit-list');
  const summary = document.querySelector('#summary');
  const empty = document.querySelector('#empty');
  let habits = loadHabits(root.localStorage);

  function nextId() {
    return root.crypto && root.crypto.randomUUID ? root.crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function render() {
    const state = counts(habits);
    summary.textContent = `${state.total} alışkanlık · ${state.completed} tamamlandı · ${state.remaining} kaldı`;
    empty.hidden = state.total > 0;
    list.replaceChildren();
    habits.forEach((habit) => {
      const item = document.createElement('li');
      item.className = `habit${habit.done ? ' done' : ''}`;
      const name = document.createElement('span');
      name.className = 'habit-name';
      name.textContent = habit.name;
      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'toggle';
      toggle.dataset.action = 'toggle';
      toggle.dataset.id = habit.id;
      toggle.textContent = habit.done ? 'Geri al' : 'Tamamla';
      toggle.setAttribute('aria-label', `${habit.name}: ${toggle.textContent}`);
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'delete';
      remove.dataset.action = 'delete';
      remove.dataset.id = habit.id;
      remove.textContent = 'Sil';
      remove.setAttribute('aria-label', `${habit.name} alışkanlığını sil`);
      item.append(name, toggle, remove);
      list.append(item);
    });
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    try {
      habits = addHabit(habits, input.value, nextId());
      saveHabits(root.localStorage, habits);
      input.value = '';
      input.focus();
      render();
    } catch (_) {
      input.focus();
    }
  });

  list.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    habits = button.dataset.action === 'toggle' ? toggleHabit(habits, button.dataset.id) : deleteHabit(habits, button.dataset.id);
    saveHabits(root.localStorage, habits);
    render();
  });

  render();
}(typeof window !== 'undefined' ? window : null));
