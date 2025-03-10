<script lang="ts">
  import * as api from "./Api"; // Assuming the API logic is in this file
  import { onMount, onDestroy} from "svelte";
  import { io } from "socket.io-client";
  import * as d3 from "d3";
  import { projectName } from "./stores"
  import { navigate } from "svelte-routing";
  // import { socket, initializeSocket } from './stores';
  // import { get } from 'svelte/store';


  let responseMessage;
  let chartData = {
    precision: [],
    recall: [],
    f1_score: [],
    accuracy: [],
  };
  let projectId = ""

  projectName.subscribe((name) => {
    projectId = name;
  });

  // let socketURL;

  // if (window.location.port === "80") {
  //     socketURL = `${window.location.hostname}`;  // e.g., ws://localhost:5000$ {window.location.port}
  // } else {
  //     socketURL = `${window.location.hostname}:${window.location.port}`;  // e.g., wss://myapp.example.com
  // }

  // if (window.location.protocol === 'https:'){
  //   socketURL = `wss://${socketURL}`;
  // } else {
  //   socketURL = `ws://${socketURL}`;
  // }

  // console.log("socketURL: ", socketURL)

  // const socket = io(socketURL, { autoConnect: true }) //, transports: ['websocket', 'polling']});

  let svg;
  const width = 600;
  const height = 400;
  const margin = { top: 20, right: 100, bottom: 40, left: 100 };

  // Initialize training state
  let isTrainingComplete = false;
  let steps_training = [];

  const updateChartData = (msg) => {
  if (msg && msg.precision && msg.recall && msg.f1_score && msg.accuracy) {
    msg.precision.forEach(value => chartData.precision.push(value));
    msg.recall.forEach(value => chartData.recall.push(value));
    msg.f1_score.forEach(value => chartData.f1_score.push(value));
    msg.accuracy.forEach(value => chartData.accuracy.push(value));
    }
  }

  const createChart = () => {
    const x0 = d3
      .scaleBand()
      .domain(steps_training)
      .rangeRound([margin.left, width - margin.right])
      .padding(0.1);

    const x1 = d3
      .scaleBand()
      .domain(["precision", "recall", "f1_score", "accuracy"]) // Bar groups for each metric
      .rangeRound([0, x0.bandwidth()])
      .padding(0.05);

    const y = d3
      .scaleLinear()
      .domain([0, 1]) // Scores between 0 and 1
      .nice()
      .range([height - margin.bottom, margin.top]);

    const color = d3
      .scaleOrdinal()
      .domain(["precision", "recall", "f1_score", "accuracy"])
      .range(["#66c2a5", "#fc8d62", "#8da0cb", "#b3b3b3"]); // Different colors for each metric

    const svgElement = d3
      .select("#chart")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])
      .attr("style", "max-width: 100%; height: auto;");

    svgElement.selectAll("*").remove(); // Clear previous chart

    // Create groups for each step on the x-axis
    const g = svgElement
      .append("g")
      .selectAll("g")
      .data(steps_training)
      .enter()
      .append("g")
      .attr("transform", (d) => `translate(${x0(d)},0)`);

    // X-axis (Step axis)
    svgElement
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x0))
      .selectAll("text")
      .style("font-size", "12px")
      .style("text-anchor", "middle");

    // Y-axis (Score values)
    svgElement
      .append("g")
      .attr("transform", `translate(${margin.left}, 0)`)
      .call(d3.axisLeft(y))
      .style("font-size", "12px");

    // Draw bars for all metrics (precision, recall, f1_score, accuracy)
    g.selectAll("rect")
      .data((d) =>
        ["precision", "recall", "f1_score", "accuracy"].map((key) => ({
          key,
          value: chartData[key][steps_training.indexOf(d)], // Use the corresponding value for each metric
        }))
      )
      .enter()
      .append("rect")
      .attr("x", (d) => x1(d.key)) // Position bars by metric (precision, recall, f1_score, accuracy)
      .attr("y", (d) => y(d.value))
      .attr("width", x1.bandwidth()) // Set the width of the bar
      .attr("height", (d) => y(0) - y(d.value)) // Height based on the score
      .attr("fill", (d) => color(d.key)); // Color based on the metric

    // Legend for all metrics (precision, recall, f1_score, accuracy)
    const legendData = [
      { label: "Precision", color: "#66c2a5" },
      { label: "Recall", color: "#fc8d62" },
      { label: "F1 Score", color: "#8da0cb" },
      { label: "Accuracy", color: "#b3b3b3" },
    ];

    const legend = svgElement
      .append("g")
      .attr("transform", `translate(${width - margin.right - 5}, 20)`); // Position the legend

    // Create colored rectangles for the legend
    const legendItems = legend
      .selectAll(".legend")
      .data(legendData)
      .enter()
      .append("g")
      .attr("class", "legend")
      .attr("transform", (d, i) => `translate(0, ${i * 20})`);

    legendItems
      .append("rect")
      .attr("width", 18)
      .attr("height", 18)
      .attr("fill", (d) => d.color);

    // Create text for legend labels
    legendItems
      .append("text")
      .attr("x", 24)
      .attr("y", 9)
      .attr("dy", ".35em") // Vertically center the text
      .style("font-size", "12px")
      .style("fill", "black")
      .text((d) => d.label);
  };

  async function getData() {
    const data = await api.getResults(projectId); // Your API call
    if (data && data.step && data.step !== null) {
      updateChartData(data);
      steps_training.push(data.step);  // Add the step label
      createChart(); // Re-create the chart with updated data
    }
  }

  let interval;

  onMount(() => {
    getData();
    interval = setInterval(() => {
      getData();
    }, 60000);
  });

  onDestroy(() => {
    clearInterval(interval);
  });

  async function interference() {
    try {
      responseMessage = await api.stopTraining({ projectId: projectId, labeling: ""});
    } catch (error) {
      responseMessage = `Error stopping model training: ${error.message}`;
    }

    // console.log("finish")
    // socket.emit("stop_training", { projectId: projectId, labeling: ""});
  }

  async function startTraining(){
    try {
      responseMessage = await api.startTraining({ projectId: projectId, labeling: ""});
    } catch (error) {
      responseMessage = `Error starting model training: ${error.message}`;
    }

    // console.log("starrt")
    // socket.emit("start training", { projectId: projectId , labeling: ""});
  }

  async function restartTraining() {
    try {
      responseMessage = await api.restartTraining({ projectId: projectId,  labeling: "file"});
    } catch (error) {
      responseMessage = `Error restarting model training: ${error.message}`;
    }

    // console.log("restart")
    // socket.emit("start retrain", { projectId: projectId , labeling: "file"});
  }

  export let location: Location;
    $: {
      // console.log(location);
      // this block is reactively triggered whenever the location variable (which contains the URL) changes
      startTraining();
    }
</script>

<div class="container-fluid px-5">
  <h1>LTS</h1>
  <h3>Current Project ID: {projectId}</h3>
  <!-- Button to start training -->
  <!-- <button
    class="btn btn-success"
    on:click={startTraining}
    disabled={isTrainingComplete}
  >
    Start Training
  </button> -->
  <svg id="chart"></svg>

  <!-- {#if isTrainingComplete}
      <p><strong>Training is complete!</strong></p>
    {/if} -->
  <!-- Button to check interference (or any API-related logic) -->
  <button
    class="btn danger"
    on:click={() => { interference; navigate("/search/random?q="); }}
    disabled={isTrainingComplete}
  >
    Stop and Fix Labels
  </button>
  <button
    class="btn btn-success"
    on:click={restartTraining}
    disabled={isTrainingComplete}
  >
    Restart Training
  </button>
</div>
<!-- <style>
  .chart-container {
      width: 100%;
      height: 400px;
    }
  .danger {background-color: #f44336;}
  .container {
    padding: 20px;
    max-width: 800px;
    margin: 0 auto;
  }

  .btn {
    margin-top: 10px;
    padding: 10px 20px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
  }

  .btn-danger {
    background-color: #d9534f;
  }

  .cards-container {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    margin-top: 20px;
  }

  .card {
    background-color: #f9f9f9;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 300px;
    transition: all 0.3s ease;
  }

  .card h3 {
    margin-bottom: 10px;
  }

  .progress-bar {
    height: 5px;
    background-color: #ccc;
    border-radius: 5px;
    margin-bottom: 15px;
  }

  .metrics {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .metric {
    display: flex;
    justify-content: space-between;
  }

  .metric label {
    font-weight: bold;
  }

  .metric span {
    padding: 5px;
    border-radius: 5px;
  }

  .green {
    color: green;
    background-color: #d4edda;
  }

  .orange {
    color: orange;
    background-color: #ffeeba;
  }

  .red {
    color: red;
    background-color: #f8d7da;
  }
</style> -->

<style>
  .danger {
    background-color: #f44336;
  }
  h1{
    color: #636363
  }
  h3{
    color: #636363
  }
</style>
