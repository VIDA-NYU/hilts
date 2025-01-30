<script>
  export let showModal; // boolean
  export let closeBtnName = "Close";
  export let onCloseAction;

  let dialog; // HTMLDialogElement

  function handleClose() {
    // Trigger any custom close action
    if (onCloseAction) {
      onCloseAction();
      dialog.close()
    }

    // Close the dialog
    dialog.close()
  }

  $: if (dialog && showModal) dialog.showModal();
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions -->
<dialog
  bind:this={dialog}
  on:close={() => (showModal = false)}
  on:click|self={() => dialog.close()}
>
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div on:click|stopPropagation class="card">
    <div class="card-header">
      <slot name="header" />
    </div>
    <div class="card-body">
      <slot name="body" />
    </div>
    <!-- svelte-ignore a11y-autofocus -->
    <button class="btn btn-primary" on:click={handleClose}>
      {#if closeBtnName !== 'Close'}
        {closeBtnName}  <!-- Custom Close Button Text -->
      {:else}
        Close <!-- Default Close Text -->
      {/if}
    </button>
    </div>
</dialog>

<style>
  dialog {
    max-width: 40em;
    border-radius: 0.2em;
    border: none;
    padding: 0;
  }
  dialog::backdrop {
    background: rgba(0, 0, 0, 0.3);
  }
  dialog > div {
    /* padding: 1em; */
  }
  dialog[open] {
    animation: zoom 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  @keyframes zoom {
    from {
      transform: scale(0.95);
    }
    to {
      transform: scale(1);
    }
  }
  dialog[open]::backdrop {
    animation: fade 0.2s ease-out;
  }
  @keyframes fade {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  button {
    display: block;
  }
</style>
