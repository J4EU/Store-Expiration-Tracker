<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";

import {
  archiveProduct,
  createDiscard,
  createProduct,
  fetchArchivedProducts,
  fetchDashboard,
  lookupProduct,
  restoreProduct,
  updateExpiration,
  updateProduct,
} from "./api";

const DEFAULT_CATEGORY = "미선택";
const DAIRY_CATEGORY = "유제품";
const CATEGORY_OPTIONS = [
  { value: DEFAULT_CATEGORY, label: "미선택" },
  { value: DAIRY_CATEGORY, label: "유제품" },
];

function formatLocalDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function classifyDueItem(item, referenceDate) {
  if (!item.expiration_date) {
    return "unchecked";
  }

  const tomorrow = new Date(`${referenceDate}T00:00:00`);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowString = formatLocalDate(tomorrow);

  if (item.expiration_date < referenceDate) {
    return "past";
  }

  if (item.expiration_date === referenceDate) {
    return "today";
  }

  if (item.expiration_date === tomorrowString) {
    return "tomorrow";
  }

  return "future";
}

function normalizeCategory(category) {
  return category === DAIRY_CATEGORY ? DAIRY_CATEGORY : DEFAULT_CATEGORY;
}

function isTodayProcessingItem(item, referenceDate) {
  const type = classifyDueItem(item, referenceDate);

  if (type === "past" || type === "today") {
    return true;
  }

  return type === "tomorrow" && normalizeCategory(item.category) === DAIRY_CATEGORY;
}

function statusLabel(type) {
  if (type === "past") {
    return "지난 상품";
  }

  if (type === "today") {
    return "오늘 만료";
  }

  if (type === "tomorrow") {
    return "내일 상품";
  }

  if (type === "future") {
    return "이후 상품";
  }

  return "미확인";
}

const referenceDate = ref(formatLocalDate(new Date()));
const currentView = ref("dashboard");
const dueFilter = ref("today_processing");
const dashboardLoading = ref(false);
const archiveLoading = ref(false);
const savingModal = ref(false);
const archiveSearch = ref("");
const errorMessage = ref("");
const editTargetId = ref(null);
const editField = ref("");
const moreMenuTargetId = ref(null);

const dashboard = reactive({
  dueItems: [],
  uncheckedItems: [],
});

const archivedItems = ref([]);
const productDrafts = reactive({});
const expirationDrafts = reactive({});
const discardDrafts = reactive({});
const uncheckedDrafts = reactive({});
const archiveSearchDraft = ref("");
const barcodeInputRef = ref(null);

const modal = reactive({
  open: false,
  barcode: "",
  expirationDate: "",
  category: DEFAULT_CATEGORY,
  name: "",
  lookupResult: null,
  step: "barcode",
  error: "",
});

const dueTabs = [
  { id: "today_processing", label: "오늘 처리" },
  { id: "all", label: "전체" },
];

const dueCounts = computed(() => {
  const counts = {
    today_processing: 0,
    all: dashboard.dueItems.length,
  };

  for (const item of dashboard.dueItems) {
    if (isTodayProcessingItem(item, referenceDate.value)) {
      counts.today_processing += 1;
    }
  }

  return counts;
});

const filteredDueItems = computed(() => {
  if (dueFilter.value === "today_processing") {
    return dashboard.dueItems.filter((item) =>
      isTodayProcessingItem(item, referenceDate.value),
    );
  }

  if (dueFilter.value === "all") {
    return dashboard.dueItems;
  }

  return dashboard.dueItems;
});

const focusHeadline = computed(() => {
  if (dueCounts.value.today_processing === 0) {
    return "오늘 처리할 소비기한 항목이 없습니다.";
  }

  const pastCount = dashboard.dueItems.filter(
    (item) => classifyDueItem(item, referenceDate.value) === "past",
  ).length;
  if (pastCount > 0) {
    return `지난 상품 ${pastCount}개를 먼저 처리해야 합니다.`;
  }

  const todayCount = dashboard.dueItems.filter(
    (item) => classifyDueItem(item, referenceDate.value) === "today",
  ).length;
  if (todayCount > 0) {
    return `오늘 만료 상품 ${todayCount}개가 바로 처리 대상입니다.`;
  }

  const dairyTomorrowCount = dashboard.dueItems.filter(
    (item) =>
      classifyDueItem(item, referenceDate.value) === "tomorrow" &&
      normalizeCategory(item.category) === DAIRY_CATEGORY,
  ).length;
  if (dairyTomorrowCount > 0) {
    return `유제품 내일 상품 ${dairyTomorrowCount}개를 오늘 함께 처리합니다.`;
  }

  return `오늘 처리 대상 ${dueCounts.value.today_processing}개가 준비되어 있습니다.`;
});

function resetModal() {
  modal.open = false;
  modal.barcode = "";
  modal.expirationDate = "";
  modal.category = DEFAULT_CATEGORY;
  modal.name = "";
  modal.lookupResult = null;
  modal.step = "barcode";
  modal.error = "";
}

function openModal() {
  modal.open = true;
  modal.step = "barcode";
  modal.error = "";
  nextTick(() => {
    barcodeInputRef.value?.focus();
  });
}

function openDatePicker(event) {
  const shell = event.currentTarget?.closest(".date-input-shell");
  const input = shell?.querySelector('input[type="date"]');

  if (!input) {
    return;
  }

  input.focus();
  input.showPicker?.();
}

function nextDayOffset(days) {
  const base = new Date(`${referenceDate.value}T00:00:00`);
  base.setDate(base.getDate() + days);
  referenceDate.value = formatLocalDate(base);
  loadDashboard();
}

function useToday() {
  referenceDate.value = formatLocalDate(new Date());
  loadDashboard();
}

async function loadDashboard() {
  dashboardLoading.value = true;
  errorMessage.value = "";

  try {
    const data = await fetchDashboard(referenceDate.value);
    dashboard.dueItems = data.due_items;
    dashboard.uncheckedItems = data.unchecked_items;
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    dashboardLoading.value = false;
  }
}

async function loadArchivedProducts() {
  archiveLoading.value = true;
  errorMessage.value = "";

  try {
    const data = await fetchArchivedProducts(archiveSearch.value);
    archivedItems.value = data.items;
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    archiveLoading.value = false;
  }
}

async function handleBarcodeLookup() {
  modal.error = "";

  try {
    const data = await lookupProduct(modal.barcode);
    modal.lookupResult = data.product;
    modal.step = data.found ? "existing" : "new";
    if (data.found) {
      modal.category = normalizeCategory(data.product.category);
    }
  } catch (error) {
    modal.error = error.message;
  }
}

async function submitModal() {
  savingModal.value = true;
  modal.error = "";

  try {
    if (modal.step === "existing" && modal.lookupResult) {
      await updateExpiration(modal.lookupResult.id, {
        expiration_date: modal.expirationDate || null,
      });
    }

    if (modal.step === "new") {
      await createProduct({
        barcode: modal.barcode,
        name: modal.name,
        category: modal.category,
        expiration_date: modal.expirationDate || null,
      });
    }

    resetModal();
    await loadDashboard();
  } catch (error) {
    modal.error = error.message;
  } finally {
    savingModal.value = false;
  }
}

function ensureProductDraft(item) {
  if (!productDrafts[item.id]) {
    productDrafts[item.id] = {
      name: item.name,
      barcode: item.barcode,
      category: normalizeCategory(item.category),
    };
  }

  return productDrafts[item.id];
}

function toggleMoreMenu(itemId) {
  moreMenuTargetId.value = moreMenuTargetId.value === itemId ? null : itemId;
}

function openProductEdit(item, field) {
  const draft = ensureProductDraft(item);

  draft.name = item.name;
  draft.barcode = item.barcode;
  draft.category = normalizeCategory(item.category);
  expirationDrafts[item.id] = item.expiration_date ?? "";
  editTargetId.value = item.id;
  editField.value = field;
  moreMenuTargetId.value = null;
}

function closeProductEdit() {
  editTargetId.value = null;
  editField.value = "";
}

function editFieldLabel(field) {
  if (field === "expiration") {
    return "소비기한 수정";
  }

  if (field === "barcode") {
    return "바코드 수정";
  }

  if (field === "category") {
    return "카테고리 수정";
  }

  return "상품명 수정";
}

async function submitProductEdit(item) {
  if (editField.value === "expiration") {
    await updateExpiration(item.id, {
      expiration_date: expirationDrafts[item.id] || null,
    });
  } else {
    const draft = ensureProductDraft(item);
    const payload = {};

    if (editField.value === "name") {
      payload.name = draft.name;
    }

    if (editField.value === "barcode") {
      payload.barcode = draft.barcode;
    }

    if (editField.value === "category") {
      payload.category = draft.category;
    }

    await updateProduct(item.id, payload);
  }

  closeProductEdit();
  await loadDashboard();
}

async function clearCategoryEdit(item) {
  ensureProductDraft(item).category = DEFAULT_CATEGORY;
  await updateProduct(item.id, { category: DEFAULT_CATEGORY });
  closeProductEdit();
  await loadDashboard();
}

async function submitDiscard(item) {
  const draft = discardDrafts[item.id] ?? { quantity: 1 };

  await createDiscard({
    product_id: item.id,
    quantity: Number(draft.quantity),
  });
  await loadDashboard();
}

async function submitUncheckedExpiration(item) {
  const draft = uncheckedDrafts[item.id] ?? { expiration_date: "" };
  await updateExpiration(item.id, {
    expiration_date: draft.expiration_date || null,
  });
  await loadDashboard();
}

async function submitArchive(item) {
  await archiveProduct(item.id);
  await loadDashboard();
  if (currentView.value === "archive") {
    await loadArchivedProducts();
  }
}

async function submitRestore(item) {
  await restoreProduct(item.id);
  await loadArchivedProducts();
  if (currentView.value === "dashboard") {
    await loadDashboard();
  }
}

function ensureDiscardDraft(itemId) {
  if (!discardDrafts[itemId]) {
    discardDrafts[itemId] = { quantity: 1 };
  }

  return discardDrafts[itemId];
}

function ensureUncheckedDraft(itemId) {
  if (!uncheckedDrafts[itemId]) {
    uncheckedDrafts[itemId] = { expiration_date: "" };
  }

  return uncheckedDrafts[itemId];
}

onMounted(() => {
  loadDashboard();
});
</script>

<template>
  <div class="app-shell">
    <div class="app-frame">
      <aside class="workspace-sidebar">
        <div class="sidebar-top">
          <div class="brand-block">
            <p class="eyebrow">Store Expiry Manager</p>
            <h1>소비기한 운영</h1>
            <p class="hero-copy">
              전체 흐름을 한쪽 사이드에서 고정하고, 작업은 오른쪽에서
              처리합니다.
            </p>
          </div>

          <section class="sidebar-register">
            <p class="section-label">빠른 등록</p>
            <h2>바코드로 바로 시작</h2>
            <p>
              기존 상품 확인 후 소비기한만 반영하거나, 없을 때만 신규
              등록합니다.
            </p>
            <button class="primary-button large full-button" @click="openModal">
              등록 시작
            </button>
          </section>

          <section class="sidebar-metrics">
            <div class="metric-box">
              <span>오늘 처리</span>
              <strong>{{ dueCounts.today_processing }}</strong>
            </div>
            <div class="metric-box soft">
              <span>미확인</span>
              <strong>{{ dashboard.uncheckedItems.length }}</strong>
            </div>
          </section>
        </div>

        <section v-if="currentView === 'dashboard'" class="sidebar-panel">
          <div class="side-header">
            <div class="side-header-copy">
              <p class="section-label">미확인</p>
              <h2>다음 소비기한 확인 필요</h2>
            </div>
            <button class="ghost-button small" @click="loadDashboard">
              새로고침
            </button>
          </div>

          <div
            v-if="dashboard.uncheckedItems.length === 0"
            class="empty-state side"
          >
            미확인 상품이 없습니다.
          </div>

          <div v-else class="sidebar-list">
            <article
              v-for="item in dashboard.uncheckedItems"
              :key="item.id"
              class="side-card"
            >
              <div class="side-card-head">
                <div>
                  <p class="mono">{{ item.barcode }}</p>
                  <strong>{{ item.name }}</strong>
                </div>
                <span class="mini-chip">미확인</span>
              </div>

              <p class="meta-line">
                카테고리 {{ normalizeCategory(item.category) }}
              </p>

              <form
                class="side-form"
                @submit.prevent="submitUncheckedExpiration(item)"
              >
                <div class="date-input-shell side-date-shell">
                  <input
                    v-model="ensureUncheckedDraft(item.id).expiration_date"
                    type="date"
                  />
                  <button
                    class="date-shell-icon"
                    type="button"
                    aria-label="소비기한 캘린더 열기"
                    @click="openDatePicker"
                  ></button>
                </div>
                <div class="inline-row">
                  <button class="primary-button small" type="submit">
                    등록
                  </button>
                  <button
                    class="warn-button small"
                    type="button"
                    @click="submitArchive(item)"
                  >
                    아카이브
                  </button>
                </div>
              </form>
            </article>
          </div>
        </section>

        <section v-else class="sidebar-panel archive-side-panel">
          <p class="section-label">Archive</p>
          <h2>보관된 상품 조회</h2>
          <p class="meta-line">
            바코드, 상품명, 카테고리로 검색하고 바로 복구할 수 있습니다.
          </p>
        </section>
      </aside>

      <section class="workspace-main">
        <header class="main-nav-bar">
          <div class="main-nav-copy">
            <p class="section-label">
              {{ currentView === "dashboard" ? "Dashboard" : "Archive" }}
            </p>
            <h2>
              {{
                currentView === "dashboard"
                  ? "지금 처리해야 하는 상품"
                  : "보관된 상품 조회"
              }}
            </h2>
          </div>

          <nav class="main-nav-actions">
            <button
              :class="['nav-button', { active: currentView === 'dashboard' }]"
              @click="currentView = 'dashboard'"
            >
              운영 화면
            </button>
            <button
              :class="['nav-button', { active: currentView === 'archive' }]"
              @click="
                currentView = 'archive';
                loadArchivedProducts();
              "
            >
              아카이브 조회
            </button>
          </nav>
        </header>

        <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

        <main v-if="currentView === 'dashboard'" class="dashboard-layout">
          <section class="main-panel">
            <div class="main-summary">
              <div>
                <p class="section-label">
                  {{ dueFilter === "today_processing" ? "오늘 처리" : "전체" }}
                </p>
                <h2>{{ focusHeadline }}</h2>
              </div>

              <div class="date-console">
                <span class="date-console-label">기준일</span>

                <div class="date-input-shell summary-date-shell">
                  <input
                    v-model="referenceDate"
                    class="text-date-input"
                    type="date"
                  />
                  <button
                    class="date-shell-icon"
                    type="button"
                    aria-label="기준일 캘린더 열기"
                    @click="openDatePicker"
                  ></button>
                </div>

                <div class="date-tools compact">
                  <button class="ghost-button small" @click="nextDayOffset(-1)">
                    이전
                  </button>
                  <button class="ghost-button" @click="loadDashboard">
                    조회
                  </button>
                  <button class="ghost-button small" @click="useToday">
                    오늘
                  </button>
                  <button class="ghost-button small" @click="nextDayOffset(1)">
                    다음
                  </button>
                </div>
              </div>
            </div>

            <div class="filter-strip">
              <button
                v-for="tab in dueTabs"
                :key="tab.id"
                :class="['tab-button', { active: dueFilter === tab.id }]"
                @click="dueFilter = tab.id"
              >
                <span>{{ tab.label }}</span>
                <strong>{{ dueCounts[tab.id] }}</strong>
              </button>
            </div>

            <div v-if="dashboardLoading" class="empty-state">
              불러오는 중...
            </div>

            <div v-else-if="filteredDueItems.length === 0" class="empty-state">
              현재 필터에 해당하는 처리 대상이 없습니다.
            </div>

            <div v-else class="queue-list">
              <article
                v-for="item in filteredDueItems"
                :key="item.id"
                class="queue-card"
              >
                <form
                  class="action-rack compact-rack"
                  @submit.prevent="submitDiscard(item)"
                >
                  <span
                    :class="[
                      'priority-chip',
                      classifyDueItem(item, referenceDate),
                    ]"
                  >
                    {{ statusLabel(classifyDueItem(item, referenceDate)) }}
                  </span>
                  <strong class="compact-name">{{ item.name }}</strong>
                  <span class="mono compact-barcode">{{ item.barcode }}</span>
                  <span class="mono compact-expiry"
                    >소비 {{ item.expiration_date }}</span
                  >
                  <span class="compact-category"
                    >카테고리 {{ normalizeCategory(item.category) }}</span
                  >
                  <input
                    v-model="ensureDiscardDraft(item.id).quantity"
                    class="compact-quantity"
                    type="number"
                    min="1"
                  />
                  <button
                    class="primary-button rack-button compact-submit"
                    type="submit"
                  >
                    폐기 완료
                  </button>
                </form>

                <div class="secondary-actions">
                  <button
                    class="warn-button small"
                    type="button"
                    @click="submitArchive(item)"
                  >
                    아카이브
                  </button>
                  <div class="more-actions">
                    <button
                      class="ghost-button small"
                      type="button"
                      @click="toggleMoreMenu(item.id)"
                    >
                      더 보기
                    </button>

                    <div
                      v-if="moreMenuTargetId === item.id"
                      class="more-actions-menu"
                    >
                      <button
                        class="ghost-button small"
                        type="button"
                        @click="openProductEdit(item, 'expiration')"
                      >
                        소비기한 수정
                      </button>
                      <button
                        class="ghost-button small"
                        type="button"
                        @click="openProductEdit(item, 'name')"
                      >
                        상품명 수정
                      </button>
                      <button
                        class="ghost-button small"
                        type="button"
                        @click="openProductEdit(item, 'barcode')"
                      >
                        바코드 수정
                      </button>
                      <button
                        class="ghost-button small"
                        type="button"
                        @click="openProductEdit(item, 'category')"
                      >
                        카테고리 수정
                      </button>
                    </div>
                  </div>
                </div>

                <form
                  v-if="editTargetId === item.id"
                  class="rename-tray"
                  @submit.prevent="submitProductEdit(item)"
                >
                  <span class="tray-label">{{
                    editFieldLabel(editField)
                  }}</span>
                  <div
                    v-if="editField === 'expiration'"
                    class="date-input-shell tray-date-shell"
                  >
                    <input
                      v-model="expirationDrafts[item.id]"
                      type="date"
                    />
                    <button
                      class="date-shell-icon"
                      type="button"
                      aria-label="소비기한 수정 캘린더 열기"
                      @click="openDatePicker"
                    ></button>
                  </div>
                  <input
                    v-else-if="editField === 'name'"
                    v-model="ensureProductDraft(item).name"
                    type="text"
                  />
                  <input
                    v-else-if="editField === 'barcode'"
                    v-model="ensureProductDraft(item).barcode"
                    type="text"
                    inputmode="numeric"
                  />
                  <select
                    v-if="editField === 'category'"
                    v-model="ensureProductDraft(item).category"
                  >
                    <option
                      v-for="option in CATEGORY_OPTIONS"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                  <button class="ghost-button small" type="submit">저장</button>
                  <button
                    v-if="editField === 'expiration'"
                    class="ghost-button small subtle"
                    type="button"
                    @click="
                      expirationDrafts[item.id] = '';
                      submitProductEdit(item);
                    "
                  >
                    비우기
                  </button>
                  <button
                    v-if="editField === 'category'"
                    class="ghost-button small subtle"
                    type="button"
                    @click="clearCategoryEdit(item)"
                  >
                    미선택
                  </button>
                  <button
                    class="ghost-button small subtle"
                    type="button"
                    @click="closeProductEdit"
                  >
                    닫기
                  </button>
                </form>
              </article>
            </div>
          </section>
        </main>

        <main v-else class="archive-layout">
          <section class="main-panel full">
            <div class="archive-header">
              <div>
                <p class="section-label">아카이브 조회</p>
                <h2>보관된 상품을 검색하고 바로 복구</h2>
              </div>

              <form
                class="search-row"
                @submit.prevent="
                  archiveSearch = archiveSearchDraft;
                  loadArchivedProducts();
                "
              >
                <input
                  v-model="archiveSearchDraft"
                  type="text"
                  placeholder="바코드, 상품명, 카테고리 검색"
                />
                <button class="ghost-button" type="submit">검색</button>
              </form>
            </div>

            <div v-if="archiveLoading" class="empty-state">불러오는 중...</div>
            <div v-else-if="archivedItems.length === 0" class="empty-state">
              아카이브 상품이 없습니다.
            </div>

            <div v-else class="archive-list">
              <article
                v-for="item in archivedItems"
                :key="item.id"
                class="archive-card"
              >
                <div>
                  <p class="mono">{{ item.barcode }}</p>
                  <h3>{{ item.name }}</h3>
                  <p class="meta-line">
                    카테고리 {{ normalizeCategory(item.category) }}
                  </p>
                </div>
                <button
                  class="primary-button small"
                  @click="submitRestore(item)"
                >
                  복구
                </button>
              </article>
            </div>
          </section>
        </main>
      </section>
    </div>

    <div v-if="modal.open" class="modal-backdrop" @click.self="resetModal">
      <section class="modal-card">
        <div class="modal-top">
          <div>
            <p class="section-label">등록 팝업</p>
            <h2>바코드 먼저 확인</h2>
          </div>
          <button class="ghost-button small" @click="resetModal">닫기</button>
        </div>

        <div class="modal-progress">
          <span :class="['progress-pill', { active: modal.step === 'barcode' }]"
            >1. 바코드 조회</span
          >
          <span
            :class="[
              'progress-pill',
              { active: modal.step === 'existing' || modal.step === 'new' },
            ]"
          >
            2. 등록 반영
          </span>
        </div>

        <div class="modal-stack">
          <label>
            바코드
            <input
              ref="barcodeInputRef"
              v-model="modal.barcode"
              type="text"
              inputmode="numeric"
              placeholder="바코드 입력"
            />
          </label>

          <div v-if="modal.step === 'barcode'" class="inline-row">
            <button
              class="primary-button"
              :disabled="savingModal"
              @click="handleBarcodeLookup"
            >
              조회
            </button>
          </div>

          <template v-if="modal.step === 'existing' && modal.lookupResult">
            <div class="lookup-box success">
              <p class="lookup-title">기존 상품 발견</p>
              <h3>{{ modal.lookupResult.name }}</h3>
              <p class="meta-line">
                {{ modal.lookupResult.barcode }} / 현재 소비기한
                {{ modal.lookupResult.expiration_date || "미확인" }}
              </p>
            </div>

            <label>
              새 소비기한
              <input v-model="modal.expirationDate" type="date" />
            </label>
          </template>

          <template v-if="modal.step === 'new'">
            <div class="lookup-box warning">
              <p class="lookup-title">새 상품 등록</p>
              <p>
                이 바코드는 아직 등록되어 있지 않습니다. 필요한 정보만 짧게
                입력하면 됩니다.
              </p>
            </div>

            <div class="modal-form-grid">
              <label>
                상품명
                <input
                  v-model="modal.name"
                  type="text"
                  placeholder="신규 상품명 입력"
                />
              </label>

              <label>
                카테고리
                <select
                  v-model="modal.category"
                >
                  <option
                    v-for="option in CATEGORY_OPTIONS"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
              </label>
            </div>

            <label>
              소비기한
              <input v-model="modal.expirationDate" type="date" />
            </label>
          </template>

          <p v-if="modal.error" class="error-text">{{ modal.error }}</p>

          <div v-if="modal.step !== 'barcode'" class="inline-row">
            <button
              class="primary-button"
              :disabled="savingModal"
              @click="submitModal"
            >
              {{ modal.step === "existing" ? "소비기한 반영" : "신규 등록" }}
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
