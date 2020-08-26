import 'core-js/stable';
import 'regenerator-runtime/runtime';
import Cookies from 'js-cookie';

const fetchDatasetsForExperiment = async (experimentID) => {
  const response = await fetch(`/ajax/json/experiment/${experimentID}/dataset/`);
  return response.json();
};

const shareDataset = async (data, experimentID, datasetID) => {
  const response = await fetch(`/ajax/json/experiment/${experimentID}/dataset/${datasetID}`,
    {
      body: data,
      method: 'PUT',
      headers: {
        Accept: 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken'),
      },
    });
  return response.json();
};
const fetchExperimentList = async () => {
  const response = await fetch('/ajax/json/experiment_list/');
  return response.json();
};

const fetchExperimentPermissions = async (experimentID) => {
  const response = await fetch(`/ajax/json/experiment/${experimentID}/get_experiment_permissions`);
  return response.json();
};
export {
  fetchDatasetsForExperiment,
  shareDataset,
  fetchExperimentList,
  fetchExperimentPermissions,
};
