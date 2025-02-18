<script>
  import * as api from "./Api";
  import Modal from "./Modal.svelte";
  import { projectName } from "./stores";
  export let dataToCSV = [];
  import { navigate } from "svelte-routing";


  export let allowedFileExtensions = ["csv"];

  let maxFileSize = 31457280;

  // Variables for form and responses
  let uploader;
  let writingText = ""; // Variable to bind the writing text
  let uploading = false; // Add a variable to track the uploading state
  let saving = false;
  let responseMessage = "";
  let responseMessagePrompt = "";
  let responseMessageSave = "";

  // LTS Generator parameters (added for the modal)
  let task_prompt = ""
  let sampling = "thompson";
  let sample_size = 100;
  let model_finetune = "bert-base-uncased";
  let labeling = "GPT";
  let metric = "f1";
  let validation_size = 200;
  let cluster_size = 5;
  let budget = "trainingSize";
  let baseline = 0;
  let bugetValue = 1000;
  let cluster = "lda"
  let projectId = "";

  projectName.subscribe((name) => {
    projectId = name;
  });

  let showModal = false; // Reactive variable to control modal visibility
  let argsDict = {};

  // // Function to update argsDict with selected option and custom value
  function updateArgs() {
    const variables = [
    "task_prompt",
    "sampling",
    "sample_size",
    "model_finetune",
    "labeling",
    "metric",
    "validation_size",
    "cluster_size",
    "budget",
    "baseline",
    "bugetValue",
    "cluster"
  ];

  // Loop through the array of variable names
  variables.forEach(variable => {
    // Use eval to get the value of the variable by its name
    argsDict[variable] = eval(variable);
  });

  console.log(argsDict);
  }

  // Handle file upload
  async function uploadFile(event) {
    event.preventDefault();
    const file = uploader.files[0];
    uploading = true; // Set uploading state to true
    await onUpload(file);
    uploading = false; // Reset uploading state
  }

  // Handle the file upload process
  async function onUpload(file) {
    try {
      responseMessage = await api.loadCSV(file, projectId);
    } catch (error) {
      responseMessage = `Error loading CSV data: ${error.message}`;
    }
  }

  // Start the LTS data generation
  async function startLTSGenerator() {
    saving = true;
    try {
      const response = await api.startLTSDataGeneration(projectId, argsDict); // Pass the entered project ID and argsDict to the API
      responseMessageSave = "Project Saved!";
      console.log(response);
    } catch (error) {
      responseMessageSave = `Error starting LTS data generation: ${error.message}`;
    }
    saving = false;
  }

  // Reset project ID function
  function resetProjectId() {
    projectId = ""; // Clear the projectId variable
    projectName.update(() => {
      return "";
    });
  }

  function confirmName(new_name) {
    projectName.update((projectId) => {
      projectId = new_name;
      return projectId;
    });
    return projectId;
  }


</script>
<div class="container-fluid px-5">
  <!-- Create Project ID Section -->
  <div class="py-4">
    <!-- <h1 class="">Enter Project Name</h1> -->
    <div class="form-group">
      <label for="projectIdInput">Project Name</label>
      <input
        id="projectIdInput"
        bind:value={projectId}
        type="text"
        class="form-control"
        style="max-width:400px"
        placeholder="Enter your project name"
      />
    </div>
    <div class="pt-2">
      <button
        class="btn btn-info"
        on:click={() => confirmName(projectId)}
      >
        <span class="fa fa-id-card mr-2" />
        Confirm Project Name
      </button>
      <!-- Reset Project ID Button -->
      <button class="btn btn-warning ml-2" on:click={resetProjectId}>
        <span class="fa fa-refresh mr-2" />
        Reset Project
      </button>
    </div>
    <!-- </div> -->

    {#if projectId}
      <div class="mt-2">
        <p><strong>Project Name: {projectId}</strong></p>
      </div>
    {/if}
  </div>

  <!-- Load Data Section -->
  <div class="py-4">
    <!-- <h1>Load Data</h1> -->
    <label for="projectData">Select Dataset</label>
    <input
      id="projectData"
      bind:this={uploader}
      type="file"
      class="form-control"
      style="max-width:400px"
    />
    <div class="pt-2">
      <button class="btn btn-primary" on:click={uploadFile}>
        <span class="fa fa-download mr-2" />
        Load File
      </button>
    </div>

    <div class="mt-2">
      {#if uploading}
        <span>
          <i class="fa fa-spinner fa-spin" aria-hidden="true" />
          Loading...
        </span>
      {:else if responseMessage}
        <div>
          <p>{responseMessage}</p>
        </div>
      {/if}
    </div>
  </div>
  <!-- Start LTS Data Generator Button -->
  <div class="py-4">
    <label for="seetings">LTS Settings</label>
    <div class="pt-2">
      <button class="btn btn-secondary" on:click={() => (showModal = true)}>
        <!-- <span class="fa fa-cogs mr-2" /> -->
        Update Settings
      </button>
      <div class="pt-2">
        <button class="btn btn-success" on:click={() => navigate("/result?q=")}>
          <!-- startLTSGenerator -->
          <span class="fa fa-cogs mr-2" />
          Start Project
        </button>
      </div>

      <div class="mt-2">
        {#if saving}
          <span>
            <i class="fa fa-spinner fa-spin" aria-hidden="true" />
            Starting LTS Data Generator...
          </span>
        {:else if responseMessageSave}
          <div>
            <p>{responseMessageSave}</p>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>


<!-- Modal for LTS Data Generator -->
<Modal bind:showModal={showModal} closeBtnName="Save" onCloseAction={updateArgs}>
  <h2 slot="header">LTS Settings</h2>
  <div slot="body">
    <!-- Modal Content (LTS Parameters) -->
    <div class="row">
      <div class="col-12">
        <label for="prompt">Describe Task</label>
        <textarea
          bind:value={task_prompt}
          rows="5"
          class="form-control"
          placeholder="Write your prompt here..."
        ></textarea>
      </div>
      <div class="col-6">
        <label for="sampling">Sampling</label>
        <select id="sampling" class="form-control" bind:value={sampling}>
          <option value="random">Random</option>
          <option value="thompson">Thompson</option>
        </select>
      </div>
      <div class="col-6">
        <label for="sample_size">Sample Size</label>
        <input
          id="sample_size"
          type="number"
          class="form-control"
          bind:value={sample_size}
        />
      </div>

      <div class="col-6">
        <label for="model_finetune">Base Model</label>
        <!-- <select
          id="model_finetune"
          class="form-control"
          bind:value={model_finetune}
        > -->
        <textarea
          bind:value={model_finetune}
          rows="1"
          class="form-control"
          placeholder="HuggingFaceModel"
        ></textarea>
          <!-- <option value="bert-base-uncased">BERT</option>
          <option value="google-bert/bert-base-multilingual-cased"
            >multilingual bert</option
          > -->
        <!-- </select> -->
      </div>
      <div class="col-6">
        <label for="labeling">LLM Labeling</label>
        <select id="labeling" class="form-control" bind:value={labeling}>
          <option value="gpt">GPT</option>
          <option value="llama">LLAMA</option>
        </select>
      </div>
      <div class="col-6">
        <label for="metric">Evaluation Metric</label>
        <select id="metric" class="form-control" bind:value={metric}>
          <option value="accuracy">Accuracy</option>
          <option value="f1">F1 Score</option>
          <option value="recall">Recall</option>
          <option value="recall">Precision</option>
        </select>
      </div>
      <!-- <div class="col-6">
        <label for="baseline">Baseline Metric Value</label>
        <input
          id="baseline"
          type="number"
          class="form-control"
          bind:value={baseline}
        />
      </div> -->
      <div class="col-6">
        <label for="validation_size">Validation Data Size</label>
        <input
          id="validation_size"
          type="number"
          class="form-control"
          bind:value={validation_size}
        />
      </div>
      <div class="col-6">
        <label for="budget">Budget</label>
        <div class="d-flex">
          <select id="budget" class="form-control" bind:value={budget}>
            <option value="trainingSize">Minimum Training Size</option>
            <option value="metric">Metric</option>
          </select>
            <input
              id="custom-budget"
              type="number"
              class="form-control ml-2"
              bind:value={bugetValue}
              placeholder="Enter custom value"
            />
        </div>
      </div>
      <div class="col-6">
        <label for="cluster">Cluster</label>
        <select id="cluster" class="form-control" bind:value={cluster}>
        <option value="hdbscan">GMM</option>
        <option value="dbscan">AGGLO</option>
        <option value="kmeans">K-means</option>
        <option value="lda">LDA</option>
        </select>
      <div class="col-6">
        <label for="cluster_size">Number of Clusters</label>
        <input
          id="cluster_size"
          type="number"
          class="form-control"
          bind:value={cluster_size}
        />
      </div>
      </div>
    </div>
  </div>
</Modal>



<style>
  h1{
    color: #636363
  }
  .container {
    padding: 20px;
    max-width: 800px;
    margin: 0 auto;
  }
</style>
