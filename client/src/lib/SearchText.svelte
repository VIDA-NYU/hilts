<script lang="ts">
    import SearchForm from "./SearchForm.svelte";
    import type { Hits, Hit } from "./Api";
    import { TextSearch } from "./Api";
    import ImageCard from "./ImageCard.svelte";
    import LabelAll from "./LabelAll.svelte";
    import {selectedDataStore } from "./stores";

    let limit: string = "64";
    let excludeLabeled: boolean = false;
    let queryStr = "";
    let result: Promise<Hits> | null = null;
    let allSelectedData: {[key: string]: boolean; };

    selectedDataStore.subscribe((storeSelectedData) => {
      allSelectedData = storeSelectedData;
    });

    function onQuerySubmit() {
      result = TextSearch(queryStr, +limit, excludeLabeled);
      result.then( (hits: Hits) => {
        if (result) {
          const imagePaths = hits.hits.map((item) => ({[item.image_path]: true}));
          selectedDataStore.update((storeSelectedData) => {
            return { ...Object.assign({}, ...imagePaths) };
          });
        }
      });
    }

    function clearSearch() {
      queryStr = "";
      result = null;
    }

    function onLabelAllEvent() {
      console.log("onChangeLabels");
      result = result;
    }

  </script>

  <div class="container">
    <div class="py-4">
      <div class="row">
        <SearchForm
          bind:value={queryStr}
          on:submit={onQuerySubmit}
          autofocus={true}
          class="form-control"
          hideLabel={true}
          label="Image search:"
          placeholder="Search..."
        />
      </div>

      <div class="row mt-2 mb-2 gx-2 align-items-center">
        <div class="col-auto">
          <label class="col-form-label" for="limitSelect">
            Number of results:
          </label>
        </div>
        <div class="col-auto me-3">
          <select
            class="form-select form-select-sm"
            id="limitSelect"
            bind:value={limit}
            on:change={onQuerySubmit}
          >
            <option value="4">4</option>
            <option value="8">8</option>
            <option value="16">16</option>
            <option value="32">32</option>
            <option value="64">64</option>
          </select>
        </div>
        <div class="col-auto form-check">
          <input
            class="form-check-input"
            type="checkbox"
            id="excludeLabeledCheck"
            bind:checked={excludeLabeled}
            on:change={onQuerySubmit}
          />
          <label class="form-check-label" for="excludeLabeledCheck">
            Exclude labeled
          </label>
        </div>
        {#await result}
          <div class="col-auto">
            <span>
              <i class="fa fa-spinner fa-spin" aria-hidden="true" />
              Loading...
            </span>
          </div>
        {:then result}
          <div class="col-auto">
            {#if queryStr}
              <button
                class="btn btn-secondary btn-sm me-1"
                on:click={clearSearch}
              >
                <span class="fa fa-close" aria-label="Close" /> Clear
              </button>
            {/if}
          </div>
          {#if result}
            <div class="col-auto">
              <span class="form-text">
                Showing {result.hits.length} results for query "{queryStr}".
              </span>
            </div>
          {/if}
        {/await}
      </div>

      {#await result}
        <!-- Awaiting state is already handled above -->
      {:then result}
        {#if result}
          <div class="d-flex flex-wrap mt-2 mb-2">
            {#each result.hits as hit}
              <div class="w-25">
                <ImageCard {hit} />
              </div>
            {/each}
            <div class="w-25">
              <LabelAll allHits={result.hits} on:changeLabels={onLabelAllEvent} />
            </div>
          </div>
        {/if}
      {:catch error}
        <div role="alert" class="alert alert-danger mt-2 mb-2">
          <strong>Error:</strong>
          {error.message}
        </div>
      {/await}
    </div>
  </div>
