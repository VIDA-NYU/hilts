<script>
  import * as api from "./Api";

  export let dataToCSV = [];
  let prevDataToCSV;

  export let allowedFileExtensions = ["csv"];

  let maxFileSize = 31457280;

  // this is the variable that the file gets bound to
  let uploader;
  let writingText = ''; // Variable to bind the writing text
  let uploading = false; // Add a variable to track the uploading state
  let responseMessage = '';
  let responseMessagePrompt = ''

  async function uploadFile(event) {
    event.preventDefault();
    const file = uploader.files[0];
    uploading = true; // Set uploading state to true
    await onUpload(file);
    uploading = false; // Reset uploading state
  }

  async function onUpload(file) {
    try {
      responseMessage = await api.loadCSV(file);
    } catch (error) {
      responseMessage = `Error loading CSV data: ${error.message}`;
    }
  }

  async function uploadPrompt() {
    if (!writingText.trim()) {
      responseMessagePrompt = 'Please enter your nada';
      return;
    }

    uploading = true; // Set uploading state to true
    try {
      responseMessagePrompt = await api.uploadText(writingText); // Assuming the API has a method to handle text uploads
    } catch (error) {
      responseMessagePrompt = `Error uploading text: ${error.message}`;
    }
    uploading = false; // Reset uploading state
  }
</script>

<div class="container">
  <div class="py-4">
    <h1>Load Seeds</h1>
    <p>Select a txt file</p>
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

  <!-- New Textarea Box for Writing -->
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
</div>
