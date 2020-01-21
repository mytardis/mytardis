import "core-js/stable";
import "regenerator-runtime/runtime";

async function fetchExperimentData (experimentID) {
  const response = await fetch("/api/v1/experiment/"+experimentID+"/?format=json");
  return await response.json();
}

export default fetchExperimentData;
