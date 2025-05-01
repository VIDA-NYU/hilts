const API_URL = "/api/v1";

export interface Hits {
  total: number;
  hits: Hit[];
}

export type prompt = "";

export type LabelType = "relevant" | "animal" | "description" | "keywords";

export interface Hit {
  _distance: number;
  image_path: string;
  title: string;
  metadata?: string;
  animal?: string;
  labels_types_dict: { [key: string]: LabelType };
}

export interface StartTrainingResponse {
  message: string;
}

export async function keywordSearch(
  queryStr: string,
  limit: number,
  excludeLabeled: boolean
): Promise<Hits> {
  const response = await fetchJSON<Hits>("/keyword_search", {
    q: queryStr,
    exclude_labeled: excludeLabeled,
    limit: limit.toString(),
  }).catch((e) => {
    console.error(e);
    throw new Error("Failed to retrieve keyword search results.", { cause: e });
  });
  return response;
}

export async function similarSearch(
  imagePath: string,
  limit: number,
  excludeLabeled: boolean
): Promise<Hits> {
  const response = await fetchJSON<Hits>("/image_search", {
    q: imagePath,
    exclude_labeled: excludeLabeled,
    limit: limit.toString(),
  }).catch((e) => {
    console.error(e);
    throw new Error("Failed to search for similar images.", { cause: e });
  });
  return response;
}

export async function SellerSearch(
  queryStr: string,
  limit: number,
  excludeLabeled: boolean
): Promise<Hits> {
  const response = await fetchJSON<Hits>("/seller_search", {
    q: queryStr,
    exclude_labeled: excludeLabeled,
    limit: limit.toString(),
  }).catch((e) => {
    console.error(e);
    throw new Error("Failed to retrieve seller search results.", { cause: e });
  });
  return response;
}

export async function random(limit: number): Promise<Hits> {
  const response = await fetchJSON<Hits>("/random", {
    limit: limit.toString(),
  }).catch((e) => {
    console.error(e);
    throw new Error("Failed to retrieve random search results.", { cause: e });
  });
  return response;
}

export async function randomHILTS(limit: number, projectId: string): Promise<Hits> {
  const response = await fetchJSON<Hits>("/random_hilts", {
    limit: limit.toString(),
    projectId: projectId,
  }).catch((e) => {
    console.error(e);
    throw new Error("Failed to retrieve random search results.", { cause: e });
  });
  return response;
}

export async function labeled(): Promise<Hits> {
  const response = await fetchJSON<Hits>("/labeled", {}).catch((e) => {
    console.error(e);
    throw new Error("Failed to retrieve labeled search results.", { cause: e });
  });
  return response;
}

interface LabelsResponse {
  labels: string[];
}

export async function loadLabels(table: string): Promise<LabelsResponse> {
  const response = await fetchJSON<LabelsResponse>("/labels", {
    table,
  }).catch((e) => {
    console.error(e);
    throw new Error("Failed to load labels.", { cause: e });
  });
  return response;
}

interface AddLabelResponse {
  success: boolean;
}

export async function addLabel(
  image_path: string,
  label: string,
  table: string
): Promise<AddLabelResponse> {
  const response = await fetchJSON<AddLabelResponse>("/add_label", {
    image_path,
    label,
    table,
  }).catch((e) => {
    console.error(e);
    throw new Error("Failed to save label.", { cause: e });
  });
  return response;
}

interface RemoveLabelResponse {
  success: boolean;
}

export async function removeLabel(
  image_path: string,
  label: string,
  table: string
): Promise<RemoveLabelResponse> {
  const response = await fetchJSON<RemoveLabelResponse>("/remove_label", {
    image_path,
    label,
    table,
  }).catch((e) => {
    console.error(e);
    throw new Error("Failed to remove label.", { cause: e });
  });
  return response;
}

export function downloadFile() {
  const url = `${API_URL}/download/binary_labeled_data`;
  const link = document.createElement("a");
  link.href = url;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export async function getData(projectId: string) {
    const url = `${API_URL}/get_data/${encodeURIComponent(projectId)}`;
    try {
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json"
      }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data
    } catch (error) {
      console.error('Fetching error:', error);
    }

  }

export async function getStatus() {
  const url = `${API_URL}/get_status/`; // ${encodeURIComponent(projectId)}?processId=${encodeURIComponent(processId)}`
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
    }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data
  } catch (error) {
    console.error('Fetching error:', error);
  }

}


export async function startTraining(
  argsDict: object
): Promise<StartTrainingResponse> {
  const url = `${API_URL}/start_training`;
  let responseMessage = "";
  console.log(url);
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({ argsDict }),
      headers: { "Content-Type": "application/json" },
    });
    if (response.ok) {
      const responseData = await response.json();
      responseMessage = "Model training started successfully";
      console.log("Model training started:", responseData);
      return {
        message: responseData.message,
      };
    } else {
      responseMessage = "Failed to start training";
      console.error("Failed to start training:", response.statusText);
      return { message: responseMessage};
    }
  } catch (error) {
    responseMessage = "Error start training";
    console.error("Error start training:", error);
    return { message: responseMessage};
  }
}

export async function restartTraining(
  argsDict: object
): Promise<StartTrainingResponse> {
  const url = `${API_URL}/restart_training`;
  let responseMessage = "";
  console.log(url);
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({ argsDict }),
      headers: { "Content-Type": "application/json" },
    });
    if (response.ok) {
      const responseData = await response.json();
      responseMessage = "Model training started successfully";
      console.log("Model training started:", responseData);
      return {
        message: responseData.message,
      };
    } else {
      responseMessage = "Failed to start training";
      console.error("Failed to start training:", response.statusText);
      return { message: responseMessage};
    }
  } catch (error) {
    responseMessage = "Error start training";
    console.error("Error start training:", error);
    return { message: responseMessage};
  }
}

export async function setLabelsDb(
  projectId: object
) {
  const url = `${API_URL}/set_db`;
  let responseMessage = "";

  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({ projectId: projectId }),
      headers: { "Content-Type": "application/json" },
    });
    if (response.ok) {
      const responseData = await response.json();
      responseMessage = "Project DB connected!";
    } else {
      responseMessage = "Failed to set db";
    }
  } catch (error) {
    responseMessage = "Error setting DB";
  }
  return responseMessage;
}

export async function connectLabelsDb(
  projectId: object
) {
  const url = `${API_URL}/connect_db`;
  let responseMessage = "";

  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({ projectId: projectId }),
      headers: { "Content-Type": "application/json" },
    });
    if (response.ok) {
      const responseData = await response.json();
      responseMessage = "Project DB connected!";
    } else {
      responseMessage = "Failed to set db";
    }
  } catch (error) {
    responseMessage = "Error setting DB";
  }
  return responseMessage;
}

export async function stopTraining(
  argsDict: object
) {
  const url = `${API_URL}/stop_training`;
  let responseMessage = "";
  console.log(url);

  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({ argsDict }),
      headers: { "Content-Type": "application/json" },
    });
    if (response.ok) {
      const responseData = await response.json();
      responseMessage = "Model training stopped successfully";
      console.log("Model training stopped:", responseData);
    } else {
      responseMessage = "Failed to stop training";
      console.error("Failed to stop training:", response.statusText);
    }
  } catch (error) {
    responseMessage = "Error stop training";
    console.error("Error stop training:", error);
  }
  return responseMessage;
}

export async function createLtsConfig(
  ProjectId: string,
  argsDict: object
) {
  const url = `${API_URL}/load/create_lts_config`;
  let responseMessage = "";
  console.log(url);

  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({ argsDict, ProjectId }),
      headers: { "Content-Type": "application/json" },
    });
    if (response.ok) {
      const responseData = await response.json();
      responseMessage = "Prompt loaded successfully";
      console.log("Prompt loaded successfully:", responseData);
    } else {
      responseMessage = "Failed to load Prompt";
      console.error("Failed to load Prompt:", response.statusText);
    }
  } catch (error) {
    responseMessage = "Error loading Prompt";
    console.error("Error loading Prompt:", error);
  }
  return responseMessage;
}

export async function loadCSV(csv: any, ProjectId: string, datatype: string) {
  const url = `${API_URL}/load/csv_data`;
  let responseMessage = "";

  try {
    // Create a Blob with the CSV data and specify the line endings
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });

    // Create FormData and append the Blob
    const formData = new FormData();
    formData.append("file", blob, "filename.csv");
    formData.append("projectId", ProjectId);
    formData.append("datatype", datatype);

    // Send the FormData using fetch
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      const responseData = await response.json();
      responseMessage = "CSV data loaded successfully";
      console.log("CSV data loaded successfully:", responseData);
    } else {
      responseMessage = "Failed to load CSV data";
      console.error("Failed to load CSV data:", response.statusText);
    }
  } catch (error) {
    responseMessage = "Error loading CSV data";
    console.error("Error loading CSV data:", error);
  }
  return responseMessage;
}

export interface LabelCountsResponse {
  counts: { [index: string]: number };
}

export function labelCounts(): Promise<LabelCountsResponse> {
  return fetchJSON<LabelCountsResponse>("/label_counts").catch((e) => {
    throw new Error("Failed to load label counts.", { cause: e });
  });
}

interface SaveCountsResponse {
  success: boolean;
  message: string;
}

export async function saveCounts(counts: { urlClickCount: number; }, project_id: string): Promise<SaveCountsResponse> {
  const url = `${API_URL}/save_counts`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ...counts, project_id }),
    });

    if (!response.ok) {
      throw new Error(`Failed to save counts. Status: ${response.status}`);
    }

    const responseData = await response.json();
    console.log("Counts saved successfully:", responseData);
    return responseData;
  } catch (error) {
    console.error("Error saving counts:", error);
    throw new Error("Error saving counts.");
  }
}

interface FetchInit {
  method: string;
  headers: { [index: string]: string };
  body?: string;
  credentials: "include";
}

export function fetchJSON<T>(
  url: string,
  args?: { [key: string]: any } | null,
  post?: object | null,
  external?: boolean
): Promise<T> {
  let argstring = "";
  if (args) {
    Object.keys(args).forEach((k, ix) => {
      const kk = encodeURIComponent(k);
      const ak = args[k] !== undefined ? encodeURIComponent(args[k]) : "";
      argstring += `${ix === 0 ? "?" : "&"}${kk}=${ak}`;
    });
  }
  const init: FetchInit = {
    method: post ? "POST" : "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  };

  if (post) {
    const content = JSON.stringify(post, null, "");
    init.headers["Content-Length"] = `${content.length}`;
    init.body = content;
  }
  const path = external ? url : `${API_URL}${url}${argstring}`;
  return fetch(path, init).then((data) => {
    if (data.status !== 200 || !data.ok) {
      throw new Error(`Server returned ${data.status}${data.ok ? " ok" : ""}`);
    }
    const ct = data.headers.get("content-type");
    if (ct && ct.includes("application/json")) {
      return data.json();
    }
    throw new TypeError("Response is not JSON encoded");
  });
}
