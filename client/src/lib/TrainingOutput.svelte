<script lang="ts">
  import * as api from "./Api"; // Assuming the API logic is in this file
  import { onMount, onDestroy } from "svelte";
  import { io } from "socket.io-client";
  // import {createChart} from "./cards/trainingChart"
  import { projectName } from "./stores";
  import { navigate } from "svelte-routing";
  import * as d3 from "d3";

  // import { socket, initializeSocket } from './stores';
  // import { get } from 'svelte/store';
  let svg;
  const width = 600;
  const height = 400;
  const margin = { top: 20, right: 100, bottom: 40, left: 100 };

  let responseMessage;
  let previousLoop = 0;
  let status = {
    loop: 0,
    lts_status: false,
    lts_state: "",
    stats: {
      llm_labels: [],
      epochs: [],
      training_metrics: { step: [] },
    },
  };
  let chartData = {
    precision: [],
    recall: [],
    f1_score: [],
    accuracy: [],
  };

  let epochs = [];
  let isTraining = false;
  let isRunning = false;
  let projectId = "";
  const epochs_history = {
  update: function(updateData) {
    console.log("Updating epochs history:", updateData);
    }
  };

  projectName.subscribe((name) => {
    projectId = name;
  });

  // Initialize training state
  let disableBottom = false;
  let steps_training = [];
  let states = [];
  let currentStep = 0;
  let loop = 0;

  const updateChartData = (msg) => {
    if (msg && msg.precision && msg.recall && msg.f1_score && msg.accuracy) {
      msg.precision.forEach((value) => chartData.precision.push(value));
      msg.recall.forEach((value) => chartData.recall.push(value));
      msg.f1_score.forEach((value) => chartData.f1_score.push(value));
      msg.accuracy.forEach((value) => chartData.accuracy.push(value));
    }
  };
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

  async function getStatus() {
    status = await api.getStatus();
    console.log(status);
    if (status && Object.keys(status).length !== 0) {
      loop = status.loop;

      $: {
        if (loop !== previousLoop) {
          epochs_history.update({previousLoop:  epochs});
          // Reset everything for the new loop
          epochs = []; // Clear previous epochs
          states = []; // Clear previous states
          currentStep = 0; // Reset to first step
          console.log(`Training started or restarted for loop ${loop}!`);
        }
      }
      previousLoop = loop;

      isRunning = status.lts_status;
      console.log(isRunning);
      if (status.lts_state && !states.includes(status.lts_state)) {
        states = [...states, status.lts_state];
        changeStep();
        $: {
          if (status.lts_state == "Training") {
            isTraining = true;
          }
        }
      }
      $: {
        if (status.stats.epochs && status.stats.epochs.length > 0) {
          epochs = status.stats.epochs;
        }
        if (
          status &&
          steps_training !== status.stats.training_metrics["step"]
        ) {
          updateChartData(status["stats"]["training_metrics"]);
          steps_training = status["stats"]["training_metrics"]["step"];
          console.log(steps_training);
          createChart(); // Re-create the chart with updated data
        }
      }
    } else {
      isRunning = false;
      isTraining = false;
    }
  }

  let interval;

  const changeStep = () => {
    if (currentStep < states.length - 1) {
      currentStep += 1;
    }
  };

  onMount(() => {
    getStatus();
    interval = setInterval(() => {
      getStatus();
    }, 6000);
  });

  onDestroy(() => {
    clearInterval(interval);
  });

  async function interference() {
    try {
      responseMessage = await api.stopTraining({ projectId: projectId });
    } catch (error) {
      responseMessage = `Error stopping model training: ${error.message}`;
    }
    disableBottom = true;
    // navigate("/search/random?q=");
  }

  async function restartTraining() {
    try {
      responseMessage = await api.restartTraining({
        projectId: projectId,
        labeling: "file",
      });
    } catch (error) {
      responseMessage = `Error restarting model training: ${error.message}`;
    }
    disableBottom = true;
  }

  export let location: Location;
  $: {
  }
</script>

<div class="container-fluid">
  <div class="row m-2">
    <div class="col-2">
      {#if states.length > 0}
        <div class="stepper">
          {#each states as step, index (step)}
            <div
              class="step"
              class:selected={index === currentStep}
              class:completed={index < currentStep || !isRunning}
            >
              <div
                class="circle spinner-grow"
                class:spinner-grow={isRunning && index === currentStep}
                style="animation-duration: 2s;"
              >
                {index + 1}
              </div>
              <div class="step-name">{step}</div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="stepper">
          <div class="step" class:selected={true} class:completed={true}>
            <div
              class="circle {isRunning ? 'spinner-grow' : ''}"
              style="animation-duration: 2s;"
            >
              0
            </div>
            <div class="step-name">Starting</div>
          </div>
        </div>
      {/if}
    </div>
    <!-- First Column (smaller) -->
    {#if isTraining}
      <div class="col-6">
        <div class="card m-2">
          <div class="card-header bg-primary text-white">LTS: Training Logs</div>
          <div class="card-body">
            <div class="w-full xl:w-4/12 mt-6">
              <!-- Epoch Logs -->
              <div class="log-epoch">
                <div class="epoch">
                  <h5>Loop {loop}</h5>
                  {#if epochs.length > 0}
                    <table class="table table-bordered">
                      <thead>
                        <tr>
                          <th>Epoch</th>
                          <th>Accuracy</th>
                          <th>F1</th>
                          <th>Precision</th>
                          <th>Recall</th>
                          <th>Loss</th>
                        </tr>
                      </thead>
                      <tbody>
                        {#each epochs as epoch}
                          <tr>
                            <td>{epoch.epoch}</td>
                            <td>{epoch.eval_accuracy}</td>
                            <td>{epoch.eval_f1}</td>
                            <td>{epoch.eval_precision}</td>
                            <td>{epoch.eval_recall}</td>
                            <td>{epoch.eval_loss}</td>
                          </tr>
                        {/each}
                      </tbody>
                    </table>
                  {:else}
                    <p>Waiting for training results</p>
                  {/if}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-4">
        <button
          class="btn btn-primary"
          on:click={interference}
          disabled={disableBottom}
        >
          <span class="fa fa-pause" />
          Stop LTS
        </button>
        <button
          class="btn btn-primary"
          on:click={restartTraining}
          disabled={disableBottom}
        >
          <span class="fa fa-play" />
          Restart LTS
        </button>
        <svg id="chart"></svg>
      </div>
    {/if}
  </div>
</div>

<style>
  .danger {
    background-color: #f44336;
  }
  h1 {
    color: #636363;
  }
  h3 {
    color: #636363;
  }

  /* Basic styling */
  .container {
    width: 80%;
    margin: auto;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 20px;
  }

  .status {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 10px;
    background-color: #eef2f7;
    border-radius: 8px;
  }
  .epoch {
    display: flex;
    flex: 1;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding: 10px;
    background-color: #eef2f7;
    border-radius: 8px;
  }

  .log-epoch {
    margin-bottom: 20px;
  }

  .log-epoch ul {
    list-style-type: none;
    padding: 0;
  }

  .log-epoch li {
    background-color: #f9fafb;
    padding: 10px;
    border-radius: 4px;
    margin: 5px 0;
    font-size: 14px;
    word-wrap: break-word;
  }

  .stepper {
    display: flex;
    flex-direction: column;
    gap: 20px;
    width: 300px;
  }

  .step {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 10px;
    border-radius: 5px;
    /* background-color: #c94444; */
    transition: background-color 0.3s;
  }

  .circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #9f4ac3;
    color: white;
    font-weight: bold;
    font-size: 18px;
  }

  .circle.selected {
    background-color: #9f4ac3; /* Green for active step */
  }

  .step.completed .circle {
    background-color: #e4dede57; /* Gray for completed steps */
  }

  .step-name {
    font-size: 16px;
  }
</style>
