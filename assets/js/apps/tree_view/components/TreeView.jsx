import React, { Fragment, useEffect, useState } from 'react';

import { decorators, Treebeard } from 'react-treebeard';

import PropTypes from 'prop-types';
import styles from './custom-theme';
import Header from './Header';
import Container from './Container';
import Loading from './Loading';
import * as filters from './Filter';
import 'regenerator-runtime/runtime';
import { TreeDownloadButton, TreeRecallButton, TreeSelectButton } from './Download';
import { DownloadArchive, FetchFilesInDir, FetchChildDirs } from './Utils';
import Spinner from '../../badges/components/utils/Spinner';
import { fetchHSMDatasetData } from '../../badges/components/utils/FetchData';


const TreeView = ({ datasetId, modified, hsmEnabled }) => {
  const [cursor, setCursor] = useState(false);
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCount, setSelectedCount] = useState(0);
  const [isAllSelected, setIsAllSelected] = useState(false);
  const [recallButtonText, setRecallButtonText] = useState('Request Dataset Recall');
  const [recallToolTip, setRecallToolTip] = useState('An email will be sent to admin, and you will be '
      + 'notified when dataset is available to download');
  const [recallButtonStatus, setRecallButtonStatus] = useState('all');
  const [showRecallDatasetButton, setShowRecallDatasetButton] = useState(false);
  const fetchBaseDirs = (pageNum, resetData) => {
    fetch(`/api/v1/dataset/${datasetId}/root-dir-nodes/?page=${pageNum}`, {
      method: 'get',
      headers: {
        'Accept': 'application/json', // eslint-disable-line quote-props
        'Content-Type': 'application/json',
      },
    }).then(responseJson => (responseJson.json()))
      .then((response) => {
        setIsLoading(false);
        if (resetData) {
          const lastElem = [...response].pop();
          if (!lastElem.next_page) {
            setData(response.pop());
          }
          setData(response);
        } else {
          // remove load more button
          data.pop();
          const lastElem = [...response].pop();
          // if no more pages to load
          if (!lastElem.next_page) {
            response.pop();
            setData([...data, ...response]);
          } else {
            setData([...data, ...response]);
          }
        }
      });
  };
  const onSelect = (node) => {
    if (node.next_page) {
      fetchBaseDirs(node.next_page_num);
    }
    node.toggled = !node.toggled;
    if (node.selected) {
      // deselect all child nodes
      // if this is a folder and has child nodes
      if (node.children && node.children.length) {
        node.selected = false;
        node.children.forEach((childNode) => {
          childNode.selected = false;
        });
      } else {
        node.selected = false;
        setSelectedCount(selectedCount - 1);
      }
    } else {
      // node.selected = true;
      // if this is a folder with no child
      if (node.children && !node.children.length) {
        // add this node to selecteNode list
        node.selected = true;
      }
      // if this is a folder with child
      if (node.children && node.children.length) {
        node.selected = true;
        node.children.forEach((childNode) => {
          if (childNode.is_online) {
            childNode.selected = true;
          }
        });
      }
      // if this is a leaf node
      if (!node.children && node.is_online) {
        node.selected = true;
      } else {
        // node.selected = true;
      }
    }
    // set selected count
    // set count
    let count = 0;
    data.forEach((item) => {
      const selectedItemCount = filters.countSelection(item, 0);
      count += selectedItemCount;
    });
    setSelectedCount(count);
  };
  useEffect(() => {
    fetchBaseDirs(0);
    if (hsmEnabled) {
      fetchHSMDatasetData(datasetId).then((value) => {
        if (value.online_files < value.total_files) {
          setShowRecallDatasetButton(true);
        }
      });
    }
  }, [datasetId, modified]);
  const onToggle = (node, toggled) => {
    // toggled = !toggled;
    // fetch children:
    // console.log(`on toggle ${node.name}`);
    if (toggled && node.children && node.children.length === 0) {
      // show loading
      node.loading = true;
      FetchChildDirs(datasetId, node.path).then((childNodes) => {
        node.children = childNodes;
        node.toggled = true;
        if (node.selected) {
          let childCount = 0;
          node.children.forEach((childNode) => {
            // do not select offline nodes
            if (node.is_online || node.children.length > 0) {
              childNode.toggled = true;
              onSelect(childNode);
              childCount += 1;
            }
          });
          setSelectedCount(selectedCount + childCount);
        }
        setData(Object.assign([], data));
      }).then(() => { node.loading = false; setData(Object.assign([], data)); });
    }
    if (cursor) {
      cursor.active = false;
    }
    node.active = true;
    if (node.children) {
      node.toggled = toggled;
    }
    setCursor(node);
    setData(Object.assign([], data));
  };
  const onFilterMouseUp = ({ target: { value } }) => {
    const filter = value.trim();
    if (!filter) {
      // set initial tree state:
      fetchBaseDirs(0, true);
      // set count to 0
      setSelectedCount(0);
    } else {
      const filteredData = [];
      // if last elem id load more button remove this
      const lastElem = [...data].pop();
      if (lastElem.next_page) {
        data.pop();
      }
      data.forEach((item) => {
        let filtered = filters.filterTree(item, filter);
        filtered = filters.expandFilteredNodes(filtered, filter);
        if (!(Object.keys(filtered).length === 0 && filtered.constructor === Object)) {
          filteredData.push(filtered);
        }
      });
      setData(filteredData);
    }
  };

  const downloadSelected = (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    let selectedData = [];
    // get selected files and folders
    data.forEach((item) => {
      const selected = filters.findSelected(item, []);
      selectedData = [...selectedData, ...selected];
    });
    // if folder is selected, get array of promises
    // This will resolve to a list of ids for each folder
    let selectedFileIds = [];
    function getFilesFromDir() {
      const promises = [];
      for (let i = 0; i < selectedData.length; i += 1) {
        if (!Array.isArray(selectedData[i])) {
          if (!selectedData[i].id) {
            const encodedDir = encodeURIComponent(selectedData[i].path);
            promises.push(FetchFilesInDir(datasetId, encodedDir));
          } else {
            selectedFileIds = [...selectedFileIds, selectedData[i].id.toString()];
          }
        }
      }
      return Promise.all(promises);
    }
    getFilesFromDir().then((responses) => {
      responses.forEach((resp) => {
        selectedFileIds = [...selectedFileIds, ...resp];
      });
      return selectedFileIds;
    }).then((selectedIds) => {
      selectedIds.forEach((id) => {
        formData.append('datafile', id.toString());
      });
      DownloadArchive(formData);
    });
  };
  const toggleSelection = (event) => {
    event.preventDefault();
    // if count < 1 select all else select None
    const selectedData = [];
    if (!isAllSelected) {
      data.forEach((item) => {
        const selectedNodes = filters.toggleSelection(item, true);
        selectedData.push(selectedNodes);
      });
    } else {
      data.forEach((item) => {
        const selectedNodes = filters.toggleSelection(item, false);
        selectedData.push(selectedNodes);
      });
    }
    // set data
    setData(selectedData);
    // set all selected to true
    setIsAllSelected(!isAllSelected);
    // set count
    let count = 0;
    selectedData.forEach((item) => {
      const selectedItemCount = filters.countSelection(item, 0);
      count += selectedItemCount;
    });
    setSelectedCount(count);
  };
  const recallDataset = (event) => {
    event.preventDefault();
    fetch(`/api/v1/hsm_dataset/${datasetId}/recall/`, {
      method: 'get',
      headers: {
        'Accept': 'application/json', // eslint-disable-line quote-props
        'Content-Type': 'application/json',
      },
    }).then((response) => {
      if (response.ok) {
        setRecallButtonText('Recall Requested');
        setRecallToolTip('Recall request sent. You will receive an email'
            + ' once this dataset is ready for download');
        setRecallButtonStatus('none');
      } else {
        throw new Error('Something went wrong');
      }
    });
  };
  return (
    <Fragment>
      <div>
        <div style={{ float: 'left' }}>
          <TreeDownloadButton
            count={selectedCount}
            onClick={downloadSelected}
          />
        </div>
        <div>
          <TreeSelectButton
            count={selectedCount}
            onClick={toggleSelection}
            buttonText={isAllSelected ? 'Select None' : 'Select All'}
          />
          {hsmEnabled && showRecallDatasetButton
            ? (
              <TreeRecallButton
                buttonText={recallButtonText}
                onClick={recallDataset}
                disabled={recallButtonStatus}
                recallTooltip={recallToolTip}
              />
            ) : ''
          }
        </div>
      </div>
      <div style={styles}>
        <div className="input-group">
          <span className="input-group-text">
            <i className="fa fa-search" />
          </span>
          <input
            name="search-input"
            className="form-control"
            onKeyUp={onFilterMouseUp}
            placeholder="Search the tree..."
            type="text"
          />
        </div>
      </div>
      <div className="p-1" style={styles}>
        { isLoading ? (
          <Fragment>
            <span style={{ opacity: 0.5 }}>
              Rendering Tree View..
              <Spinner />
            </span>
          </Fragment>
        )
          : (
            <Treebeard
              data={data}
              style={styles}
              onToggle={onToggle}
              onSelect={onSelect}
              decorators={{
                ...decorators, Header, Container, Loading, hsmEnabled,
              }}
            />
          )
        }

      </div>
    </Fragment>
  );
};

TreeView.propTypes = {
  datasetId: PropTypes.string.isRequired,
  modified: PropTypes.string,
  hsmEnabled: PropTypes.bool,
};

TreeView.defaultProps = {
  modified: '',
  hsmEnabled: false,
};

export default TreeView;
