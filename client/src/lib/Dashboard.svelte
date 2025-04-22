<script lang="ts">
  import * as api from "./Api";
  import type { Hit } from "./Api";
  import { onMount } from "svelte";
  import { createChart } from "./cards/heatMap";
  import ImageCard from "./ImageCard.svelte";
  import embed from "vega-embed";
  import { navigate } from "svelte-routing"; // Import navigate for navigation


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
  let productsCount = 25; //$products || 5;
  let speciesCount = 25; //$species|| 5;
  let projectMessage="";

  let minValue = 0;
  let maxValue = 1000000;

  onMount(() => {
    // Initial chart creation when the component mounts
    // if (Object.keys(graphData).length !== 0 && productsCount && speciesCount) {
    if (Object.keys(graphData).length !== 0) {
      const {
        chartData,
        productsCount,
        speciesCount,
      } = graphData;
      createChart(chartData, productsCount, speciesCount, HandleClick);
    }
  });

  projectName.subscribe((name) => {
    projectId = name;
  });

  function HandleClick(matchingImages, matchingData) {
    // Process images (if needed)
    imagePaths = [];
    matchingImages.slice(0, 4).forEach((item) => {
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
    }

    // Count sellers in the matching data
    const sellers = {};
    matchingData.forEach((item) => {
      if (item.seller) {
        sellers[item.seller] = (sellers[item.seller] || 0) + 1;
      }
    });

    // Convert sellers object to an array and sort by count
    const sortedSellers = Object.entries(sellers)
      .map(([seller, count]) => ({ seller, count }))
      .sort((a, b) => b.count - a.count);

    // Call createBarChart with the updated seller data
    createBarChart("barchart", sortedSellers);
  }

  async function getData() {
    const response = await api.getData(projectId);
    chartData = response;

    try {
      projectMessage = await api.connectLabelsDb(projectId);
    } catch (error) {
      projectMessage = `Error setting labels db: ${error.message}`;
    }

    createChart(chartData, productsCount, speciesCount, HandleClick);
    dataGraph.set({
      chartData,
      productsCount,
      speciesCount,
    });
    // products.set(productsCount);
    // species.set(speciesCount);
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

  export function createBarChart(container, sortedSellers) {
    // Remove the existing chart if it exists
    const barChartContainer = document.getElementById(container);
    barChartContainer.innerHTML = "";

    // Sort sellers by count in descending order
    sortedSellers = sortedSellers.sort((a, b) => b.count - a.count);

    // Limit to the top 10 sellers
    sortedSellers = sortedSellers.slice(0, 10);

    // Define the Vega-Lite specification
    const spec = {
      $schema: "https://vega.github.io/schema/vega-lite/v5.json",
      description: "Bar Chart of Sellers",
      width: 250, // Chart width
      height: 150, // Chart height
      data: {
        values: sortedSellers,
      },
      mark: {
        type: "bar",
        tooltip: true,
      },
      encoding: {
        x: {
          field: "seller",
          type: "ordinal",
          sort: "-y", // Explicitly sort by the y-axis (count) in descending order
          axis: {
            title: "Sellers",
            titleFontSize: 16,
            labelFontSize: 12,
            labelAngle: -45, // Rotate labels for better readability
          },
        },
        y: {
          field: "count",
          type: "quantitative",
          axis: {
            title: "Count",
            titleFontSize: 16,
            labelFontSize: 12,
          },
        },
        color: {
          field: "count", // Use count to determine the color intensity
          type: "quantitative",
          scale: { scheme: "purples" }, // Use the "purples" color scheme
          legend: {
            title: "Count",
            titleFontSize: 16,
            labelFontSize: 12,
          },
        },
      },
      // title: {
      //   text: "Sellers of Selected Product and Animal",
      //   fontSize: 18,
      //   fontWeight: "bold",
      //   anchor: "middle",
      // },
    };

    // Embed the Vega-Lite chart
    embed(barChartContainer, spec, { actions: false }).then((result) => {
      // Add click event listener
      result.view.addEventListener("click", (event, item) => {
        if (item && item.datum) {
          console.log("Clicked bar:", item.datum);
          navigate(`/search/seller?q=${encodeURIComponent(item.datum.seller)}`);
          // Add custom click handling logic here
        }
      });
    });
  }
</script>

<div class="container-fluid m-3">
  <!-- First Column (smaller) -->
  <div class="col-2">
    <div class="card">
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

      <!-- <div class="card-body">
        <b>Select Price Range</b> -->
        <!-- Min Value Slider -->
        <!-- <label for="min-range" class="block mb-2">Set Minimum Value</label> -->
        <!-- <input
          id="min-range"
          type="range"
          min="0"
          max="1000000"
          step="1"
          bind:value={minValue}
          class="form-range block border border-gray-300 rounded-md"
        />
        <div class="mt-2 text-sm text-gray-600">Min: {minValue}</div> -->

        <!-- Max Value Slider -->
        <!-- <label for="max-range" class="block">Set Maximum Value</label> -->
        <!-- <input
          id="max-range"
          type="range"
          min="0"
          max="1000000"
          step="1"
          bind:value={maxValue}
          class="form-range block border border-gray-300 rounded-md"
        /> -->
        <!-- <div class="mt-2 text-sm text-gray-600">Max: {maxValue}</div>
      </div> -->

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
  <div class="col-10">
    <div class="row">
      <div class="col-6">
        <!-- <div class="card m-2"> -->
        <div id="heatmap" class="__svg-container"></div>
      <!-- </div> -->
    </div>
      <div class="col-6">
        <!-- <div class="card m-2"> -->
        <!-- <h3>Visualization Area 2</h3> -->
        <div id="barchart" class="__svg-container"></div>
      <!-- </div> -->
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
