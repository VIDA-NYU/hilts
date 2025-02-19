<script lang="ts">
  import * as api from "./Api";
  import type { Hit } from "./Api";
  import { onMount, afterUpdate } from "svelte";
  import { createChart, updateChartSize } from "./cards/heatMap";
  import { createchartSeller } from "./cards/barChart";
  import ImageCard from "./ImageCard.svelte";

  // import { createVisualization } from './cards/imagesChart'

  import { projectName, dataGraph, products, species } from "./stores";

  let chartData = [];
  let projectId = "";
  let animals = [];
  let sellers = {};
  let sortedSellers = [];
  let imagePaths = [];
  let hits: Hit[];
  let graphData = $dataGraph; // Reactive store value
  let productsCount = 5; //$products || 5;
  let speciesCount = 5; //$species|| 5;

  let minValue = 0;
  let maxValue = 1000000;

  onMount(() => {
    // Initial chart creation when the component mounts
    if (graphData && productsCount && speciesCount) {
      createChart(graphData, productsCount, speciesCount, HandleClick);
    }
  });

  projectName.subscribe((name) => {
    projectId = name;
  });

  function HandleClick(data, matchingData) {
    imagePaths = [];
    data.slice(0, 4).forEach((item) => {
      imagePaths.push(item.split("/").pop());
    });

    if (imagePaths.length > 0) {
      hits = imagePaths.map((image_path) => ({
        _distance: 0,
        image_path: image_path,
        title: "",
        metadata: "",
        labels_types_dict: {},
      }));

      countSellers(matchingData);
      createchartSeller(sortedSellers);
    }
  }

  async function getData() {
    const response = await api.getData(projectId);
    chartData = response;

    createChart(chartData, productsCount, speciesCount, HandleClick);
    dataGraph.set(chartData);
    products.set(productsCount);
    species.set(speciesCount);
  }

  function countSellers(data) {
    console.log(data);
    data.forEach((item) => {
      if (item.seller) {
        sellers[item.seller] = (sellers[item.seller] || 0) + 1;
      }
    });
    sortedSellers = Object.entries(sellers)
      .sort((a, b) => b[1] - a[1]) // Sort by count (second value of each entry)
      .map((entry) => ({ seller: entry[0], count: entry[1] }));
  }
</script>

<div class="container-fluid">
  <!-- First Column (smaller) -->
  <div class="col-2">
    <div class="card m-2">
      <div class="card-header bg-primary text-white">Filters</div>
      <div class="card-body">
        <div class="w-full xl:w-4/12 mt-6">
          <label for="projectIdInput"><b>Project Name</b></label>
          <input
            id="projectIdInput"
            bind:value={projectId}
            type="text"
            class="form-control"
            style="max-width:400px"
            placeholder="Enter your project name"
          />
        </div>
      </div>
      <div class="card-body">
        <label for="select1"><b>Select number of species</b></label>
        <select
          id="speciesCount"
          class="form-select block p-2 border border-gray-300 rounded-md"
          bind:value={speciesCount}
        >
          <option value="5">5</option>
          <option value="10">10</option>
          <option value="15">15</option>
          <option value="20">20</option>
          <option value="25">25</option>
        </select>
      </div>

      <div class="card-body">
        <label for="select2"><b>Select number of product types</b></label>
        <select
          id="select2"
          class="form-select block p-2 border border-gray-300 rounded-md"
          bind:value={productsCount}
        >
          <option value="5">5</option>
          <option value="10">10</option>
          <option value="15">15</option>
          <option value="20">20</option>
          <option value="25">25</option>
        </select>
      </div>

      <div class="card-body">
        <b>Select Price Range</b>
        <!-- Min Value Slider -->
        <!-- <label for="min-range" class="block mb-2">Set Minimum Value</label> -->
        <input
          id="min-range"
          type="range"
          min="0"
          max="1000000"
          step="1"
          bind:value={minValue}
          class="form-range block border border-gray-300 rounded-md"
        />
        <div class="mt-2 text-sm text-gray-600">Min: {minValue}</div>

        <!-- Max Value Slider -->
        <!-- <label for="max-range" class="block">Set Maximum Value</label> -->
        <input
          id="max-range"
          type="range"
          min="0"
          max="1000000"
          step="1"
          bind:value={maxValue}
          class="form-range block border border-gray-300 rounded-md"
        />
        <div class="mt-2 text-sm text-gray-600">Max: {maxValue}</div>
      </div>

      <div class="card-body">
        <button on:click={getData} class="btn btn-info mb-2 mt-2">
          Start Visualization
        </button>
      </div>
    </div>
  </div>

  <!-- Second Column (grey background for visualizations) -->
  <!-- <div class ="container" > -->

  <!-- <div style="width: 100%; height: 100%; background-color: red; display: flex; flex-direction: column;">
        <div style=" flex: 3; background-color: blue;"></div>
        <div style="flex: 1; background-color: green;"></div>

        <h1>test</h1>
      </div> -->
  <div class="col-8">
    <div class="row">
      <div class="col-5">
        <div class="card m-2">
        <div id="heatmap" class="svg-container"></div>
      </div>

    </div>
      <div class="col-5">
        <div class="card m-2">
        <!-- <h3>Visualization Area 2</h3> -->
        <div id="barchart" class="svg-container"></div>
      </div>
    </div>
    </div>
    <div class="row">
      {#if hits && hits.length > 0}
        <div class="d-flex flex-wrap mt-2 mb-2">
          {#each hits as hit}
            <div class="w-25">
              <ImageCard {hit} />
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .container-fluid {
    display: flex;
    gap: 10px;
    width: 100%;
  }
  :host {
    display: flex;
    width: 100%;
    height: 100%;
  }
  select {
    width: 100%;
    padding: 10px;
    font-size: 14px;
  }

  .svg-container {
    display: inline-block;
    position: relative;
    width: 100%;
    /* height: 100%; */
    padding-bottom: 100%;
    vertical-align: top;
    overflow: hidden;
  }
  .svg-content-responsive {
    display: inline-block;
    position: absolute;
    top: 10px;
    left: 0;
  }
  .form-range {
    width: 100%;
    height: 10px;
    background: #ddd;
    border-radius: 5px;
  }
</style>
