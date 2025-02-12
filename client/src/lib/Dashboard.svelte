<script lang="ts">
  import * as api from "./Api";
  import type { Hit } from "./Api";

  // import LineChart from "./cards/LineChart.svelte";
  // import BarChart from "./cards/BarChart.svelte";
  // import CardPageVisits from "cards/CardPageVisits.svelte";
  // import CardSocialTraffic from ".cards/CardSocialTraffic.svelte";
  // export let location;
  import * as d3 from "d3";
  import { onMount } from "svelte";
  import { createChart } from "./cards/chart";
  import { createchartSeller } from "./cards/chartseller";
  import ImageCard from "./ImageCard.svelte";

  // import { createVisualization } from './cards/imagesChart'


  import { projectName, dataGraph, products, species } from "./stores";



  let chartData = [];
  let projectId = "default";
  let animals = [];
  let sellers = {};
  let sortedSellers = [];
  let imagePaths = [];
  let hits: Hit[]
  let graphData = $dataGraph;  // Reactive store value
  let productsCount = $products || 5;
  let speciesCount = $species|| 5;

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

    if (imagePaths.length > 0 ) {
      hits = imagePaths.map((image_path) => ({
      _distance: 0,
      image_path: image_path,
      title: "",
      metadata: "",
      labels_types_dict: {}
    }))

    countSellers(matchingData)
    createchartSeller(sortedSellers)
    };

  }


  async function getData() {
    const response = await api.getData(projectId);
    // console.log("response:")
    // console.log(response)
    chartData = response;
    // countSellers(chartData);
    createChart(chartData, productsCount, speciesCount, HandleClick);
    dataGraph.set(chartData);
    products.set(productsCount);
    species.set(speciesCount);
  }

  function countSellers(data) {
    console.log(data)
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

<div>
  <div class="container-fluid px-5">
    <div class="row">
      <div class="col-4">
        <svg id="svg"></svg>
      </div>
      <div class="col-4">
        <svg id="chart2"></svg>
      </div>
      <div>
      </div>
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
    <!-- Dropdown and Button to choose the number of animals -->
      <div class="col-4">
    <div class="w-full xl:w-4/12 mt-6">
      <label for="projectIdInput">Project Name</label>
      <input
        id="projectIdInput"
        bind:value={projectId}
        type="text"
        class="form-control"
        style="max-width:400px"
        placeholder="Enter your project name"
      />

      <label
        for="speciesCount"
        class="block text-gray-700 text-sm font-bold mb-2"
      >
        Select number of species to display:
      </label>
      <!-- Dropdown to select the number of animals -->
      <select
        id="speciesCount"
        class="form-select block w-25 p-2 border border-gray-300 rounded-md"
        bind:value={speciesCount}
      >
        <option value="5">5</option>
        <option value="10">10</option>
        <option value="15">15</option>
        <option value="20">20</option>
        <option value="25">25</option>
      </select>

      <label
        for="productsCount"
        class="block text-gray-700 text-sm font-bold mb-2"
      >
        Select number of product types to display:
      </label>
      <!-- Dropdown to select the number of animals -->
      <select
        id="productsCount"
        class="form-select block w-25 p-2 border border-gray-300 rounded-md"
        bind:value={productsCount}
      >
        <option value="5">5</option>
        <option value="10">10</option>
        <option value="15">15</option>
        <option value="20">20</option>
        <option value="25">25</option>
      </select>

      <!-- Button to trigger getData function -->
      <button on:click={getData} class="btn btn-info mb-2 mt-2">
        Start Visualization
      </button>
      <!-- dropdown select seller to display products -->
      <!-- <label for="seller" class="form-select block w-25 p-2 border border-gray-300 rounded-md">
        Select a Seller:
      </label> -->
      <!-- <select id="seller" class="form-select seller-dropdown block w-25 p-2 border border-gray-300 rounded-md" bind:value={sellerSelected}>
        <option value="">Select a seller</option>
        {#each sortedSellers as { seller, count }}
          <option value={seller}>
            {seller} ({count})
          </option>
        {/each}
      </select> -->
    </div>
    </div>
  </div>
</div>

