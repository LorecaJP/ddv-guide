<script lang="ts">
  import type { CategoryMeta } from '../lib/schema'
  import { navigate } from '../lib/router'

  let { meta }: { meta: CategoryMeta | null } = $props()

  const typeLabel: Record<string, string> = {
    'image-grid': '図鑑グリッド（②）で表示予定',
    table: 'ソート・フィルタ可能な一覧表で表示予定',
    links: '参照元へのリンク集で表示予定',
    dashboard: '集計ダッシュボードで表示予定',
  }
</script>

<div class="ph">
  {#if meta}
    <span class="big">{meta.emoji}</span>
    <h1>{meta.name_ja}</h1>
    <p class="type">{typeLabel[meta.display]}</p>
    <p class="note">
      このカテゴリはデータ投入・実装が未完了です（準備中）。<br />
      タスクC でこのカテゴリの JSON を生成 → シードに追加すると、ここに表示されます。
    </p>
  {:else}
    <span class="big">🔍</span>
    <h1>ページが見つかりません</h1>
  {/if}
  <button class="back" onclick={() => navigate(null)}>← トップに戻る</button>
</div>

<style>
  .ph {
    text-align: center;
    max-width: 460px;
    margin: 8vh auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }
  .big { font-size: 56px; }
  h1 { font-size: 28px; }
  .type { color: var(--c-accent-ink); background: var(--c-accent-soft); padding: 4px 12px; border-radius: 999px; font-size: 13px; font-weight: 600; }
  .note { color: var(--c-ink-soft); font-size: 14px; line-height: 1.8; }
  .back {
    margin-top: 8px;
    background: var(--c-surface);
    border: 1px solid var(--c-line);
    color: var(--c-ink);
    padding: 10px 18px;
    border-radius: var(--radius-sm);
    font-weight: 600;
  }
</style>
