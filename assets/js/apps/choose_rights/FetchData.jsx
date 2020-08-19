const fetchModalData = async (experimentID) => {
  const response = await fetch(`/ajax/experiment/${experimentID}/rights`);
  return response.json();
};
const fetchLicenses = async (licenseType) => {
  const response = await fetch(`/ajax/license/list?public_access=${licenseType}`);
  return response.json();
};
export { fetchModalData, fetchLicenses };
