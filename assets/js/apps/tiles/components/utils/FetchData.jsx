import 'core-js/stable';
import 'regenerator-runtime/runtime';

const fetchDatasetsForExperiment = async (experimentID) => {
  const response = await fetch(`/ajax/json/experiment/${experimentID}/dataset/`);
  return response.json();
};

export default fetchDatasetsForExperiment;
