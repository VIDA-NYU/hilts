<script lang="ts">
  import type { Hit } from "./Api";
  import {
    descriptionsStore,
    animalStore,
    negativeKeywordStore,
    selectedDataStore,
  } from "./stores";
  import AutoComplete from "simple-svelte-autocomplete";
  import * as api from "./Api";
  import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

  export let allHits: Hit[];

  let allDescriptions: string[];
  let allAnimals: string[];
  let allNegKeywords: string[];

  let selectedDescription: string;
  let selectedAnimal: string;
  let selectedNegKeyword: string;

  let allSelectedData: { [key: string]: boolean };

  let labels = {};

  descriptionsStore.subscribe((storeLabels) => {
    allDescriptions = storeLabels;
  });

  animalStore.subscribe((storeAnimals) => {
    allAnimals = storeAnimals;
  });

  negativeKeywordStore.subscribe((storeNegKeyword) => {
    allNegKeywords = storeNegKeyword;
  });

  selectedDataStore.subscribe((storeSelectedData) => {
    allSelectedData = storeSelectedData;
  });

  function addLabelExclusive(newLabel: string, type: api.LabelType) {
    if (!newLabel || newLabel === "") {
      return;
    }
    console.log(labels);

    if (
      labels &&
      Object.keys(labels).length !== 0
    ) {
      const labelKey = Object.keys(labels).find((key) => labels[key] === type);
      if (labelKey && labelKey !== newLabel) {
        delete labels[labelKey];
      }
    }
    labels[newLabel] = `${type}`;

    const selectedHits = allHits.filter(hit => allSelectedData[hit.image_path] === true);

    // Send label for all hits marked
    for (let hit of selectedHits) {
      let hitLabels = hit.labels_types_dict;
      let hitKey = Object.keys(hitLabels).find((key) => hitLabels[key] === type);
      if (hitKey) {
        if (hitKey === newLabel) {
          // label already applied, skip to next
          continue;
        } else {
          api.removeLabel(hit.image_path, hitKey, `${type}`);
          delete hit.labels_types_dict[hitKey];
        }
      }
      hit.labels_types_dict[newLabel] = type;
      sendToBackend(hit.image_path, newLabel, type);
    }
    dispatch('changeLabels', {
		});
    console.log(labels)
  }

  function addLabelInclusive(newLabel: string, type: api.LabelType) {
    console.log("addLabelInclusive", newLabel, type);
    if (!newLabel || newLabel === "") {
      return;
    }
    labels[newLabel] = `${type}`;

    // add label for each hit on page
    const selectedHits = allHits.filter(hit => allSelectedData[hit.image_path] === true);
    for (let hit of selectedHits) {
      let hitLabels = hit.labels_types_dict;
      hitLabels[newLabel] = `${type}`;
      hit.labels_types_dict = hitLabels;
      sendToBackend(hit.image_path, newLabel, type);
    }
    dispatch('changeLabels', {
		});
  }

  function sendToBackend(image_path: string, label: string, type: api.LabelType) {
    console.log('Send to backend: ', image_path, label, type);
    try {
      api.addLabel(image_path, label, type); // FIXME
    } catch (e) {
      console.log(e);
    }
  }

  function onChangeDescription(newLabel: string) {
    addLabelInclusive(newLabel, "description");
  }

  function onChangeKeyword(newKeyword: string) {
    addLabelInclusive(newKeyword, "keywords");
  }

  function handleCreateDescription(newLabel: string) {
    descriptionsStore.update((storeLabels) => {
      return [...new Set([...storeLabels, newLabel])];
    });
    return newLabel; // return the new label to the autocomplete
  }

  function handleCreateKeyword(newKeyword: string) {
    negativeKeywordStore.update((storeNegKeyword) => {
      return [...new Set([...storeNegKeyword, newKeyword])];
    });
    return newKeyword;
  }

  function onChangeAnimal(newAnimal: string) {
    console.log("change", labels, newAnimal);
    if (newAnimal) {
      console.log("onChangeAnimal", newAnimal);
      addLabelExclusive(newAnimal, "animal");
    } else {
      console.log("undefined label: ", newAnimal);
    }
  }

  function removeLabels(label: string) {
    delete labels[label];
    labels = labels; // required to update component

    const selectedHits = allHits.filter(hit => allSelectedData[hit.image_path] === true);
    for (let hit of selectedHits) {
      if (allSelectedData[hit.image_path] === true) {

        const hitLabels = hit.labels_types_dict;
        if (hitLabels && hitLabels[label]) {
          api.removeLabel(hit.image_path, label, hitLabels[label]);
          delete hitLabels[label];
        }
      }
    }

    dispatch('changeLabels', {
		});
  }

</script>

<div class="card me-3 mb-3">
  <div class="card-header">Label All Ads</div>
  <div class="box-container">
    <div class="card-body">
      <div class="btn-toolbar mt-1">
        <div class="btn-group me-2" role="group" aria-label="">
          <button
            class="btn btn-sm btn-success"
            on:click={() => addLabelExclusive("animal origin", "relevant")}
          >
            <i class="fa fa-thumbs-up" aria-hidden="true" />
          </button>
          <button
            class="btn btn-sm btn-warning"
            on:click={() => addLabelExclusive("not animal origin", "relevant")}
          >
            <i class="fa fa-thumbs-down" aria-hidden="true" />
          </button>
        </div>
        <div class="btn-group me-2 mt-1" role="group" aria-label="">
          <AutoComplete
            debug={false}
            inputClassName="form-control"
            items={allAnimals}
            bind:selectedItem={selectedAnimal}
            create={false}
            onChange={onChangeAnimal}
            placeholder="Animal"
          />
        </div>
        <div class="box-container">
          <div class="btn-group me-2" role="group" aria-label="">
            <AutoComplete
              debug={false}
              inputClassName="form-control"
              items={allDescriptions}
              bind:selectedItem={selectedDescription}
              create={true}
              onCreate={handleCreateDescription}
              onChange={onChangeDescription}
              placeholder="Description"
            />
          </div>
        </div>
        <div class="box-container">
          <div class="btn-group me-2" role="group" aria-label="">
            <AutoComplete
              debug={false}
              inputClassName="form-control"
              items={allNegKeywords}
              bind:selectedItem={selectedNegKeyword}
              create={true}
              onChange={onChangeKeyword}
              onCreate={handleCreateKeyword}
              placeholder="Negative Keyword"
            />
          </div>
        </div>
      </div>
      {#if labels && Object.keys(labels).length > 0}
        <div class="btn-toolbar">
          {#each Object.entries(labels) as [label, value], idx}
            <span
              class="badge rounded-pill bg-secondary me-1 mt-2 position-relative"
            >
              <!-- style="background-color: {colors[idx]} !important;" -->
              {label}
              <span
                role="button"
                on:click={() => removeLabels(label)}
                class="position-absolute top-0 start-100 translate-middle"
              >
                <i class="fa fa-times-circle" aria-hidden="true" />
                <span class="visually-hidden">Remove label</span>
              </span>
            </span>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  :global(.autocomplete-list) {
    --bs-dropdown-zindex: 1000;
    --bs-dropdown-min-width: 10rem;
    --bs-dropdown-padding-x: 0;
    --bs-dropdown-padding-y: 0.1rem;
    --bs-dropdown-spacer: 0.125rem;
    --bs-dropdown-font-size: 1rem;
    --bs-dropdown-color: var(--bs-body-color);
    --bs-dropdown-bg: var(--bs-body-bg);
    --bs-dropdown-border-color: var(--bs-border-color-translucent);
    --bs-dropdown-border-radius: var(--bs-border-radius);
    --bs-dropdown-border-width: var(--bs-border-width);
    --bs-dropdown-inner-border-radius: calc(
      var(--bs-border-radius) - var(--bs-border-width)
    );
    --bs-dropdown-divider-bg: var(--bs-border-color-translucent);
    --bs-dropdown-divider-margin-y: 0.1rem;
    --bs-dropdown-box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    --bs-dropdown-link-color: var(--bs-body-color);
    --bs-dropdown-link-hover-color: var(--bs-body-color);
    --bs-dropdown-link-hover-bg: var(--bs-tertiary-bg);
    --bs-dropdown-link-active-color: #fff;
    --bs-dropdown-link-active-bg: #7c6bb2;
    --bs-dropdown-link-disabled-color: var(--bs-tertiary-color);
    --bs-dropdown-item-padding-x: 1rem;
    --bs-dropdown-item-padding-y: 0.25rem;
    --bs-dropdown-header-color: #6c757d;
    --bs-dropdown-header-padding-x: 1rem;
    --bs-dropdown-header-padding-y: 0.1rem;

    color: var(--bs-dropdown-color) !important;
    text-align: left !important;
    list-style: none !important;
    background-color: var(--bs-dropdown-bg) !important;
    background-clip: padding-box !important;
    border: var(--bs-dropdown-border-width) solid
      var(--bs-dropdown-border-color) !important;
    border-radius: var(--bs-dropdown-border-radius) !important;
    width: 171px !important;
  }
  :global(.autocomplete-list-item) {
    color: var(--bs-dropdown-color) !important;
  }
  :global(
      .autocomplete-list .selected,
      .dropdown-item:hover,
      .dropdown-item:focus
    ) {
    color: var(--bs-dropdown-link-hover-color) !important;
    background-color: var(--bs-dropdown-link-hover-bg) !important;
  }
  :global(.input-container > .form-control) {
    padding: 0.25rem 0.5rem !important;
    font-size: 0.875rem !important;
    border-radius: var(--bs-border-radius-sm);
  }
  :global(.autocomplete) {
    height: 2em !important;
    min-width: 100px !important;
  }
  :global(.autocomplete-list-item-create) {
    width: 169px !important;
  }
  :global(.input-container) {
    /* width: 207px !important; */
    width: 171px !important;
  }
  h1 {
    font-size: 1rem;
    text-align: center;
  }
</style>
