<script lang="ts">
  import * as api from "./Api"; // Assuming the API logic is in this file
  import { onMount, onDestroy } from "svelte";
  import { io } from "socket.io-client";
  import { createChart } from "./cards/trainingChart";
  import { projectName } from "./stores";
  import { navigate } from "svelte-routing";
  import * as d3 from "d3";

  let svg;
  const width = 600;
  const height = 400;
  const margin = { top: 20, right: 100, bottom: 40, left: 100 };

  let responseMessage;
  let previousLoop = 1;
  let isTrainingInProgress=false;
  let checkLabels=false;

  let status = {
    loop: 1,
    lts_status: false,
    lts_state: "",
    stats: {
      llm_labels: [],
      epochs: {},
      training_metrics: { step: [] },
      inference_progress: null
    },
  };

  let chartData =  {
    precision: [],
    recall: [],
    f1_score: [],
    accuracy: [],
  };

  let epochs: Record<string, any[]> = {};
  let isTraining = false;
  let isRunning = false;
  let projectId = "";

  projectName.subscribe((name) => {
    projectId = name;
  });

  // Initialize training state
  let disableBottom = true;
  let steps_training: [];
  let states: string[] = [];
  let currentStep = 0;
  let loop = 0;

  if (!states) {
    states = [];
  }

  const updateChartData = (msg) => {
    if (msg && msg.precision && msg.recall && msg.f1_score && msg.accuracy) {
      // Reset chartData to avoid indefinite growth
      chartData = {
        precision: [],
        recall: [],
        f1_score: [],
        accuracy: [],
      };

      // Keep only the last 5 values for each score list
      chartData.precision.push(...msg.precision.slice(-5));
      chartData.recall.push(...msg.recall.slice(-5));
      chartData.f1_score.push(...msg.f1_score.slice(-5));
      chartData.accuracy.push(...msg.accuracy.slice(-5));
    }
  };

  const formatNumber = (number) => {
  return number.toFixed(3); // Limits the number to 5 decimal places
  };

  // Add inference progress tracking
  let inferenceProgress = {
    totalChunks: 0,
    currentChunk: 0,
    totalRecords: 0,
    processedRecords: 0
  };

  async function getStatus() {
    status = await api.getStatus();
    console.log(status);
    if (status && Object.keys(status).length !== 0) {
      loop = status.loop;

      $: {
        if (loop !== previousLoop) {
          states = []; // Clear previous states
          currentStep = 0; // Reset to first step
          console.log(`Training started or restarted for loop ${loop}!`);
        }
      }
      previousLoop = loop;

      isRunning = status.lts_status;

      checkLabels = status.lts_state === "User Labeling";

      // Update inference progress if available
      if (status.stats.inference_progress) {
        inferenceProgress = status.stats.inference_progress;
      }

      if (status.lts_state && !states.includes(status.lts_state)) {
        states = [...states, status.lts_state];
        changeStep();
        $: {
          if (status.lts_state == "Training") {
            isTraining = true;
            disableBottom =false;
          }
        }
      }
      $: {
        if (Object.keys(status.stats.epochs).length > 0) {
          epochs = status.stats.epochs;
        }
        if (
          status &&
          steps_training !== status.stats.training_metrics["step"]
        ) {
          updateChartData(status["stats"]["training_metrics"]);
          steps_training = status["stats"]["training_metrics"]["step"];
          if (steps_training.length > 5){
            steps_training = steps_training.slice(-5)
          }
          createChart(chartData, steps_training);
        }
      }
    } else {
      isRunning = false;
      isTraining = false;
      isTrainingInProgress = false;
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

  // async function interference() {
  //   try {
  //     responseMessage = await api.stopTraining({ projectId: projectId });
  //   } catch (error) {
  //     responseMessage = `Error stopping model training: ${error.message}`;
  //   }
  //   disableBottom = true;
  //   isTrainingInProgress = true;
  // }

  export let location: Location;
  $: {
  }

</script>

<div class="container-fluid m-3">
  <div class="row">
    <div class="col-2">
      <div class="card">
        <div class="card-header bg-primary text-white">LTS Status:
            {isRunning ? "Running" : "Not running"}</div>
      </div>
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
              <div class="step-content">
                <div class="step-name">{step}</div>
                {#if step === "Cluster Inference" && status.stats.inference_progress}
                  <div class="inference-progress">
                    <div class="progress-bar">
                      <div class="progress-bar-fill" style="width: {Math.round((status.stats.inference_progress.processed_records / status.stats.inference_progress.total_records) * 100)}%"></div>
                    </div>
                    <div class="progress-text">
                      Chunk {status.stats.inference_progress.current_chunk}/{status.stats.inference_progress.total_chunks}
                    </div>
                  </div>
                {/if}
              </div>
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
            <div class="step-name">Waiting</div>
          </div>
        </div>
      {/if}
  </div>
  <div class="col-2">
    <button
        class="btn btn-outline-primary m-2"
        on:click={(() => navigate("/search/random?q="))}
        disabled={!checkLabels}
      >
      <span class="fa fa-tag" />
      Check Labels
    </button>
  </div>
    {#if isTraining || Object.entries(epochs).length > 0}
      <div class="col-4">
        <div class="card">
          <div class="card-header bg-primary text-white justify-content-between">LTS: Training Logs
            <!-- <button
              class="btn btn-light mb-2 m-2"
              on:click={interference}
              disabled={disableBottom}
            >
              <span class="fa fa-pause" />
              Stop LTS
            </button> -->
            <!-- {#if isTrainingInProgress}
            <span>
              <i class="fa fa-spinner fa-spin" aria-hidden="true"></i>
              Waiting for current training to finish...
            </span>
            {/if} -->
          </div>
          <!-- <div class="log-container"> -->
            <!-- <div class="log-epoch"> -->
              <div class="epoch">
                {#each Object.entries(epochs).reverse() as [loopNumber, epochsForLoop]}
                  <div class="row">
                    <h6>Training #{loopNumber}:</h6>
                    <table class="table table-striped table-primary">
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
                        {#each epochsForLoop.reverse() as epoch}
                          <tr>
                            <td>{epoch.epoch}</td>
                            <td>{formatNumber(epoch.eval_accuracy)}</td>
                            <td>{formatNumber(epoch.eval_f1)}</td>
                            <td>{formatNumber(epoch.eval_precision)}</td>
                            <td>{formatNumber(epoch.eval_recall)}</td>
                            <td>{formatNumber(epoch.eval_loss)}</td>
                          </tr>
                        {/each}
                      </tbody>
                    </table>
                  </div>
                {/each}
              </div>
            </div>
          </div>
        <!-- </div> -->
      <!-- </div> -->
      <div class="col-4">
        <div class="card">
          <div class="card-header bg-primary text-white justify-content-between align-items-center">Model Metrics</div>
        </div>
        <svg id="chart" style="width: 100%; height: 400px;"></svg>
      </div>
    {/if}
  </div>
</div>

<style>
  .epoch {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding: 10px;
    background-color: #eef2f7;
    border-radius: 8px;
  }

  .log-epoch {
    display: flex;
    flex-direction: column;
    margin-bottom: 20px;
  }

  .log-container {
    height: 400px; /* Set a fixed height for the logs container */
    overflow-y: auto; /* Enable vertical scrolling */
    overflow-x: hidden; /* Prevent horizontal scrolling */
    padding: 10px; /* Optional: Add padding for better spacing */
    background-color: #f9f9f9; /* Optional: Add a background color */
    border: 1px solid #ddd; /* Optional: Add a border */
    border-radius: 8px; /* Optional: Add rounded corners */
  }

  .table {
    width: 100%;
    table-layout: fixed;
    text-align: center;
  }

  .table th,
  .table td {
    white-space: nowrap; /* Prevent text wrapping */
  }

  .table {
    margin-top: 10px;
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
    background-color: #806e6e57; /* Gray for completed steps */
  }

  .step-name {
    font-size: 16px;
  }

  .card-body {
  padding: 0;
  overflow-x: auto;
}

.table {
  width: 100%;
  table-layout: fixed;
  text-align: center;
}

.table-bordered {
  border-collapse: collapse; /* Optional: Ensures borders are collapsed */
}
.fixed-card {
  height: 500px; /* Adjust this height value as needed */
  display: flex;
  flex-direction: column;
}

.progress {
  height: 25px;
  font-size: 14px;
  line-height: 25px;
}

.progress-bar {
  transition: width 0.3s ease;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 1;
}

.inference-progress {
  width: 100%;
  margin-top: 5px;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background-color: #e0e0e0;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 2px;
}

.progress-bar-fill {
  height: 100%;
  background-color: #9f4ac3;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #666;
}

</style>
