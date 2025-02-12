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
  import { projectName } from "./stores";
  import { createChart } from "./cards/chart";
  import { createImageVisualization } from "./cards/imagesChart";
  import ImageCard from "./ImageCard.svelte";

  // import { createVisualization } from './cards/imagesChart'

  let chartData = [];
  let projectId = "default";
  let productsCount = 20;
  let speciesCount = 20;
  let animals = [];
  let sellers = {};
  let sortedSellers = [];
  let imagePaths = [];
  let hits: Hit[]



  projectName.subscribe((name) => {
    projectId = name;
  });

  function HandleClick(data) {
    imagePaths = [];
    data.slice(0, 4).forEach((item) => {
      imagePaths.push(item.split("/").pop());
    });
    // createImageVisualization(imagePaths);
    // Now `imagePaths` contains the last part of the path for each image
    console.log(imagePaths); // You can log it to check the result

    hits = imagePaths.map((image_path) => ({
      _distance: 0,  // You can modify this based on your requirement
      image_path: image_path,
      title: "",  // You can set a title if needed, or leave it empty
      metadata: "",  // Set metadata as an empty string
      labels_types_dict: {}  // Empty dictionary for labels (modify if needed)
    }));
  }

  async function getData() {
    const response = await api.getData(projectId);
    // console.log("response:")
    // console.log(response)
    chartData = response;
    countSellers(chartData);
    createChart(chartData, productsCount, speciesCount, HandleClick);
  }

  function countSellers(data) {
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
      <div class="col-8">
        <svg id="svg"></svg>
      </div>
      <div>
      </div>
      <!-- <div class="col-4">
        <div id="image-grid"></div>
      </div> -->
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

<style>
  .form-select.seller-dropdown {
    /* max-height: 15px; Adjust the height to control how many items can fit before scrolling */
    overflow-y: auto; /* Enable vertical scrolling */
  }
  .container-fluid {
    padding: 20px;
    max-height: 100vh; /* Ensure the content doesn't overflow the viewport */
    overflow-y: auto; /* Allow vertical scrolling for the content */
  }
</style>
