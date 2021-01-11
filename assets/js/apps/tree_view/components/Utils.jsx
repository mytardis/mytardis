import 'core-js/stable';
import 'regenerator-runtime/runtime';
import Cookies from 'js-cookie';
import { saveAs } from 'file-saver';

async function FetchFilesInDir(datasetId, encodedDir) {
  const response = await fetch(`/api/v1/dataset/${datasetId}/child-dir-files/?dir_path=${encodedDir}`);
  return response.json();
}
async function FetchChildDirs(datasetId, dirPath) {
  const encodedDir = encodeURIComponent(dirPath);
  const response = await fetch(`/api/v1/dataset/${datasetId}/child-dir-nodes/?dir_path=${encodedDir}`, {
    method: 'get',
    headers: {
      'Accept': 'application/json', // eslint-disable-line quote-props
      'Content-Type': 'application/json',
    },
  });
  return response.json();
}
async function DownloadArchive(formData) {
  fetch('/download/datafiles/', {
    method: 'POST',
    body: formData,
    headers: {
      'X-CSRFToken': Cookies.get('csrftoken'),
    },
  }).then((resp) => {
    let fileName = '';
    const disposition = resp.headers.get('Content-Disposition');
    if (disposition && disposition.indexOf('attachment') !== -1) {
      const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
      const matches = filenameRegex.exec(disposition);
      if (matches != null && matches[1]) {
        fileName = matches[1].replace(/['"]/g, '');
      }
    }
    resp.blob().then((fileContent) => {
      saveAs(fileContent, fileName);
    });
  });
}

async function DownloadFile(dataFileId) {
  const response = await fetch(`/api/v1/dataset_file/${dataFileId}/download/`, {});
  return response;
}
export {
  FetchFilesInDir, DownloadArchive, FetchChildDirs, DownloadFile,
};
