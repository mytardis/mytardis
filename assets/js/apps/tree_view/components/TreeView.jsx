import React, { useState, useEffect, Fragment } from 'react';

import { Treebeard, decorators } from 'react-treebeard';

import PropTypes from 'prop-types';
import { saveAs } from 'file-saver';
import Cookies from 'js-cookie';
import styles from './custom-theme';
import Header from './Header';
import Container from './Container';
import * as filters from './Filter';
import 'regenerator-runtime/runtime';
import { TreeDownloadButton } from './Download';


const TreeView = ({ datasetId, modified }) => {
  const [cursor, setCursor] = useState(false);
  const [data, setData] = useState([]);
  const [selectedCount, setSelectedCount] = useState(0);
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
          node.children.forEach((childNode) => {
            childNode.selected = true;
          });
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
  const onSelect = (node) => {
    node.toggled = !node.toggled;
    if (node.selected) {
      // select all child nodes
      node.selected = false;
      setSelectedCount(selectedCount - 1);
      node.children.forEach((childNode) => {
        childNode.selected = false;
        setSelectedCount(selectedCount - 1);
      });
    } else {
      node.selected = true;
      setSelectedCount(selectedCount + 1);
    }
  };
  const downloadSelected = (event) => {
    let fileName = '';
    event.preventDefault();
    const formData = new FormData(event.target);
    console.log(data);
    let selectedData = [];
    data.forEach((item) => {
      const selected = filters.findSelected(item, []);
      selectedData = [...selectedData, ...selected];
    });
    console.log(selectedData);
    selectedData.forEach((id) => {
      if (typeof id === 'number') {
        formData.append('datafile', id.toString());
      }
    });
    fetch('/download/datafiles/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': Cookies.get('csrftoken'),
      },
    }).then((resp) => {
      console.log(resp);
      const disposition = resp.headers.get('Content-Disposition');
      console.log(disposition);
      if (disposition && disposition.indexOf('attachment') !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        console.log(matches[1]);
        if (matches != null && matches[1]) {
          fileName = matches[1].replace(/['"]/g, '');
        }
      }
      resp.blob().then((fileContent) => {
        saveAs(fileContent, fileName);
      });
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
