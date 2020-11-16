import React, { Fragment, useEffect, useState } from 'react';

import { decorators, Treebeard } from 'react-treebeard';

import PropTypes from 'prop-types';
import styles from './custom-theme';
import Header from './Header';
import Container from './Container';
import Loading from './Loading';
import * as filters from './Filter';
import 'regenerator-runtime/runtime';
import { TreeDownloadButton, TreeSelectButton } from './Download';
import { DownloadArchive, FetchFilesInDir, FetchChildDirs } from './Utils';
import Spinner from '../../badges/components/utils/Spinner';


const TreeView = ({ datasetId, modified }) => {
  const [cursor, setCursor] = useState(false);
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCount, setSelectedCount] = useState(0);
  const [isAllSelected, setIsAllSelected] = useState(false);
  const onSelect = (node) => {
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
      node.selected = true;
      // if this is a folder with no child
      if (node.children && !node.children.length) {
        // add this node to selecteNode list
        node.selected = true;
      }
      // if this is a folder with child
      if (node.children && node.children.length) {
        node.children.forEach((childNode) => {
          childNode.selected = true;
        });
      } else {
        node.selected = true;
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
  const fetchBaseDirs = () => {
    fetch(`/api/v1/dataset/${datasetId}/root-dir-nodes/`, {
      method: 'get',
      headers: {
        'Accept': 'application/json', // eslint-disable-line quote-props
        'Content-Type': 'application/json',
      },
    }).then(responseJson => (responseJson.json()))
      .then((response) => {
        setIsLoading(false);
        setData(response);
      });
  };
  useEffect(() => {
    fetchBaseDirs('');
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
            childNode.toggled = true;
            onSelect(childNode);
            childCount += 1;
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
      fetchBaseDirs('');
      // set count to 0
      setSelectedCount(0);
    }
    const filteredData = [];
    data.forEach((item) => {
      let filtered = filters.filterTree(item, filter);
      filtered = filters.expandFilteredNodes(filtered, filter);
      filteredData.push(filtered);
    });

    setData(filteredData);
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
                ...decorators, Header, Container, Loading,
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
};

TreeView.defaultProps = {
  modified: '',
};

export default TreeView;
