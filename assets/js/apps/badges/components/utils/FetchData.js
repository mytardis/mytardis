import 'core-js/stable';
import 'regenerator-runtime/runtime';

async function fetchExperimentData(experimentID) {
  const response = await fetch(`/api/v1/experiment/${experimentID}/?format=json`);
  return await response.json();
}
async function fetchDatasetData(datasetId) {
  const response = await fetch(`/api/v1/dataset/${datasetId}?format=json`);
  return await response.json();
}

async function fetchHSMDatasetData(datasetId) {
  const response = await fetch(`/api/v1/hsm_dataset/${datasetId}/count/?format=json`);
  return await response.json();
}

async function fetchProjectData(projectId) {
  const response = await fetch(`/api/v1/project/${projectId}/?format=json`);
  return await response.json();
}

export { fetchExperimentData, fetchDatasetData, fetchHSMDatasetData , fetchProjectData};
