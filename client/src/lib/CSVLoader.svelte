<script>
  import * as api from "./Api";

  export let dataToCSV = [];
  let prevDataToCSV;

  export let allowedFileExtensions = ["csv"];

  let maxFileSize = 31457280;

  // Variables for form and responses
  let uploader;
  let writingText = ''; // Variable to bind the writing text
  let uploading = false; // Add a variable to track the uploading state
  let responseMessage = '';
  let responseMessagePrompt = '';
  let projectId = '';  // Variable to store the user's entered project ID

  async function uploadFile(event) {
    event.preventDefault();
    const file = uploader.files[0];
    uploading = true; // Set uploading state to true
    await onUpload(file);
    uploading = false; // Reset uploading state
  }

  async function onUpload(file) {
    try {
      responseMessage = await api.loadCSV(file, projectId);
    } catch (error) {
      responseMessage = `Error loading CSV data: ${error.message}`;
    }
  }

  async function uploadPrompt() {
    if (!writingText.trim()) {
      responseMessagePrompt = 'Please enter your prompt';
      return;
    }

    uploading = true; // Set uploading state to true
    try {
      responseMessagePrompt = await api.uploadPromptText(writingText, projectId); // Assuming the API has a method to handle text uploads
    } catch (error) {
      responseMessagePrompt = `Error uploading text: ${error.message}`;
    }
    uploading = false; // Reset uploading state
  }

  async function startLTSGenerator() {
    // Logic to start the LTS data generation (this is a placeholder, modify as needed)
    uploading = true;
    try {
      const response = await api.startLTSDataGeneration(projectId);  // Pass the entered project ID to the API
      responseMessage = 'LTS Data Generation Started';
      console.log(response);
    } catch (error) {
      responseMessage = `Error starting LTS data generation: ${error.message}`;
    }
    uploading = false;
  }

  // Reset project ID function
  function resetProjectId() {
    projectId = ''; // Clear the projectId variable
  }
</script>

<div class="container">
  <!-- Create Project ID Section -->
  <div class="py-4">
    <h1>Enter Project ID</h1>
    <div class="form-group">
      <label for="projectIdInput">Project ID</label>
      <input
        id="projectIdInput"
        bind:value={projectId}
        type="text"
        class="form-control"
        style="max-width:400px"
        placeholder="Enter your project ID"
      />
    </div>
    <div class="pt-2">
      <button class="btn btn-info" on:click={() => console.log("Project ID entered: ", projectId)}>
        <span class="fa fa-id-card mr-2" />
        Confirm Project ID
      </button>
      <!-- Reset Project ID Button -->
      <button class="btn btn-warning ml-2" on:click={resetProjectId}>
        <span class="fa fa-refresh mr-2" />
        Reset Project ID
      </button>
    </div>

    {#if projectId}
      <div class="mt-2">
        <p><strong>Your Project ID: {projectId}</strong></p>
      </div>
    {/if}
  </div>

  <!-- Load Data Section -->
  <div class="py-4">
    <h1>Load Data</h1>
    <p>Select a dataset file</p>
    <input bind:this={uploader} type="file" class="form-control" style="max-width:400px"/>
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

  <!-- Write and Upload Prompt Section -->
  <div class="py-4">
    <h2>Write and Upload Prompt</h2>
    <textarea bind:value={writingText} rows="5" class="form-control" style="max-width:400px" placeholder="Write your prompt here..."></textarea>
    <div class="pt-2">
      <button class="btn btn-primary" on:click={uploadPrompt}>
        <span class="fa fa-upload mr-2" />
        Upload Prompt
      </button>
    </div>

    <div class="mt-2">
      {#if uploading}
        <span>
          <i class="fa fa-spinner fa-spin" aria-hidden="true" />
          Uploading...
        </span>
      {:else if responseMessagePrompt}
        <div>
          <p>{responseMessagePrompt}</p>
        </div>
      {/if}
    </div>
  </div>

  <!-- Start LTS Data Generator Button -->
  <div class="py-4">
    <h2>Start LTS Data Generator</h2>
    <div class="pt-2">
      <button class="btn btn-success" on:click={startLTSGenerator}>
        <span class="fa fa-cogs mr-2" />
        Start LTS Generator
      </button>
    </div>

    <div class="mt-2">
      {#if uploading}
        <span>
          <i class="fa fa-spinner fa-spin" aria-hidden="true" />
          Starting LTS Data Generator...
        </span>
      {:else if responseMessage}
        <div>
          <p>{responseMessage}</p>
        </div>
      {/if}
    </div>
  </div>
</div>
