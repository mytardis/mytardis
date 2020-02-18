import React, { Fragment, useEffect, useState } from 'react';

import { decorators, Treebeard } from 'react-treebeard';

import PropTypes from 'prop-types';
import styles from './custom-theme';
import Header from './Header';
import Container from './Container';
import * as filters from './Filter';
import 'regenerator-runtime/runtime';
import { TreeDownloadButton } from './Download';
import { DownloadArchive, FetchFilesInDir } from './Utils';


const TreeView = ({ datasetId, modified }) => {
  const [cursor, setCursor] = useState(false);
  const [data, setData] = useState([]);
  const [selectedCount, setSelectedCount] = useState(0);
  const onSelect = (node) => {
    node.toggled = !node.toggled;
    if (node.selected) {
      // deselect all child nodes
      // if this is a folder and has child nodes
      if (node.children && node.children.length) {
        node.selected = false;
        let childCount = 1;
        node.children.forEach((childNode) => {
          childNode.selected = false;
          childCount += 1;
        });
        setSelectedCount(selectedCount - childCount);
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
        setSelectedCount(selectedCount + 1);
      }
      // if this is a folder with child
      if (node.children && node.children.length) {
        let childCount = 1;
        node.children.forEach((childNode) => {
          childNode.selected = true;
          childCount += 1;
        });
        setSelectedCount(selectedCount + childCount);
      } else {
        node.selected = true;
        setSelectedCount(selectedCount + 1);
      }
    }
  };
  const fetchBaseDirs = () => {
    fetch(`/api/v1/dataset/${datasetId}/root-dir-nodes/`, {
      method: 'get',
      headers: {
        'Accept': 'application/json', // eslint-disable-line quote-props
        'Content-Type': 'application/json',
      },
    }).then(responseJson => (responseJson.json()))
      .then((response) => { setData(response); });
  };
  const fetchChildDirs = (node, dirPath) => {
    const encodedDir = encodeURIComponent(dirPath);
    fetch(`/api/v1/dataset/${datasetId}/child-dir-nodes/?dir_path=${encodedDir}`, {
      method: 'get',
      headers: {
        'Accept': 'application/json', // eslint-disable-line quote-props
        'Content-Type': 'application/json',
      },
    }).then(response => (response.json()))
      .then((childNodes) => {
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
      });
    //
  };
  useEffect(() => {
    fetchBaseDirs('');
  }, [datasetId, modified]);
  const onToggle = (node, toggled) => {
    // fetch children:
    // console.log(`on toggle ${node.name}`);
    if (toggled && node.children && node.children.length === 0) {
      fetchChildDirs(node, node.path);
      return;
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
  return (
    <Fragment>
      <TreeDownloadButton
        count={selectedCount}
        onClick={downloadSelected}
      />
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
        <Treebeard
          data={data}
          style={styles}
          onToggle={onToggle}
          onSelect={onSelect}
          decorators={{ ...decorators, Header, Container }}
          animation={false}
        />
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
