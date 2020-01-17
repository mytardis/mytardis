export const fetchExperimentData = (experimentID) => {
  return fetch("/api/v1/experiment/"+experimentID+"/?format=json").then(
    response => response.json()
  )
};
